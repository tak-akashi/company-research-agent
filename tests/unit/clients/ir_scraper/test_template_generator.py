"""IRTemplateGeneratorのユニットテスト."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from company_research_agent.clients.ir_scraper.template_generator import (
    IRTemplateGenerator,
)
from company_research_agent.schemas.ir_schemas import (
    CompanyInfo,
    DiscoveredSection,
    IRPageConfig,
    IRTemplateConfig,
    SectionConfig,
)

if TYPE_CHECKING:
    pass


class TestIRTemplateGenerator:
    """IRTemplateGeneratorのテスト."""

    class TestInit:
        """初期化のテスト."""

        def test_default_initialization(self) -> None:
            """デフォルト初期化ができること."""
            generator = IRTemplateGenerator()

            assert generator._templates_dir.name == "ir_templates"
            assert generator._llm_provider is None

        def test_custom_templates_dir(self, tmp_path: Path) -> None:
            """カスタムテンプレートディレクトリを指定できること."""
            generator = IRTemplateGenerator(templates_dir=tmp_path)

            assert generator._templates_dir == tmp_path

        def test_custom_llm_provider(self) -> None:
            """カスタムLLMプロバイダーを指定できること."""
            mock_provider = MagicMock()
            generator = IRTemplateGenerator(llm_provider=mock_provider)

            assert generator._llm_provider is mock_provider

    class TestMakeRelativeUrl:
        """URL相対化のテスト."""

        def test_already_relative_path(self) -> None:
            """すでに相対パスの場合はそのまま返すこと."""
            generator = IRTemplateGenerator()

            result = generator._make_relative_url(
                "https://example.com/ir/",
                "documents/annual.pdf",
            )

            assert result == "documents/annual.pdf"

        def test_same_domain_same_path_prefix(self) -> None:
            """同一ドメインで同じパスプレフィックスの場合は相対化すること."""
            generator = IRTemplateGenerator()

            result = generator._make_relative_url(
                "https://example.com/ir/",
                "https://example.com/ir/documents/report.pdf",
            )

            assert result == "documents/report.pdf"

        def test_same_domain_different_path(self) -> None:
            """同一ドメインで異なるパスの場合はパスを返すこと."""
            generator = IRTemplateGenerator()

            result = generator._make_relative_url(
                "https://example.com/ir/",
                "https://example.com/news/article.html",
            )

            assert result == "/news/article.html"

        def test_different_domain(self) -> None:
            """異なるドメインの場合は元のURLを返すこと."""
            generator = IRTemplateGenerator()

            result = generator._make_relative_url(
                "https://example.com/ir/",
                "https://other.com/documents/report.pdf",
            )

            assert result == "https://other.com/documents/report.pdf"

        def test_same_page_empty_string(self) -> None:
            """同一ページの場合は空文字列を返すこと."""
            generator = IRTemplateGenerator()

            result = generator._make_relative_url(
                "https://example.com/ir",
                "https://example.com/ir/",
            )

            assert result == ""

    class TestDeduplicateSections:
        """セクション重複排除のテスト."""

        def test_no_duplicates(self) -> None:
            """重複がない場合はそのまま返すこと."""
            generator = IRTemplateGenerator()

            sections = [
                DiscoveredSection(
                    category="earnings",
                    url="/ir/earnings",
                    selector="a.pdf-link",
                    confidence=0.9,
                ),
                DiscoveredSection(
                    category="news",
                    url="/ir/news",
                    selector="a.news-link",
                    confidence=0.8,
                ),
            ]

            result = generator._deduplicate_sections(sections, "https://example.com/ir/")

            assert len(result) == 2
            assert "earnings" in result
            assert "news" in result

        def test_keep_higher_confidence(self) -> None:
            """同じカテゴリの場合は信頼度の高いものを残すこと."""
            generator = IRTemplateGenerator()

            sections = [
                DiscoveredSection(
                    category="earnings",
                    url="/ir/earnings/old",
                    selector="a.old-link",
                    confidence=0.5,
                ),
                DiscoveredSection(
                    category="earnings",
                    url="/ir/earnings/new",
                    selector="a.new-link",
                    confidence=0.9,
                ),
            ]

            result = generator._deduplicate_sections(sections, "https://example.com/ir/")

            assert len(result) == 1
            assert result["earnings"].url == "/ir/earnings/new"
            assert result["earnings"].confidence == 0.9

        def test_empty_list(self) -> None:
            """空のリストの場合は空の辞書を返すこと."""
            generator = IRTemplateGenerator()

            result = generator._deduplicate_sections([], "https://example.com/ir/")

            assert result == {}

    class TestSaveTemplate:
        """テンプレート保存のテスト."""

        def test_save_basic_template(self, tmp_path: Path) -> None:
            """基本的なテンプレートを保存できること."""
            generator = IRTemplateGenerator(templates_dir=tmp_path)

            template = IRTemplateConfig(
                company=CompanyInfo(
                    sec_code="72030",
                    name="トヨタ自動車",
                ),
                ir_page=IRPageConfig(
                    base_url="https://global.toyota/jp/ir/",
                    sections={
                        "earnings": SectionConfig(
                            url="/ir/library",
                            selector="a.pdf-link",
                        ),
                    },
                ),
            )

            filepath = generator.save_template(template)

            assert filepath.exists()
            assert filepath.name == "72030_トヨタ自動車.yaml"

            # YAMLの内容を検証
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
                assert "# トヨタ自動車 IRテンプレート" in content

                # コメント行を除去してYAMLをパース
                yaml_content = "\n".join(
                    line for line in content.split("\n") if not line.startswith("#")
                )
                data = yaml.safe_load(yaml_content)

            assert data["company"]["sec_code"] == "72030"
            assert data["company"]["name"] == "トヨタ自動車"
            assert data["ir_page"]["base_url"] == "https://global.toyota/jp/ir/"
            assert "earnings" in data["ir_page"]["sections"]

        def test_save_with_edinet_code(self, tmp_path: Path) -> None:
            """EDINETコード付きテンプレートを保存できること."""
            generator = IRTemplateGenerator(templates_dir=tmp_path)

            template = IRTemplateConfig(
                company=CompanyInfo(
                    sec_code="72030",
                    name="Toyota",
                    edinet_code="E02144",
                ),
                ir_page=IRPageConfig(
                    base_url="https://global.toyota/jp/ir/",
                    sections={},
                ),
            )

            filepath = generator.save_template(template)

            with open(filepath, encoding="utf-8") as f:
                content = f.read()
                yaml_content = "\n".join(
                    line for line in content.split("\n") if not line.startswith("#")
                )
                data = yaml.safe_load(yaml_content)

            assert data["company"]["edinet_code"] == "E02144"

        def test_save_with_all_section_fields(self, tmp_path: Path) -> None:
            """全フィールド付きセクションを保存できること."""
            generator = IRTemplateGenerator(templates_dir=tmp_path)

            template = IRTemplateConfig(
                company=CompanyInfo(
                    sec_code="72030",
                    name="Test",
                ),
                ir_page=IRPageConfig(
                    base_url="https://example.com/ir/",
                    sections={
                        "earnings": SectionConfig(
                            url="/earnings",
                            selector="a.pdf",
                            link_pattern=r".*\.pdf$",
                            date_selector=".date",
                            date_format="%Y年%m月%d日",
                        ),
                    },
                ),
            )

            filepath = generator.save_template(template)

            with open(filepath, encoding="utf-8") as f:
                content = f.read()
                yaml_content = "\n".join(
                    line for line in content.split("\n") if not line.startswith("#")
                )
                data = yaml.safe_load(yaml_content)

            section = data["ir_page"]["sections"]["earnings"]
            assert section["link_pattern"] == r".*\.pdf$"
            assert section["date_selector"] == ".date"
            assert section["date_format"] == "%Y年%m月%d日"

        def test_overwrite_existing(self, tmp_path: Path) -> None:
            """既存ファイルを上書きできること."""
            generator = IRTemplateGenerator(templates_dir=tmp_path)

            template = IRTemplateConfig(
                company=CompanyInfo(
                    sec_code="72030",
                    name="Test",
                ),
                ir_page=IRPageConfig(
                    base_url="https://example.com/ir/",
                    sections={},
                ),
            )

            # 1回目の保存
            filepath1 = generator.save_template(template)
            assert filepath1.exists()

            # 上書き保存
            filepath2 = generator.save_template(template, overwrite=True)
            assert filepath2 == filepath1

        def test_error_on_existing_without_overwrite(self, tmp_path: Path) -> None:
            """上書きなしで既存ファイルがある場合はエラーになること."""
            generator = IRTemplateGenerator(templates_dir=tmp_path)

            template = IRTemplateConfig(
                company=CompanyInfo(
                    sec_code="72030",
                    name="Test",
                ),
                ir_page=IRPageConfig(
                    base_url="https://example.com/ir/",
                    sections={},
                ),
            )

            # 1回目の保存
            generator.save_template(template)

            # 2回目はエラー
            with pytest.raises(FileExistsError):
                generator.save_template(template, overwrite=False)

    class TestDiscoverSubpages:
        """サブページ発見のテスト."""

        @pytest.mark.asyncio
        async def test_extract_ir_links(self) -> None:
            """IR関連リンクを抽出できること."""
            generator = IRTemplateGenerator()

            html = """
            <html>
            <body>
                <nav>
                    <a href="/ir/earnings">決算情報</a>
                    <a href="/ir/news">IRニュース</a>
                    <a href="/about">会社概要</a>
                </nav>
            </body>
            </html>
            """

            mock_scraper = MagicMock()

            result = await generator._discover_subpages(
                mock_scraper,
                "https://example.com/ir/",
                html,
                "テスト企業",
            )

            assert len(result) == 2
            assert "https://example.com/ir/earnings" in result
            assert "https://example.com/ir/news" in result

        @pytest.mark.asyncio
        async def test_exclude_pdf_links(self) -> None:
            """PDFリンクは除外されること."""
            generator = IRTemplateGenerator()

            html = """
            <html>
            <body>
                <a href="/ir/earnings.pdf">決算資料PDF</a>
                <a href="/ir/earnings">決算情報</a>
            </body>
            </html>
            """

            mock_scraper = MagicMock()

            result = await generator._discover_subpages(
                mock_scraper,
                "https://example.com/ir/",
                html,
                "テスト企業",
            )

            assert len(result) == 1
            assert "https://example.com/ir/earnings" in result

        @pytest.mark.asyncio
        async def test_exclude_external_domain(self) -> None:
            """外部ドメインのリンクは除外されること."""
            generator = IRTemplateGenerator()

            html = """
            <html>
            <body>
                <a href="https://other.com/ir/news">外部ニュース</a>
                <a href="/ir/news">IRニュース</a>
            </body>
            </html>
            """

            mock_scraper = MagicMock()

            result = await generator._discover_subpages(
                mock_scraper,
                "https://example.com/ir/",
                html,
                "テスト企業",
            )

            assert len(result) == 1
            assert "https://example.com/ir/news" in result

        @pytest.mark.asyncio
        async def test_limit_to_10_pages(self) -> None:
            """最大10ページに制限されること."""
            generator = IRTemplateGenerator()

            # 20個のリンクを含むHTML
            links = "\n".join(f'<a href="/ir/news{i}">ニュース{i}</a>' for i in range(20))
            html = f"<html><body>{links}</body></html>"

            mock_scraper = MagicMock()

            result = await generator._discover_subpages(
                mock_scraper,
                "https://example.com/ir/",
                html,
                "テスト企業",
            )

            assert len(result) <= 10

    class TestAnalyzePage:
        """ページ解析のテスト."""

        @pytest.mark.asyncio
        async def test_analyze_page_success(self) -> None:
            """ページ解析が成功すること."""
            mock_provider = MagicMock()
            mock_provider.ainvoke_structured = AsyncMock(
                return_value=MagicMock(
                    sections=[
                        DiscoveredSection(
                            category="earnings",
                            url="https://example.com/ir/earnings",
                            selector="a.pdf-link",
                            confidence=0.9,
                        ),
                    ],
                ),
            )

            generator = IRTemplateGenerator(llm_provider=mock_provider)

            html = "<html><body>Test content</body></html>"

            result = await generator._analyze_page(
                "https://example.com/ir/",
                html,
                "テスト企業",
            )

            assert len(result) == 1
            assert result[0].category == "earnings"
            mock_provider.ainvoke_structured.assert_called_once()

        @pytest.mark.asyncio
        async def test_analyze_page_error_returns_empty(self) -> None:
            """ページ解析エラー時は空リストを返すこと."""
            mock_provider = MagicMock()
            mock_provider.ainvoke_structured = AsyncMock(side_effect=Exception("LLM Error"))

            generator = IRTemplateGenerator(llm_provider=mock_provider)

            result = await generator._analyze_page(
                "https://example.com/ir/",
                "<html></html>",
                "テスト企業",
            )

            assert result == []

        @pytest.mark.asyncio
        async def test_analyze_page_truncates_long_html(self) -> None:
            """長いHTMLは切り詰められること."""
            mock_provider = MagicMock()
            mock_provider.ainvoke_structured = AsyncMock(
                return_value=MagicMock(sections=[]),
            )

            generator = IRTemplateGenerator(llm_provider=mock_provider)

            # 50000文字のHTML
            long_html = "<html><body>" + "x" * 50000 + "</body></html>"

            await generator._analyze_page(
                "https://example.com/ir/",
                long_html,
                "テスト企業",
            )

            # プロンプトに渡されたHTMLが30000文字以下であることを確認
            call_args = mock_provider.ainvoke_structured.call_args
            prompt = call_args.kwargs["prompt"]
            # truncatedコメントが含まれていることを確認
            assert "<!-- truncated -->" in prompt

    class TestGenerateTemplate:
        """テンプレート生成のテスト."""

        @pytest.mark.asyncio
        async def test_generate_template_basic(self) -> None:
            """基本的なテンプレート生成ができること."""
            mock_provider = MagicMock()
            mock_provider.ainvoke_structured = AsyncMock(
                return_value=MagicMock(
                    sections=[
                        DiscoveredSection(
                            category="earnings",
                            url="https://example.com/ir/earnings",
                            selector="a.pdf-link",
                            confidence=0.9,
                        ),
                    ],
                ),
            )

            generator = IRTemplateGenerator(llm_provider=mock_provider)

            mock_scraper = MagicMock()
            mock_scraper.fetch_page = AsyncMock(return_value="<html><body>Test</body></html>")

            template = await generator.generate_template(
                scraper=mock_scraper,
                sec_code="72030",
                company_name="トヨタ自動車",
                ir_url="https://example.com/ir/",
            )

            assert template.company.sec_code == "72030"
            assert template.company.name == "トヨタ自動車"
            assert template.ir_page.base_url == "https://example.com/ir/"
            assert "earnings" in template.ir_page.sections

    class TestValidateTemplate:
        """テンプレート検証のテスト."""

        @pytest.mark.asyncio
        async def test_validate_returns_document_counts(self, tmp_path: Path) -> None:
            """検証がドキュメント数を返すこと."""
            generator = IRTemplateGenerator(templates_dir=tmp_path)

            template = IRTemplateConfig(
                company=CompanyInfo(
                    sec_code="72030",
                    name="Test",
                ),
                ir_page=IRPageConfig(
                    base_url="https://example.com/ir/",
                    sections={
                        "earnings": SectionConfig(
                            url="/earnings",
                            selector="a.pdf",
                        ),
                    },
                ),
            )

            mock_scraper = MagicMock()

            with patch(
                "company_research_agent.clients.ir_scraper.template_loader.TemplateLoader"
            ) as MockLoader:
                mock_loader = MockLoader.return_value
                mock_loader.scrape_with_template = AsyncMock(
                    return_value=[MagicMock(), MagicMock()]
                )

                result = await generator.validate_template(mock_scraper, template)

            assert result["earnings"] == 2

        @pytest.mark.asyncio
        async def test_validate_error_returns_negative(self, tmp_path: Path) -> None:
            """検証エラー時は-1を返すこと."""
            generator = IRTemplateGenerator(templates_dir=tmp_path)

            template = IRTemplateConfig(
                company=CompanyInfo(
                    sec_code="72030",
                    name="Test",
                ),
                ir_page=IRPageConfig(
                    base_url="https://example.com/ir/",
                    sections={
                        "earnings": SectionConfig(
                            url="/earnings",
                            selector="a.pdf",
                        ),
                    },
                ),
            )

            mock_scraper = MagicMock()

            with patch(
                "company_research_agent.clients.ir_scraper.template_loader.TemplateLoader"
            ) as MockLoader:
                mock_loader = MockLoader.return_value
                mock_loader.scrape_with_template = AsyncMock(side_effect=Exception("Error"))

                result = await generator.validate_template(mock_scraper, template)

            assert result["earnings"] == -1
