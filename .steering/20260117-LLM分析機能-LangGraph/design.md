# 設計書

## アーキテクチャ概要

LangGraphを使用したワークフローベースのアーキテクチャを採用し、各分析機能をノードとして構造化する。

```
┌─────────────────────────────────────────────────────────────┐
│   ワークフローレイヤー (workflows/)  ← 今回の実装対象        │
│   └─ AnalysisGraph: LangGraphベースのワークフロー管理        │
│   └─ nodes/: 各分析ノードの実装                              │
├─────────────────────────────────────────────────────────────┤
│   スキーマレイヤー (schemas/)                                │
│   └─ llm_analysis.py: 分析結果のデータ構造定義              │
├─────────────────────────────────────────────────────────────┤
│   プロンプトレイヤー (prompts/)                              │
│   └─ 各分析機能用のプロンプトテンプレート                    │
├─────────────────────────────────────────────────────────────┤
│   既存レイヤー                                               │
│   └─ clients/gemini_client.py: LLM API呼び出し             │
│   └─ parsers/pdf_parser.py: PDF解析                        │
│   └─ services/edinet_document_service.py: EDINET連携        │
└─────────────────────────────────────────────────────────────┘
```

## ワークフロー構成（並列フロー）

```
                    ┌─────────────────┐
                    │  EDINETNode     │
                    │  (書類取得)      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  PDFParseNode   │
                    │  (マークダウン化) │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
┌────────▼────────┐ ┌────────▼────────┐ ┌────────▼────────┐
│ BusinessSummary │ │ RiskExtraction  │ │ FinancialAnalysis│
│    Node         │ │     Node        │ │      Node        │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │ PeriodComparison │
                    │     Node        │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Aggregator     │
                    │     Node        │
                    └─────────────────┘
```

## コンポーネント設計

### 1. AnalysisState（workflows/state.py）

**責務**:
- 各ノード間で共有する状態の管理
- 入力・中間結果・出力の保持

**クラス構造**:
```python
from typing import TypedDict
from company_research_agent.schemas.llm_analysis import (
    BusinessSummary,
    RiskAnalysis,
    FinancialAnalysis,
    PeriodComparison,
    ComprehensiveReport,
)

class AnalysisState(TypedDict):
    """LLM分析ワークフローの状態."""

    # 入力
    doc_id: str
    prior_doc_id: str | None

    # 中間結果（PDFパス）
    pdf_path: str | None
    prior_pdf_path: str | None

    # 中間結果（マークダウン）
    markdown_content: str | None
    prior_markdown_content: str | None

    # 個別出力（各ノードの結果）
    business_summary: BusinessSummary | None
    risk_analysis: RiskAnalysis | None
    financial_analysis: FinancialAnalysis | None
    period_comparison: PeriodComparison | None

    # 統合出力
    comprehensive_report: ComprehensiveReport | None

    # メタデータ
    errors: list[str]
    completed_nodes: list[str]
```

### 2. 分析結果スキーマ（schemas/llm_analysis.py）

**クラス構造**:
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

type RiskCategory = Literal[
    "market", "operational", "financial", "regulatory",
    "technology", "human_resource", "environmental", "other"
]
type ChangeDirection = Literal["positive", "negative", "neutral"]
type Significance = Literal["high", "medium", "low"]

@dataclass
class BusinessSummary:
    """事業状況・経営分析の要約."""
    company_name: str
    fiscal_year: str
    business_overview: str
    management_analysis: str
    key_points: list[str]
    generated_at: datetime = field(default_factory=datetime.now)

@dataclass
class RiskItem:
    """リスク項目."""
    category: RiskCategory
    title: str
    description: str
    likelihood: Significance
    impact: Significance
    mitigation: str | None = None

@dataclass
class RiskAnalysis:
    """リスク分析結果."""
    company_name: str
    fiscal_year: str
    risks: list[RiskItem]
    risk_summary: str
    key_risks: list[str]
    generated_at: datetime = field(default_factory=datetime.now)

@dataclass
class FinancialHighlight:
    """財務ハイライト."""
    item_name: str
    value: str
    unit: str
    change_from_prior: str | None = None
    significance: Significance = "medium"
    comment: str | None = None

@dataclass
class FinancialAnalysis:
    """財務分析結果."""
    company_name: str
    fiscal_year: str
    highlights: list[FinancialHighlight]
    strengths: list[str]
    concerns: list[str]
    trend_analysis: str
    generated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ChangePoint:
    """変化点."""
    area: str
    prior_state: str
    current_state: str
    direction: ChangeDirection
    significance: Significance
    analysis: str

@dataclass
class PeriodComparison:
    """前期比較結果."""
    company_name: str
    current_fiscal_year: str
    prior_fiscal_year: str
    change_points: list[ChangePoint]
    improvement_areas: list[str]
    concern_areas: list[str]
    overall_assessment: str
    generated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ComprehensiveReport:
    """包括的分析レポート."""
    company_name: str
    fiscal_year: str
    business_summary: BusinessSummary
    risk_analysis: RiskAnalysis
    financial_analysis: FinancialAnalysis
    period_comparison: PeriodComparison | None = None
    investment_considerations: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
```

### 3. ノード基底クラス（workflows/nodes/base.py）

**責務**:
- 各ノードの共通インターフェース定義
- エラーハンドリングの統一

**クラス構造**:
```python
from abc import ABC, abstractmethod
from typing import TypeVar
from company_research_agent.workflows.state import AnalysisState

T = TypeVar("T")

class BaseNode(ABC):
    """分析ノードの基底クラス."""

    @property
    @abstractmethod
    def name(self) -> str:
        """ノード名."""
        ...

    @abstractmethod
    def __call__(self, state: AnalysisState) -> dict:
        """ノードを実行し、状態の更新分を返す."""
        ...
```

### 4. 各分析ノード（workflows/nodes/）

| ノード | ファイル | 責務 |
|-------|---------|------|
| EDINETNode | edinet_node.py | doc_idからPDFをダウンロード |
| PDFParseNode | pdf_parse_node.py | PDFをマークダウンに変換 |
| BusinessSummaryNode | business_summary_node.py | 事業・経営分析の要約 |
| RiskExtractionNode | risk_extraction_node.py | リスク要因の抽出 |
| FinancialAnalysisNode | financial_analysis_node.py | 財務データの分析 |
| PeriodComparisonNode | period_comparison_node.py | 前期比較 |
| AggregatorNode | aggregator_node.py | 結果の統合 |

### 5. グラフ構築（workflows/graph.py）

**責務**:
- LangGraphのStateGraphを構築
- ノードの登録とエッジの設定
- 並列実行の設定

**クラス構造**:
```python
from langgraph.graph import StateGraph, END
from company_research_agent.workflows.state import AnalysisState
from company_research_agent.workflows.nodes import (
    EDINETNode,
    PDFParseNode,
    BusinessSummaryNode,
    RiskExtractionNode,
    FinancialAnalysisNode,
    PeriodComparisonNode,
    AggregatorNode,
)

class AnalysisGraph:
    """LLM分析ワークフローのグラフ."""

    def __init__(self) -> None:
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """グラフを構築する."""
        graph = StateGraph(AnalysisState)

        # ノードの登録
        graph.add_node("edinet", EDINETNode())
        graph.add_node("pdf_parse", PDFParseNode())
        graph.add_node("business_summary", BusinessSummaryNode())
        graph.add_node("risk_extraction", RiskExtractionNode())
        graph.add_node("financial_analysis", FinancialAnalysisNode())
        graph.add_node("period_comparison", PeriodComparisonNode())
        graph.add_node("aggregator", AggregatorNode())

        # エッジの設定
        graph.set_entry_point("edinet")
        graph.add_edge("edinet", "pdf_parse")

        # 並列分岐
        graph.add_edge("pdf_parse", "business_summary")
        graph.add_edge("pdf_parse", "risk_extraction")
        graph.add_edge("pdf_parse", "financial_analysis")

        # 合流
        graph.add_edge("business_summary", "period_comparison")
        graph.add_edge("risk_extraction", "period_comparison")
        graph.add_edge("financial_analysis", "period_comparison")

        graph.add_edge("period_comparison", "aggregator")
        graph.add_edge("aggregator", END)

        return graph.compile()

    def run_full_analysis(
        self,
        doc_id: str,
        prior_doc_id: str | None = None,
    ) -> AnalysisState:
        """全ワークフローを実行する."""
        initial_state: AnalysisState = {
            "doc_id": doc_id,
            "prior_doc_id": prior_doc_id,
            "pdf_path": None,
            "prior_pdf_path": None,
            "markdown_content": None,
            "prior_markdown_content": None,
            "business_summary": None,
            "risk_analysis": None,
            "financial_analysis": None,
            "period_comparison": None,
            "comprehensive_report": None,
            "errors": [],
            "completed_nodes": [],
        }
        return self._graph.invoke(initial_state)

    def run_single_node(
        self,
        node_name: str,
        doc_id: str,
    ) -> AnalysisState:
        """個別ノードを実行する."""
        # 部分グラフを構築して実行
        ...
```

## プロンプト設計

### プロンプトテンプレート（prompts/）

各分析ノード用のプロンプトを個別ファイルで管理:

```python
# prompts/business_summary.py
BUSINESS_SUMMARY_PROMPT = """
あなたは日本の上場企業の有価証券報告書を分析する専門家です。
以下の有価証券報告書の内容を分析し、事業の状況と経営者による分析を要約してください。

## 入力
{content}

## 出力形式
以下のJSON形式で出力してください：

```json
{{
    "company_name": "企業名",
    "fiscal_year": "2024年3月期",
    "business_overview": "事業概要の要約（200-300文字）",
    "management_analysis": "経営者による分析の要約（200-300文字）",
    "key_points": [
        "重要ポイント1",
        "重要ポイント2",
        "重要ポイント3（最大5件）"
    ]
}}
```

## 注意事項
- 数値は正確に引用してください
- 専門用語は適切に使用してください
- 重要ポイントは投資判断に関連する情報を優先してください
""".strip()
```

## データフロー

### 全ワークフロー実行時

```
1. ユーザーがdoc_id（とprior_doc_id）を指定
2. EDINETNodeがPDFをダウンロード
3. PDFParseNodeがマークダウンに変換
4. 3つの分析ノードが並列実行
   - BusinessSummaryNode: 事業要約
   - RiskExtractionNode: リスク抽出
   - FinancialAnalysisNode: 財務分析
5. PeriodComparisonNodeが前期比較（prior_doc_idがある場合）
6. AggregatorNodeが結果を統合
7. ComprehensiveReportとして返却
```

### 個別ノード実行時

```
1. ユーザーがノード名とdoc_idを指定
2. 必要な前段ノード（EDINET、PDFParse）を自動実行
3. 指定されたノードを実行
4. 個別結果を返却
```

## エラーハンドリング戦略

### カスタムエラークラス

```python
# core/exceptions.py に追加

@dataclass
class LLMAnalysisError(CompanyResearchAgentError):
    """LLM分析に関するエラー."""
    message: str
    node_name: str | None = None
    model: str | None = None
```

### エラーハンドリングパターン

- **EDINET取得失敗**: EDINETAPIErrorをStateのerrorsに記録し、後続ノードをスキップ
- **PDF解析失敗**: PDFParseErrorをStateのerrorsに記録し、後続ノードをスキップ
- **LLM API失敗**: リトライ後、LLMAnalysisErrorをStateのerrorsに記録
- **JSONパース失敗**: 再度LLMに修正を依頼、失敗時はerrorsに記録

## テスト戦略

### ユニットテスト（tests/unit/workflows/）
- 各ノードの単体テスト
- State変更の検証
- エラーケースのテスト

### 統合テスト（tests/integration/）
- ノード間の連携テスト
- 並列実行の検証

### E2Eテスト（tests/e2e/）
- 実際の有報PDFを使用した全ワークフローテスト
- 10社×2期のテストデータで検証

## ディレクトリ構造

```
src/company_research_agent/
├── workflows/                    # 新規ディレクトリ
│   ├── __init__.py
│   ├── state.py                 # AnalysisState
│   ├── graph.py                 # AnalysisGraph
│   └── nodes/
│       ├── __init__.py
│       ├── base.py              # BaseNode
│       ├── edinet_node.py
│       ├── pdf_parse_node.py
│       ├── business_summary_node.py
│       ├── risk_extraction_node.py
│       ├── financial_analysis_node.py
│       ├── period_comparison_node.py
│       └── aggregator_node.py
├── schemas/
│   └── llm_analysis.py          # 新規ファイル
├── prompts/                     # 新規ディレクトリ
│   ├── __init__.py
│   ├── business_summary.py
│   ├── risk_extraction.py
│   ├── financial_analysis.py
│   └── period_comparison.py
└── core/
    └── exceptions.py            # LLMAnalysisError追加

tests/
├── unit/
│   └── workflows/
│       ├── __init__.py
│       ├── test_state.py
│       ├── test_graph.py
│       └── nodes/
│           ├── __init__.py
│           ├── test_business_summary_node.py
│           ├── test_risk_extraction_node.py
│           ├── test_financial_analysis_node.py
│           └── test_period_comparison_node.py
├── integration/
│   └── workflows/
│       └── test_workflow_integration.py
└── e2e/
    └── test_analysis_workflow.py
```

## 依存ライブラリ

既存のpyproject.tomlで定義済み:

```toml
[project]
dependencies = [
    "langgraph>=1.0.0",
    "langchain>=1.0.0",
    "langchain-google-genai>=2.1.0",
]
```

## 実装の順序

### フェーズ3.1: 基盤整備
1. `schemas/llm_analysis.py` - 分析結果スキーマ
2. `workflows/state.py` - AnalysisState
3. `workflows/nodes/base.py` - ノード基底クラス
4. `core/exceptions.py` - LLMAnalysisError追加

### フェーズ3.2: 各ノード実装
1. `workflows/nodes/edinet_node.py`
2. `workflows/nodes/pdf_parse_node.py`
3. `prompts/business_summary.py` + `workflows/nodes/business_summary_node.py`
4. `prompts/risk_extraction.py` + `workflows/nodes/risk_extraction_node.py`
5. `prompts/financial_analysis.py` + `workflows/nodes/financial_analysis_node.py`
6. `prompts/period_comparison.py` + `workflows/nodes/period_comparison_node.py`
7. `workflows/nodes/aggregator_node.py`

### フェーズ3.3: ワークフロー統合
1. `workflows/graph.py` - グラフ構築
2. 並列実行の設定
3. E2Eテスト

## セキュリティ考慮事項

- プロンプトインジェクション対策（入力のサニタイズ）
- APIキーの適切な管理（環境変数経由）
- 機密情報のログ出力防止

## パフォーマンス考慮事項

- 並列実行による処理時間短縮
- 長文テキストのチャンク分割
- LLM APIのレート制限対応（既存のGeminiClientを活用）

## 将来の拡張性

- Human-in-the-loop機能の追加
- ベクトル検索との統合
- 追加の分析ノード（競合分析、業界分析等）
- 非同期処理のサポート
