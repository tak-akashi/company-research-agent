"""Langfuseハンドラーのテスト."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from company_research_agent.observability.handler import (
    clear_handler_cache,
    create_trace_handler,
    get_langfuse_handler,
    is_langfuse_enabled,
)


class TestLangfuseHandler:
    """Langfuseハンドラーのテスト."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """各テスト前にキャッシュをクリア."""
        clear_handler_cache()
        yield
        clear_handler_cache()

    def test_is_langfuse_enabled_false_by_default(self) -> None:
        """デフォルトでLangfuseが無効であることを確認."""
        # .envファイルからの読み込みを避けるため、環境変数を明示的に無効化
        env_vars = {
            "LANGFUSE_ENABLED": "false",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            assert is_langfuse_enabled() is False

    def test_is_langfuse_enabled_true_with_config(self) -> None:
        """設定が完了している場合にTrueを返すことを確認."""
        env_vars = {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
            "LANGFUSE_SECRET_KEY": "sk-lf-test",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            assert is_langfuse_enabled() is True

    def test_get_langfuse_handler_returns_none_when_disabled(self) -> None:
        """無効な場合にNoneを返すことを確認."""
        # .envファイルからの読み込みを避けるため、環境変数を明示的に無効化
        with patch.dict(os.environ, {"LANGFUSE_ENABLED": "false"}, clear=True):
            handler = get_langfuse_handler()
            assert handler is None

    def test_get_langfuse_handler_returns_none_without_keys(self) -> None:
        """キーが不完全な場合にNoneを返すことを確認."""
        env_vars = {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
            "LANGFUSE_SECRET_KEY": "",  # 空文字列で設定
        }
        with patch.dict(os.environ, env_vars, clear=True):
            handler = get_langfuse_handler()
            assert handler is None

    def test_get_langfuse_handler_creates_handler_when_enabled(self) -> None:
        """有効な場合にハンドラーを作成することを確認."""
        env_vars = {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
            "LANGFUSE_SECRET_KEY": "sk-lf-test",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with patch("langfuse.langchain.CallbackHandler") as MockHandler:
                MockHandler.return_value = MagicMock()
                handler = get_langfuse_handler(trace_name="test")
                assert handler is not None
                MockHandler.assert_called_once()

    def test_get_langfuse_handler_with_parameters(self) -> None:
        """パラメータが正しく渡されることを確認."""
        env_vars = {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
            "LANGFUSE_SECRET_KEY": "sk-lf-test",
            "LANGFUSE_BASE_URL": "https://custom.langfuse.com",
            "LANGFUSE_DEBUG": "true",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with patch("langfuse.langchain.CallbackHandler") as MockHandler:
                mock_handler = MagicMock()
                MockHandler.return_value = mock_handler
                handler = get_langfuse_handler(
                    session_id="session-1",
                    user_id="user-1",
                    trace_name="my-trace",
                    tags=["tag1", "tag2"],
                    metadata={"key": "value"},
                )
                assert handler is not None
                # Langfuse 3.x では update_trace と trace_context で初期化
                MockHandler.assert_called_once_with(
                    update_trace=True,
                    trace_context={"trace_id": "my-trace-session-1"},
                )

    def test_create_trace_handler_returns_none_when_disabled(self) -> None:
        """無効な場合にNoneを返すことを確認."""
        # .envファイルからの読み込みを避けるため、環境変数を明示的に無効化
        with patch.dict(os.environ, {"LANGFUSE_ENABLED": "false"}, clear=True):
            handler = create_trace_handler(operation="test")
            assert handler is None

    def test_create_trace_handler_with_metadata(self) -> None:
        """メタデータ付きでハンドラーを作成できることを確認."""
        env_vars = {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
            "LANGFUSE_SECRET_KEY": "sk-lf-test",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with patch("langfuse.langchain.CallbackHandler") as MockHandler:
                mock_handler = MagicMock()
                MockHandler.return_value = mock_handler
                handler = create_trace_handler(
                    operation="analysis",
                    doc_id="S100TEST",
                    provider="google",
                    model="gemini-2.5-flash",
                )
                assert handler is not None
                # Langfuse 3.x では update_trace=True で初期化される
                MockHandler.assert_called_once_with(
                    update_trace=True,
                    trace_context=None,  # session_id が渡されていないのでNone
                )

    def test_clear_handler_cache(self) -> None:
        """キャッシュクリアが動作することを確認."""
        env_vars = {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
            "LANGFUSE_SECRET_KEY": "sk-lf-test",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            assert is_langfuse_enabled() is True

        # キャッシュをクリアして環境変数を変更
        clear_handler_cache()

        # .envファイルからの読み込みを避けるため、環境変数を明示的に無効化
        with patch.dict(os.environ, {"LANGFUSE_ENABLED": "false"}, clear=True):
            # キャッシュがクリアされたので、新しい設定が読み込まれる
            assert is_langfuse_enabled() is False

    def test_get_langfuse_handler_handles_exception(self) -> None:
        """例外が発生した場合にNoneを返すことを確認."""
        env_vars = {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
            "LANGFUSE_SECRET_KEY": "sk-lf-test",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with patch("langfuse.langchain.CallbackHandler") as MockHandler:
                MockHandler.side_effect = Exception("Connection failed")
                handler = get_langfuse_handler()
                assert handler is None
