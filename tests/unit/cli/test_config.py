"""Tests for cli/config.py - CLI configuration and constants."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from company_research_agent.cli.config import (
    DEFAULT_DOC_TYPES,
    DEFAULT_DOWNLOAD_DOC_TYPES,
    DEFAULT_DOWNLOAD_LIMIT,
    DEFAULT_FORMAT,
    DEFAULT_LIMIT,
    DOC_TYPE_NAMES,
    get_download_dir,
)


class TestDocTypeNames:
    """DOC_TYPE_NAMES 定数のテスト."""

    def test_contains_yuho(self) -> None:
        """有価証券報告書が含まれること."""
        assert "120" in DOC_TYPE_NAMES
        assert DOC_TYPE_NAMES["120"] == "有価証券報告書"

    def test_contains_quarterly(self) -> None:
        """四半期報告書が含まれること."""
        assert "140" in DOC_TYPE_NAMES
        assert DOC_TYPE_NAMES["140"] == "四半期報告書"

    def test_contains_semiannual(self) -> None:
        """半期報告書が含まれること."""
        assert "160" in DOC_TYPE_NAMES
        assert DOC_TYPE_NAMES["160"] == "半期報告書"

    def test_contains_extraordinary(self) -> None:
        """臨時報告書が含まれること."""
        assert "180" in DOC_TYPE_NAMES
        assert DOC_TYPE_NAMES["180"] == "臨時報告書"

    def test_all_values_are_japanese(self) -> None:
        """全ての値が日本語文字列であること."""
        for code, name in DOC_TYPE_NAMES.items():
            assert isinstance(code, str)
            assert isinstance(name, str)
            assert len(name) > 0


class TestDefaultConstants:
    """デフォルト定数のテスト."""

    def test_default_limit(self) -> None:
        """DEFAULT_LIMIT が 20 であること."""
        assert DEFAULT_LIMIT == 20

    def test_default_download_limit(self) -> None:
        """DEFAULT_DOWNLOAD_LIMIT が 5 であること."""
        assert DEFAULT_DOWNLOAD_LIMIT == 5

    def test_default_doc_types(self) -> None:
        """DEFAULT_DOC_TYPES に有報と四半期報告が含まれること."""
        assert "120" in DEFAULT_DOC_TYPES
        assert "140" in DEFAULT_DOC_TYPES

    def test_default_download_doc_types(self) -> None:
        """DEFAULT_DOWNLOAD_DOC_TYPES に有報が含まれること."""
        assert "120" in DEFAULT_DOWNLOAD_DOC_TYPES

    def test_default_format(self) -> None:
        """DEFAULT_FORMAT が 'pdf' であること."""
        assert DEFAULT_FORMAT == "pdf"


class TestGetDownloadDir:
    """get_download_dir() のテスト."""

    def test_returns_path_object(self) -> None:
        """Pathオブジェクトを返すこと."""
        result = get_download_dir()
        assert isinstance(result, Path)

    def test_default_is_downloads_subdir(self) -> None:
        """環境変数未設定時はカレントディレクトリ/downloads を返すこと."""
        with patch.dict(os.environ, {}, clear=True):
            # CRA_DOWNLOAD_DIR が設定されていない場合
            if "CRA_DOWNLOAD_DIR" in os.environ:
                del os.environ["CRA_DOWNLOAD_DIR"]
            result = get_download_dir()
            assert result.name == "downloads"
            assert result.parent == Path.cwd()

    def test_env_var_override(self) -> None:
        """CRA_DOWNLOAD_DIR 環境変数で上書きできること."""
        custom_path = "/custom/download/path"
        with patch.dict(os.environ, {"CRA_DOWNLOAD_DIR": custom_path}):
            result = get_download_dir()
            assert result == Path(custom_path)

    def test_empty_env_var_uses_default(self) -> None:
        """空の環境変数はデフォルトを使用すること."""
        with patch.dict(os.environ, {"CRA_DOWNLOAD_DIR": ""}):
            result = get_download_dir()
            # 空文字列はFalsyなのでデフォルトが使われる
            assert result.name == "downloads"
