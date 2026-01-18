"""テキスト処理ユーティリティ."""

from __future__ import annotations

from typing import Any


def extract_text_from_content(content: Any) -> str:
    """AIMessage.contentからテキストを抽出する.

    LangChainのAIMessage.contentは以下の形式を取りうる:
    - 文字列: "テキスト"
    - リスト: [{"type": "text", "text": "テキスト"}, ...]
    - None
    - その他

    Args:
        content: AIMessage.contentの値

    Returns:
        抽出されたテキスト。テキストが見つからない場合は空文字列。
    """
    if content is None:
        return ""

    # 文字列の場合はそのまま返す
    if isinstance(content, str):
        return content

    # リスト形式の場合（マルチモーダル）
    if isinstance(content, list):
        text_parts: list[str] = []
        for block in content:
            # dictの場合: {"type": "text", "text": "..."} 形式を想定
            if isinstance(block, dict):
                block_type = block.get("type", "")
                if block_type == "text":
                    text = block.get("text")
                    if isinstance(text, str) and text:
                        text_parts.append(text)
                # 他のタイプ（image, tool_use等）は無視
            # 文字列の場合: リスト内に直接文字列が入っているケース
            elif isinstance(block, str):
                text_parts.append(block)
            # その他の型は無視（エラーにしない）

        return "\n".join(text_parts) if text_parts else ""

    # その他の型は文字列化してフォールバック
    try:
        return str(content)
    except Exception:
        return ""
