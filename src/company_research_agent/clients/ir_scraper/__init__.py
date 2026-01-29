"""IR Scraper client package.

企業のIRページからIR資料を取得するためのクライアント群。
"""

from company_research_agent.clients.ir_scraper.base import BaseIRScraper

__all__ = [
    "BaseIRScraper",
]


def __getattr__(name: str) -> object:
    """遅延インポートを実現するためのgetattr.

    LLMExplorer, TemplateLoaderは別フェーズで実装するため、
    使用時にインポートする。
    """
    if name == "LLMExplorer":
        from company_research_agent.clients.ir_scraper.llm_explorer import LLMExplorer

        return LLMExplorer
    if name == "TemplateLoader":
        from company_research_agent.clients.ir_scraper.template_loader import (
            TemplateLoader,
        )

        return TemplateLoader
    if name == "IRTemplateConfig":
        from company_research_agent.schemas.ir_schemas import IRTemplateConfig

        return IRTemplateConfig
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
