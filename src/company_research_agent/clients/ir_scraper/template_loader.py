"""TemplateLoader - YAMLテンプレートに基づくIR資料抽出."""

from __future__ import annotations

import importlib
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol
from urllib.parse import urljoin

import yaml
from bs4 import BeautifulSoup, Tag

from company_research_agent.schemas.ir_schemas import (
    IRDocument,
    IRTemplateConfig,
)

if TYPE_CHECKING:
    from company_research_agent.clients.ir_scraper.base import BaseIRScraper

logger = logging.getLogger(__name__)


class CustomScraper(Protocol):
    """カスタムスクレイパーのプロトコル.

    YAMLテンプレートでは対応できない複雑なケースに使用する。
    """

    async def scrape(
        self,
        scraper: BaseIRScraper,
        config: IRTemplateConfig,
        category: str | None = None,
    ) -> list[IRDocument]:
        """IR資料を抽出する.

        Args:
            scraper: BaseIRScraperインスタンス
            config: テンプレート設定
            category: 取得するカテゴリ（省略時は全カテゴリ）

        Returns:
            抽出されたIR資料のリスト
        """
        ...


class TemplateLoader:
    """YAMLテンプレートを読み込み、IR資料を抽出するクラス.

    YAMLファイルで定義された企業IRページの構造に基づいて、
    BeautifulSoupを使用してPDFリンクを抽出する。

    Example:
        >>> loader = TemplateLoader(Path("config/ir_templates"))
        >>> template = loader.load_template("72030")
        >>> async with BaseIRScraper() as scraper:
        ...     docs = await loader.scrape_with_template(scraper, template)
    """

    def __init__(self, templates_dir: Path | None = None) -> None:
        """TemplateLoaderを初期化する.

        Args:
            templates_dir: テンプレートファイルのディレクトリ。
                省略時はプロジェクトルートの config/ir_templates を使用。
        """
        if templates_dir is None:
            # プロジェクトルートからの相対パス
            self._templates_dir = Path(__file__).parents[4] / "config" / "ir_templates"
        else:
            self._templates_dir = templates_dir

        self._templates: dict[str, IRTemplateConfig] = {}
        self._custom_scrapers: dict[str, CustomScraper] = {}

    def load_template(self, sec_code: str) -> IRTemplateConfig | None:
        """証券コードからテンプレートを読み込む.

        Args:
            sec_code: 証券コード（5桁）

        Returns:
            テンプレート設定。見つからない場合はNone。
        """
        # キャッシュ確認
        if sec_code in self._templates:
            return self._templates[sec_code]

        # ファイル検索（{sec_code}_{company_name}.yaml形式）
        pattern = f"{sec_code}_*.yaml"
        yaml_files = list(self._templates_dir.glob(pattern))

        if not yaml_files:
            logger.debug(f"No template found for sec_code: {sec_code}")
            return None

        yaml_path = yaml_files[0]  # 最初にマッチしたファイルを使用

        try:
            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            config = IRTemplateConfig.model_validate(data)
            self._templates[sec_code] = config
            logger.debug(f"Loaded template for {sec_code}: {yaml_path}")
            return config

        except Exception as e:
            logger.error(f"Failed to load template {yaml_path}: {e}")
            return None

    def list_templates(self) -> list[str]:
        """利用可能なテンプレートの証券コード一覧を取得する.

        Returns:
            証券コードのリスト
        """
        sec_codes: list[str] = []

        if not self._templates_dir.exists():
            return sec_codes

        for yaml_file in self._templates_dir.glob("*.yaml"):
            # ファイル名から証券コードを抽出（{sec_code}_{company_name}.yaml）
            parts = yaml_file.stem.split("_")
            if parts and parts[0].isdigit() and len(parts[0]) == 5:
                sec_codes.append(parts[0])

        return sorted(sec_codes)

    async def scrape_with_template(
        self,
        scraper: BaseIRScraper,
        template: IRTemplateConfig,
        category: str | None = None,
    ) -> list[IRDocument]:
        """テンプレートに基づいてIR資料を抽出する.

        Args:
            scraper: BaseIRScraperインスタンス
            template: テンプレート設定
            category: 取得するカテゴリ（省略時は全カテゴリ）

        Returns:
            抽出されたIR資料のリスト
        """
        # カスタムスクレイパーが指定されている場合
        if template.custom_class:
            custom_scraper = self._load_custom_scraper(template.custom_class)
            if custom_scraper:
                return await custom_scraper.scrape(scraper, template, category)

        documents: list[IRDocument] = []
        base_url = template.ir_page.base_url

        # カテゴリをフィルタリング
        sections = template.ir_page.sections
        if category:
            sections = {k: v for k, v in sections.items() if k == category}

        for cat, section_config in sections.items():
            # セクションURLを構築
            section_url = urljoin(base_url, section_config.url)

            try:
                # ページを取得
                html = await scraper.fetch_page(section_url)

                # BeautifulSoupで解析
                soup = BeautifulSoup(html, "html.parser")

                # セレクターで要素を抽出
                elements = soup.select(section_config.selector)
                logger.debug(f"Found {len(elements)} elements for {cat} at {section_url}")

                for element in elements:
                    doc = self._extract_document_from_element(
                        element=element,
                        base_url=section_url,
                        category=cat,
                        link_pattern=section_config.link_pattern,
                        date_selector=section_config.date_selector,
                        date_format=section_config.date_format,
                    )
                    if doc:
                        documents.append(doc)

            except Exception as e:
                logger.error(f"Failed to scrape {cat} section at {section_url}: {e}")
                continue

        return documents

    def _extract_document_from_element(
        self,
        element: Tag,
        base_url: str,
        category: str,
        link_pattern: str | None = None,
        date_selector: str | None = None,
        date_format: str | None = None,
    ) -> IRDocument | None:
        """HTML要素からIRDocumentを抽出する.

        Args:
            element: BeautifulSoup Tag要素
            base_url: ベースURL
            category: カテゴリ
            link_pattern: リンクをフィルタリングする正規表現
            date_selector: 日付を抽出するセレクター
            date_format: 日付フォーマット

        Returns:
            IRDocument。抽出できない場合はNone。
        """
        # リンクを取得
        href = element.get("href") if element.name == "a" else None
        if not href:
            link = element.find("a")
            href = link.get("href") if link else None

        if not href:
            return None

        href = str(href)

        # リンクパターンでフィルタリング
        if link_pattern:
            if not re.search(link_pattern, href):
                return None

        # PDFリンクのみを対象
        if not href.lower().endswith(".pdf"):
            return None

        # 絶対URLに変換
        url = urljoin(base_url, href)

        # タイトルを取得
        title = element.get_text(strip=True)
        if not title:
            # ファイル名をタイトルとして使用
            title = Path(href).stem

        # 日付を抽出
        published_date: date | None = None
        if date_selector and date_format:
            date_elem = element.select_one(date_selector)
            if date_elem:
                try:
                    date_text = date_elem.get_text(strip=True)
                    published_date = datetime.strptime(date_text, date_format).date()
                except ValueError:
                    pass

        return IRDocument(
            title=title,
            url=url,
            category=category,  # type: ignore[arg-type]
            published_date=published_date,
        )

    def _load_custom_scraper(self, class_name: str) -> CustomScraper | None:
        """カスタムスクレイパークラスを動的にロードする.

        Args:
            class_name: クラス名（例: "toyota.ToyotaScraper"）

        Returns:
            カスタムスクレイパーインスタンス。ロード失敗時はNone。
        """
        if class_name in self._custom_scrapers:
            return self._custom_scrapers[class_name]

        try:
            # モジュールとクラスを分離
            parts = class_name.rsplit(".", 1)
            if len(parts) == 2:
                module_name, cls_name = parts
            else:
                module_name = class_name
                cls_name = class_name.split(".")[-1]

            # 完全なモジュールパスを構築
            full_module = f"company_research_agent.clients.ir_scraper.templates.{module_name}"

            module = importlib.import_module(full_module)
            cls = getattr(module, cls_name)
            instance: CustomScraper = cls()

            self._custom_scrapers[class_name] = instance
            logger.debug(f"Loaded custom scraper: {class_name}")
            return instance

        except Exception as e:
            logger.error(f"Failed to load custom scraper {class_name}: {e}")
            return None
