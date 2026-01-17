"""LLM分析結果のスキーマ定義.

有価証券報告書のLLM分析機能で使用する出力スキーマを定義する。
各スキーマはLangGraphワークフローのノード出力として使用される。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """重要度レベル."""

    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


class RiskCategory(str, Enum):
    """リスクカテゴリ."""

    MARKET = "市場リスク"
    REGULATORY = "規制リスク"
    FINANCIAL = "財務リスク"
    OPERATIONAL = "オペレーショナルリスク"
    STRATEGIC = "戦略リスク"
    TECHNOLOGY = "技術リスク"
    ENVIRONMENTAL = "環境リスク"
    REPUTATION = "レピュテーションリスク"
    OTHER = "その他"


class ChangeCategory(str, Enum):
    """変化点カテゴリ."""

    BUSINESS = "事業"
    FINANCIAL = "財務"
    RISK = "リスク"
    STRATEGY = "戦略"
    GOVERNANCE = "ガバナンス"
    ORGANIZATION = "組織"
    OTHER = "その他"


# =============================================================================
# 事業要約 (BusinessSummary)
# =============================================================================


class BusinessSegment(BaseModel):
    """事業セグメント."""

    name: str = Field(..., description="セグメント名")
    description: str = Field(..., description="セグメントの説明")
    revenue_share: str | None = Field(None, description="売上構成比（例: '35%'）")
    key_products: list[str] = Field(default_factory=list, description="主要製品・サービス")


class BusinessSummary(BaseModel):
    """事業要約の出力スキーマ.

    有価証券報告書の「事業の状況」セクションから抽出された
    企業の事業概要、戦略、競争優位性などの情報。
    """

    company_name: str = Field(..., description="企業名")
    fiscal_year: str = Field(..., description="対象会計年度（例: '2024年3月期'）")
    business_description: str = Field(..., description="事業概要（200-500字程度）")
    main_products_services: list[str] = Field(
        default_factory=list, description="主要製品・サービス"
    )
    business_segments: list[BusinessSegment] = Field(
        default_factory=list, description="事業セグメント"
    )
    competitive_advantages: list[str] = Field(default_factory=list, description="競争優位性")
    growth_strategy: str = Field(..., description="成長戦略の概要")
    key_initiatives: list[str] = Field(default_factory=list, description="重点施策")


# =============================================================================
# リスク分析 (RiskAnalysis)
# =============================================================================


class RiskItem(BaseModel):
    """リスク項目."""

    category: RiskCategory = Field(..., description="リスクカテゴリ")
    title: str = Field(..., description="リスクタイトル")
    description: str = Field(..., description="リスク説明（100-300字程度）")
    severity: Severity = Field(..., description="重要度")
    mitigation: str | None = Field(None, description="対策・軽減策")


class RiskAnalysis(BaseModel):
    """リスク分析の出力スキーマ.

    有価証券報告書の「事業等のリスク」セクションから抽出された
    リスク要因の一覧と分類。
    """

    risks: list[RiskItem] = Field(default_factory=list, description="リスク一覧")
    new_risks: list[str] = Field(default_factory=list, description="新規リスク（前期比較時のみ）")
    risk_summary: str = Field(..., description="リスク総括（200-400字程度）")


# =============================================================================
# 財務分析 (FinancialAnalysis)
# =============================================================================


class FinancialHighlight(BaseModel):
    """財務ハイライト."""

    metric_name: str = Field(..., description="指標名（例: '売上高'）")
    current_value: str = Field(..., description="当期値（例: '1兆2,345億円'）")
    prior_value: str | None = Field(None, description="前期値")
    change_rate: str | None = Field(None, description="増減率（例: '+5.3%'）")
    comment: str = Field(..., description="コメント")


class FinancialAnalysis(BaseModel):
    """財務分析の出力スキーマ.

    有価証券報告書の財務セクションから抽出された
    財務状況、業績分析、キャッシュフロー分析など。
    """

    revenue_analysis: str = Field(..., description="売上分析（200-400字程度）")
    profit_analysis: str = Field(..., description="利益分析（200-400字程度）")
    cash_flow_analysis: str = Field(..., description="キャッシュフロー分析（200-400字程度）")
    financial_position: str = Field(..., description="財政状態（200-400字程度）")
    highlights: list[FinancialHighlight] = Field(default_factory=list, description="財務ハイライト")
    outlook: str = Field(..., description="今後の見通し（200-400字程度）")


# =============================================================================
# 前期比較 (PeriodComparison)
# =============================================================================


class ChangePoint(BaseModel):
    """変化点."""

    category: ChangeCategory = Field(..., description="カテゴリ")
    title: str = Field(..., description="変化タイトル")
    prior_state: str = Field(..., description="前期の状態")
    current_state: str = Field(..., description="当期の状態")
    significance: Severity = Field(..., description="重要度")
    implication: str = Field(..., description="示唆（投資判断への影響）")


class PeriodComparison(BaseModel):
    """前期比較の出力スキーマ.

    当期と前期の有価証券報告書を比較して抽出された
    重要な変化点と新規・終了事項。
    """

    change_points: list[ChangePoint] = Field(default_factory=list, description="変化点一覧")
    new_developments: list[str] = Field(default_factory=list, description="新規展開事項")
    discontinued_items: list[str] = Field(default_factory=list, description="終了・中止事項")
    overall_assessment: str = Field(..., description="総合評価（200-400字程度）")


# =============================================================================
# 統合レポート (ComprehensiveReport)
# =============================================================================


class ComprehensiveReport(BaseModel):
    """統合レポートの出力スキーマ.

    全ての分析結果を統合したレポート。
    投資判断に必要な情報を一覧で提供する。
    """

    executive_summary: str = Field(..., description="エグゼクティブサマリー（300-500字）")
    business_summary: BusinessSummary = Field(..., description="事業要約")
    risk_analysis: RiskAnalysis = Field(..., description="リスク分析")
    financial_analysis: FinancialAnalysis = Field(..., description="財務分析")
    period_comparison: PeriodComparison | None = Field(None, description="前期比較（オプション）")
    investment_highlights: list[str] = Field(
        default_factory=list, description="投資ハイライト（ポジティブ要因）"
    )
    concerns: list[str] = Field(default_factory=list, description="懸念事項（ネガティブ要因）")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成日時")

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}
