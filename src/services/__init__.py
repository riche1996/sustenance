"""Core services for code analysis, embeddings, and reporting."""

# Use lazy imports to avoid circular import issues
__all__ = [
    "CodeAnalysisAgent",
    "CodeFile",
    "EmbeddingService", 
    "OpenSearchClient",
    "LogHistoryManager",
    "ReportGenerator",
    "IssueHistoryService",
    "GitHubOpenSearchSync",
    "sync_github_issues_to_opensearch",
    # Code Indexing Services (for large repository support)
    "CodeChunker",
    "CodeChunk",
    "CodeIndexService",
    "CodeSearchService",
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
    elif name == "IssueHistoryService":
        from .issue_history_service import IssueHistoryService
        return IssueHistoryService
    elif name == "GitHubOpenSearchSync":
        from .github_opensearch_sync import GitHubOpenSearchSync
        return GitHubOpenSearchSync
    elif name == "sync_github_issues_to_opensearch":
        from .github_opensearch_sync import sync_github_issues_to_opensearch
        return sync_github_issues_to_opensearch
    # Code Indexing Services
    elif name == "CodeChunker":
        from .code_chunker import CodeChunker
        return CodeChunker
    elif name == "CodeChunk":
        from .code_chunker import CodeChunk
        return CodeChunk
    elif name == "CodeIndexService":
        from .code_index_service import CodeIndexService
        return CodeIndexService
    elif name == "CodeSearchService":
        from .code_search_service import CodeSearchService
        return CodeSearchService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
