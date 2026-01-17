"""Tests for accuracy benchmark utilities."""

from decimal import Decimal

import pytest

from company_research_agent.parsers.accuracy_benchmark import (
    AccuracyBenchmark,
    BenchmarkItem,
    BenchmarkResult,
)


class TestBenchmarkItem:
    """Tests for BenchmarkItem dataclass."""

    def test_create_benchmark_item(self) -> None:
        """BenchmarkItem should be creatable with required fields."""
        item = BenchmarkItem(item_name="売上高", expected_value="1,234,567")
        assert item.item_name == "売上高"
        assert item.expected_value == "1,234,567"
        assert item.extracted_value is None
        assert item.is_match is False
        assert item.error_rate is None

    def test_create_benchmark_item_with_all_fields(self) -> None:
        """BenchmarkItem should accept all optional fields."""
        item = BenchmarkItem(
            item_name="営業利益",
            expected_value="123,456",
            extracted_value="123,400",
            is_match=True,
            error_rate=0.045,
        )
        assert item.extracted_value == "123,400"
        assert item.is_match is True
        assert item.error_rate == 0.045


class TestBenchmarkResult:
    """Tests for BenchmarkResult dataclass."""

    def test_create_benchmark_result(self) -> None:
        """BenchmarkResult should be creatable with required fields."""
        result = BenchmarkResult(
            company_name="テスト株式会社",
            document_id="S100ABC1",
            fiscal_year=2024,
        )
        assert result.company_name == "テスト株式会社"
        assert result.document_id == "S100ABC1"
        assert result.fiscal_year == 2024
        assert result.items == []
        assert result.accuracy == 0.0

    def test_calculate_accuracy_empty(self) -> None:
        """calculate_accuracy should return 0 for empty items."""
        result = BenchmarkResult(
            company_name="テスト",
            document_id="S100ABC1",
            fiscal_year=2024,
        )
        accuracy = result.calculate_accuracy()
        assert accuracy == 0.0
        assert result.total_count == 0
        assert result.matched_count == 0

    def test_calculate_accuracy_all_match(self) -> None:
        """calculate_accuracy should return 100% when all items match."""
        result = BenchmarkResult(
            company_name="テスト",
            document_id="S100ABC1",
            fiscal_year=2024,
            items=[
                BenchmarkItem(item_name="売上高", expected_value="100", is_match=True),
                BenchmarkItem(item_name="営業利益", expected_value="50", is_match=True),
            ],
        )
        accuracy = result.calculate_accuracy()
        assert accuracy == 100.0
        assert result.matched_count == 2
        assert result.total_count == 2

    def test_calculate_accuracy_partial_match(self) -> None:
        """calculate_accuracy should return correct percentage for partial match."""
        result = BenchmarkResult(
            company_name="テスト",
            document_id="S100ABC1",
            fiscal_year=2024,
            items=[
                BenchmarkItem(item_name="売上高", expected_value="100", is_match=True),
                BenchmarkItem(item_name="営業利益", expected_value="50", is_match=False),
                BenchmarkItem(item_name="経常利益", expected_value="40", is_match=True),
                BenchmarkItem(item_name="純利益", expected_value="30", is_match=False),
            ],
        )
        accuracy = result.calculate_accuracy()
        assert accuracy == 50.0
        assert result.matched_count == 2
        assert result.total_count == 4


class TestAccuracyBenchmarkNormalizeNumber:
    """Tests for AccuracyBenchmark.normalize_number method."""

    @pytest.fixture
    def benchmark(self) -> AccuracyBenchmark:
        """Provide a benchmark instance."""
        return AccuracyBenchmark()

    def test_normalize_simple_number(self, benchmark: AccuracyBenchmark) -> None:
        """Should normalize simple integer."""
        result = benchmark.normalize_number("12345")
        assert result == Decimal("12345")

    def test_normalize_comma_separated(self, benchmark: AccuracyBenchmark) -> None:
        """Should normalize comma-separated number."""
        result = benchmark.normalize_number("1,234,567")
        assert result == Decimal("1234567")

    def test_normalize_japanese_comma(self, benchmark: AccuracyBenchmark) -> None:
        """Should normalize Japanese full-width comma."""
        result = benchmark.normalize_number("1，234，567")
        assert result == Decimal("1234567")

    def test_normalize_negative_triangle(self, benchmark: AccuracyBenchmark) -> None:
        """Should handle △ negative indicator."""
        result = benchmark.normalize_number("△123,456")
        assert result == Decimal("-123456")

    def test_normalize_negative_triangle_filled(self, benchmark: AccuracyBenchmark) -> None:
        """Should handle ▲ negative indicator."""
        result = benchmark.normalize_number("▲123,456")
        assert result == Decimal("-123456")

    def test_normalize_negative_minus(self, benchmark: AccuracyBenchmark) -> None:
        """Should handle - negative indicator."""
        result = benchmark.normalize_number("-123,456")
        assert result == Decimal("-123456")

    def test_normalize_with_yen(self, benchmark: AccuracyBenchmark) -> None:
        """Should remove yen suffix."""
        result = benchmark.normalize_number("123,456円")
        assert result == Decimal("123456")

    def test_normalize_with_million_yen(self, benchmark: AccuracyBenchmark) -> None:
        """Should remove 百万円 suffix."""
        result = benchmark.normalize_number("1,234百万円")
        assert result == Decimal("1234")

    def test_normalize_with_percent(self, benchmark: AccuracyBenchmark) -> None:
        """Should remove percent sign."""
        result = benchmark.normalize_number("12.5%")
        assert result == Decimal("12.5")

    def test_normalize_decimal(self, benchmark: AccuracyBenchmark) -> None:
        """Should handle decimal numbers."""
        result = benchmark.normalize_number("123.45")
        assert result == Decimal("123.45")

    def test_normalize_empty(self, benchmark: AccuracyBenchmark) -> None:
        """Should return None for empty string."""
        result = benchmark.normalize_number("")
        assert result is None

    def test_normalize_invalid(self, benchmark: AccuracyBenchmark) -> None:
        """Should return None for invalid input."""
        result = benchmark.normalize_number("abc")
        assert result is None

    def test_normalize_with_whitespace(self, benchmark: AccuracyBenchmark) -> None:
        """Should handle leading/trailing whitespace."""
        result = benchmark.normalize_number("  123,456  ")
        assert result == Decimal("123456")


class TestAccuracyBenchmarkCompareValues:
    """Tests for AccuracyBenchmark.compare_values method."""

    @pytest.fixture
    def benchmark(self) -> AccuracyBenchmark:
        """Provide a benchmark instance with 1% tolerance."""
        return AccuracyBenchmark(tolerance_percent=1.0)

    def test_exact_match(self, benchmark: AccuracyBenchmark) -> None:
        """Should match identical values."""
        is_match, error_rate = benchmark.compare_values("1,234,567", "1,234,567")
        assert is_match is True
        assert error_rate == 0.0

    def test_within_tolerance(self, benchmark: AccuracyBenchmark) -> None:
        """Should match values within tolerance."""
        # 0.5% error should match with 1% tolerance
        is_match, error_rate = benchmark.compare_values("1,000,000", "1,005,000")
        assert is_match is True
        assert error_rate == pytest.approx(0.5, rel=0.01)

    def test_exceeds_tolerance(self, benchmark: AccuracyBenchmark) -> None:
        """Should not match values exceeding tolerance."""
        # 2% error should not match with 1% tolerance
        is_match, error_rate = benchmark.compare_values("1,000,000", "1,020,000")
        assert is_match is False
        assert error_rate == pytest.approx(2.0, rel=0.01)

    def test_zero_expected(self, benchmark: AccuracyBenchmark) -> None:
        """Should handle zero expected value."""
        is_match, error_rate = benchmark.compare_values("0", "0")
        assert is_match is True
        assert error_rate == 0.0

    def test_zero_expected_nonzero_extracted(self, benchmark: AccuracyBenchmark) -> None:
        """Should not match when expected is zero but extracted is not."""
        is_match, error_rate = benchmark.compare_values("0", "100")
        assert is_match is False
        assert error_rate == 100.0

    def test_string_exact_match(self, benchmark: AccuracyBenchmark) -> None:
        """Should match identical strings when not numeric."""
        is_match, error_rate = benchmark.compare_values("株式会社ABC", "株式会社ABC")
        assert is_match is True
        assert error_rate is None

    def test_string_mismatch(self, benchmark: AccuracyBenchmark) -> None:
        """Should not match different strings."""
        is_match, error_rate = benchmark.compare_values("株式会社ABC", "株式会社XYZ")
        assert is_match is False
        assert error_rate is None

    def test_string_whitespace_normalized(self, benchmark: AccuracyBenchmark) -> None:
        """Should normalize whitespace in string comparison."""
        is_match, error_rate = benchmark.compare_values("株式会社 ABC", "株式会社ABC")
        assert is_match is True


class TestAccuracyBenchmarkExtractValue:
    """Tests for AccuracyBenchmark.extract_value_for_item method."""

    @pytest.fixture
    def benchmark(self) -> AccuracyBenchmark:
        """Provide a benchmark instance."""
        return AccuracyBenchmark()

    def test_extract_table_format(self, benchmark: AccuracyBenchmark) -> None:
        """Should extract value from markdown table format."""
        text = "| 売上高 | 1,234,567 |"
        result = benchmark.extract_value_for_item("売上高", text)
        assert result == "1,234,567"

    def test_extract_colon_format(self, benchmark: AccuracyBenchmark) -> None:
        """Should extract value with colon separator."""
        text = "売上高: 1,234,567"
        result = benchmark.extract_value_for_item("売上高", text)
        assert result == "1,234,567"

    def test_extract_japanese_colon(self, benchmark: AccuracyBenchmark) -> None:
        """Should extract value with Japanese colon."""
        text = "売上高：1,234,567"
        result = benchmark.extract_value_for_item("売上高", text)
        assert result == "1,234,567"

    def test_extract_space_separated(self, benchmark: AccuracyBenchmark) -> None:
        """Should extract value with space separator."""
        text = "売上高 1,234,567"
        result = benchmark.extract_value_for_item("売上高", text)
        assert result == "1,234,567"

    def test_extract_with_unit(self, benchmark: AccuracyBenchmark) -> None:
        """Should extract value with unit suffix."""
        text = "売上高 1,234,567百万円"
        result = benchmark.extract_value_for_item("売上高", text)
        assert result == "1,234,567"

    def test_extract_negative_value(self, benchmark: AccuracyBenchmark) -> None:
        """Should extract negative value."""
        text = "営業利益: △123,456"
        result = benchmark.extract_value_for_item("営業利益", text)
        assert result == "△123,456"

    def test_extract_not_found(self, benchmark: AccuracyBenchmark) -> None:
        """Should return None when item not found."""
        text = "売上高: 1,234,567"
        result = benchmark.extract_value_for_item("営業利益", text)
        assert result is None

    def test_extract_decimal_value(self, benchmark: AccuracyBenchmark) -> None:
        """Should extract decimal value."""
        text = "自己資本比率: 45.5%"
        result = benchmark.extract_value_for_item("自己資本比率", text)
        assert result == "45.5"


class TestAccuracyBenchmarkCompareFinancialItems:
    """Tests for AccuracyBenchmark.compare_financial_items method."""

    @pytest.fixture
    def benchmark(self) -> AccuracyBenchmark:
        """Provide a benchmark instance."""
        return AccuracyBenchmark(tolerance_percent=1.0)

    def test_compare_single_item_match(self, benchmark: AccuracyBenchmark) -> None:
        """Should correctly compare single matching item."""
        expected_items = {"売上高": "1,234,567"}
        extracted_text = "売上高: 1,234,567百万円"

        result = benchmark.compare_financial_items(
            expected_items=expected_items,
            extracted_text=extracted_text,
            company_name="テスト株式会社",
            document_id="S100ABC1",
            fiscal_year=2024,
        )

        assert result.accuracy == 100.0
        assert result.matched_count == 1
        assert result.total_count == 1
        assert result.items[0].is_match is True

    def test_compare_multiple_items(self, benchmark: AccuracyBenchmark) -> None:
        """Should correctly compare multiple items."""
        expected_items = {
            "売上高": "1,000,000",
            "営業利益": "100,000",
            "経常利益": "90,000",
        }
        extracted_text = """
        売上高: 1,000,000百万円
        営業利益: 100,500百万円
        経常利益: 80,000百万円
        """

        result = benchmark.compare_financial_items(
            expected_items=expected_items,
            extracted_text=extracted_text,
            company_name="テスト株式会社",
            document_id="S100ABC1",
            fiscal_year=2024,
        )

        # 売上高: exact match, 営業利益: 0.5% error (within tolerance), 経常利益: >10% error
        assert result.matched_count == 2
        assert result.total_count == 3
        assert result.accuracy == pytest.approx(66.67, rel=0.01)

    def test_compare_with_missing_item(self, benchmark: AccuracyBenchmark) -> None:
        """Should handle missing items in extracted text."""
        expected_items = {
            "売上高": "1,000,000",
            "営業利益": "100,000",
        }
        extracted_text = "売上高: 1,000,000百万円"

        result = benchmark.compare_financial_items(
            expected_items=expected_items,
            extracted_text=extracted_text,
            company_name="テスト株式会社",
            document_id="S100ABC1",
            fiscal_year=2024,
        )

        assert result.matched_count == 1
        assert result.total_count == 2
        assert result.accuracy == 50.0

        # Check the missing item
        missing_item = next(i for i in result.items if i.item_name == "営業利益")
        assert missing_item.extracted_value is None
        assert missing_item.is_match is False


class TestAccuracyBenchmarkAggregateResults:
    """Tests for AccuracyBenchmark.aggregate_results method."""

    @pytest.fixture
    def benchmark(self) -> AccuracyBenchmark:
        """Provide a benchmark instance."""
        return AccuracyBenchmark()

    def test_aggregate_empty(self, benchmark: AccuracyBenchmark) -> None:
        """Should handle empty results list."""
        overall_accuracy, total_matched, total_items = benchmark.aggregate_results([])
        assert overall_accuracy == 0.0
        assert total_matched == 0
        assert total_items == 0

    def test_aggregate_single_result(self, benchmark: AccuracyBenchmark) -> None:
        """Should aggregate single result correctly."""
        result = BenchmarkResult(
            company_name="テスト",
            document_id="S100ABC1",
            fiscal_year=2024,
            matched_count=8,
            total_count=10,
        )
        overall_accuracy, total_matched, total_items = benchmark.aggregate_results([result])
        assert overall_accuracy == 80.0
        assert total_matched == 8
        assert total_items == 10

    def test_aggregate_multiple_results(self, benchmark: AccuracyBenchmark) -> None:
        """Should aggregate multiple results correctly."""
        results = [
            BenchmarkResult(
                company_name="会社A",
                document_id="S100ABC1",
                fiscal_year=2024,
                matched_count=9,
                total_count=10,
            ),
            BenchmarkResult(
                company_name="会社B",
                document_id="S100ABC2",
                fiscal_year=2024,
                matched_count=8,
                total_count=10,
            ),
            BenchmarkResult(
                company_name="会社C",
                document_id="S100ABC3",
                fiscal_year=2024,
                matched_count=10,
                total_count=10,
            ),
        ]
        overall_accuracy, total_matched, total_items = benchmark.aggregate_results(results)
        assert overall_accuracy == 90.0  # 27/30
        assert total_matched == 27
        assert total_items == 30


class TestAccuracyBenchmarkGenerateReport:
    """Tests for AccuracyBenchmark.generate_report method."""

    @pytest.fixture
    def benchmark(self) -> AccuracyBenchmark:
        """Provide a benchmark instance."""
        return AccuracyBenchmark()

    def test_generate_report_pass(self, benchmark: AccuracyBenchmark) -> None:
        """Should generate passing report for 95%+ accuracy."""
        result = BenchmarkResult(
            company_name="テスト株式会社",
            document_id="S100ABC1",
            fiscal_year=2024,
            items=[
                BenchmarkItem(
                    item_name="売上高",
                    expected_value="1,000,000",
                    extracted_value="1,000,000",
                    is_match=True,
                    error_rate=0.0,
                ),
            ],
            accuracy=100.0,
            matched_count=1,
            total_count=1,
        )
        report = benchmark.generate_report([result])

        assert "# PDF解析精度測定レポート" in report
        assert "**全体精度**: 100.0%" in report
        assert "✅ 合格" in report
        assert "テスト株式会社" in report
        assert "売上高" in report

    def test_generate_report_fail(self, benchmark: AccuracyBenchmark) -> None:
        """Should generate failing report for <95% accuracy."""
        result = BenchmarkResult(
            company_name="テスト株式会社",
            document_id="S100ABC1",
            fiscal_year=2024,
            items=[
                BenchmarkItem(
                    item_name="売上高",
                    expected_value="1,000,000",
                    extracted_value="800,000",
                    is_match=False,
                    error_rate=20.0,
                ),
            ],
            accuracy=0.0,
            matched_count=0,
            total_count=1,
        )
        report = benchmark.generate_report([result])

        assert "❌ 不合格" in report
        assert "20.00%" in report  # error rate

    def test_generate_report_with_missing_value(self, benchmark: AccuracyBenchmark) -> None:
        """Should show missing values in report."""
        result = BenchmarkResult(
            company_name="テスト株式会社",
            document_id="S100ABC1",
            fiscal_year=2024,
            items=[
                BenchmarkItem(
                    item_name="売上高",
                    expected_value="1,000,000",
                    extracted_value=None,
                    is_match=False,
                    error_rate=None,
                ),
            ],
            accuracy=0.0,
            matched_count=0,
            total_count=1,
        )
        report = benchmark.generate_report([result])

        assert "（未検出）" in report
