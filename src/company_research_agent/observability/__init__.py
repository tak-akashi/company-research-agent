"""Observability module for Langfuse integration.

このモジュールはLangfuseによるオブザーバビリティ機能を提供します。
LLM呼び出しのトレース、コスト分析、エラーハンドリングのキャプチャを可能にします。

Example:
    >>> from company_research_agent.observability import is_langfuse_enabled
    >>> if is_langfuse_enabled():
    ...     handler = get_langfuse_handler(trace_name="my-trace")
    ...     # LLM呼び出しにhandlerを渡す

環境変数:
    LANGFUSE_ENABLED: Langfuseの有効/無効 (true/false)
    LANGFUSE_PUBLIC_KEY: Langfuse Public Key
    LANGFUSE_SECRET_KEY: Langfuse Secret Key
    LANGFUSE_BASE_URL: Langfuse API Base URL (default: https://cloud.langfuse.com)
    LANGFUSE_DEBUG: デバッグモードの有効/無効 (true/false)
"""

from company_research_agent.observability.config import LangfuseConfig
from company_research_agent.observability.handler import (
    clear_handler_cache,
    create_trace_handler,
    get_langfuse_handler,
    is_langfuse_enabled,
)

__all__ = [
    "LangfuseConfig",
    "clear_handler_cache",
    "create_trace_handler",
    "get_langfuse_handler",
    "is_langfuse_enabled",
]
