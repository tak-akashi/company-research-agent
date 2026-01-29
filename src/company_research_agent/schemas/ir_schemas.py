"""IR資料取得に関するスキーマ定義."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

# =============================================================================
# 内部ドメインモデル（dataclass）
# =============================================================================


@dataclass
class ImpactPoint:
    """株価影響ポイント.

    IR資料から抽出された、株価に影響を与える可能性のある情報。

    Attributes:
        label: 影響の方向性（bullish=上昇要因, bearish=下落要因, warning=注意事項）
        content: 影響ポイントの内容
    """

    label: Literal["bullish", "bearish", "warning"]
    content: str


@dataclass
class IRSummary:
    """IR資料の要約結果.

    LLMによる要約処理の結果を格納する。

    Attributes:
        overview: 全体要約（100-200文字）
        impact_points: 株価影響ポイントのリスト（最大5件）
    """

    overview: str
    impact_points: list[ImpactPoint] = field(default_factory=list)


@dataclass
class IRDocument:
    """IR資料のメタデータ.

    取得したIR資料の情報を格納する。

    Attributes:
        title: 資料タイトル
        url: 資料のURL
        category: カテゴリ（earnings=決算関連, news=事業ニュース, disclosures=適時開示）
        published_date: 公開日（不明な場合はNone）
        file_path: ダウンロード後のローカルパス（未ダウンロードの場合はNone）
        summary: LLMによる要約結果（未要約の場合はNone）
        is_skipped: 既存ファイルによりダウンロードがスキップされた場合True
    """

    title: str
    url: str
    category: Literal["earnings", "news", "disclosures"]
    published_date: date | None = None
    file_path: Path | None = None
    summary: IRSummary | None = None
    is_skipped: bool = False


# =============================================================================
# Pydanticモデル（YAMLテンプレート設定）
# =============================================================================


class SectionConfig(BaseModel):
    """IRページのセクション設定.

    YAMLテンプレートで使用するセクション単位の設定。

    Attributes:
        url: セクションのURL（相対または絶対パス）
        selector: BeautifulSoupで使用するCSSセレクター
        link_pattern: PDFリンクを抽出するための正規表現パターン（オプション）
        date_selector: 公開日を抽出するためのCSSセレクター（オプション）
        date_format: 公開日のフォーマット（strptime形式、オプション）
    """

    url: str = Field(..., description="セクションのURL")
    selector: str = Field(..., description="資料リンクを抽出するCSSセレクター")
    link_pattern: str | None = Field(
        default=None, description="PDFリンクを抽出する正規表現パターン"
    )
    date_selector: str | None = Field(default=None, description="公開日を抽出するCSSセレクター")
    date_format: str | None = Field(
        default=None, description="公開日のフォーマット（例: %Y年%m月%d日）"
    )


class IRPageConfig(BaseModel):
    """IRページ全体の設定.

    企業のIRページに関する設定。

    Attributes:
        base_url: IRページのベースURL
        sections: カテゴリ別のセクション設定
    """

    base_url: str = Field(..., description="IRページのベースURL")
    sections: dict[str, SectionConfig] = Field(
        default_factory=dict, description="カテゴリ別のセクション設定"
    )


class CompanyInfo(BaseModel):
    """企業情報.

    テンプレートで使用する企業の基本情報。

    Attributes:
        sec_code: 証券コード（5桁）
        name: 企業名
        edinet_code: EDINETコード（オプション）
    """

    sec_code: str = Field(..., pattern=r"^\d{5}$", description="証券コード（5桁）")
    name: str = Field(..., description="企業名")
    edinet_code: str | None = Field(default=None, pattern=r"^E\d{5}$", description="EDINETコード")


class IRTemplateConfig(BaseModel):
    """IRテンプレートの設定.

    企業ごとのIRページスクレイピング設定を格納する。
    YAMLファイルから読み込まれる。

    Attributes:
        company: 企業情報
        ir_page: IRページ設定
        custom_class: カスタムスクレイパークラス名（オプション）
    """

    company: CompanyInfo = Field(..., description="企業情報")
    ir_page: IRPageConfig = Field(..., description="IRページ設定")
    custom_class: str | None = Field(
        default=None,
        description="カスタムスクレイパークラス名（Pythonオーバーライド用）",
    )


# =============================================================================
# LLM構造化出力用モデル
# =============================================================================


class ExtractedLink(BaseModel):
    """LLMが抽出したリンク情報.

    アドホック解析でLLMがページから抽出したリンク情報。

    Attributes:
        title: 資料タイトル
        url: 資料のURL
        category: 推測されたカテゴリ
        published_date: 推測された公開日（YYYY-MM-DD形式、不明な場合は空文字）
        confidence: 抽出の確信度（0.0-1.0）
    """

    title: str = Field(..., description="資料タイトル")
    url: str = Field(..., description="資料のURL")
    category: Literal["earnings", "news", "disclosures"] = Field(
        ..., description="カテゴリ（earnings=決算関連, news=事業ニュース, disclosures=適時開示）"
    )
    published_date: str = Field(default="", description="公開日（YYYY-MM-DD形式、空=不明）")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="抽出の確信度（0.0-1.0）")


class ExtractedLinksResponse(BaseModel):
    """LLMによるリンク抽出結果.

    LLMのstructured outputとして使用する。

    Attributes:
        links: 抽出されたリンクのリスト
        page_description: ページの概要説明
    """

    links: list[ExtractedLink] = Field(default_factory=list, description="抽出されたリンクのリスト")
    page_description: str = Field(default="", description="ページの概要説明")


class IRSummaryResponse(BaseModel):
    """IR資料要約のLLM出力.

    LLMのstructured outputとして使用する。

    Attributes:
        overview: 全体要約（100-200文字）
        impact_points: 株価影響ポイントのリスト
    """

    overview: str = Field(..., description="全体要約（100-200文字）")
    impact_points: list[ImpactPointResponse] = Field(
        default_factory=list, description="株価影響ポイント（最大5件）"
    )


class ImpactPointResponse(BaseModel):
    """株価影響ポイントのLLM出力.

    Attributes:
        label: 影響の方向性
        content: 影響ポイントの内容
    """

    label: Literal["bullish", "bearish", "warning"] = Field(
        ..., description="影響の方向性（bullish=上昇要因, bearish=下落要因, warning=注意事項）"
    )
    content: str = Field(..., description="影響ポイントの内容")


# IRSummaryResponseのforward referenceを解決
IRSummaryResponse.model_rebuild()


# =============================================================================
# テンプレート生成用モデル
# =============================================================================


class DiscoveredSection(BaseModel):
    """発見されたIRページセクション.

    LLMがページ解析で発見したセクション情報。

    Attributes:
        category: カテゴリ（earnings/news/disclosures）
        url: セクションのURL（相対パス推奨）
        selector: PDFリンクを抽出するCSSセレクター
        link_pattern: リンクURLをフィルタリングする正規表現（オプション）
        date_selector: 日付を抽出するCSSセレクター（オプション）
        date_format: 日付フォーマット（オプション）
        confidence: 発見の確信度
    """

    category: Literal["earnings", "news", "disclosures"] = Field(..., description="カテゴリ")
    url: str = Field(..., description="セクションのURL（相対または絶対パス）")
    selector: str = Field(..., description="PDFリンクを抽出するCSSセレクター")
    link_pattern: str | None = Field(
        default=None, description="リンクURLをフィルタリングする正規表現"
    )
    date_selector: str | None = Field(default=None, description="日付を抽出するCSSセレクター")
    date_format: str | None = Field(default=None, description="日付フォーマット")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="発見の確信度")


class IRPageAnalysisResponse(BaseModel):
    """IRページ解析結果.

    LLMによるIRページ構造解析の結果。

    Attributes:
        base_url: IRページのベースURL
        sections: 発見されたセクションのリスト
        notes: 解析に関する補足情報
    """

    base_url: str = Field(..., description="IRページのベースURL")
    sections: list[DiscoveredSection] = Field(
        default_factory=list, description="発見されたセクション"
    )
    notes: str = Field(default="", description="解析に関する補足情報")
