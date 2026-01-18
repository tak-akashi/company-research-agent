"""自然言語検索オーケストレーター用スキーマ."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


@dataclass
class CompanyInfo:
    """企業情報.

    EDINETコードリストから取得した企業の基本情報。

    Attributes:
        edinet_code: EDINETコード（例: E02144）
        sec_code: 証券コード（5桁、例: 72030）。未上場の場合はNone。
        company_name: 企業名
        company_name_kana: 企業名（カナ）
        company_name_en: 企業名（英語）
        listing_code: 上場区分コード
        industry_code: 業種コード
    """

    edinet_code: str
    sec_code: str | None
    company_name: str
    company_name_kana: str | None
    company_name_en: str | None
    listing_code: str | None
    industry_code: str | None


@dataclass
class CompanyCandidate:
    """企業候補（検索結果）.

    企業名検索で見つかった候補と類似度スコア。

    Attributes:
        company: 企業情報
        similarity_score: 類似度スコア（0-100）。100が完全一致。
        match_field: マッチしたフィールド（"company_name", "company_name_kana", etc.）
    """

    company: CompanyInfo
    similarity_score: float
    match_field: str


class ComparisonItem(BaseModel):
    """比較項目.

    企業間の比較結果の1項目。
    """

    aspect: str = Field(description="比較観点（例: 事業内容、財務状況）")
    company_a: str = Field(description="企業Aの内容")
    company_b: str = Field(description="企業Bの内容")
    difference: str = Field(description="主な違い")


class ComparisonReport(BaseModel):
    """比較分析レポート.

    複数書類の比較分析結果。
    """

    documents: list[str] = Field(description="比較した書類ID")
    aspects: list[str] = Field(description="比較観点")
    comparisons: list[ComparisonItem] = Field(description="比較結果")
    summary: str = Field(description="総括")


class Summary(BaseModel):
    """要約レポート.

    書類の要約結果。
    """

    doc_id: str = Field(description="書類ID")
    focus: str | None = Field(default=None, description="要約の焦点")
    key_points: list[str] = Field(description="重要ポイント")
    summary_text: str = Field(description="要約テキスト")


class DocumentResultMetadata(BaseModel):
    """分析対象書類のメタデータ.

    分析結果に含まれる書類の識別情報。
    """

    doc_id: str = Field(description="書類ID（S100XXXX形式）")
    filer_name: str | None = Field(default=None, description="企業名")
    doc_description: str | None = Field(
        default=None,
        description="書類タイトル（例: 有価証券報告書－第45期(2024/04/01－2025/03/31)）",
    )
    period_start: str | None = Field(default=None, description="対象期間開始日（YYYY-MM-DD）")
    period_end: str | None = Field(default=None, description="対象期間終了日（YYYY-MM-DD）")


class OrchestratorResult(BaseModel):
    """オーケストレーター結果.

    自然言語クエリの処理結果。
    """

    query: str = Field(description="元のクエリ")
    intent: str = Field(description="判定された意図（検索/分析/比較/要約）")
    result: Any = Field(description="処理結果")
    tools_used: list[str] = Field(default_factory=list, description="使用したツール")
    documents: list[DocumentResultMetadata] = Field(
        default_factory=list,
        description="分析対象書類のメタデータ",
    )
