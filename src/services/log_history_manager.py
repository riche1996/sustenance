"""Log history manager for tracking and storing bug analysis logs."""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from src.services.opensearch_client import OpenSearchClient
from src.services.embedding_service import EmbeddingService
from src.trackers.jira_client import JiraIssue

logger = logging.getLogger(__name__)


class LogHistoryManager:
    """Manages log history with embeddings stored in OpenSearch."""
    
    def __init__(self, opensearch_host: str = "localhost", 
                 opensearch_port: int = 9200,
                 index_name: str = "bug_analysis_logs",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the log history manager.
        
        Args:
            opensearch_host: OpenSearch host
            opensearch_port: OpenSearch port
            index_name: Index name for logs
            embedding_model: Model name for embeddings
        """
        logger.info("Initializing Log History Manager...")
        
        # Initialize OpenSearch client
        self.opensearch = OpenSearchClient(
            host=opensearch_host,
            port=opensearch_port,
            index_name=index_name
        )
        
        # Initialize embedding service
        self.embedding_service = EmbeddingService(model_name=embedding_model)
        
        logger.info("✓ Log History Manager initialized")
    
    def log_analysis(self, 
                    bug: JiraIssue,
                    analysis_result: Dict[str, Any],
                    files_analyzed: List[str],
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a bug analysis with embedding.
        
        Args:
            bug: Jira bug issue
            analysis_result: Analysis results from Claude
            files_analyzed: List of files that were analyzed
            metadata: Additional metadata
            
        Returns:
            Document ID in OpenSearch
        """
        try:
            # Extract analysis text
            analysis_text = self._extract_analysis_text(analysis_result)
            
            # Generate embedding
            embedding = self.embedding_service.create_log_embedding(
                bug_summary=bug.summary,
                bug_description=bug.description or "",
                analysis_result=analysis_text
            )
            
            # Convert file paths to strings (handle WindowsPath objects)
            files_analyzed_str = [str(f) for f in files_analyzed]
            
            # Prepare log document
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'log_type': 'bug_analysis',
                'bug_id': bug.key,
                'bug_summary': bug.summary,
                'bug_description': bug.description or "",
                'bug_status': bug.status,
                'bug_priority': bug.priority,
                'analysis_result': analysis_text,
                'findings': analysis_result.get('findings', []),
                'files_analyzed': files_analyzed_str,
                'total_findings': len(analysis_result.get('findings', [])),
                'embedding': embedding,
                'metadata': metadata or {}
            }
            
            # Index in OpenSearch
            doc_id = self.opensearch.index_log(log_data)
            logger.info(f"✓ Logged analysis for bug {bug.key} (ID: {doc_id})")
            
            return doc_id
        except Exception as e:
            logger.error(f"Error logging analysis: {e}")
            raise
    
    def log_error(self, bug_id: str, error_message: str, 
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Log an error during analysis.
        
        Args:
            bug_id: Bug ID
            error_message: Error description
            metadata: Additional metadata
            
        Returns:
            Document ID
        """
        try:
            # Generate embedding for error
            embedding = self.embedding_service.embed_text(
                f"Error analyzing bug {bug_id}: {error_message}"
            )
            
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'log_type': 'error',
                'bug_id': bug_id,
                'error_message': error_message,
                'embedding': embedding,
                'metadata': metadata or {}
            }
            
            doc_id = self.opensearch.index_log(log_data)
            logger.warning(f"✓ Logged error for bug {bug_id}")
            
            return doc_id
        except Exception as e:
            logger.error(f"Error logging error: {e}")
            raise
    
    def search_similar_bugs(self, query: str, limit: int = 10, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search for similar bugs using semantic search.
        
        Args:
            query: Search query (e.g., bug description or symptoms)
            limit: Maximum number of results
            min_score: Minimum similarity score (0.0-1.0, default 0.0 = no filtering)
            
        Returns:
            List of similar bug analyses
        """
        try:
            # Generate embedding for query
            query_embedding = self.embedding_service.embed_text(query)
            
            # Perform semantic search with min_score filter
            results = self.opensearch.semantic_search(
                query_embedding, 
                size=limit,
                min_score=min_score
            )
            
            logger.info(f"Found {len(results)} similar bugs for query (min_score={min_score})")
            return results
        except Exception as e:
            logger.error(f"Error searching similar bugs: {e}")
            return []
    
    def get_bug_history(self, bug_id: str) -> List[Dict[str, Any]]:
        """
        Get complete analysis history for a bug.
        
        Args:
            bug_id: Bug ID
            
        Returns:
            List of all analyses for the bug
        """
        try:
            return self.opensearch.get_logs_by_bug(bug_id)
        except Exception as e:
            logger.error(f"Error getting bug history: {e}")
            return []
    
    def get_recent_analyses(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get most recent analyses.
        
        Args:
            limit: Number of analyses to retrieve
            
        Returns:
            List of recent analyses
        """
        try:
            return self.opensearch.get_recent_logs(size=limit)
        except Exception as e:
            logger.error(f"Error getting recent analyses: {e}")
            return []
    
    def find_duplicate_bugs(self, bug: JiraIssue, 
                           threshold: float = 0.85) -> List[Dict[str, Any]]:
        """
        Find potential duplicate bugs based on semantic similarity.
        
        Args:
            bug: Bug to check for duplicates
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of potential duplicate bugs
        """
        try:
            # Search for similar bugs
            query = f"{bug.summary} {bug.description or ''}"
            similar = self.search_similar_bugs(query, limit=20)
            
            # Filter by similarity threshold and exclude same bug
            duplicates = [
                log for log in similar
                if log.get('score', 0) >= threshold and log.get('bug_id') != bug.key
            ]
            
            logger.info(f"Found {len(duplicates)} potential duplicates for {bug.key}")
            return duplicates
        except Exception as e:
            logger.error(f"Error finding duplicates: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about logged analyses.
        
        Returns:
            Statistics dictionary
        """
        try:
            recent_logs = self.opensearch.get_recent_logs(size=1000)
            
            stats = {
                'total_analyses': len(recent_logs),
                'bugs_analyzed': len(set(log.get('bug_id') for log in recent_logs)),
                'total_findings': sum(log.get('total_findings', 0) for log in recent_logs),
                'avg_findings_per_bug': 0,
                'recent_errors': len([log for log in recent_logs if log.get('log_type') == 'error'])
            }
            
            if stats['bugs_analyzed'] > 0:
                stats['avg_findings_per_bug'] = round(
                    stats['total_findings'] / stats['bugs_analyzed'], 2
                )
            
            return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def _extract_analysis_text(self, analysis_result: Dict[str, Any]) -> str:
        """
        Extract readable text from analysis results.
        
        Args:
            analysis_result: Analysis results dictionary
            
        Returns:
            Formatted text
        """
        try:
            text_parts = []
            
            # Add summary if present
            if 'summary' in analysis_result:
                text_parts.append(analysis_result['summary'])
            
            # Add findings
            findings = analysis_result.get('findings', [])
            for finding in findings:
                if isinstance(finding, dict):
                    file_name = finding.get('file', 'Unknown')
                    line = finding.get('line', 'N/A')
                    issue = finding.get('issue', '')
                    severity = finding.get('severity', '')
                    
                    text_parts.append(
                        f"File: {file_name}, Line: {line}, Severity: {severity}, Issue: {issue}"
                    )
                elif isinstance(finding, str):
                    text_parts.append(finding)
            
            return " ".join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting analysis text: {e}")
            return str(analysis_result)
    
    def close(self):
        """Close connections and cleanup."""
        self.opensearch.close()
        logger.info("Log History Manager closed")
