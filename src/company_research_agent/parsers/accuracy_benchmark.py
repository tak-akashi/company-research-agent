"""Accuracy benchmark utilities for PDF parsing validation.

This module provides tools for measuring Japanese text extraction accuracy
against known reference data (e.g., earnings summaries).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class BenchmarkItem:
    """A single benchmark item for accuracy measurement.

    Attributes:
        item_name: Name of the financial item (e.g., "売上高", "営業利益").
        expected_value: Expected value from reference source.
        extracted_value: Value extracted from PDF.
        is_match: Whether the values match within tolerance.
        error_rate: Percentage error between expected and extracted values.
    """

    item_name: str
    expected_value: str
    extracted_value: str | None = None
    is_match: bool = False
    error_rate: float | None = None


@dataclass
class BenchmarkResult:
    """Result of a benchmark comparison.

    Attributes:
        company_name: Name of the company.
        document_id: EDINET document ID.
        fiscal_year: Fiscal year of the document.
        items: List of benchmark items.
        accuracy: Overall accuracy percentage.
        matched_count: Number of matched items.
        total_count: Total number of items.
    """

    company_name: str
    document_id: str
    fiscal_year: int
    items: list[BenchmarkItem] = field(default_factory=list)
    accuracy: float = 0.0
    matched_count: int = 0
    total_count: int = 0

    def calculate_accuracy(self) -> float:
        """Calculate and update the accuracy based on matched items."""
        self.total_count = len(self.items)
        self.matched_count = sum(1 for item in self.items if item.is_match)
        self.accuracy = (
            (self.matched_count / self.total_count * 100) if self.total_count > 0 else 0.0
        )
        return self.accuracy


class AccuracyBenchmark:
    """Benchmark framework for measuring PDF extraction accuracy.

    This class provides methods for comparing extracted text against
    reference data to measure Japanese text recognition accuracy.

    Example:
        benchmark = AccuracyBenchmark(tolerance_percent=1.0)
        result = benchmark.compare_financial_items(
            expected_items={"売上高": "1,234,567", "営業利益": "123,456"},
            extracted_text="売上高は1,234,567百万円...",
        )
        print(f"Accuracy: {result.accuracy}%")
    """

    # Common Japanese financial terms to extract
    FINANCIAL_ITEMS = [
        "売上高",
        "営業収益",
        "営業利益",
        "経常利益",
        "当期純利益",
        "親会社株主に帰属する当期純利益",
        "総資産",
        "純資産",
        "自己資本比率",
        "1株当たり当期純利益",
        "1株当たり配当金",
        "営業活動によるキャッシュ・フロー",
        "投資活動によるキャッシュ・フロー",
        "財務活動によるキャッシュ・フロー",
        "現金及び現金同等物の期末残高",
    ]

    def __init__(self, tolerance_percent: float = 1.0) -> None:
        """Initialize the benchmark.

        Args:
            tolerance_percent: Acceptable error percentage for numeric comparison.
                              Default is 1.0% as specified in PRD.
        """
        self.tolerance_percent = tolerance_percent

    def normalize_number(self, value: str) -> Decimal | None:
        """Normalize a Japanese number string to Decimal.

        Handles:
        - Comma-separated numbers (1,234,567)
        - Japanese unit suffixes (百万円, 千円, 億円)
        - Negative numbers (△123, -123, ▲123)

        Args:
            value: Number string to normalize.

        Returns:
            Normalized Decimal value, or None if parsing fails.
        """
        if not value:
            return None

        # Remove whitespace
        value = value.strip()

        # Handle negative indicators
        is_negative = False
        if value.startswith(("△", "▲", "-", "－")):
            is_negative = True
            value = value[1:]

        # Remove common suffixes and units
        value = re.sub(r"[百千万億兆円]", "", value)
        value = re.sub(r"百万", "", value)

        # Remove commas and spaces
        value = value.replace(",", "").replace("，", "").replace(" ", "")

        # Remove % sign
        value = value.replace("%", "").replace("％", "")

        try:
            result = Decimal(value)
            return -result if is_negative else result
        except InvalidOperation:
            return None

    def compare_values(
        self,
        expected: str,
        extracted: str,
    ) -> tuple[bool, float | None]:
        """Compare expected and extracted values.

        Args:
            expected: Expected value string.
            extracted: Extracted value string.

        Returns:
            Tuple of (is_match, error_rate).
            error_rate is None if comparison is not numeric.
        """
        # Normalize both values
        expected_num = self.normalize_number(expected)
        extracted_num = self.normalize_number(extracted)

        # If both are numeric, compare with tolerance
        if expected_num is not None and extracted_num is not None:
            if expected_num == 0:
                is_match = extracted_num == 0
                error_rate = 0.0 if is_match else 100.0
            else:
                error_rate = float(abs(extracted_num - expected_num) / abs(expected_num) * 100)
                is_match = error_rate <= self.tolerance_percent
            return is_match, error_rate

        # Fall back to exact string comparison (after normalization)
        expected_normalized = expected.strip().replace(" ", "").replace("　", "")
        extracted_normalized = extracted.strip().replace(" ", "").replace("　", "")
        is_match = expected_normalized == extracted_normalized
        return is_match, None

    def extract_value_for_item(
        self,
        item_name: str,
        text: str,
    ) -> str | None:
        """Extract value for a specific financial item from text.

        Args:
            item_name: Name of the financial item to find.
            text: Text to search in.

        Returns:
            Extracted value string, or None if not found.
        """
        # Pattern: item_name followed by number (with possible units)
        # Handles various formats:
        # - 売上高 1,234,567
        # - 売上高: 1,234,567百万円
        # - 売上高　1,234,567
        # - | 売上高 | 1,234,567 |
        patterns = [
            # Table format: | item | value |
            rf"\|\s*{re.escape(item_name)}\s*\|\s*([△▲\-－]?[\d,，]+(?:\.\d+)?)\s*\|",
            # Colon separated: item: value
            rf"{re.escape(item_name)}\s*[:：]\s*([△▲\-－]?[\d,，]+(?:\.\d+)?)",
            # Space/tab separated: item value
            rf"{re.escape(item_name)}\s+([△▲\-－]?[\d,，]+(?:\.\d+)?)",
            # With units: item value百万円
            rf"{re.escape(item_name)}\s*([△▲\-－]?[\d,，]+(?:\.\d+)?)\s*(?:百万)?円?",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    def compare_financial_items(
        self,
        expected_items: dict[str, str],
        extracted_text: str,
        company_name: str = "",
        document_id: str = "",
        fiscal_year: int = 0,
    ) -> BenchmarkResult:
        """Compare expected financial items against extracted text.

        Args:
            expected_items: Dictionary of item names to expected values.
            extracted_text: Full extracted text from PDF.
            company_name: Company name for the result.
            document_id: Document ID for the result.
            fiscal_year: Fiscal year for the result.

        Returns:
            BenchmarkResult with comparison details.
        """
        result = BenchmarkResult(
            company_name=company_name,
            document_id=document_id,
            fiscal_year=fiscal_year,
        )

        for item_name, expected_value in expected_items.items():
            extracted_value = self.extract_value_for_item(item_name, extracted_text)

            benchmark_item = BenchmarkItem(
                item_name=item_name,
                expected_value=expected_value,
                extracted_value=extracted_value,
            )

            if extracted_value is not None:
                is_match, error_rate = self.compare_values(expected_value, extracted_value)
                benchmark_item.is_match = is_match
                benchmark_item.error_rate = error_rate

            result.items.append(benchmark_item)

        result.calculate_accuracy()
        return result

    def aggregate_results(
        self,
        results: Sequence[BenchmarkResult],
    ) -> tuple[float, int, int]:
        """Aggregate multiple benchmark results.

        Args:
            results: Sequence of BenchmarkResult objects.

        Returns:
            Tuple of (overall_accuracy, total_matched, total_items).
        """
        total_matched = sum(r.matched_count for r in results)
        total_items = sum(r.total_count for r in results)
        overall_accuracy = (total_matched / total_items * 100) if total_items > 0 else 0.0
        return overall_accuracy, total_matched, total_items

    def generate_report(
        self,
        results: Sequence[BenchmarkResult],
    ) -> str:
        """Generate a markdown report from benchmark results.

        Args:
            results: Sequence of BenchmarkResult objects.

        Returns:
            Markdown formatted report string.
        """
        overall_accuracy, total_matched, total_items = self.aggregate_results(results)

        lines = [
            "# PDF解析精度測定レポート",
            "",
            "## サマリ",
            "",
            f"- **全体精度**: {overall_accuracy:.1f}%",
            f"- **一致項目数**: {total_matched} / {total_items}",
            "- **目標精度**: 95%",
            f"- **判定**: {'✅ 合格' if overall_accuracy >= 95 else '❌ 不合格'}",
            "",
            "## 詳細結果",
            "",
        ]

        for result in results:
            lines.extend(
                [
                    f"### {result.company_name} ({result.fiscal_year}年度)",
                    "",
                    f"- 書類ID: {result.document_id}",
                    f"- 精度: {result.accuracy:.1f}%",
                    "",
                    "| 項目 | 期待値 | 抽出値 | 一致 | 誤差率 |",
                    "|------|-------|-------|:----:|--------|",
                ]
            )

            for item in result.items:
                match_mark = "✅" if item.is_match else "❌"
                extracted = item.extracted_value or "（未検出）"
                error = f"{item.error_rate:.2f}%" if item.error_rate is not None else "-"
                line = (
                    f"| {item.item_name} | {item.expected_value} "
                    f"| {extracted} | {match_mark} | {error} |"
                )
                lines.append(line)

            lines.append("")

        return "\n".join(lines)
