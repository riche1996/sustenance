"""GitHub Issues to OpenSearch synchronization service."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.helpers import bulk
import logging
import hashlib

logger = logging.getLogger(__name__)

# Lazy load embedding service to avoid import issues
_embedding_service = None
_attachment_service = None

# Local embedding model path (offline model)
LOCAL_EMBEDDING_MODEL = r"C:\AIForce\offline_model\embedding_model\multi-qa-MiniLM-L6-cos-v1"

def get_embedding_service():
    """Get or create the embedding service singleton using local model."""
    global _embedding_service
    if _embedding_service is None:
        try:
            from src.services.embedding_service import EmbeddingService
            # Use local model path
            _embedding_service = EmbeddingService(model_name=LOCAL_EMBEDDING_MODEL)
            logger.info(f"Embedding service initialized with local model: {LOCAL_EMBEDDING_MODEL}")
        except Exception as e:
            logger.warning(f"Failed to initialize embedding service: {e}")
            _embedding_service = False  # Mark as failed
    return _embedding_service if _embedding_service else None


def get_attachment_service():
    """Get or create the attachment service singleton."""
    global _attachment_service
    if _attachment_service is None:
        try:
            from src.services.attachment_service import AttachmentService
            _attachment_service = AttachmentService()
            logger.info("Attachment service initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize attachment service: {e}")
            _attachment_service = False  # Mark as failed
    return _attachment_service if _attachment_service else None


class GitHubOpenSearchSync:
    """Synchronize GitHub issues with OpenSearch for indexing and search."""
    
    ISSUES_INDEX = "github_issues"
    
    def __init__(self, host: str = "localhost", port: int = 9200, 
                 index_name: Optional[str] = None,
                 enable_embeddings: bool = True):
        """
        Initialize GitHub OpenSearch sync service.
        
        Args:
            host: OpenSearch host
            port: OpenSearch port  
            index_name: Custom index name (default: github_issues)
            enable_embeddings: Whether to generate embeddings for semantic search
        """
        self.host = host
        self.port = port
        self.index_name = index_name or self.ISSUES_INDEX
        self.enable_embeddings = enable_embeddings
        self._embedding_service = None
        
        # Initialize OpenSearch client
        self.client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            connection_class=RequestsHttpConnection,
            timeout=30
        )
        
        self._connected = False
        self._check_connection()
        
        # Initialize embedding service if enabled
        if self.enable_embeddings:
            self._embedding_service = get_embedding_service()
            if self._embedding_service:
                logger.info("Embeddings enabled for semantic search")
            else:
                logger.warning("Embeddings disabled - service unavailable")
                self.enable_embeddings = False
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text content."""
        if not self.enable_embeddings or not self._embedding_service:
            return None
        try:
            return self._embedding_service.embed_text(text)
        except Exception as e:
            logger.warning(f"Failed to generate embedding: {e}")
            return None
    
    def _generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts efficiently."""
        if not self.enable_embeddings or not self._embedding_service:
            return [None] * len(texts)
        try:
            return self._embedding_service.embed_texts(texts)
        except Exception as e:
            logger.warning(f"Failed to generate batch embeddings: {e}")
            return [None] * len(texts)
    
    def _check_connection(self) -> bool:
        """Check if OpenSearch is accessible."""
        try:
            info = self.client.info()
            logger.info(f"Connected to OpenSearch: {info['version']['number']}")
            self._connected = True
            return True
        except Exception as e:
            logger.warning(f"OpenSearch not available: {e}")
            self._connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to OpenSearch."""
        return self._connected
    
    def create_issues_index(self) -> bool:
        """Create the GitHub issues index with proper mappings."""
        try:
            if self.client.indices.exists(index=self.index_name):
                logger.info(f"Index '{self.index_name}' already exists")
                return True
            
            index_body = {
                'settings': {
                    'index': {
                        'number_of_shards': 1,
                        'number_of_replicas': 0,
                        'knn': True  # Enable k-NN for vector search
                    },
                    'analysis': {
                        'analyzer': {
                            'issue_analyzer': {
                                'type': 'custom',
                                'tokenizer': 'standard',
                                'filter': ['lowercase', 'stop', 'snowball']
                            }
                        }
                    }
                },
                'mappings': {
                    'properties': {
                        # Issue identifiers
                        'issue_id': {'type': 'keyword'},
                        'number': {'type': 'integer'},
                        'repository': {'type': 'keyword'},
                        'owner': {'type': 'keyword'},
                        
                        # Issue content
                        'title': {
                            'type': 'text',
                            'analyzer': 'issue_analyzer',
                            'fields': {
                                'keyword': {'type': 'keyword', 'ignore_above': 512}
                            }
                        },
                        'body': {
                            'type': 'text',
                            'analyzer': 'issue_analyzer'
                        },
                        'body_preview': {'type': 'text'},  # Truncated body for display
                        
                        # Issue metadata
                        'state': {'type': 'keyword'},
                        'labels': {'type': 'keyword'},
                        'assignee': {'type': 'keyword'},
                        'assignees': {'type': 'keyword'},
                        'created_by': {'type': 'keyword'},
                        'milestone': {'type': 'keyword'},
                        
                        # Timestamps
                        'created_at': {'type': 'date'},
                        'updated_at': {'type': 'date'},
                        'closed_at': {'type': 'date'},
                        'indexed_at': {'type': 'date'},
                        
                        # URLs
                        'html_url': {'type': 'keyword'},
                        
                        # Embedding for semantic search
                        'embedding': {
                            'type': 'knn_vector',
                            'dimension': 384  # For sentence-transformers models
                        },
                        
                        # Sync metadata
                        'sync_source': {'type': 'keyword'},
                        'sync_batch_id': {'type': 'keyword'}
                    }
                }
            }
            
            self.client.indices.create(index=self.index_name, body=index_body)
            logger.info(f"Created OpenSearch index: {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False
    
    def index_attachment(self, attachment_doc: Dict[str, Any], 
                        index_name: str = "issue_history") -> Optional[str]:
        """
        Index a single attachment document in the issue_history index.
        
        Args:
            attachment_doc: Attachment document (from AttachmentService.create_attachment_document)
            index_name: Index name (default: issue_history to store with issues)
            
        Returns:
            Document ID or None on failure
        """
        try:
            doc_id = attachment_doc.get('document_id')
            
            # Ensure document_type is set to 'attachment'
            attachment_doc['document_type'] = 'attachment'
            
            # Generate embedding for content if enabled
            if self.enable_embeddings and 'embedding' not in attachment_doc:
                content = attachment_doc.get('text_content', '') or attachment_doc.get('content', '')
                if content:
                    # Truncate for embedding (max ~5000 chars)
                    embed_content = content[:5000]
                    embedding = self._generate_embedding(embed_content)
                    if embedding:
                        attachment_doc['embedding'] = embedding
            
            # Add timestamp
            attachment_doc['indexed_at'] = datetime.utcnow().isoformat()
            
            # Create text preview
            content = attachment_doc.get('text_content', '') or attachment_doc.get('content', '')
            attachment_doc['text_preview'] = content[:500] + '...' if len(content) > 500 else content
            
            response = self.client.index(
                index=index_name,
                id=doc_id,
                body=attachment_doc,
                refresh=True
            )
            
            logger.info(f"Indexed attachment: {doc_id}")
            return response['_id']
            
        except Exception as e:
            logger.error(f"Error indexing attachment: {e}")
            return None
    
    def bulk_index_attachments(self, attachment_docs: List[Dict[str, Any]],
                               index_name: str = "issue_history",
                               batch_size: int = 50) -> Dict[str, Any]:
        """
        Bulk index multiple attachment documents in the issue_history index.
        
        Args:
            attachment_docs: List of attachment documents
            index_name: Index name (default: issue_history to store with issues)
            batch_size: Number of documents per bulk request
            
        Returns:
            Summary dict with success count, failed count
        """
        if not attachment_docs:
            return {'success': 0, 'failed': 0, 'message': 'No attachments to index'}
        
        total_success = 0
        total_failed = 0
        embeddings_generated = 0
        
        logger.info(f"Starting bulk index of {len(attachment_docs)} attachments to {index_name}")
        
        # Process in batches
        for i in range(0, len(attachment_docs), batch_size):
            batch = attachment_docs[i:i + batch_size]
            
            # Generate embeddings for batch if enabled
            if self.enable_embeddings:
                texts = [(doc.get('text_content', '') or doc.get('content', ''))[:5000] for doc in batch]
                batch_embeddings = self._generate_embeddings_batch(texts)
                
                for j, doc in enumerate(batch):
                    if batch_embeddings and j < len(batch_embeddings) and batch_embeddings[j]:
                        doc['embedding'] = batch_embeddings[j]
                        embeddings_generated += 1
            
            actions = []
            for doc in batch:
                # Ensure document_type is set
                doc['document_type'] = 'attachment'
                doc['indexed_at'] = datetime.utcnow().isoformat()
                content = doc.get('text_content', '') or doc.get('content', '')
                doc['text_preview'] = content[:500] + '...' if len(content) > 500 else content
                
                actions.append({
                    '_index': index_name,
                    '_id': doc.get('document_id'),
                    '_source': doc
                })
            
            try:
                success, errors = bulk(
                    self.client,
                    actions,
                    refresh=True,
                    raise_on_error=False,
                    raise_on_exception=False
                )
                total_success += success
                
                if errors:
                    total_failed += len(errors)
                    
            except Exception as e:
                logger.error(f"Bulk indexing error: {e}")
                total_failed += len(actions)
        
        result = {
            'success': total_success,
            'failed': total_failed,
            'embeddings_generated': embeddings_generated,
            'total': len(attachment_docs),
            'message': f"Indexed {total_success}/{len(attachment_docs)} attachments"
        }
        
        logger.info(f"Bulk attachment index complete: {result['message']}")
        return result
    
    def search_attachments(self, query: str, size: int = 10,
                          issue_id: Optional[str] = None,
                          owner: Optional[str] = None,
                          repo: Optional[str] = None,
                          index_name: str = "issue_history") -> List[Dict[str, Any]]:
        """
        Search attachment content in the issue_history index.
        
        Args:
            query: Search query text
            size: Number of results
            issue_id: Filter by issue ID
            owner: Filter by owner
            repo: Filter by repository
            index_name: Index name (default: issue_history)
            
        Returns:
            List of matching attachment documents
        """
        try:
            must = []
            filter_clauses = [
                {'term': {'document_type': 'attachment'}}  # Only search attachments
            ]
            
            if query:
                must.append({
                    'multi_match': {
                        'query': query,
                        'fields': ['text_content^2', 'filename', 'text_preview'],
                        'type': 'best_fields',
                        'fuzziness': 'AUTO'
                    }
                })
            
            if issue_id:
                filter_clauses.append({'term': {'issue_id': issue_id}})
            if owner:
                filter_clauses.append({'term': {'repo_owner': owner}})
            if repo:
                filter_clauses.append({'term': {'repo_name': repo}})
            
            search_body = {
                'query': {
                    'bool': {
                        'must': must if must else [{'match_all': {}}],
                        'filter': filter_clauses
                    }
                },
                'size': size,
                '_source': {
                    'excludes': ['embedding', 'text_content']  # Exclude large fields
                }
            }
            
            response = self.client.search(index=index_name, body=search_body)
            
            return [
                {**hit['_source'], '_score': hit['_score']}
                for hit in response['hits']['hits']
            ]
            
        except Exception as e:
            logger.error(f"Error searching attachments: {e}")
            return []
    
    def _generate_issue_id(self, owner: str, repo: str, number: int) -> str:
        """Generate a unique ID for an issue."""
        return f"{owner}/{repo}#{number}"
    
    def _convert_issue_to_document(self, issue: Any, owner: str, repo: str, 
                                   batch_id: Optional[str] = None,
                                   embedding: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Convert a GitHubIssue to an OpenSearch document.
        
        Args:
            issue: GitHubIssue object or dict
            owner: Repository owner
            repo: Repository name
            batch_id: Optional batch ID for tracking sync batches
            embedding: Optional embedding vector
            
        Returns:
            OpenSearch document dict
        """
        # Handle both GitHubIssue objects and dicts
        if hasattr(issue, 'model_dump'):
            issue_data = issue.model_dump()
        elif hasattr(issue, 'dict'):
            issue_data = issue.dict()
        elif isinstance(issue, dict):
            issue_data = issue
        else:
            raise ValueError(f"Unsupported issue type: {type(issue)}")
        
        # Create body preview (first 500 chars)
        body = issue_data.get('body') or ''
        body_preview = body[:500] + '...' if len(body) > 500 else body
        
        doc = {
            'issue_id': self._generate_issue_id(owner, repo, issue_data['number']),
            'number': issue_data['number'],
            'repository': repo,
            'owner': owner,
            'title': issue_data['title'],
            'body': body,
            'body_preview': body_preview,
            'state': issue_data['state'],
            'labels': issue_data.get('labels', []),
            'assignee': issue_data.get('assignee'),
            'assignees': issue_data.get('assignees', []),
            'created_by': issue_data.get('created_by'),
            'milestone': issue_data.get('milestone'),
            'created_at': issue_data['created_at'],
            'updated_at': issue_data['updated_at'],
            'closed_at': issue_data.get('closed_at'),
            'html_url': issue_data['html_url'],
            'indexed_at': datetime.utcnow().isoformat(),
            'sync_source': 'github',
            'sync_batch_id': batch_id
        }
        
        # Use provided embedding or generate one if embeddings are enabled
        if embedding:
            doc['embedding'] = embedding
        elif self.enable_embeddings and not embedding:
            # Auto-generate embedding from title + body
            content = f"{issue_data['title']}\n{body}"
            auto_embedding = self._generate_embedding(content)
            if auto_embedding:
                doc['embedding'] = auto_embedding
        
        return doc
    
    def index_issue(self, issue: Any, owner: str, repo: str,
                    embedding: Optional[List[float]] = None) -> Optional[str]:
        """
        Index a single GitHub issue with automatic embedding generation.
        
        Args:
            issue: GitHubIssue object or dict
            owner: Repository owner
            repo: Repository name
            embedding: Optional pre-computed embedding vector
            
        Returns:
            Document ID or None on failure
        """
        try:
            doc = self._convert_issue_to_document(issue, owner, repo, embedding=embedding)
            issue_id = doc['issue_id']
            
            response = self.client.index(
                index=self.index_name,
                id=issue_id,  # Use issue_id as document ID for upsert behavior
                body=doc,
                refresh=True
            )
            
            logger.info(f"Indexed issue: {issue_id}")
            return response['_id']
            
        except Exception as e:
            logger.error(f"Error indexing issue: {e}")
            return None
    
    def get_existing_issue_ids(self, owner: str, repo: str) -> set:
        """
        Get all existing issue IDs for a repository from the index.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Set of existing issue IDs
        """
        existing_ids = set()
        try:
            # Use scroll API for large result sets
            search_body = {
                'query': {
                    'bool': {
                        'must': [
                            {'term': {'owner': owner}},
                            {'term': {'repository': repo}}
                        ]
                    }
                },
                '_source': ['issue_id'],
                'size': 1000
            }
            
            response = self.client.search(
                index=self.index_name,
                body=search_body,
                scroll='2m'
            )
            
            scroll_id = response.get('_scroll_id')
            hits = response['hits']['hits']
            
            while hits:
                for hit in hits:
                    existing_ids.add(hit['_source']['issue_id'])
                
                if not scroll_id:
                    break
                    
                response = self.client.scroll(scroll_id=scroll_id, scroll='2m')
                scroll_id = response.get('_scroll_id')
                hits = response['hits']['hits']
            
            # Clear scroll context
            if scroll_id:
                try:
                    self.client.clear_scroll(scroll_id=scroll_id)
                except Exception:
                    pass
                    
            logger.info(f"Found {len(existing_ids)} existing issues for {owner}/{repo}")
            
        except Exception as e:
            logger.warning(f"Error fetching existing issue IDs: {e}")
        
        return existing_ids
    
    def bulk_index_issues(self, issues: List[Any], owner: str, repo: str,
                          embeddings: Optional[List[List[float]]] = None,
                          batch_size: int = 100,
                          skip_duplicates: bool = True) -> Dict[str, Any]:
        """
        Bulk index multiple GitHub issues efficiently with automatic embedding generation.
        
        Args:
            issues: List of GitHubIssue objects or dicts
            owner: Repository owner
            repo: Repository name
            embeddings: Optional list of pre-computed embedding vectors (same order as issues)
            batch_size: Number of documents per bulk request
            skip_duplicates: Skip issues that already exist in the index (default: True)
            
        Returns:
            Summary dict with success count, failed count, and details
        """
        if not issues:
            return {'success': 0, 'failed': 0, 'skipped': 0, 'message': 'No issues to index'}
        
        # Generate batch ID for this sync operation
        batch_id = hashlib.md5(
            f"{owner}/{repo}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Get existing issue IDs to avoid duplicates
        existing_ids = set()
        skipped_count = 0
        if skip_duplicates:
            existing_ids = self.get_existing_issue_ids(owner, repo)
            logger.info(f"Checking against {len(existing_ids)} existing issues")
        
        total_success = 0
        total_failed = 0
        failed_issues = []
        embeddings_generated = 0
        
        logger.info(f"Starting bulk index of {len(issues)} issues (batch: {batch_id}, embeddings: {self.enable_embeddings})")
        
        # Process in batches
        for i in range(0, len(issues), batch_size):
            batch = issues[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size] if embeddings else None
            
            # Generate embeddings for this batch if enabled and not pre-computed
            if self.enable_embeddings and batch_embeddings is None:
                # Extract texts for embedding
                texts = []
                for issue in batch:
                    if hasattr(issue, 'model_dump'):
                        issue_data = issue.model_dump()
                    elif hasattr(issue, 'dict'):
                        issue_data = issue.dict()
                    else:
                        issue_data = issue
                    content = f"{issue_data.get('title', '')}\n{issue_data.get('body', '') or ''}"
                    texts.append(content)
                
                # Batch generate embeddings
                batch_embeddings = self._generate_embeddings_batch(texts)
                if batch_embeddings and any(e is not None for e in batch_embeddings):
                    embeddings_generated += sum(1 for e in batch_embeddings if e is not None)
            
            actions = []
            for j, issue in enumerate(batch):
                try:
                    embedding = batch_embeddings[j] if batch_embeddings and j < len(batch_embeddings) else None
                    doc = self._convert_issue_to_document(
                        issue, owner, repo, 
                        batch_id=batch_id,
                        embedding=embedding
                    )
                    
                    # Skip if issue already exists
                    if skip_duplicates and doc['issue_id'] in existing_ids:
                        skipped_count += 1
                        continue
                    
                    actions.append({
                        '_index': self.index_name,
                        '_id': doc['issue_id'],
                        '_source': doc
                    })
                except Exception as e:
                    logger.error(f"Error converting issue: {e}")
                    total_failed += 1
                    failed_issues.append({'issue': str(issue), 'error': str(e)})
            
            if actions:
                try:
                    success, errors = bulk(
                        self.client, 
                        actions, 
                        refresh=True,
                        raise_on_error=False,
                        raise_on_exception=False
                    )
                    total_success += success
                    
                    if errors:
                        for error in errors:
                            total_failed += 1
                            failed_issues.append(error)
                            
                    logger.info(f"Batch {i // batch_size + 1}: indexed {success} issues, skipped {skipped_count} duplicates")
                    
                except Exception as e:
                    logger.error(f"Bulk indexing error: {e}")
                    total_failed += len(actions)
        
        result = {
            'success': total_success,
            'failed': total_failed,
            'skipped': skipped_count,
            'embeddings_generated': embeddings_generated,
            'total': len(issues),
            'batch_id': batch_id,
            'index': self.index_name,
            'message': f"Indexed {total_success}/{len(issues)} issues ({skipped_count} skipped, {embeddings_generated} embeddings)"
        }
        
        if failed_issues:
            result['failed_details'] = failed_issues[:10]  # Limit to first 10
        
        logger.info(f"Bulk index complete: {result['message']}")
        return result
    
    def search_issues(self, query: str, size: int = 20,
                      owner: Optional[str] = None,
                      repo: Optional[str] = None,
                      state: Optional[str] = None,
                      labels: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search issues using text query with optional filters.
        
        Args:
            query: Search query text
            size: Number of results
            owner: Filter by repository owner
            repo: Filter by repository name
            state: Filter by issue state (open/closed)
            labels: Filter by labels
            
        Returns:
            List of matching issues
        """
        try:
            # Build query
            must = []
            filter_clauses = []
            
            # Main text search
            if query:
                must.append({
                    'multi_match': {
                        'query': query,
                        'fields': ['title^3', 'body^2', 'labels'],
                        'type': 'best_fields',
                        'fuzziness': 'AUTO'
                    }
                })
            
            # Filters
            if owner:
                filter_clauses.append({'term': {'owner': owner}})
            if repo:
                filter_clauses.append({'term': {'repository': repo}})
            if state:
                filter_clauses.append({'term': {'state': state}})
            if labels:
                filter_clauses.append({'terms': {'labels': labels}})
            
            search_body = {
                'query': {
                    'bool': {
                        'must': must if must else [{'match_all': {}}],
                        'filter': filter_clauses
                    }
                },
                'size': size,
                'sort': [
                    {'_score': 'desc'},
                    {'updated_at': 'desc'}
                ],
                '_source': {
                    'excludes': ['embedding']  # Exclude large embedding field
                }
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            
            results = []
            for hit in response['hits']['hits']:
                result = hit['_source']
                result['_score'] = hit['_score']
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching issues: {e}")
            return []
    
    def semantic_search_issues(self, query_embedding: List[float], size: int = 10,
                               owner: Optional[str] = None,
                               repo: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search issues using semantic similarity (k-NN).
        
        Args:
            query_embedding: Query vector
            size: Number of results
            owner: Filter by owner
            repo: Filter by repository
            
        Returns:
            List of similar issues
        """
        try:
            # Build filter
            filter_clauses = []
            if owner:
                filter_clauses.append({'term': {'owner': owner}})
            if repo:
                filter_clauses.append({'term': {'repository': repo}})
            
            search_body = {
                'query': {
                    'knn': {
                        'embedding': {
                            'vector': query_embedding,
                            'k': size
                        }
                    }
                },
                'size': size,
                '_source': {
                    'excludes': ['embedding']
                }
            }
            
            # Add filter if specified
            if filter_clauses:
                search_body['query'] = {
                    'bool': {
                        'must': [search_body['query']],
                        'filter': filter_clauses
                    }
                }
            
            response = self.client.search(index=self.index_name, body=search_body)
            
            return [
                {**hit['_source'], '_score': hit['_score']}
                for hit in response['hits']['hits']
            ]
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def get_issue_by_number(self, owner: str, repo: str, number: int) -> Optional[Dict[str, Any]]:
        """Get a specific issue by its number."""
        issue_id = self._generate_issue_id(owner, repo, number)
        try:
            response = self.client.get(index=self.index_name, id=issue_id)
            return response['_source']
        except Exception as e:
            logger.debug(f"Issue not found: {issue_id}")
            return None
    
    def get_issues_stats(self, owner: Optional[str] = None, 
                         repo: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about indexed issues.
        
        Args:
            owner: Filter by owner
            repo: Filter by repository
            
        Returns:
            Statistics dict
        """
        try:
            # Build filter
            filter_clauses = []
            if owner:
                filter_clauses.append({'term': {'owner': owner}})
            if repo:
                filter_clauses.append({'term': {'repository': repo}})
            
            query = {'bool': {'filter': filter_clauses}} if filter_clauses else {'match_all': {}}
            
            search_body = {
                'query': query,
                'size': 0,
                'aggs': {
                    'total_issues': {'value_count': {'field': 'number'}},
                    'by_state': {'terms': {'field': 'state'}},
                    'by_repository': {'terms': {'field': 'repository', 'size': 50}},
                    'by_labels': {'terms': {'field': 'labels', 'size': 50}},
                    'latest_sync': {'max': {'field': 'indexed_at'}},
                    'date_range': {
                        'stats': {'field': 'created_at'}
                    }
                }
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            aggs = response['aggregations']
            
            return {
                'total_issues': aggs['total_issues']['value'],
                'by_state': {b['key']: b['doc_count'] for b in aggs['by_state']['buckets']},
                'by_repository': {b['key']: b['doc_count'] for b in aggs['by_repository']['buckets']},
                'top_labels': {b['key']: b['doc_count'] for b in aggs['by_labels']['buckets'][:20]},
                'latest_sync': aggs['latest_sync']['value_as_string'],
                'date_range': {
                    'earliest': aggs['date_range']['min_as_string'],
                    'latest': aggs['date_range']['max_as_string']
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {'error': str(e)}
    
    def delete_repository_issues(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Delete all issues for a specific repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Deletion result
        """
        try:
            delete_body = {
                'query': {
                    'bool': {
                        'must': [
                            {'term': {'owner': owner}},
                            {'term': {'repository': repo}}
                        ]
                    }
                }
            }
            
            response = self.client.delete_by_query(
                index=self.index_name,
                body=delete_body,
                refresh=True
            )
            
            return {
                'deleted': response['deleted'],
                'repository': f"{owner}/{repo}"
            }
            
        except Exception as e:
            logger.error(f"Error deleting issues: {e}")
            return {'error': str(e)}
    
    def close(self):
        """Close the OpenSearch connection."""
        self.client.close()


def sync_github_issues_to_opensearch(
    github_client,
    opensearch_host: str = "localhost",
    opensearch_port: int = 9200,
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    state: str = "all",
    max_issues: int = 500,
    enable_embeddings: bool = True,
    skip_duplicates: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to sync GitHub issues to OpenSearch with embeddings.
    
    Args:
        github_client: GitHubMCPServer instance
        opensearch_host: OpenSearch host
        opensearch_port: OpenSearch port
        owner: Repository owner (uses client default if not specified)
        repo: Repository name (uses client default if not specified)
        state: Issue state filter ('open', 'closed', 'all')
        max_issues: Maximum issues to fetch
        enable_embeddings: Whether to generate embeddings for semantic search (default: True)
        skip_duplicates: Skip issues that already exist in the index (default: True)
        
    Returns:
        Sync result summary
    """
    from datetime import datetime
    
    owner = owner or github_client.owner
    repo = repo or github_client.repo
    
    print(f"\n{'='*60}")
    print(f"GitHub Issues → OpenSearch Sync")
    print(f"{'='*60}")
    print(f"Repository: {owner}/{repo}")
    print(f"State filter: {state}")
    print(f"Max issues: {max_issues}")
    print(f"Embeddings: {'enabled' if enable_embeddings else 'disabled'}")
    print(f"OpenSearch: {opensearch_host}:{opensearch_port}")
    print(f"{'='*60}\n")
    
    # Initialize sync service with embeddings
    sync_service = GitHubOpenSearchSync(
        host=opensearch_host,
        port=opensearch_port,
        enable_embeddings=enable_embeddings
    )
    
    if not sync_service.is_connected():
        return {
            'success': False,
            'error': 'Failed to connect to OpenSearch',
            'message': 'Please ensure OpenSearch is running and accessible'
        }
    
    # Create index
    if not sync_service.create_issues_index():
        return {
            'success': False,
            'error': 'Failed to create index'
        }
    
    # Fetch issues from GitHub
    print(f"📥 Fetching {state} issues from GitHub...")
    issues = github_client.get_issues(
        owner=owner,
        repo=repo,
        state=state,
        max_results=max_issues
    )
    
    if not issues:
        return {
            'success': True,
            'message': 'No issues to sync',
            'issues_fetched': 0,
            'issues_indexed': 0
        }
    
    print(f"✓ Fetched {len(issues)} issues")
    
    # Bulk index to OpenSearch (embeddings are generated automatically if enabled)
    dup_msg = "(skipping duplicates)" if skip_duplicates else "(force re-index)"
    embed_msg = "with embeddings" if enable_embeddings else "without embeddings"
    print(f"📤 Indexing {len(issues)} issues to OpenSearch {dup_msg} {embed_msg}...")
    
    result = sync_service.bulk_index_issues(
        issues=issues,
        owner=owner,
        repo=repo,
        skip_duplicates=skip_duplicates
    )
    
    # Get final stats
    stats = sync_service.get_issues_stats(owner=owner, repo=repo)
    
    sync_service.close()
    
    print(f"\n{'='*60}")
    print(f"Sync Complete!")
    print(f"{'='*60}")
    print(f"✓ Issues indexed: {result['success']}/{len(issues)}")
    print(f"✓ Duplicates skipped: {result.get('skipped', 0)}")
    print(f"✓ Embeddings generated: {result.get('embeddings_generated', 0)}")
    print(f"✓ Index: {result['index']}")
    print(f"✓ Batch ID: {result['batch_id']}")
    if 'by_state' in stats:
        print(f"✓ By state: {stats['by_state']}")
    print(f"{'='*60}\n")
    
    return {
        'success': result['failed'] == 0,
        'issues_fetched': len(issues),
        'issues_indexed': result['success'],
        'issues_skipped': result.get('skipped', 0),
        'embeddings_generated': result.get('embeddings_generated', 0),
        'issues_failed': result['failed'],
        'batch_id': result['batch_id'],
        'index': result['index'],
        'stats': stats
    }
