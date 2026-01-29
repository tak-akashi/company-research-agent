"""BaseIRScraper - Playwrightを使用したIRページスクレイピング基盤."""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Self
from urllib.parse import urljoin, urlparse

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from company_research_agent.core.exceptions import (
    IRDocumentDownloadError,
    IRPageAccessError,
)

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Download, Page, Playwright

logger = logging.getLogger(__name__)


class BaseIRScraper:
    """IRページスクレイピングの基盤クラス.

    Playwrightを使用してJavaScript動的コンテンツを含むIRページを取得し、
    PDFファイルをダウンロードする機能を提供する。

    robots.txtを遵守し、リクエスト間隔を制御することで、
    サーバーへの負荷を軽減する。

    Example:
        >>> async with BaseIRScraper() as scraper:
        ...     html = await scraper.fetch_page("https://example.com/ir")
        ...     await scraper.download_pdf("https://example.com/ir/doc.pdf", Path("./doc.pdf"))
    """

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36 CompanyResearchAgent/1.0"
    )

    def __init__(
        self,
        rate_limit_seconds: float = 1.0,
        timeout: int = 30000,
        headless: bool = True,
        user_agent: str | None = None,
    ) -> None:
        """BaseIRScraperを初期化する.

        Args:
            rate_limit_seconds: リクエスト間隔（秒）。robots.txt遵守のため最低1秒推奨。
            timeout: ページ読み込みタイムアウト（ミリ秒）
            headless: ヘッドレスモードで実行するか
            user_agent: User-Agentヘッダー（省略時はデフォルト値）
        """
        self._rate_limit_seconds = rate_limit_seconds
        self._timeout = timeout
        self._headless = headless
        self._user_agent = user_agent or self.DEFAULT_USER_AGENT

        # Playwright関連（__aenter__で初期化）
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

        # レート制限用
        self._last_request_time: float = 0.0

        # robots.txtキャッシュ
        self._robots_cache: dict[str, set[str]] = {}

    async def __aenter__(self) -> Self:
        """コンテキストマネージャのエントリーポイント.

        Playwrightを起動し、ブラウザを初期化する。

        Returns:
            初期化されたBaseIRScraperインスタンス
        """
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
        )
        self._context = await self._browser.new_context(
            user_agent=self._user_agent,
            # 不要なリソースをブロックしてパフォーマンス向上
            bypass_csp=True,
        )

        # 画像・CSS・フォントのブロック設定
        await self._context.route(
            re.compile(r"\.(png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot|css)$"),
            lambda route: route.abort(),
        )

        logger.debug("BaseIRScraper initialized with Playwright")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """コンテキストマネージャの終了処理.

        ブラウザとPlaywrightをクリーンアップする。
        """
        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        logger.debug("BaseIRScraper cleaned up")

    async def _wait_for_rate_limit(self) -> None:
        """レート制限のための待機処理."""
        import time

        current_time = time.time()
        elapsed = current_time - self._last_request_time

        if elapsed < self._rate_limit_seconds:
            wait_time = self._rate_limit_seconds - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self._last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(IRPageAccessError),
        reraise=True,
    )
    async def fetch_page(self, url: str) -> str:
        """ページのHTMLを取得する.

        JavaScriptを実行した後のレンダリング済みHTMLを取得する。

        Args:
            url: 取得するページのURL

        Returns:
            レンダリング済みのHTML文字列

        Raises:
            IRPageAccessError: ページ取得に失敗した場合
        """
        if not self._context:
            raise IRPageAccessError(
                message="Scraper not initialized. Use 'async with' context manager.",
                url=url,
            )

        await self._wait_for_rate_limit()

        page: Page | None = None
        try:
            page = await self._context.new_page()
            response = await page.goto(url, timeout=self._timeout, wait_until="networkidle")

            if response is None:
                raise IRPageAccessError(
                    message="No response received",
                    url=url,
                )

            if response.status >= 400:
                raise IRPageAccessError(
                    message=f"HTTP error: {response.status}",
                    url=url,
                    status_code=response.status,
                )

            html: str = await page.content()
            logger.debug(f"Fetched page: {url} ({len(html)} bytes)")
            return html

        except IRPageAccessError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch page {url}: {e}")
            raise IRPageAccessError(
                message=str(e),
                url=url,
            ) from e
        finally:
            if page:
                await page.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(IRDocumentDownloadError),
        reraise=True,
    )
    async def download_pdf(
        self,
        url: str,
        save_path: Path,
        *,
        force: bool = False,
        referer: str | None = None,
    ) -> Path:
        """PDFファイルをダウンロードする.

        Args:
            url: ダウンロードするPDFのURL
            save_path: 保存先のパス
            force: Trueの場合、既存ファイルを上書き
            referer: Refererヘッダー（省略時はURLから自動生成）

        Returns:
            保存されたファイルのパス

        Raises:
            IRDocumentDownloadError: ダウンロードに失敗した場合
        """
        if save_path.exists() and not force:
            logger.debug(f"File already exists, skipping: {save_path}")
            return save_path

        await self._wait_for_rate_limit()

        # RefererがなければURLのベースから生成
        if referer is None:
            parsed = urlparse(url)
            referer = f"{parsed.scheme}://{parsed.netloc}/"

        # ブラウザリクエストを模倣するヘッダー
        headers = {
            "User-Agent": self._user_agent,
            "Referer": referer,
            "Accept": "application/pdf,application/octet-stream,*/*;q=0.9",
            "Accept-Language": "ja,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }

        try:
            # まずhttpxで試行（高速）
            async with httpx.AsyncClient(
                timeout=60.0,
                follow_redirects=True,
                headers=headers,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                # ディレクトリが存在しない場合は作成
                save_path.parent.mkdir(parents=True, exist_ok=True)

                # ファイルに書き込み
                save_path.write_bytes(response.content)

                logger.info(f"Downloaded PDF: {url} -> {save_path}")
                return save_path

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                # 403の場合はPlaywrightでフォールバック
                logger.warning(f"403 Forbidden with httpx, trying Playwright: {url}")
                return await self._download_pdf_with_playwright(url, save_path)
            logger.error(f"HTTP error downloading PDF {url}: {e}")
            raise IRDocumentDownloadError(
                message=f"HTTP error: {e.response.status_code}",
                url=url,
            ) from e
        except Exception as e:
            logger.error(f"Failed to download PDF {url}: {e}")
            raise IRDocumentDownloadError(
                message=str(e),
                url=url,
            ) from e

    async def _download_pdf_with_playwright(
        self,
        url: str,
        save_path: Path,
    ) -> Path:
        """Playwrightを使用してPDFをダウンロードする.

        httpxでダウンロードできない場合のフォールバック。
        ブラウザコンテキストを使用するため、より強力なボット対策を回避可能。

        Args:
            url: ダウンロードするPDFのURL
            save_path: 保存先のパス

        Returns:
            保存されたファイルのパス

        Raises:
            IRDocumentDownloadError: ダウンロードに失敗した場合
        """
        if not self._context:
            raise IRDocumentDownloadError(
                message="Scraper not initialized. Use 'async with' context manager.",
                url=url,
            )

        page = None
        download_future: asyncio.Future[Download] | None = None

        try:
            page = await self._context.new_page()

            # ディレクトリが存在しない場合は作成
            save_path.parent.mkdir(parents=True, exist_ok=True)

            # ダウンロードイベントのハンドラを設定
            download_future = asyncio.get_event_loop().create_future()

            def on_download(download: Download) -> None:
                if not download_future.done():
                    download_future.set_result(download)

            page.on("download", on_download)

            # ナビゲーションを開始（ダウンロードがトリガーされる）
            # wait_until="domcontentloaded"だとPDFでは失敗するので、例外を許容
            try:
                await page.goto(url, timeout=self._timeout, wait_until="domcontentloaded")
            except Exception as nav_err:
                # "Download is starting" エラーは想定内
                if "Download is starting" not in str(nav_err):
                    raise

            # ダウンロードの完了を待機
            try:
                download = await asyncio.wait_for(download_future, timeout=self._timeout / 1000)
                await download.save_as(save_path)
                logger.info(f"Downloaded PDF (Playwright): {url} -> {save_path}")
                return save_path
            except TimeoutError as e:
                raise IRDocumentDownloadError(
                    message="Download timeout",
                    url=url,
                ) from e

        except IRDocumentDownloadError:
            raise
        except Exception as e:
            logger.error(f"Failed to download PDF with Playwright {url}: {e}")
            raise IRDocumentDownloadError(
                message=f"Playwright download failed: {e}",
                url=url,
            ) from e
        finally:
            if page:
                await page.close()

    async def check_robots_txt(self, base_url: str, path: str) -> bool:
        """robots.txtを確認してアクセス可否を判定する.

        Args:
            base_url: サイトのベースURL（例: https://example.com）
            path: チェックするパス（例: /ir/documents）

        Returns:
            アクセスが許可されている場合True
        """
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        # キャッシュ確認
        if robots_url in self._robots_cache:
            disallowed = self._robots_cache[robots_url]
            return not any(path.startswith(d) for d in disallowed)

        try:
            async with httpx.AsyncClient(
                timeout=10.0,
                headers={"User-Agent": self._user_agent},
            ) as client:
                response = await client.get(robots_url)

                if response.status_code == 404:
                    # robots.txtが存在しない場合は全てのアクセスを許可
                    self._robots_cache[robots_url] = set()
                    return True

                response.raise_for_status()

                # 簡易的なrobots.txt解析
                disallowed_paths: set[str] = set()
                current_user_agent = ""
                lines = response.text.split("\n")

                for line in lines:
                    line = line.strip().lower()
                    if line.startswith("user-agent:"):
                        current_user_agent = line.split(":", 1)[1].strip()
                    elif line.startswith("disallow:") and current_user_agent in ("*", ""):
                        disallowed_path = line.split(":", 1)[1].strip()
                        if disallowed_path:
                            disallowed_paths.add(disallowed_path)

                self._robots_cache[robots_url] = disallowed_paths

                is_allowed = not any(path.startswith(d) for d in disallowed_paths)
                status = "allowed" if is_allowed else "disallowed"
                logger.debug(f"robots.txt check for {path}: {status}")
                return is_allowed

        except Exception as e:
            logger.warning(f"Failed to fetch robots.txt from {robots_url}: {e}")
            # robots.txt取得失敗時はデフォルトで許可（ただし注意を促す）
            self._robots_cache[robots_url] = set()
            return True

    def resolve_url(self, base_url: str, relative_url: str) -> str:
        """相対URLを絶対URLに変換する.

        Args:
            base_url: ベースURL
            relative_url: 相対URL

        Returns:
            絶対URL
        """
        return urljoin(base_url, relative_url)
