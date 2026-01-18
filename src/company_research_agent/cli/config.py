"""CLI configuration and constants."""

from __future__ import annotations

import os
from pathlib import Path

# 書類種別コード
DOC_TYPE_NAMES: dict[str, str] = {
    "120": "有価証券報告書",
    "130": "訂正有価証券報告書",
    "140": "四半期報告書",
    "150": "訂正四半期報告書",
    "160": "半期報告書",
    "170": "訂正半期報告書",
    "180": "臨時報告書",
    "350": "大量保有報告書",
}

# デフォルト値
DEFAULT_LIMIT = 20
DEFAULT_DOWNLOAD_LIMIT = 5
DEFAULT_DOC_TYPES = ["120", "140"]
DEFAULT_DOWNLOAD_DOC_TYPES = ["120"]
DEFAULT_FORMAT = "pdf"


def get_download_dir() -> Path:
    """ダウンロードディレクトリを取得.

    環境変数 CRA_DOWNLOAD_DIR が設定されている場合はそれを使用。
    未設定の場合はカレントディレクトリ配下の downloads を使用。
    """
    env_dir = os.environ.get("CRA_DOWNLOAD_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.cwd() / "downloads"
