"""EDINETコードリストクライアント.

EDINETコードリストのダウンロード、キャッシュ、検索機能を提供する。
"""

from __future__ import annotations

import csv
import io
import logging
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from rapidfuzz import fuzz
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from company_research_agent.core.exceptions import CodeListDownloadError
from company_research_agent.schemas.query_schemas import (
    CompanyCandidate,
    CompanyInfo,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class EDINETCodeListClient:
    """EDINETコードリストのダウンロード・キャッシュ・検索を行うクライアント.

    EDINETが提供するコードリスト（ZIP形式）をダウンロードし、
    ローカルにキャッシュして企業検索を行う。

    Attributes:
        CACHE_DIR: キャッシュディレクトリ
        CACHE_VALIDITY_DAYS: キャッシュ有効期限（日）
        CODE_LIST_URL: コードリストのダウンロードURL

    Example:
        >>> client = EDINETCodeListClient()
        >>> await client.ensure_code_list()
        >>> candidates = await client.search_companies("トヨタ")
        >>> for c in candidates:
        ...     print(f"{c.company.company_name} - {c.similarity_score}")
    """

    CACHE_DIR = Path("data/cache/edinet_code_list")
    CACHE_VALIDITY_DAYS = 7
    CODE_LIST_URL = "https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip"
    CSV_FILENAME = "EdinetcodeDlInfo.csv"

    def __init__(
        self,
        cache_dir: Path | None = None,
        cache_validity_days: int | None = None,
    ) -> None:
        """初期化.

        Args:
            cache_dir: キャッシュディレクトリ。Noneの場合はデフォルト使用。
            cache_validity_days: キャッシュ有効期限（日）。Noneの場合はデフォルト使用。
        """
        self._cache_dir = cache_dir or self.CACHE_DIR
        self._cache_validity_days = cache_validity_days or self.CACHE_VALIDITY_DAYS
        self._companies: list[CompanyInfo] | None = None
        self._companies_by_edinet_code: dict[str, CompanyInfo] | None = None
        self._companies_by_sec_code: dict[str, CompanyInfo] | None = None

    @property
    def _csv_path(self) -> Path:
        """キャッシュされたCSVファイルのパス."""
        return self._cache_dir / self.CSV_FILENAME

    @property
    def _timestamp_path(self) -> Path:
        """タイムスタンプファイルのパス."""
        return self._cache_dir / ".timestamp"

    def _is_cache_valid(self) -> bool:
        """キャッシュが有効かどうかを判定.

        Returns:
            キャッシュが存在し、有効期限内であればTrue
        """
        if not self._csv_path.exists():
            return False

        if not self._timestamp_path.exists():
            return False

        try:
            timestamp_str = self._timestamp_path.read_text().strip()
            timestamp = datetime.fromisoformat(timestamp_str)
            expiry = timestamp + timedelta(days=self._cache_validity_days)
            return datetime.now() < expiry
        except (ValueError, OSError) as e:
            logger.warning(f"Failed to read cache timestamp: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        reraise=True,
    )
    async def _download_and_extract(self) -> None:
        """コードリストをダウンロードして展開.

        Raises:
            CodeListDownloadError: ダウンロードまたは展開に失敗した場合
        """
        logger.info(f"Downloading EDINET code list from {self.CODE_LIST_URL}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.CODE_LIST_URL,
                    timeout=60.0,
                    follow_redirects=True,
                )
                response.raise_for_status()

            # ZIPを展開
            self._cache_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                # CSVファイルを探す
                csv_files = [n for n in zf.namelist() if n.endswith(".csv")]
                if not csv_files:
                    raise CodeListDownloadError(
                        message="No CSV file found in ZIP",
                        url=self.CODE_LIST_URL,
                    )

                # 最初のCSVファイルを展開
                csv_content = zf.read(csv_files[0])
                self._csv_path.write_bytes(csv_content)

            # タイムスタンプを記録
            self._timestamp_path.write_text(datetime.now().isoformat())

            logger.info(f"EDINET code list saved to {self._csv_path}")

        except httpx.HTTPStatusError as e:
            raise CodeListDownloadError(
                message=f"HTTP error {e.response.status_code}",
                url=self.CODE_LIST_URL,
            ) from e
        except zipfile.BadZipFile as e:
            raise CodeListDownloadError(
                message=f"Invalid ZIP file: {e}",
                url=self.CODE_LIST_URL,
            ) from e
        except OSError as e:
            raise CodeListDownloadError(
                message=f"File system error: {e}",
                url=self.CODE_LIST_URL,
            ) from e

    def _load_from_cache(self) -> None:
        """キャッシュからコードリストを読み込む."""
        if self._companies is not None:
            return

        logger.debug(f"Loading EDINET code list from {self._csv_path}")

        companies: list[CompanyInfo] = []
        by_edinet_code: dict[str, CompanyInfo] = {}
        by_sec_code: dict[str, CompanyInfo] = {}

        # CSVはShift_JISエンコーディング
        with self._csv_path.open("r", encoding="cp932") as f:
            # 最初の行はヘッダー説明なのでスキップ
            next(f, None)
            reader = csv.DictReader(f)

            for row in reader:
                edinet_code = row.get("ＥＤＩＮＥＴコード", "").strip()
                if not edinet_code:
                    continue

                sec_code = row.get("証券コード", "").strip() or None
                company_name = row.get("提出者名", "").strip()
                company_name_kana = row.get("提出者名（カナ）", "").strip() or None
                company_name_en = row.get("提出者名（英字）", "").strip() or None
                listing_code = row.get("上場区分", "").strip() or None
                industry_code = row.get("提出者業種", "").strip() or None

                company = CompanyInfo(
                    edinet_code=edinet_code,
                    sec_code=sec_code,
                    company_name=company_name,
                    company_name_kana=company_name_kana,
                    company_name_en=company_name_en,
                    listing_code=listing_code,
                    industry_code=industry_code,
                )

                companies.append(company)
                by_edinet_code[edinet_code] = company
                if sec_code:
                    by_sec_code[sec_code] = company

        self._companies = companies
        self._companies_by_edinet_code = by_edinet_code
        self._companies_by_sec_code = by_sec_code

        logger.info(f"Loaded {len(companies)} companies from EDINET code list")

    async def ensure_code_list(self, force_refresh: bool = False) -> Path:
        """コードリストを確保（必要に応じてダウンロード）.

        Args:
            force_refresh: Trueの場合、キャッシュを無視して再ダウンロード

        Returns:
            CSVファイルのパス

        Raises:
            CodeListDownloadError: ダウンロードに失敗した場合
        """
        if not force_refresh and self._is_cache_valid():
            logger.debug("Using cached EDINET code list")
        else:
            await self._download_and_extract()

        self._load_from_cache()
        return self._csv_path

    async def search_companies(
        self,
        query: str,
        limit: int = 10,
    ) -> list[CompanyCandidate]:
        """企業名で検索し、類似度スコア付き候補リストを返す.

        rapidfuzzを使用して類似度を計算。企業名、カナ名、英語名を検索対象とする。

        Args:
            query: 検索クエリ（企業名、EDINETコード、証券コード）
            limit: 返却する候補の最大数

        Returns:
            類似度スコア付きの企業候補リスト（スコア降順）
        """
        await self.ensure_code_list()

        if self._companies is None:
            return []

        # EDINETコードで直接検索
        if query.upper().startswith("E") and len(query) == 6:
            company = await self.get_by_edinet_code(query.upper())
            if company:
                return [
                    CompanyCandidate(
                        company=company,
                        similarity_score=100.0,
                        match_field="edinet_code",
                    )
                ]

        # 証券コードで直接検索
        if query.isdigit() and len(query) in (4, 5):
            # 4桁の場合は末尾に0を付加して5桁に（EDINETの証券コード形式）
            sec_code = query + "0" if len(query) == 4 else query
            company = await self.get_by_sec_code(sec_code)
            if company:
                return [
                    CompanyCandidate(
                        company=company,
                        similarity_score=100.0,
                        match_field="sec_code",
                    )
                ]

        # あいまい検索
        candidates: list[CompanyCandidate] = []

        for company in self._companies:
            best_score = 0.0
            best_field = "company_name"

            # 企業名との類似度
            score = fuzz.partial_ratio(query, company.company_name)
            if score > best_score:
                best_score = score
                best_field = "company_name"

            # カナ名との類似度
            if company.company_name_kana:
                score = fuzz.partial_ratio(query, company.company_name_kana)
                if score > best_score:
                    best_score = score
                    best_field = "company_name_kana"

            # 英語名との類似度
            if company.company_name_en:
                score = fuzz.partial_ratio(query.upper(), company.company_name_en.upper())
                if score > best_score:
                    best_score = score
                    best_field = "company_name_en"

            # しきい値以上のスコアのみ追加
            if best_score >= 50:
                candidates.append(
                    CompanyCandidate(
                        company=company,
                        similarity_score=best_score,
                        match_field=best_field,
                    )
                )

        # スコア降順でソート（同スコアの場合は追加条件で優先度を決定）
        # 優先順位:
        # 1. 類似度スコア
        # 2. 企業名がクエリで始まる（プレフィックスマッチ、法人格除去後）
        # 3. 上場企業（sec_code がある）
        # 4. 業種を示す一般的な単語を含む（自動車、電機など主要企業の可能性）
        major_industry_keywords = (
            "自動車",
            "電機",
            "電器",
            "製薬",
            "銀行",
            "証券",
            "保険",
            "製作所",
        )
        legal_prefixes = ("株式会社", "有限会社", "合同会社", "合資会社", "合名会社")

        def normalize_name(name: str) -> str:
            """法人格を除去した企業名を返す."""
            for prefix in legal_prefixes:
                if name.startswith(prefix):
                    return name[len(prefix) :]
            return name

        def sort_key(c: CompanyCandidate) -> tuple[float, int, int, int]:
            name = c.company.company_name
            normalized = normalize_name(name)
            is_prefix_match = 1 if (name.startswith(query) or normalized.startswith(query)) else 0
            is_listed = 1 if c.company.sec_code else 0
            has_major_keyword = 1 if any(kw in name for kw in major_industry_keywords) else 0
            return (c.similarity_score, is_prefix_match, is_listed, has_major_keyword)

        candidates.sort(key=sort_key, reverse=True)
        return candidates[:limit]

    async def get_by_edinet_code(self, code: str) -> CompanyInfo | None:
        """EDINETコードで企業を検索.

        Args:
            code: EDINETコード（例: E02144）

        Returns:
            企業情報。見つからない場合はNone。
        """
        await self.ensure_code_list()

        if self._companies_by_edinet_code is None:
            return None

        return self._companies_by_edinet_code.get(code.upper())

    async def get_by_sec_code(self, code: str) -> CompanyInfo | None:
        """証券コードで企業を検索.

        Args:
            code: 証券コード（5桁、例: 72030）

        Returns:
            企業情報。見つからない場合はNone。
        """
        await self.ensure_code_list()

        if self._companies_by_sec_code is None:
            return None

        # 4桁の場合は末尾に0を付加して5桁に（EDINETの証券コード形式）
        normalized_code = code + "0" if len(code) == 4 else code
        return self._companies_by_sec_code.get(normalized_code)
