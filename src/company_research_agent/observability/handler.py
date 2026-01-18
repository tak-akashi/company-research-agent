"""Langfuse callback handler management."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langfuse.langchain import CallbackHandler

logger = logging.getLogger(__name__)

# Langfuse環境変数が設定済みかどうかのフラグ
_langfuse_env_exported = False


def _export_langfuse_env(config: Any) -> None:
    """Langfuse SDK用に環境変数をエクスポートする.

    Langfuse 3.x では CallbackHandler が環境変数から認証情報を読み込むため、
    pydantic-settingsで読み込んだ設定値を環境変数としてエクスポートする。

    Args:
        config: LangfuseConfig インスタンス
    """
    import os

    global _langfuse_env_exported
    if _langfuse_env_exported:
        return

    if config.public_key:
        os.environ["LANGFUSE_PUBLIC_KEY"] = config.public_key
    if config.secret_key:
        os.environ["LANGFUSE_SECRET_KEY"] = config.secret_key
    if config.base_url:
        os.environ["LANGFUSE_HOST"] = config.base_url
    if config.debug:
        os.environ["LANGFUSE_DEBUG"] = "true"

    _langfuse_env_exported = True


@lru_cache(maxsize=1)
def _get_langfuse_config() -> Any:
    """Langfuse設定を取得する（キャッシュ付き）.

    Returns:
        LangfuseConfig インスタンス
    """
    from company_research_agent.observability.config import LangfuseConfig

    return LangfuseConfig()


def is_langfuse_enabled() -> bool:
    """Langfuseが有効かどうかを返す.

    Returns:
        Langfuseが正しく設定されている場合True
    """
    config = _get_langfuse_config()
    return bool(config.is_configured())


def get_langfuse_handler(
    session_id: str | None = None,
    user_id: str | None = None,
    trace_name: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> CallbackHandler | None:
    """Langfuse CallbackHandlerを取得する.

    Args:
        session_id: セッションID（オプション）
        user_id: ユーザーID（オプション）
        trace_name: トレース名（オプション）
        tags: タグリスト（オプション）
        metadata: 追加メタデータ（オプション）

    Returns:
        Langfuseが有効な場合はCallbackHandler、無効な場合はNone
    """
    config = _get_langfuse_config()

    if not config.is_configured():
        logger.debug("Langfuse is not configured, returning None")
        return None

    try:
        from langfuse.langchain import CallbackHandler
        from langfuse.types import TraceContext

        # Langfuse 3.x では環境変数から認証情報を読み込む
        # config値を環境変数としてエクスポート（Langfuse SDKが読み込む）
        _export_langfuse_env(config)

        # trace_context でカスタムtrace_idを設定可能
        trace_ctx: TraceContext | None = None
        if session_id:
            # session_idをtrace_idとして使用
            trace_ctx = {"trace_id": f"{trace_name or 'trace'}-{session_id}"}

        handler = CallbackHandler(
            update_trace=True,
            trace_context=trace_ctx,
        )

        # 注意: Langfuse 3.x では session_id, user_id, tags, metadata は
        # CallbackHandler経由では設定できない。
        # これらを使用する場合は @observe デコレータを使用する。
        if user_id or tags or metadata:
            logger.debug(
                f"Langfuse 3.x: user_id, tags, metadata are not supported "
                f"via CallbackHandler. trace_name={trace_name}"
            )

        logger.debug(f"Created Langfuse handler: trace_name={trace_name}")
        return handler

    except Exception as e:
        logger.warning(f"Failed to create Langfuse handler: {e}")
        return None


def create_trace_handler(
    operation: str,
    doc_id: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> CallbackHandler | None:
    """操作用のトレースハンドラーを作成する.

    Args:
        operation: 操作名（例: "analysis", "query", "vision"）
        doc_id: EDINET書類ID（オプション）
        provider: LLMプロバイダー名（オプション）
        model: モデル名（オプション）

    Returns:
        設定済みのCallbackHandler、または無効な場合None
    """
    tags = [operation]
    if provider:
        tags.append(f"provider:{provider}")

    metadata: dict[str, Any] = {}
    if doc_id:
        metadata["doc_id"] = doc_id
    if model:
        metadata["model"] = model

    return get_langfuse_handler(
        trace_name=f"company-research-{operation}",
        tags=tags,
        metadata=metadata if metadata else None,
    )


def clear_handler_cache() -> None:
    """ハンドラーキャッシュをクリアする（テスト用）."""
    import os

    global _langfuse_env_exported
    _get_langfuse_config.cache_clear()
    _langfuse_env_exported = False

    # Langfuse関連の環境変数もクリア
    for key in ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST", "LANGFUSE_DEBUG"]:
        os.environ.pop(key, None)
