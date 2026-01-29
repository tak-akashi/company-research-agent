"""IRScraperService - IR資料取得の統合サービス."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from company_research_agent.clients.ir_scraper.base import BaseIRScraper
from company_research_agent.clients.ir_scraper.llm_explorer import LLMExplorer
from company_research_agent.clients.ir_scraper.template_loader import TemplateLoader
from company_research_agent.core.config import get_config
from company_research_agent.core.exceptions import (
    IRPageAccessError,
    IRTemplateNotFoundError,
)
from company_research_agent.prompts.ir_summary import CATEGORY_NAMES, IR_SUMMARY_PROMPT
from company_research_agent.schemas.ir_schemas import (
    ImpactPoint,
    IRDocument,
    IRSummary,
    IRSummaryResponse,
)

if TYPE_CHECKING:
    from company_research_agent.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class IRScraperService:
    """IR資料取得の統合サービス.

    テンプレート方式とLLM方式を統合し、フォールバック戦略を提供する。
    資料のダウンロード、要約生成、ファイル管理を行う。

    Example:
        >>> service = IRScraperService()
        >>> docs = await service.fetch_ir_documents("72030")
        >>> for doc in docs:
        ...     print(f"{doc.title}: {doc.summary.overview}")
    """

    def __init__(
        self,
        templates_dir: Path | None = None,
        data_dir: Path | None = None,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        """IRScraperServiceを初期化する.

        Args:
            templates_dir: テンプレートファイルのディレクトリ
            data_dir: データ保存ディレクトリ
            llm_provider: LLMプロバイダー
        """
        self._config = get_config()
        self._template_loader = TemplateLoader(templates_dir)
        self._llm_explorer = LLMExplorer(llm_provider)
        self._llm_provider = llm_provider

        if data_dir is None:
            self._data_dir = self._config.download.download_dir
        else:
            self._data_dir = data_dir

    def _get_provider(self) -> LLMProvider:
        """LLMプロバイダーを取得する."""
        if self._llm_provider is None:
            from company_research_agent.llm.factory import get_default_provider

            self._llm_provider = get_default_provider()
        return self._llm_provider

    async def fetch_ir_documents(
        self,
        sec_code: str,
        category: str | None = None,
        since: date | None = None,
        force: bool = False,
        with_summary: bool = True,
    ) -> list[IRDocument]:
        """登録企業のIR資料を取得する.

        テンプレート方式を優先し、失敗時はLLM方式にフォールバックする。

        Args:
            sec_code: 証券コード（5桁）
            category: 取得するカテゴリ（earnings|news|disclosures、省略時は全カテゴリ）
            since: 検索開始日（省略時はDEFAULT_SINCE_DAYS日前）
            force: Trueの場合、既存ファイルを上書き
            with_summary: Trueの場合、要約を生成

        Returns:
            取得したIR資料のリスト

        Raises:
            IRTemplateNotFoundError: テンプレートが見つからず、LLM方式でも取得できない場合
        """
        if since is None:
            since = date.today() - timedelta(days=self._config.ir_scraper.default_since_days)

        documents: list[IRDocument] = []

        async with BaseIRScraper() as scraper:
            # テンプレート方式を試行
            template = self._template_loader.load_template(sec_code)

            if template:
                try:
                    logger.info(f"Using template for {sec_code}: {template.company.name}")
                    documents = await self._template_loader.scrape_with_template(
                        scraper, template, category
                    )
                except IRPageAccessError as e:
                    logger.warning(f"Template scraping failed, falling back to LLM: {e}")
                    documents = []

                # テンプレート方式失敗時はテンプレートのbase_urlでLLM方式にフォールバック
                if not documents and template.ir_page.base_url:
                    logger.info(f"Falling back to LLM exploration for {sec_code}")
                    try:
                        documents = await self._llm_explorer.explore_ir_page(
                            scraper, template.ir_page.base_url
                        )
                    except Exception as e:
                        logger.warning(f"LLM exploration also failed: {e}")

            # テンプレートがない場合
            if not template:
                ir_url = await self._find_ir_page_for_company(scraper, sec_code)
                if ir_url:
                    documents = await self._llm_explorer.explore_ir_page(scraper, ir_url)
                else:
                    raise IRTemplateNotFoundError(
                        message="No template found and IR page could not be discovered",
                        sec_code=sec_code,
                    )

            # テンプレートはあるが資料が見つからない場合
            if template and not documents:
                base_url = template.ir_page.base_url
                raise IRTemplateNotFoundError(
                    message=f"Template found but no IR documents discovered from {base_url}",
                    sec_code=sec_code,
                )

            # 日付でフィルタリング
            documents = self._filter_by_date(documents, since)

            # URL重複を排除（同じURLは1つのカテゴリのみに）
            documents = self._deduplicate_by_url(documents)

            # タイトルに基づいてカテゴリを再分類
            documents = self._reclassify_by_title(documents)

            # 企業名を取得（テンプレートから、またはEDINETコードリストから）
            company_name: str | None = None
            if template:
                company_name = template.company.name

            # ダウンロードと要約
            for i, doc in enumerate(documents):
                is_pdf = doc.url.lower().endswith(".pdf")

                # HTMLページはダウンロードせず、LLMで要約
                if not is_pdf:
                    if with_summary:
                        try:
                            doc.summary = await self._summarize_html_page(scraper, doc)
                            logger.info(f"Summarized HTML page: {doc.title}")
                        except Exception as e:
                            logger.error(f"Failed to summarize HTML page {doc.title}: {e}")
                    documents[i] = doc
                    continue

                save_path = self._get_save_path(sec_code, doc, company_name)

                if self._should_skip_download(doc.url, save_path, force):
                    doc.file_path = save_path
                    doc.is_skipped = True
                    logger.debug(f"Skipped (already exists): {save_path}")
                else:
                    try:
                        doc.file_path = await scraper.download_pdf(doc.url, save_path, force=force)
                        logger.info(f"Downloaded: {doc.title}")
                    except Exception as e:
                        logger.error(f"Failed to download {doc.url}: {e}")
                        continue

                # 要約生成（新規ダウンロードのPDFのみ）
                if with_summary and doc.file_path and not doc.is_skipped:
                    try:
                        doc.summary = await self._summarize_document(doc)
                    except Exception as e:
                        logger.error(f"Failed to summarize {doc.title}: {e}")

                documents[i] = doc

        return documents

    async def explore_ir_page(
        self,
        url: str,
        since: date | None = None,
        force: bool = False,
        with_summary: bool = True,
    ) -> list[IRDocument]:
        """アドホックでIRページを探索する.

        Args:
            url: IRページのURL
            since: 検索開始日（省略時はDEFAULT_SINCE_DAYS日前）
            force: Trueの場合、既存ファイルを上書き
            with_summary: Trueの場合、要約を生成

        Returns:
            探索されたIR資料のリスト
        """
        if since is None:
            since = date.today() - timedelta(days=self._config.ir_scraper.default_since_days)

        async with BaseIRScraper() as scraper:
            documents = await self._llm_explorer.explore_ir_page(scraper, url)

            # 日付でフィルタリング
            documents = self._filter_by_date(documents, since)

            # URL重複を排除（同じURLは1つのカテゴリのみに）
            documents = self._deduplicate_by_url(documents)

            # タイトルに基づいてカテゴリを再分類
            documents = self._reclassify_by_title(documents)

            # URLからsec_code相当のディレクトリ名を生成
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain_parts = parsed.netloc.replace("www.", "").split(".")
            dir_name = domain_parts[0] if domain_parts else "unknown"

            # ダウンロードと要約
            for i, doc in enumerate(documents):
                is_pdf = doc.url.lower().endswith(".pdf")

                # HTMLページはダウンロードせず、LLMで要約
                if not is_pdf:
                    if with_summary:
                        try:
                            doc.summary = await self._summarize_html_page(scraper, doc)
                            logger.info(f"Summarized HTML page: {doc.title}")
                        except Exception as e:
                            logger.error(f"Failed to summarize HTML page {doc.title}: {e}")
                    documents[i] = doc
                    continue

                save_path = self._get_save_path(dir_name, doc)

                if self._should_skip_download(doc.url, save_path, force):
                    doc.file_path = save_path
                    doc.is_skipped = True
                else:
                    try:
                        doc.file_path = await scraper.download_pdf(doc.url, save_path, force=force)
                    except Exception as e:
                        logger.error(f"Failed to download {doc.url}: {e}")
                        continue

                # 要約生成（新規ダウンロードのPDFのみ）
                if with_summary and doc.file_path and not doc.is_skipped:
                    try:
                        doc.summary = await self._summarize_document(doc)
                    except Exception as e:
                        logger.error(f"Failed to summarize {doc.title}: {e}")

                documents[i] = doc

        return documents

    async def fetch_all_registered(
        self,
        category: str | None = None,
        since: date | None = None,
        force: bool = False,
    ) -> dict[str, list[IRDocument]]:
        """全登録企業のIR資料を取得する.

        Args:
            category: 取得するカテゴリ
            since: 検索開始日
            force: 既存ファイルを上書きするか

        Returns:
            証券コードをキーとしたIR資料のリストの辞書
        """
        results: dict[str, list[IRDocument]] = {}

        sec_codes = self._template_loader.list_templates()
        logger.info(f"Fetching IR documents for {len(sec_codes)} registered companies")

        for sec_code in sec_codes:
            try:
                docs = await self.fetch_ir_documents(
                    sec_code=sec_code,
                    category=category,
                    since=since,
                    force=force,
                )
                results[sec_code] = docs
                logger.info(f"Fetched {len(docs)} documents for {sec_code}")
            except Exception as e:
                logger.error(f"Failed to fetch documents for {sec_code}: {e}")
                results[sec_code] = []

        return results

    def _should_skip_download(self, url: str, save_path: Path, force: bool) -> bool:
        """ダウンロードをスキップすべきか判定する.

        Args:
            url: ダウンロードURL
            save_path: 保存先パス
            force: 強制上書きフラグ

        Returns:
            スキップすべき場合True
        """
        if force:
            return False
        return save_path.exists()

    def _deduplicate_by_url(self, documents: list[IRDocument]) -> list[IRDocument]:
        """URLの重複を排除する.

        同じURLが複数カテゴリに存在する場合、タイトルに基づいて
        最も適切なカテゴリを選択する。

        Args:
            documents: 重複を含む可能性のあるドキュメント

        Returns:
            重複を排除したドキュメント
        """
        # URLごとにドキュメントをグループ化
        by_url: dict[str, list[IRDocument]] = {}
        for doc in documents:
            if doc.url not in by_url:
                by_url[doc.url] = []
            by_url[doc.url].append(doc)

        # 各URLについて最適なカテゴリを選択
        result: list[IRDocument] = []
        for url, docs in by_url.items():
            if len(docs) == 1:
                result.append(docs[0])
            else:
                # タイトルに基づいてカテゴリを決定
                best_doc = self._select_best_category(docs)
                result.append(best_doc)
                logger.debug(
                    f"Deduplicated {url}: selected {best_doc.category} "
                    f"from {[d.category for d in docs]}"
                )

        return result

    def _reclassify_by_title(self, documents: list[IRDocument]) -> list[IRDocument]:
        """タイトルに基づいてカテゴリを再分類する.

        LLMの分類が間違っている場合に、タイトルのキーワードに基づいて
        正しいカテゴリに修正する。

        Args:
            documents: 分類済みのドキュメント

        Returns:
            再分類されたドキュメント
        """
        from dataclasses import replace

        result: list[IRDocument] = []

        for doc in documents:
            correct_category = self._determine_category_by_title(doc.title)

            if correct_category != doc.category:
                logger.debug(
                    f"Reclassified '{doc.title[:30]}...' from {doc.category} to {correct_category}"
                )
                # dataclassのreplaceでカテゴリを変更
                doc = replace(doc, category=correct_category)

            result.append(doc)

        return result

    def _determine_category_by_title(
        self, title: str
    ) -> Literal["earnings", "news", "disclosures"]:
        """タイトルからカテゴリを決定する.

        Args:
            title: ドキュメントのタイトル

        Returns:
            カテゴリ文字列（earnings/disclosures/news）
        """
        title_lower = title.lower()

        # disclosures（適時開示）を優先判定
        disclosure_keywords = [
            "自己株式",
            "業績予想",
            "配当予想",
            "修正",
            "異動",
            "提携",
            "子会社",
            "合併",
            "分割",
            "増資",
            "減資",
            "訴訟",
            "行政処分",
            "取得状況",
            "処分",
            "消却",
        ]
        for kw in disclosure_keywords:
            if kw in title_lower:
                return "disclosures"

        # earnings（決算関連）を判定
        earnings_keywords = [
            "決算",
            "業績",
            "四半期",
            "通期",
            "月次",
            "売上",
            "財務",
            "有価証券報告",
            "報告書",
            "ファクトシート",
            "ハイライト",
            "レポート",
            "quarterly",
            "annual",
            "financial",
        ]
        for kw in earnings_keywords:
            if kw in title_lower:
                return "earnings"

        # news（事業ニュース）を判定
        news_keywords = [
            "新製品",
            "新サービス",
            "発売",
            "開始",
            "受注",
            "契約",
            "発表",
            "リリース",
            "参入",
            "特許",
            "受賞",
            "認定",
            "launch",
            "release",
            "announce",
        ]
        for kw in news_keywords:
            if kw in title_lower:
                return "news"

        # デフォルトはdisclosures（IRお知らせ系が多いため）
        return "disclosures"

    def _select_best_category(self, docs: list[IRDocument]) -> IRDocument:
        """重複したドキュメントから最適なカテゴリを選択する.

        Args:
            docs: 同じURLを持つドキュメントのリスト

        Returns:
            最適なカテゴリを持つドキュメント
        """
        if not docs:
            raise ValueError("docs must not be empty")

        title = docs[0].title.lower()

        # タイトルに基づくカテゴリ判定ルール
        # disclosuresを優先すべきキーワード
        disclosure_keywords = [
            "自己株式",
            "業績予想",
            "配当予想",
            "修正",
            "異動",
            "提携",
            "子会社",
            "合併",
            "分割",
            "増資",
            "減資",
        ]
        # earningsを優先すべきキーワード
        earnings_keywords = [
            "決算",
            "業績",
            "四半期",
            "通期",
            "月次",
            "売上",
            "財務",
            "有価証券報告",
            "quarterly",
            "annual",
        ]
        # newsを優先すべきキーワード
        news_keywords = [
            "新製品",
            "新サービス",
            "発売",
            "開始",
            "受注",
            "発表",
            "リリース",
            "launch",
            "release",
        ]

        # カテゴリごとのスコアを計算
        scores = {"disclosures": 0, "earnings": 0, "news": 0}

        for kw in disclosure_keywords:
            if kw in title:
                scores["disclosures"] += 2

        for kw in earnings_keywords:
            if kw in title:
                scores["earnings"] += 2

        for kw in news_keywords:
            if kw in title:
                scores["news"] += 2

        # 最高スコアのカテゴリを持つドキュメントを返す
        best_category = max(scores, key=lambda k: scores[k])

        # そのカテゴリのドキュメントを探す
        for doc in docs:
            if doc.category == best_category:
                return doc

        # 見つからない場合は最初のドキュメントを返す
        return docs[0]

    def _filter_by_date(self, documents: list[IRDocument], since: date) -> list[IRDocument]:
        """公開日でフィルタリングする.

        公開日が不明なドキュメントは含める（除外しない）。

        Args:
            documents: フィルタリング対象のドキュメント
            since: 検索開始日

        Returns:
            フィルタリング後のドキュメント
        """
        return [
            doc for doc in documents if doc.published_date is None or doc.published_date >= since
        ]

    def _get_save_path(
        self, sec_code: str, doc: IRDocument, company_name: str | None = None
    ) -> Path:
        """保存先パスを生成する.

        Args:
            sec_code: 証券コード
            doc: IRDocument
            company_name: 企業名（省略時はsec_codeのみ使用）

        Returns:
            保存先パス（{base_dir}/{sec_code}_{company_name}/ir/{category}/{filename}）
        """
        from urllib.parse import unquote, urlparse

        from company_research_agent.core.download_path import sanitize_filename

        # URLからファイル名を取得
        parsed = urlparse(doc.url)
        filename = unquote(Path(parsed.path).name)

        # 不正なファイル名文字を置換
        filename = filename.replace("/", "_").replace("\\", "_")

        # フォルダ名: {sec_code}_{company_name} または {sec_code}
        if company_name:
            folder_name = f"{sec_code}_{sanitize_filename(company_name)}"
        else:
            folder_name = sec_code

        # パス構造: {base_dir}/{company_folder}/ir/{category}/{filename}
        return self._data_dir / folder_name / "ir" / doc.category / filename

    async def _summarize_document(self, doc: IRDocument) -> IRSummary:
        """IR資料を要約する.

        Args:
            doc: 要約対象のIRDocument

        Returns:
            要約結果
        """
        if doc.file_path is None:
            raise ValueError("file_path is required for summarization")

        # PDFを読み込み
        from company_research_agent.parsers.pdf_parser import PDFParser

        parser = PDFParser()
        parsed_result = parser.to_markdown(doc.file_path)
        content = parsed_result.text

        # 内容が長すぎる場合は切り詰め
        max_content_length = 30000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[以下省略...]"

        # プロンプトを作成
        category_name = CATEGORY_NAMES.get(doc.category, doc.category)
        published_date_str = (
            doc.published_date.strftime("%Y年%m月%d日") if doc.published_date else "不明"
        )

        prompt = IR_SUMMARY_PROMPT.format(
            title=doc.title,
            category=category_name,
            published_date=published_date_str,
            content=content,
        )

        # LLMで要約
        provider = self._get_provider()
        response = await provider.ainvoke_structured(
            prompt=prompt,
            output_schema=IRSummaryResponse,
        )

        # レスポンスをIRSummaryに変換
        impact_points = [
            ImpactPoint(label=p.label, content=p.content) for p in response.impact_points
        ]

        return IRSummary(
            overview=response.overview,
            impact_points=impact_points,
        )

    async def _summarize_html_page(self, scraper: BaseIRScraper, doc: IRDocument) -> IRSummary:
        """HTMLページを要約する.

        Args:
            scraper: BaseIRScraperインスタンス
            doc: 要約対象のIRDocument（URLがHTMLページ）

        Returns:
            要約結果
        """
        from bs4 import BeautifulSoup

        # HTMLページを取得
        html = await scraper.fetch_page(doc.url)

        # HTMLをマークダウンに変換
        soup = BeautifulSoup(html, "html.parser")

        # 不要な要素を削除
        for tag in soup(["script", "style", "nav", "footer", "noscript"]):
            tag.decompose()

        # メインコンテンツを抽出
        # article, main, または本文っぽい要素を探す
        main_content = soup.find("article") or soup.find("main") or soup.find("body")
        if main_content:
            content = main_content.get_text(separator="\n", strip=True)
        else:
            content = soup.get_text(separator="\n", strip=True)

        # 内容が長すぎる場合は切り詰め
        max_content_length = 30000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[以下省略...]"

        # プロンプトを作成
        category_name = CATEGORY_NAMES.get(doc.category, doc.category)
        published_date_str = (
            doc.published_date.strftime("%Y年%m月%d日") if doc.published_date else "不明"
        )

        prompt = IR_SUMMARY_PROMPT.format(
            title=doc.title,
            category=category_name,
            published_date=published_date_str,
            content=content,
        )

        # LLMで要約
        provider = self._get_provider()
        response = await provider.ainvoke_structured(
            prompt=prompt,
            output_schema=IRSummaryResponse,
        )

        # レスポンスをIRSummaryに変換
        impact_points = [
            ImpactPoint(label=p.label, content=p.content) for p in response.impact_points
        ]

        return IRSummary(
            overview=response.overview,
            impact_points=impact_points,
        )

    async def _find_ir_page_for_company(self, scraper: BaseIRScraper, sec_code: str) -> str | None:
        """証券コードから企業のIRページURLを探す.

        Args:
            scraper: BaseIRScraperインスタンス
            sec_code: 証券コード

        Returns:
            IRページのURL。見つからない場合はNone。
        """
        # 一般的な企業ドメインパターンを試行
        # 実際の実装では、企業名からドメインを推測するか、
        # 検索エンジンを使用することを検討
        logger.debug(f"Attempting to find IR page for {sec_code}")
        return None

    def list_registered_companies(self) -> list[str]:
        """登録企業の証券コード一覧を取得する.

        Returns:
            証券コードのリスト
        """
        return self._template_loader.list_templates()
