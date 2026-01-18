"""EDINET node for downloading documents.

EDINET書類をダウンロードするノード。
doc_idを受け取り、PDFファイルをダウンロードしてパスを返す。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from company_research_agent.core.config import EDINETConfig
from company_research_agent.workflows.nodes.base import AnalysisNode
from company_research_agent.workflows.state import AnalysisState

logger = logging.getLogger(__name__)


class EDINETNode(AnalysisNode[str]):
    """EDINET書類取得ノード.

    EDINET APIを使用して書類をダウンロードし、
    ローカルファイルパスを返す。

    Example:
        node = EDINETNode()
        result = await node(state)
        # result = {"pdf_path": "/path/to/document.pdf", "completed_nodes": ["edinet"]}
    """

    def __init__(
        self,
        config: EDINETConfig | None = None,
        download_dir: Path | None = None,
    ) -> None:
        """ノードを初期化する.

        Args:
            config: EDINET API設定。Noneの場合は環境変数から読み込む。
            download_dir: ダウンロード先ディレクトリ。Noneの場合はdata/downloads/pdf。
        """
        self._config = config
        self._download_dir = download_dir or Path("data/downloads/pdf")

    @property
    def name(self) -> str:
        """ノード名を返す."""
        return "edinet"

    def _get_config(self) -> EDINETConfig:
        """設定を取得する."""
        if self._config is None:
            # pydantic-settings reads from environment variables
            self._config = EDINETConfig()  # type: ignore[call-arg]
        return self._config

    async def execute(self, state: AnalysisState) -> str:
        """EDINET書類をダウンロードする.

        Args:
            state: 現在のワークフロー状態

        Returns:
            ダウンロードしたPDFファイルのパス

        Raises:
            ValueError: doc_idが指定されていない場合
            EDINETAPIError: ダウンロードに失敗した場合
        """
        from company_research_agent.clients.edinet_client import EDINETClient

        doc_id = self._get_required_field(state, "doc_id")
        logger.info(f"Downloading document: {doc_id}")

        # ダウンロードパスを準備
        self._download_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = self._download_dir / f"{doc_id}.pdf"

        # 既にダウンロード済みの場合はスキップ
        if pdf_path.exists():
            logger.info(f"Document already exists: {pdf_path}")
            return str(pdf_path)

        # EDINETからダウンロード
        config = self._get_config()
        async with EDINETClient(config) as client:
            # DocumentDownloadType: 2 = PDF
            await client.download_document(
                doc_id=doc_id,
                doc_type=2,
                save_path=pdf_path,
            )

        logger.info(f"Document downloaded: {pdf_path}")
        return str(pdf_path)

    def _update_state(self, state: AnalysisState, result: str) -> dict[str, Any]:
        """実行結果でStateを更新する.

        Args:
            state: 現在のワークフロー状態
            result: ダウンロードしたPDFファイルのパス

        Returns:
            更新するキーと値のdict
        """
        return {"pdf_path": result}
