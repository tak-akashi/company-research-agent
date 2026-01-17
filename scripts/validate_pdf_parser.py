#!/usr/bin/env python3
"""PDF解析・マークダウン化機能の検証スクリプト.

PRDの受入条件を検証するためのスクリプトです。

使用方法:
    # 基本的な検証（PDFファイルを指定）
    uv run python scripts/validate_pdf_parser.py /path/to/document.pdf

    # 期待値を指定して精度検証
    uv run python scripts/validate_pdf_parser.py /path/to/document.pdf \\
        --expected-sales 1234567 \\
        --expected-operating-profit 123456

    # 特定の解析戦略を指定
    uv run python scripts/validate_pdf_parser.py /path/to/document.pdf --strategy pymupdf4llm

    # Gemini APIを使用（GOOGLE_API_KEY環境変数が必要）
    uv run python scripts/validate_pdf_parser.py /path/to/document.pdf --strategy gemini

    # ページ範囲を指定
    uv run python scripts/validate_pdf_parser.py /path/to/document.pdf --start-page 1 --end-page 10

    # 詳細出力
    uv run python scripts/validate_pdf_parser.py /path/to/document.pdf --verbose

    # 結果をファイルに保存（デフォルトでoutputs/に出力される）
    # 出力先を明示的に指定する場合:
    uv run python scripts/validate_pdf_parser.py /path/to/document.pdf --output result.md

検証項目:
    1. PDFからテキストを抽出できる
    2. 表データをマークダウン形式で出力できる
    3. 日本語の認識精度が95%以上
    4. 1書類（50-100ページ）の解析が5分以内に完了する

Note:
    GOOGLE_API_KEYは.envファイルから読み込まれます（Gemini戦略使用時）。
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

# プロジェクトルートの .env を読み込み
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from company_research_agent.core.types import ParseStrategy
from company_research_agent.parsers.accuracy_benchmark import AccuracyBenchmark
from company_research_agent.parsers.pdf_parser import PDFParser

if TYPE_CHECKING:
    from company_research_agent.parsers.accuracy_benchmark import BenchmarkResult


@dataclass
class ValidationResult:
    """検証結果."""

    pdf_path: str
    total_pages: int
    extracted_text_length: int
    has_tables: bool
    processing_time_seconds: float
    strategy_used: str
    accuracy_result: BenchmarkResult | None = None
    errors: list[str] | None = None

    @property
    def passes_text_extraction(self) -> bool:
        """テキスト抽出が成功したか."""
        return self.extracted_text_length > 0

    @property
    def passes_table_extraction(self) -> bool:
        """表データ抽出が成功したか."""
        return self.has_tables

    @property
    def passes_accuracy(self) -> bool:
        """精度が95%以上か."""
        if self.accuracy_result is None:
            return True  # 期待値未指定の場合はスキップ
        return self.accuracy_result.accuracy >= 95.0

    @property
    def passes_performance(self) -> bool:
        """5分以内に完了したか."""
        return self.processing_time_seconds <= 300.0

    @property
    def all_passed(self) -> bool:
        """全ての検証をパスしたか."""
        return (
            self.passes_text_extraction
            and self.passes_table_extraction
            and self.passes_accuracy
            and self.passes_performance
        )


def validate_pdf(
    pdf_path: Path,
    strategy: ParseStrategy = "auto",
    start_page: int | None = None,
    end_page: int | None = None,
    expected_values: dict[str, str] | None = None,
    company_name: str = "",
    document_id: str = "",
    fiscal_year: int = 0,
    verbose: bool = False,
) -> ValidationResult:
    """PDFの解析を検証.

    Args:
        pdf_path: PDFファイルのパス
        strategy: 解析戦略
        start_page: 開始ページ
        end_page: 終了ページ
        expected_values: 期待される財務項目の値
        company_name: 会社名
        document_id: 書類ID
        fiscal_year: 会計年度
        verbose: 詳細出力

    Returns:
        ValidationResult: 検証結果
    """
    errors: list[str] = []
    parser = PDFParser()

    # 1. PDF情報取得
    if verbose:
        print("  PDFメタデータを取得中...")

    try:
        pdf_info = parser.get_info(pdf_path)
        total_pages = pdf_info.total_pages
        if verbose:
            print(f"  ページ数: {total_pages}")
            print(f"  メタデータ: {pdf_info.metadata}")
    except Exception as e:
        errors.append(f"PDF情報取得エラー: {e}")
        total_pages = 0

    # 2. テキスト抽出・マークダウン変換
    if verbose:
        print(f"  解析戦略: {strategy}")
        print("  テキスト抽出中...")

    start_time = time.perf_counter()

    try:
        result = parser.to_markdown(
            pdf_path,
            start_page=start_page,
            end_page=end_page,
            strategy=strategy,
        )
        extracted_text = result.text
        strategy_used = result.strategy_used
    except Exception as e:
        errors.append(f"テキスト抽出エラー: {e}")
        extracted_text = ""
        strategy_used = strategy

    processing_time = time.perf_counter() - start_time

    if verbose:
        print(f"  処理時間: {processing_time:.2f}秒")
        print(f"  使用戦略: {strategy_used}")
        print(f"  抽出文字数: {len(extracted_text)}")

    # 3. 表データの検出
    has_tables = "|" in extracted_text or "---" in extracted_text

    if verbose:
        print(f"  表データ検出: {'あり' if has_tables else 'なし'}")

    # 4. 精度検証（期待値が指定されている場合）
    accuracy_result = None
    if expected_values:
        if verbose:
            print("  精度検証中...")

        benchmark = AccuracyBenchmark(tolerance_percent=1.0)
        accuracy_result = benchmark.compare_financial_items(
            expected_items=expected_values,
            extracted_text=extracted_text,
            company_name=company_name,
            document_id=document_id,
            fiscal_year=fiscal_year,
        )

        if verbose:
            print(f"  精度: {accuracy_result.accuracy:.1f}%")
            print(f"  一致項目: {accuracy_result.matched_count}/{accuracy_result.total_count}")

    return ValidationResult(
        pdf_path=str(pdf_path),
        total_pages=total_pages,
        extracted_text_length=len(extracted_text),
        has_tables=has_tables,
        processing_time_seconds=processing_time,
        strategy_used=strategy_used,
        accuracy_result=accuracy_result,
        errors=errors if errors else None,
    )


def generate_report(result: ValidationResult, extracted_text: str = "") -> str:
    """検証結果のレポートを生成.

    Args:
        result: 検証結果
        extracted_text: 抽出されたテキスト（サンプル表示用）

    Returns:
        マークダウン形式のレポート
    """
    lines = [
        "# PDF解析検証レポート",
        "",
        "## 検証対象",
        "",
        f"- **ファイル**: `{result.pdf_path}`",
        f"- **ページ数**: {result.total_pages}",
        f"- **使用戦略**: {result.strategy_used}",
        "",
        "## 検証結果サマリ",
        "",
        "| 検証項目 | 結果 | 詳細 |",
        "|---------|:----:|------|",
    ]

    # 1. テキスト抽出
    status = "✅" if result.passes_text_extraction else "❌"
    detail = f"{result.extracted_text_length:,}文字抽出"
    lines.append(f"| テキスト抽出 | {status} | {detail} |")

    # 2. 表データ抽出
    status = "✅" if result.passes_table_extraction else "⚠️"
    detail = "マークダウンテーブル検出" if result.has_tables else "テーブル未検出"
    lines.append(f"| 表データ抽出 | {status} | {detail} |")

    # 3. 精度検証
    if result.accuracy_result:
        status = "✅" if result.passes_accuracy else "❌"
        acc = result.accuracy_result
        detail = f"{acc.accuracy:.1f}% ({acc.matched_count}/{acc.total_count})"
    else:
        status = "⏭️"
        detail = "期待値未指定のためスキップ"
    lines.append(f"| 日本語認識精度 (≥95%) | {status} | {detail} |")

    # 4. パフォーマンス
    status = "✅" if result.passes_performance else "❌"
    detail = f"{result.processing_time_seconds:.2f}秒"
    lines.append(f"| 処理時間 (≤5分) | {status} | {detail} |")

    lines.append("")

    # 総合判定
    if result.all_passed:
        lines.append("## 総合判定: ✅ **合格**")
    else:
        lines.append("## 総合判定: ❌ **不合格**")

    lines.append("")

    # エラーがあれば表示
    if result.errors:
        lines.append("## エラー")
        lines.append("")
        for error in result.errors:
            lines.append(f"- {error}")
        lines.append("")

    # 精度詳細
    if result.accuracy_result:
        lines.append("## 精度検証詳細")
        lines.append("")
        lines.append("| 項目 | 期待値 | 抽出値 | 一致 | 誤差率 |")
        lines.append("|------|-------|-------|:----:|--------|")

        for item in result.accuracy_result.items:
            match_mark = "✅" if item.is_match else "❌"
            extracted = item.extracted_value or "（未検出）"
            error = f"{item.error_rate:.2f}%" if item.error_rate is not None else "-"
            row = f"| {item.item_name} | {item.expected_value} "
            row += f"| {extracted} | {match_mark} | {error} |"
            lines.append(row)

        lines.append("")

    # テキストサンプル
    if extracted_text:
        sample = extracted_text[:2000]
        if len(extracted_text) > 2000:
            sample += "\n\n... (省略)"

        lines.extend(
            [
                "## 抽出テキストサンプル（先頭2000文字）",
                "",
                "```markdown",
                sample,
                "```",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> int:
    """メイン処理."""
    args = parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"エラー: ファイルが見つかりません: {pdf_path}", file=sys.stderr)
        return 1

    print("=== PDF解析・マークダウン化 検証 ===")
    print(f"ファイル: {pdf_path}")
    print(f"戦略: {args.strategy}")
    print()

    # 期待値の構築
    expected_values: dict[str, str] = {}
    if args.expected_sales:
        expected_values["売上高"] = args.expected_sales
    if args.expected_operating_profit:
        expected_values["営業利益"] = args.expected_operating_profit
    if args.expected_ordinary_profit:
        expected_values["経常利益"] = args.expected_ordinary_profit
    if args.expected_net_income:
        expected_values["当期純利益"] = args.expected_net_income
    if args.expected_total_assets:
        expected_values["総資産"] = args.expected_total_assets
    if args.expected_net_assets:
        expected_values["純資産"] = args.expected_net_assets

    # 検証実行
    print("検証を実行中...")
    result = validate_pdf(
        pdf_path=pdf_path,
        strategy=args.strategy,
        start_page=args.start_page,
        end_page=args.end_page,
        expected_values=expected_values if expected_values else None,
        company_name=args.company_name,
        document_id=args.document_id,
        fiscal_year=args.fiscal_year,
        verbose=args.verbose,
    )

    # 抽出テキストを取得（レポート用）
    extracted_text = ""
    if args.verbose or args.output:
        parser = PDFParser()
        try:
            parse_result = parser.to_markdown(
                pdf_path,
                start_page=args.start_page,
                end_page=args.end_page,
                strategy=args.strategy,
            )
            extracted_text = parse_result.text
        except Exception:
            pass

    # レポート生成
    report = generate_report(result, extracted_text if args.verbose else "")

    # 結果出力
    print()
    print(report)

    # 出力先の決定（デフォルトはoutputs/ディレクトリ）
    if args.output:
        output_path = Path(args.output)
    else:
        # デフォルト出力先: outputs/validation_<pdfname>_<timestamp>.md
        outputs_dir = Path(__file__).parent.parent / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_stem = pdf_path.stem
        output_path = outputs_dir / f"validation_{pdf_stem}_{timestamp}.md"

    # ファイル出力
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"\nレポートを保存しました: {output_path}")

    print("\n=== 検証完了 ===")

    return 0 if result.all_passed else 1


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパース."""
    parser = argparse.ArgumentParser(
        description="PDF解析・マークダウン化機能の検証スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 基本的な検証
  %(prog)s /path/to/document.pdf

  # 期待値を指定して精度検証
  %(prog)s /path/to/document.pdf --expected-sales 1234567

  # 特定の戦略を使用
  %(prog)s /path/to/document.pdf --strategy pymupdf4llm

  # ページ範囲を指定
  %(prog)s /path/to/document.pdf --start-page 1 --end-page 10

  # 詳細出力 + ファイル保存
  %(prog)s /path/to/document.pdf --verbose --output result.md

PRD検証項目:
  1. PDFからテキストを抽出できる
  2. 表データをマークダウン形式で出力できる
  3. 日本語の認識精度が95%%以上
  4. 1書類（50-100ページ）の解析が5分以内に完了する
        """,
    )

    # 必須引数
    parser.add_argument(
        "pdf_path",
        type=str,
        help="検証対象のPDFファイルパス",
    )

    # 解析オプション
    parse_group = parser.add_argument_group("解析オプション")
    parse_group.add_argument(
        "--strategy",
        type=str,
        choices=["auto", "pdfplumber", "pymupdf4llm", "yomitoku", "gemini"],
        default="auto",
        help="解析戦略 (デフォルト: auto)",
    )
    parse_group.add_argument(
        "--start-page",
        type=int,
        default=None,
        help="開始ページ番号 (1から開始)",
    )
    parse_group.add_argument(
        "--end-page",
        type=int,
        default=None,
        help="終了ページ番号",
    )

    # 精度検証用の期待値
    accuracy_group = parser.add_argument_group("精度検証（期待値）")
    accuracy_group.add_argument(
        "--expected-sales",
        type=str,
        default=None,
        help="期待される売上高 (例: 1234567)",
    )
    accuracy_group.add_argument(
        "--expected-operating-profit",
        type=str,
        default=None,
        help="期待される営業利益",
    )
    accuracy_group.add_argument(
        "--expected-ordinary-profit",
        type=str,
        default=None,
        help="期待される経常利益",
    )
    accuracy_group.add_argument(
        "--expected-net-income",
        type=str,
        default=None,
        help="期待される当期純利益",
    )
    accuracy_group.add_argument(
        "--expected-total-assets",
        type=str,
        default=None,
        help="期待される総資産",
    )
    accuracy_group.add_argument(
        "--expected-net-assets",
        type=str,
        default=None,
        help="期待される純資産",
    )

    # 文書情報
    doc_group = parser.add_argument_group("文書情報（レポート用）")
    doc_group.add_argument(
        "--company-name",
        type=str,
        default="",
        help="会社名",
    )
    doc_group.add_argument(
        "--document-id",
        type=str,
        default="",
        help="EDINET書類ID",
    )
    doc_group.add_argument(
        "--fiscal-year",
        type=int,
        default=0,
        help="会計年度",
    )

    # 出力オプション
    output_group = parser.add_argument_group("出力オプション")
    output_group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="詳細出力",
    )
    output_group.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="レポート出力先ファイルパス (デフォルト: outputs/validation_<pdf名>_<日時>.md)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
