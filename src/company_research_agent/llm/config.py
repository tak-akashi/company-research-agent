"""LLMプロバイダーの設定.

後方互換性のためのモジュール。core.configから再エクスポートする。
"""

from company_research_agent.core.config import LLMConfig

__all__ = ["LLMConfig"]
