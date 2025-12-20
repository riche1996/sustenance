"""Core services for code analysis, embeddings, and reporting."""

# Use lazy imports to avoid circular import issues
__all__ = [
    "CodeAnalysisAgent",
    "CodeFile",
    "EmbeddingService", 
    "OpenSearchClient",
    "LogHistoryManager",
    "ReportGenerator"
]


def __getattr__(name):
    """Lazy import to avoid import-time issues."""
    if name == "CodeAnalysisAgent":
        from .code_analyzer import CodeAnalysisAgent
        return CodeAnalysisAgent
    elif name == "CodeFile":
        from .code_analyzer import CodeFile
        return CodeFile
    elif name == "EmbeddingService":
        from .embedding_service import EmbeddingService
        return EmbeddingService
    elif name == "OpenSearchClient":
        from .opensearch_client import OpenSearchClient
        return OpenSearchClient
    elif name == "LogHistoryManager":
        from .log_history_manager import LogHistoryManager
        return LogHistoryManager
    elif name == "ReportGenerator":
        from .report_generator import ReportGenerator
        return ReportGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
