#!/usr/bin/env python3
"""
[DEPRECATED] 旧CLIスクリプト - 新CLIモジュールへリダイレクト

このスクリプトは後方互換性のために維持されています。
以下のコマンドを使用してください:

    uv run cra <command> [options]
    uv run python -m company_research_agent <command> [options]

使用例:
    uv run cra search --name "トヨタ"
    uv run cra download --sec-code 72030 --limit 3
    uv run cra cache --stats
"""

from __future__ import annotations

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from company_research_agent.cli import main  # noqa: E402

if __name__ == "__main__":
    print("[DEPRECATED] このスクリプトは非推奨です。")
    print("以下のコマンドを使用してください:")
    print("  uv run cra <command>")
    print("  uv run python -m company_research_agent <command>")
    print()
    main()
