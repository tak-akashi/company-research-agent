"""Tests for IR schemas."""

from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from company_research_agent.schemas.ir_schemas import (
    CompanyInfo,
    ExtractedLink,
    ExtractedLinksResponse,
    ImpactPoint,
    ImpactPointResponse,
    IRDocument,
    IRPageConfig,
    IRSummary,
    IRSummaryResponse,
    IRTemplateConfig,
    SectionConfig,
)


class TestImpactPoint:
    """Tests for ImpactPoint dataclass."""

    def test_create_bullish_impact(self) -> None:
        """bullishラベルのImpactPointを作成できること."""
        point = ImpactPoint(label="bullish", content="売上高が前年比20%増加")
        assert point.label == "bullish"
        assert point.content == "売上高が前年比20%増加"

    def test_create_bearish_impact(self) -> None:
        """bearishラベルのImpactPointを作成できること."""
        point = ImpactPoint(label="bearish", content="利益率が低下")
        assert point.label == "bearish"
        assert point.content == "利益率が低下"

    def test_create_warning_impact(self) -> None:
        """warningラベルのImpactPointを作成できること."""
        point = ImpactPoint(label="warning", content="訴訟リスクあり")
        assert point.label == "warning"
        assert point.content == "訴訟リスクあり"


class TestIRSummary:
    """Tests for IRSummary dataclass."""

    def test_create_summary_with_points(self) -> None:
        """影響ポイント付きの要約を作成できること."""
        points = [
            ImpactPoint(label="bullish", content="好材料1"),
            ImpactPoint(label="bearish", content="悪材料1"),
        ]
        summary = IRSummary(overview="全体要約テキスト", impact_points=points)
        assert summary.overview == "全体要約テキスト"
        assert len(summary.impact_points) == 2

    def test_create_summary_default_empty_points(self) -> None:
        """デフォルトで空の影響ポイントリストが作成されること."""
        summary = IRSummary(overview="要約のみ")
        assert summary.impact_points == []


class TestIRDocument:
    """Tests for IRDocument dataclass."""

    def test_create_minimal_document(self) -> None:
        """最小限の情報でIRDocumentを作成できること."""
        doc = IRDocument(
            title="決算説明会資料",
            url="https://example.com/ir/doc.pdf",
            category="earnings",
        )
        assert doc.title == "決算説明会資料"
        assert doc.url == "https://example.com/ir/doc.pdf"
        assert doc.category == "earnings"
        assert doc.published_date is None
        assert doc.file_path is None
        assert doc.summary is None
        assert doc.is_skipped is False

    def test_create_full_document(self) -> None:
        """全ての情報を含むIRDocumentを作成できること."""
        summary = IRSummary(overview="要約")
        doc = IRDocument(
            title="決算説明会資料",
            url="https://example.com/ir/doc.pdf",
            category="earnings",
            published_date=date(2024, 1, 15),
            file_path=Path("/data/ir/7203/earnings/doc.pdf"),
            summary=summary,
            is_skipped=True,
        )
        assert doc.published_date == date(2024, 1, 15)
        assert doc.file_path == Path("/data/ir/7203/earnings/doc.pdf")
        assert doc.summary.overview == "要約"
        assert doc.is_skipped is True


class TestSectionConfig:
    """Tests for SectionConfig Pydantic model."""

    def test_create_minimal_section(self) -> None:
        """最小限の情報でSectionConfigを作成できること."""
        config = SectionConfig(url="/ir/library", selector=".document-list a")
        assert config.url == "/ir/library"
        assert config.selector == ".document-list a"
        assert config.link_pattern is None
        assert config.date_selector is None

    def test_create_full_section(self) -> None:
        """全ての情報を含むSectionConfigを作成できること."""
        config = SectionConfig(
            url="/ir/library",
            selector=".document-list a",
            link_pattern=r".*\.pdf$",
            date_selector=".date",
            date_format="%Y年%m月%d日",
        )
        assert config.link_pattern == r".*\.pdf$"
        assert config.date_selector == ".date"
        assert config.date_format == "%Y年%m月%d日"


class TestIRPageConfig:
    """Tests for IRPageConfig Pydantic model."""

    def test_create_ir_page_config(self) -> None:
        """IRPageConfigを作成できること."""
        config = IRPageConfig(
            base_url="https://example.com/ir",
            sections={
                "earnings": SectionConfig(url="/library", selector=".earnings a"),
                "news": SectionConfig(url="/news", selector=".news-item a"),
            },
        )
        assert config.base_url == "https://example.com/ir"
        assert "earnings" in config.sections
        assert "news" in config.sections


class TestCompanyInfo:
    """Tests for CompanyInfo Pydantic model."""

    def test_create_company_info(self) -> None:
        """CompanyInfoを作成できること."""
        info = CompanyInfo(sec_code="72030", name="トヨタ自動車")
        assert info.sec_code == "72030"
        assert info.name == "トヨタ自動車"
        assert info.edinet_code is None

    def test_create_company_info_with_edinet(self) -> None:
        """EDINETコード付きでCompanyInfoを作成できること."""
        info = CompanyInfo(sec_code="72030", name="トヨタ自動車", edinet_code="E02144")
        assert info.edinet_code == "E02144"

    def test_invalid_sec_code_raises_error(self) -> None:
        """不正な証券コードでエラーが発生すること."""
        with pytest.raises(ValidationError):
            CompanyInfo(sec_code="1234", name="Test")  # 4桁は不正

    def test_invalid_edinet_code_raises_error(self) -> None:
        """不正なEDINETコードでエラーが発生すること."""
        with pytest.raises(ValidationError):
            CompanyInfo(sec_code="12340", name="Test", edinet_code="X12345")


class TestIRTemplateConfig:
    """Tests for IRTemplateConfig Pydantic model."""

    def test_create_template_config(self) -> None:
        """IRTemplateConfigを作成できること."""
        config = IRTemplateConfig(
            company=CompanyInfo(sec_code="72030", name="トヨタ自動車"),
            ir_page=IRPageConfig(
                base_url="https://global.toyota/jp/ir/",
                sections={
                    "earnings": SectionConfig(url="library/index.html", selector=".ir-list a")
                },
            ),
        )
        assert config.company.sec_code == "72030"
        assert config.ir_page.base_url == "https://global.toyota/jp/ir/"
        assert config.custom_class is None

    def test_create_template_with_custom_class(self) -> None:
        """カスタムクラス指定付きでIRTemplateConfigを作成できること."""
        config = IRTemplateConfig(
            company=CompanyInfo(sec_code="72030", name="トヨタ自動車"),
            ir_page=IRPageConfig(base_url="https://example.com"),
            custom_class="toyota.ToyotaScraper",
        )
        assert config.custom_class == "toyota.ToyotaScraper"


class TestExtractedLink:
    """Tests for ExtractedLink Pydantic model."""

    def test_create_extracted_link(self) -> None:
        """ExtractedLinkを作成できること."""
        link = ExtractedLink(
            title="2024年3月期 決算説明会資料",
            url="https://example.com/ir/doc.pdf",
            category="earnings",
            published_date="2024-05-15",
            confidence=0.95,
        )
        assert link.title == "2024年3月期 決算説明会資料"
        assert link.category == "earnings"
        assert link.confidence == 0.95

    def test_confidence_bounds(self) -> None:
        """confidenceが0-1の範囲内であること."""
        # 範囲外の値でエラー
        with pytest.raises(ValidationError):
            ExtractedLink(
                title="Test",
                url="https://example.com",
                category="news",
                confidence=1.5,
            )


class TestExtractedLinksResponse:
    """Tests for ExtractedLinksResponse Pydantic model."""

    def test_create_response(self) -> None:
        """ExtractedLinksResponseを作成できること."""
        response = ExtractedLinksResponse(
            links=[
                ExtractedLink(
                    title="Doc1",
                    url="https://example.com/1.pdf",
                    category="earnings",
                )
            ],
            page_description="企業のIRページ",
        )
        assert len(response.links) == 1
        assert response.page_description == "企業のIRページ"


class TestIRSummaryResponse:
    """Tests for IRSummaryResponse Pydantic model."""

    def test_create_summary_response(self) -> None:
        """IRSummaryResponseを作成できること."""
        response = IRSummaryResponse(
            overview="2024年3月期は増収増益となった。",
            impact_points=[
                ImpactPointResponse(label="bullish", content="売上高20%増"),
            ],
        )
        assert "増収増益" in response.overview
        assert len(response.impact_points) == 1
        assert response.impact_points[0].label == "bullish"
