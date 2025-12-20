"""OpenSearch client for storing and retrieving embedded log data."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.helpers import bulk
import logging

logger = logging.getLogger(__name__)


class OpenSearchClient:
    """Manages connections and operations with OpenSearch."""
    
    def __init__(self, host: str = "localhost", port: int = 9200, 
                 index_name: str = "bug_analysis_logs"):
        """
        Initialize OpenSearch client.
        
        Args:
            host: OpenSearch host
            port: OpenSearch port
            index_name: Index name for storing logs
        """
        self.host = host
        self.port = port
        self.index_name = index_name
        
        # Initialize OpenSearch client
        self.client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            connection_class=RequestsHttpConnection
        )
        
        # Create index if it doesn't exist
        self._create_index_if_not_exists()
    
    def _create_index_if_not_exists(self):
        """Create the index with proper mappings if it doesn't exist."""
        if not self.client.indices.exists(index=self.index_name):
            index_body = {
                'settings': {
                    'index': {
                        'number_of_shards': 1,
                        'number_of_replicas': 0,
                        'knn': True  # Enable k-NN for vector search
                    }
                },
                'mappings': {
                    'properties': {
                        'timestamp': {'type': 'date'},
                        'log_type': {'type': 'keyword'},
                        'bug_id': {'type': 'keyword'},
                        'bug_summary': {'type': 'text'},
                        'bug_description': {'type': 'text'},
                        'bug_status': {'type': 'keyword'},
                        'bug_priority': {'type': 'keyword'},
                        'analysis_result': {'type': 'text'},
                        'findings': {
                            'type': 'object',
                            'enabled': True
                        },
                        'files_analyzed': {'type': 'keyword'},
                        'total_findings': {'type': 'integer'},
                        'error_message': {'type': 'text'},
                        'embedding': {
                            'type': 'knn_vector',
                            'dimension': 384
                        },
                        'metadata': {
                            'type': 'object',
                            'enabled': True
                        }
                    }
                }
            }
            
            self.client.indices.create(index=self.index_name, body=index_body)
            logger.info(f"Created OpenSearch index: {self.index_name}")
        else:
            logger.info(f"OpenSearch index already exists: {self.index_name}")
    
    def index_log(self, log_data: Dict[str, Any]) -> str:
        """
        Index a single log entry.
        
        Args:
            log_data: Log data to index
            
        Returns:
            Document ID
        """
        try:
            # Validate embedding dimensions if present
            if 'embedding' in log_data:
                if not isinstance(log_data['embedding'], list):
                    logger.warning("Converting embedding to list")
                    log_data['embedding'] = log_data['embedding'].tolist()
                
                expected_dim = 384
                actual_dim = len(log_data['embedding'])
                if actual_dim != expected_dim:
                    logger.warning(f"Embedding dimension mismatch: expected {expected_dim}, got {actual_dim}")
            
            response = self.client.index(
                index=self.index_name,
                body=log_data,
                refresh=True
            )
            logger.info(f"Indexed log: {response['_id']}")
            return response['_id']
        except Exception as e:
            logger.error(f"Error indexing log: {e}")
            logger.error(f"Log data keys: {log_data.keys()}")
            if 'embedding' in log_data:
                logger.error(f"Embedding type: {type(log_data['embedding'])}, length: {len(log_data['embedding']) if hasattr(log_data['embedding'], '__len__') else 'N/A'}")
            raise
    
    def bulk_index_logs(self, logs: List[Dict[str, Any]]) -> bool:
        """
        Bulk index multiple log entries.
        
        Args:
            logs: List of log entries
            
        Returns:
            Success status
        """
        try:
            actions = [
                {
                    '_index': self.index_name,
                    '_source': log
                }
                for log in logs
            ]
            
            success, failed = bulk(self.client, actions, refresh=True)
            logger.info(f"Bulk indexed {success} logs, {failed} failed")
            return failed == 0
        except Exception as e:
            logger.error(f"Error bulk indexing logs: {e}")
            return False
    
    def search_logs(self, query: str, size: int = 10) -> List[Dict[str, Any]]:
        """
        Search logs using text query.
        
        Args:
            query: Search query
            size: Number of results
            
        Returns:
            List of matching logs
        """
        try:
            search_body = {
                'query': {
                    'multi_match': {
                        'query': query,
                        'fields': ['bug_summary^3', 'bug_description^2', 'analysis_result']
                    }
                },
                'size': size
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            return []
    
    def semantic_search(self, query_embedding: List[float], size: int = 10, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search logs using semantic similarity (k-NN).
        
        Args:
            query_embedding: Query vector
            size: Number of results
            min_score: Minimum similarity score (0.0-1.0, default 0.0 = no filtering)
            
        Returns:
            List of similar logs
        """
        try:
            search_body = {
                'query': {
                    'knn': {
                        'embedding': {
                            'vector': query_embedding,
                            'k': size
                        }
                    }
                },
                'size': size
            }
            
            # Add min_score filter if specified
            if min_score > 0.0:
                search_body['min_score'] = min_score
            
            response = self.client.search(index=self.index_name, body=search_body)
            return [
                {
                    **hit['_source'],
                    'score': hit['_score']
                }
                for hit in response['hits']['hits']
            ]
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def get_logs_by_bug(self, bug_id: str) -> List[Dict[str, Any]]:
        """
        Get all logs for a specific bug.
        
        Args:
            bug_id: Bug ID
            
        Returns:
            List of logs
        """
        try:
            search_body = {
                'query': {
                    'term': {'bug_id': bug_id}
                },
                'sort': [{'timestamp': 'desc'}]
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            logger.error(f"Error getting logs by bug: {e}")
            return []
    
    def get_recent_logs(self, size: int = 50) -> List[Dict[str, Any]]:
        """
        Get most recent logs.
        
        Args:
            size: Number of logs to retrieve
            
        Returns:
            List of recent logs
        """
        try:
            search_body = {
                'query': {'match_all': {}},
                'sort': [{'timestamp': 'desc'}],
                'size': size
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            return []
    
    def delete_logs_by_bug(self, bug_id: str) -> bool:
        """
        Delete all logs for a specific bug.
        
        Args:
            bug_id: Bug ID
            
        Returns:
            Success status
        """
        try:
            delete_body = {
                'query': {
                    'term': {'bug_id': bug_id}
                }
            }
            
            response = self.client.delete_by_query(
                index=self.index_name, 
                body=delete_body
            )
            logger.info(f"Deleted {response['deleted']} logs for bug {bug_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting logs: {e}")
            return False
    
    def close(self):
        """Close the OpenSearch connection."""
        self.client.close()
