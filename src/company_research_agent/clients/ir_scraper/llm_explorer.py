"""LLMExplorer - LLMを使用したIRページの動的解析."""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from company_research_agent.schemas.ir_schemas import (
    ExtractedLinksResponse,
    IRDocument,
)

if TYPE_CHECKING:
    from company_research_agent.clients.ir_scraper.base import BaseIRScraper
    from company_research_agent.llm.provider import LLMProvider

logger = logging.getLogger(__name__)

# LLMへのプロンプト
EXPLORE_IR_PAGE_PROMPT = """あなたは企業のIRページを解析する専門家です。
以下のウェブページから、IR資料やIRニュースへのリンクを抽出し、正確に分類してください。

## カテゴリ定義（重要：正確に分類すること）

### 1. 決算関連 (earnings)
**定義**: 会社の業績・財務状況を報告する資料
**該当するもの**:
- 決算短信（第1四半期、第2四半期、第3四半期、通期）
- 決算説明会資料、決算補足資料
- 有価証券報告書、四半期報告書
- 月次売上レポート、月次事業進捗レポート
- 業績ハイライト、ファクトシート
**キーワード例**: 決算、業績、売上、利益、財務、quarterly、annual、financial results

### 2. 適時開示 (disclosures)
**定義**: 証券取引所への開示義務がある重要情報
**該当するもの**:
- 業績予想の修正（上方修正、下方修正）
- 配当予想の修正
- 自己株式の取得・処分・公開買付け
- M&A、資本業務提携、子会社設立
- 役員の異動、代表者の異動
- 株式分割、増資、減資
- 訴訟、行政処分
**キーワード例**: 修正、お知らせ、自己株式、取得、異動、提携、公開買付け、notice

### 3. 事業ニュース (news)
**定義**: 事業活動に関するプレスリリース・ニュース
**該当するもの**:
- 新製品・新サービスの発表
- 大型受注、契約締結
- 新規事業への参入
- 技術開発、特許取得
- 受賞、認定
**キーワード例**: 発表、リリース、開始、発売、受注、release、launch

## 分類の優先ルール
- 「業績予想修正」「配当予想修正」→ disclosures（earningsではない）
- 「自己株式取得」「公開買付け」→ disclosures（newsではない）
- 「月次レポート」「月次売上」→ earnings
- 迷った場合は最も適切と思われるカテゴリ1つのみに分類

## 抽出ルール
- **最新のニュースを優先して抽出すること**（日付が新しいものを優先）
- PDFファイル（.pdf拡張子）へのリンクを優先
- PDFがない場合はIRニュースページ（HTML）へのリンクも抽出可
- 同じ資料を複数カテゴリに重複して抽出しないこと
- 最大{max_links}件まで
- 公開日が分かる場合はYYYY-MM-DD形式で記載（ページ上の日付を確認）

## ページ情報
- URL: {page_url}
- ベースURL: {base_url}

## ページコンテンツ
```
{content}
```

上記から、IR資料・IRニュースのリンク情報を抽出してください。
"""


class LLMExplorer:
    """LLMを使用してIRページを動的に解析するクラス.

    未登録企業のIRページでも、LLMがページ構造を理解してIR資料・ニュースリンクを抽出する。
    PDFファイルだけでなく、IRニュースページ（HTML）へのリンクも抽出対象。

    Example:
        >>> explorer = LLMExplorer()
        >>> async with BaseIRScraper() as scraper:
        ...     docs = await explorer.explore_ir_page(scraper, "https://example.com/ir")
    """

    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        """LLMExplorerを初期化する.

        Args:
            llm_provider: LLMプロバイダー。省略時はデフォルトプロバイダーを使用。
        """
        self._llm_provider = llm_provider

    def _get_provider(self) -> LLMProvider:
        """LLMプロバイダーを取得する."""
        if self._llm_provider is None:
            from company_research_agent.llm.factory import get_default_provider

            self._llm_provider = get_default_provider()
        return self._llm_provider

    async def explore_ir_page(
        self,
        scraper: BaseIRScraper,
        url: str,
        max_links: int = 10,
    ) -> list[IRDocument]:
        """IRページを解析してIR資料リンクを抽出する.

        Args:
            scraper: BaseIRScraperインスタンス
            url: IRページのURL
            max_links: 抽出する最大リンク数

        Returns:
            抽出されたIR資料のリスト
        """
        try:
            # ページを取得
            html = await scraper.fetch_page(url)

            # HTMLをマークダウンに変換（トークン削減）
            markdown = self._html_to_markdown(html, url)

            # LLMでリンクを抽出
            provider = self._get_provider()

            # URLからベースURLを抽出
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            prompt = EXPLORE_IR_PAGE_PROMPT.format(
                max_links=max_links,
                base_url=base_url,
                page_url=url,
                content=markdown[:15000],  # トークン制限のため切り詰め
            )

            response = await provider.ainvoke_structured(
                prompt=prompt,
                output_schema=ExtractedLinksResponse,
            )

            # ExtractedLinkをIRDocumentに変換
            documents: list[IRDocument] = []
            for link in response.links:
                # 相対URLを絶対URLに変換
                absolute_url = urljoin(url, link.url)

                # 公開日を解析
                published_date: date | None = None
                if link.published_date:
                    try:
                        published_date = datetime.strptime(link.published_date, "%Y-%m-%d").date()
                    except ValueError:
                        pass

                doc = IRDocument(
                    title=link.title,
                    url=absolute_url,
                    category=link.category,
                    published_date=published_date,
                )
                documents.append(doc)

            logger.info(f"Extracted {len(documents)} IR documents from {url}")
            return documents

        except Exception as e:
            logger.error(f"Failed to explore IR page {url}: {e}")
            return []

    def _html_to_markdown(self, html: str, base_url: str) -> str:
        """HTMLをマークダウンに変換する.

        リンク情報を保持しつつ、LLMへの入力サイズを削減する。

        Args:
            html: HTML文字列
            base_url: ベースURL（相対リンクの解決用）

        Returns:
            マークダウン形式の文字列
        """
        soup = BeautifulSoup(html, "html.parser")

        # 不要な要素を削除
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        # テキストを抽出しつつリンクを保持
        markdown_parts: list[str] = []

        for element in soup.find_all(["a", "p", "h1", "h2", "h3", "h4", "li", "td", "div"]):
            if element.name == "a":
                href = element.get("href", "")
                text = element.get_text(strip=True)
                if href and text:
                    # PDFリンクを強調
                    if str(href).lower().endswith(".pdf"):
                        markdown_parts.append(f"[PDF] [{text}]({href})")
                    else:
                        markdown_parts.append(f"[{text}]({href})")
            elif element.name in ["h1", "h2", "h3", "h4"]:
                text = element.get_text(strip=True)
                if text:
                    level = int(element.name[1])
                    markdown_parts.append(f"{'#' * level} {text}")
            else:
                text = element.get_text(strip=True)
                if text and len(text) > 10:  # 短すぎるテキストは除外
                    markdown_parts.append(text)

        # 重複を削除しつつ順序を保持
        seen: set[str] = set()
        unique_parts: list[str] = []
        for part in markdown_parts:
            if part not in seen:
                seen.add(part)
                unique_parts.append(part)

        return "\n\n".join(unique_parts)

    async def find_ir_page_url(
        self,
        scraper: BaseIRScraper,
        company_url: str,
    ) -> str | None:
        """企業のトップページからIRページのURLを探す.

        Args:
            scraper: BaseIRScraperインスタンス
            company_url: 企業のトップページURL

        Returns:
            IRページのURL。見つからない場合はNone。
        """
        try:
            html = await scraper.fetch_page(company_url)
            soup = BeautifulSoup(html, "html.parser")

            # IRページへのリンクを探す（一般的なパターン）
            ir_patterns = [
                r"/ir/?",
                r"/investor/?",
                r"/investors/?",
                r"/stockholders/?",
                r"investor[-_]?relations",
            ]

            for link in soup.find_all("a", href=True):
                href_attr = link.get("href", "")
                href_str = str(href_attr) if href_attr else ""
                href = href_str.lower()
                text = link.get_text(strip=True).lower()

                # URLパターンでマッチ
                for pattern in ir_patterns:
                    if re.search(pattern, href):
                        return urljoin(company_url, href_str)

                # テキストでマッチ
                if any(keyword in text for keyword in ["ir", "投資家", "株主", "investor"]):
                    return urljoin(company_url, href_str)

            return None

        except Exception as e:
            logger.error(f"Failed to find IR page URL from {company_url}: {e}")
            return None
