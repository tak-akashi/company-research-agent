"""IRTemplateGenerator - LLMを使用したIRテンプレート自動生成."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlparse

import yaml
from bs4 import BeautifulSoup

from company_research_agent.core.config import get_config
from company_research_agent.prompts.ir_template import (
    IR_PAGE_ANALYSIS_PROMPT,
)
from company_research_agent.schemas.ir_schemas import (
    CompanyInfo,
    DiscoveredSection,
    IRPageAnalysisResponse,
    IRPageConfig,
    IRTemplateConfig,
    SectionConfig,
)

if TYPE_CHECKING:
    from company_research_agent.clients.ir_scraper.base import BaseIRScraper
    from company_research_agent.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class IRTemplateGenerator:
    """LLMを使用してIRテンプレートを自動生成するクラス.

    企業のIRページを解析し、スクレイピング用のYAMLテンプレートを生成する。

    Example:
        >>> generator = IRTemplateGenerator()
        >>> async with BaseIRScraper() as scraper:
        ...     template = await generator.generate_template(
        ...         scraper=scraper,
        ...         sec_code="72030",
        ...         company_name="トヨタ自動車",
        ...         ir_url="https://global.toyota/jp/ir/",
        ...     )
        ...     generator.save_template(template)
    """

    def __init__(
        self,
        templates_dir: Path | None = None,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        """IRTemplateGeneratorを初期化する.

        Args:
            templates_dir: テンプレート保存ディレクトリ
            llm_provider: LLMプロバイダー
        """
        self._config = get_config()
        self._llm_provider = llm_provider

        if templates_dir is None:
            self._templates_dir = Path(__file__).parents[4] / "config" / "ir_templates"
        else:
            self._templates_dir = templates_dir

    def _get_provider(self) -> LLMProvider:
        """LLMプロバイダーを取得する."""
        if self._llm_provider is None:
            from company_research_agent.llm.factory import get_default_provider

            self._llm_provider = get_default_provider()
        return self._llm_provider

    async def discover_ir_url(
        self,
        company_name: str,
        sec_code: str | None = None,
    ) -> str | None:
        """Google検索で企業のIRページURLを発見する.

        Playwrightを使用してGoogle検索を実行し、IRページを発見する。

        Args:
            company_name: 企業名
            sec_code: 証券コード（オプション、検索精度向上に使用）

        Returns:
            発見されたIRページのURL。見つからない場合はNone。
        """
        from playwright.async_api import async_playwright

        # 検索クエリを構築
        query = f"{company_name} IR 投資家情報"
        if sec_code:
            query = f"{company_name} {sec_code} IR"

        logger.info(f"Searching for IR page via Google: {query}")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="ja-JP",
                )
                page = await context.new_page()

                # Google検索
                search_url = f"https://www.google.com/search?q={query}&hl=ja"
                await page.goto(search_url, wait_until="domcontentloaded")

                # 検索結果を少し待つ
                await page.wait_for_timeout(1000)

                # 検索結果のリンクを取得
                html = await page.content()
                await browser.close()

                soup = BeautifulSoup(html, "html.parser")

                # Google検索結果からURLを抽出
                ir_urls: list[tuple[str, int]] = []  # (url, score)

                # Google検索結果のリンク要素を取得
                for link in soup.select("a[href]"):
                    href_attr = link.get("href")
                    # hrefが文字列でない場合はスキップ
                    if not isinstance(href_attr, str):
                        continue
                    href: str = href_attr

                    # Googleのリダイレクト形式から実際のURLを抽出
                    if href.startswith("/url?"):
                        from urllib.parse import parse_qs

                        parsed = urlparse(href)
                        params = parse_qs(parsed.query)
                        if "q" in params:
                            href = params["q"][0]

                    if not href.startswith("http"):
                        continue

                    # スコアリング
                    score = 0
                    url_lower = href.lower()

                    # IRページらしいURLパターン
                    if "/ir" in url_lower or "/investor" in url_lower:
                        score += 10
                    if "ir." in url_lower:  # ir.example.com
                        score += 8

                    # 公式サイトらしいか（企業名の一部がドメインに含まれる）
                    company_name_normalized = (
                        company_name.lower()
                        .replace(" ", "")
                        .replace("株式会社", "")
                        .replace("　", "")
                    )
                    if len(company_name_normalized) >= 3:
                        # 企業名の最初の3文字以上がURLに含まれるか
                        if company_name_normalized[:3] in url_lower.replace("-", ""):
                            score += 5

                    # 避けるべきサイト
                    skip_domains = [
                        "google.com",
                        "google.co.jp",
                        "wikipedia",
                        "bloomberg",
                        "reuters",
                        "yahoo.co.jp/finance",
                        "finance.yahoo",
                        "nikkei.com",
                        "kabutan",
                        "minkabu",
                        "stockclip",
                        "youtube.com",
                        "twitter.com",
                        "facebook.com",
                    ]
                    if any(d in url_lower for d in skip_domains):
                        continue

                    if score > 0:
                        ir_urls.append((href, score))

                # スコア順にソート
                ir_urls.sort(key=lambda x: x[1], reverse=True)

                if ir_urls:
                    best_url = ir_urls[0][0]
                    logger.info(f"Found IR page: {best_url}")
                    return best_url

                logger.warning(f"No IR page found for {company_name}")
                return None

        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return None

    async def generate_template(
        self,
        scraper: BaseIRScraper,
        sec_code: str,
        company_name: str,
        ir_url: str,
        edinet_code: str | None = None,
    ) -> IRTemplateConfig:
        """IRテンプレートを生成する.

        Args:
            scraper: BaseIRScraperインスタンス
            sec_code: 証券コード（5桁）
            company_name: 企業名
            ir_url: IRページのURL
            edinet_code: EDINETコード（オプション）

        Returns:
            生成されたIRテンプレート設定
        """
        logger.info(f"Generating template for {company_name} ({sec_code})")

        # 1. IRページを取得
        html = await scraper.fetch_page(ir_url)
        logger.debug(f"Fetched IR page: {len(html)} bytes")

        # 2. ナビゲーションを解析してサブページを発見
        subpages = await self._discover_subpages(scraper, ir_url, html, company_name)
        logger.info(f"Discovered {len(subpages)} subpages")

        # 3. 各ページを解析してセクション設定を生成
        all_sections: list[DiscoveredSection] = []

        # メインページを解析
        main_sections = await self._analyze_page(ir_url, html, company_name)
        all_sections.extend(main_sections)

        # サブページを解析
        for subpage_url in subpages:
            try:
                subpage_html = await scraper.fetch_page(subpage_url)
                sections = await self._analyze_page(subpage_url, subpage_html, company_name)
                all_sections.extend(sections)
            except Exception as e:
                logger.warning(f"Failed to analyze subpage {subpage_url}: {e}")

        # 4. 重複を除去し、最も確信度の高いセクションを選択
        sections_by_category = self._deduplicate_sections(all_sections, ir_url)

        # 5. テンプレートを構築
        template = IRTemplateConfig(
            company=CompanyInfo(
                sec_code=sec_code,
                name=company_name,
                edinet_code=edinet_code,
            ),
            ir_page=IRPageConfig(
                base_url=ir_url,
                sections={
                    cat: SectionConfig(
                        url=section.url,
                        selector=section.selector,
                        link_pattern=section.link_pattern,
                        date_selector=section.date_selector,
                        date_format=section.date_format,
                    )
                    for cat, section in sections_by_category.items()
                },
            ),
        )

        logger.info(
            f"Generated template with {len(sections_by_category)} sections: "
            f"{list(sections_by_category.keys())}"
        )

        return template

    async def _discover_subpages(
        self,
        scraper: BaseIRScraper,
        base_url: str,
        html: str,
        company_name: str,
    ) -> list[str]:
        """ナビゲーションからサブページを発見する.

        Args:
            scraper: BaseIRScraperインスタンス
            base_url: ベースURL
            html: HTMLコンテンツ
            company_name: 企業名

        Returns:
            発見されたサブページURLのリスト
        """
        # HTMLを簡略化（主にナビゲーション部分を抽出）
        soup = BeautifulSoup(html, "html.parser")

        # IR関連のリンクを正規表現で抽出
        subpages: set[str] = set()

        # リンクをすべて抽出
        for link in soup.find_all("a", href=True):
            href = str(link.get("href", ""))
            text = link.get_text(strip=True).lower()

            # IR関連のキーワードをチェック
            ir_keywords = [
                "決算",
                "業績",
                "財務",
                "earnings",
                "financial",
                "ニュース",
                "news",
                "press",
                "適時開示",
                "disclosure",
                "有価証券",
                "securities",
                "ir資料",
                "ir library",
                "資料室",
            ]

            if any(kw in href.lower() or kw in text for kw in ir_keywords):
                # 相対URLを絶対URLに変換
                absolute_url = urljoin(base_url, href)

                # 同一ドメインのみ
                if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                    # PDFや画像は除外
                    if not re.search(r"\.(pdf|png|jpg|jpeg|gif)$", absolute_url, re.I):
                        subpages.add(absolute_url)

        return list(subpages)[:10]  # 最大10ページ

    async def _analyze_page(
        self,
        url: str,
        html: str,
        company_name: str,
    ) -> list[DiscoveredSection]:
        """ページを解析してセクション設定を抽出する.

        Args:
            url: ページURL
            html: HTMLコンテンツ
            company_name: 企業名

        Returns:
            発見されたセクションのリスト
        """
        # HTMLを適切なサイズに切り詰め
        soup = BeautifulSoup(html, "html.parser")

        # scriptとstyleを除去
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # HTMLを文字列に変換して切り詰め
        clean_html = str(soup)
        max_length = 30000
        if len(clean_html) > max_length:
            clean_html = clean_html[:max_length] + "\n<!-- truncated -->"

        # LLMでページ構造を解析
        prompt = IR_PAGE_ANALYSIS_PROMPT.format(
            url=url,
            company_name=company_name,
            html_content=clean_html,
        )

        provider = self._get_provider()

        try:
            response = await provider.ainvoke_structured(
                prompt=prompt,
                output_schema=IRPageAnalysisResponse,
            )

            # URLを相対パスに変換
            for section in response.sections:
                section.url = self._make_relative_url(url, section.url)

            return response.sections

        except Exception as e:
            logger.error(f"Failed to analyze page {url}: {e}")
            return []

    def _make_relative_url(self, base_url: str, target_url: str) -> str:
        """URLを相対パスに変換する.

        Args:
            base_url: ベースURL
            target_url: 変換対象のURL

        Returns:
            相対パス（同一ページの場合は空文字列）
        """
        # すでに相対パスの場合はそのまま返す
        if not target_url.startswith(("http://", "https://")):
            return target_url

        base_parsed = urlparse(base_url)
        target_parsed = urlparse(target_url)

        # 異なるドメインの場合はそのまま返す
        if base_parsed.netloc != target_parsed.netloc:
            return target_url

        # パスの相対化を試みる
        base_path = base_parsed.path.rstrip("/")
        target_path = target_parsed.path

        if target_path.startswith(base_path):
            relative = target_path[len(base_path) :].lstrip("/")
            return relative if relative else ""

        return target_path

    def _deduplicate_sections(
        self,
        sections: list[DiscoveredSection],
        base_url: str,
    ) -> dict[str, DiscoveredSection]:
        """セクションの重複を除去し、カテゴリごとに最良のものを選択.

        Args:
            sections: 発見されたセクションのリスト
            base_url: ベースURL

        Returns:
            カテゴリをキーとしたセクションの辞書
        """
        result: dict[str, DiscoveredSection] = {}

        for section in sections:
            category = section.category

            if category not in result:
                result[category] = section
            elif section.confidence > result[category].confidence:
                result[category] = section

        return result

    def save_template(
        self,
        template: IRTemplateConfig,
        overwrite: bool = False,
    ) -> Path:
        """テンプレートをYAMLファイルとして保存する.

        Args:
            template: 保存するテンプレート
            overwrite: 既存ファイルを上書きするか

        Returns:
            保存先のパス

        Raises:
            FileExistsError: overwrite=Falseで既存ファイルがある場合
        """
        # ファイル名を生成（証券コード_企業名.yaml）
        company_name_safe = re.sub(r"[^\w\-]", "", template.company.name.lower())
        filename = f"{template.company.sec_code}_{company_name_safe}.yaml"
        filepath = self._templates_dir / filename

        # ディレクトリを作成
        self._templates_dir.mkdir(parents=True, exist_ok=True)

        # 既存ファイルのチェック
        if filepath.exists() and not overwrite:
            raise FileExistsError(f"Template already exists: {filepath}")

        # YAMLに変換
        company_dict: dict[str, str] = {
            "sec_code": template.company.sec_code,
            "name": template.company.name,
        }
        if template.company.edinet_code:
            company_dict["edinet_code"] = template.company.edinet_code

        sections_dict: dict[str, dict[str, str | None]] = {}
        for cat, section in template.ir_page.sections.items():
            section_dict: dict[str, str | None] = {
                "url": section.url,
                "selector": section.selector,
            }
            if section.link_pattern:
                section_dict["link_pattern"] = section.link_pattern
            if section.date_selector:
                section_dict["date_selector"] = section.date_selector
            if section.date_format:
                section_dict["date_format"] = section.date_format
            sections_dict[cat] = section_dict

        template_dict: dict[str, Any] = {
            "company": company_dict,
            "ir_page": {
                "base_url": template.ir_page.base_url,
                "sections": sections_dict,
            },
        }

        # ファイルに書き込み
        with open(filepath, "w", encoding="utf-8") as f:
            # コメントを追加
            f.write(f"# {template.company.name} IRテンプレート\n")
            yaml.dump(
                template_dict,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )

        logger.info(f"Saved template to {filepath}")
        return filepath

    async def validate_template(
        self,
        scraper: BaseIRScraper,
        template: IRTemplateConfig,
    ) -> dict[str, int]:
        """テンプレートが正しく動作するか検証する.

        Args:
            scraper: BaseIRScraperインスタンス
            template: 検証するテンプレート

        Returns:
            カテゴリごとに発見されたPDF数の辞書
        """
        from company_research_agent.clients.ir_scraper.template_loader import TemplateLoader

        loader = TemplateLoader(self._templates_dir)
        results: dict[str, int] = {}

        for category in template.ir_page.sections:
            try:
                docs = await loader.scrape_with_template(scraper, template, category)
                results[category] = len(docs)
                logger.info(f"Validation: {category} = {len(docs)} documents")
            except Exception as e:
                logger.warning(f"Validation failed for {category}: {e}")
                results[category] = -1  # エラーを示す

        return results
