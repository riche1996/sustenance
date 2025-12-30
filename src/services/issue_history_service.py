"""Issue History Service - Embeds and stores issues in OpenSearch for historical context."""
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import hashlib

logger = logging.getLogger(__name__)


class IssueHistoryService:
    """Service for managing issue history with embeddings in OpenSearch.
    
    Supports repository-level indexing for issues from multiple trackers:
    - GitHub: owner/repo
    - Jira: project_key
    - TFS: project/repo
    """
    
    INDEX_NAME = "issue_history"
    
    def __init__(self, opensearch_client=None, embedding_service=None):
        """
        Initialize the issue history service.
        
        Args:
            opensearch_client: OpenSearch client instance
            embedding_service: Embedding service instance
        """
        self.opensearch = opensearch_client
        self.embedding = embedding_service
        self._index_created = False
        
        if self.opensearch:
            self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Create the issue history index if it doesn't exist."""
        if self._index_created:
            return
            
        try:
            if not self.opensearch.client.indices.exists(index=self.INDEX_NAME):
                index_body = {
                    'settings': {
                        'index': {
                            'number_of_shards': 1,
                            'number_of_replicas': 0,
                            'knn': True
                        }
                    },
                    'mappings': {
                        'properties': {
                            # Issue identifiers
                            'issue_id': {'type': 'keyword'},
                            'issue_hash': {'type': 'keyword'},  # For deduplication
                            'tracker': {'type': 'keyword'},  # github, jira, tfs
                            
                            # Repository-level identifiers
                            'repo_owner': {'type': 'keyword'},
                            'repo_name': {'type': 'keyword'},
                            'repo_full_name': {'type': 'keyword'},  # owner/repo or project_key
                            'project_key': {'type': 'keyword'},  # For Jira/TFS projects
                            
                            # Issue content
                            'title': {'type': 'text', 'analyzer': 'standard'},
                            'body': {'type': 'text', 'analyzer': 'standard'},
                            'state': {'type': 'keyword'},
                            'labels': {'type': 'keyword'},
                            'issue_type': {'type': 'keyword'},  # Bug, Story, Task, etc.
                            'priority': {'type': 'keyword'},
                            
                            # Metadata
                            'created_at': {'type': 'date'},
                            'updated_at': {'type': 'date'},
                            'closed_at': {'type': 'date'},
                            'created_by': {'type': 'keyword'},
                            'assignee': {'type': 'keyword'},
                            'assignees': {'type': 'keyword'},
                            'milestone': {'type': 'keyword'},
                            'html_url': {'type': 'keyword'},
                            'comments_count': {'type': 'integer'},
                            
                            # Indexing metadata
                            'indexed_at': {'type': 'date'},
                            'last_synced': {'type': 'date'},
                            
                            # Embedding for semantic search
                            'embedding': {
                                'type': 'knn_vector',
                                'dimension': 384  # all-MiniLM-L6-v2 dimension
                            },
                            
                            # Combined text for search
                            'combined_text': {'type': 'text', 'analyzer': 'standard'}
                        }
                    }
                }
                
                self.opensearch.client.indices.create(index=self.INDEX_NAME, body=index_body)
                logger.info(f"✓ Created OpenSearch index: {self.INDEX_NAME}")
            else:
                logger.info(f"✓ OpenSearch index exists: {self.INDEX_NAME}")
            
            self._index_created = True
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise
    
    def _generate_issue_hash(self, issue: Dict[str, Any], tracker: str, repo_full_name: str = None) -> str:
        """Generate a unique hash for an issue to prevent duplicates."""
        repo_id = repo_full_name or ''
        hash_content = f"{tracker}:{repo_id}:{issue.get('id')}:{issue.get('updated_at', '')}"
        return hashlib.md5(hash_content.encode()).hexdigest()
    
    def _prepare_issue_document(self, issue: Dict[str, Any], tracker: str, 
                                 repo_owner: str = None, repo_name: str = None,
                                 project_key: str = None) -> Dict[str, Any]:
        """Prepare an issue document for indexing with full repository context."""
        # Combine title and body for embedding
        title = issue.get('title', '') or issue.get('summary', '')
        body = issue.get('body') or issue.get('description', '') or ''
        labels = issue.get('labels', [])
        
        # Create combined text for embedding
        labels_text = ' '.join(labels) if labels else ''
        combined_text = f"{title} {title} {body} {labels_text}"  # Title weighted 2x
        
        # Generate embedding
        embedding = None
        if self.embedding and combined_text.strip():
            try:
                embedding = self.embedding.embed_text(combined_text[:8000])  # Limit text length
            except Exception as e:
                logger.warning(f"Failed to generate embedding for issue {issue.get('id')}: {e}")
        
        # Parse dates
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).isoformat()
            except:
                return date_str
        
        # Build repo_full_name based on tracker
        if tracker == 'github':
            repo_full_name = f"{repo_owner}/{repo_name}" if repo_owner and repo_name else repo_name
        elif tracker == 'jira':
            repo_full_name = project_key or repo_name
        elif tracker == 'tfs':
            repo_full_name = f"{project_key}/{repo_name}" if project_key and repo_name else (project_key or repo_name)
        else:
            repo_full_name = repo_name
        
        # Generate unique hash with repo context
        issue_hash = self._generate_issue_hash(issue, tracker, repo_full_name)
        
        doc = {
            'issue_id': str(issue.get('id') or issue.get('number', '')),
            'issue_hash': issue_hash,
            'tracker': tracker,
            'repo_owner': repo_owner,
            'repo_name': repo_name,
            'repo_full_name': repo_full_name,
            'project_key': project_key,
            'title': title,
            'body': body[:50000] if body else None,  # Limit body size
            'state': issue.get('state') or issue.get('status', 'unknown'),
            'labels': labels,
            'issue_type': issue.get('issue_type') or issue.get('type', 'issue'),
            'priority': issue.get('priority'),
            'created_at': parse_date(issue.get('created_at') or issue.get('created')),
            'updated_at': parse_date(issue.get('updated_at') or issue.get('updated')),
            'closed_at': parse_date(issue.get('closed_at')),
            'created_by': issue.get('created_by') or issue.get('reporter'),
            'assignee': issue.get('assignee'),
            'assignees': issue.get('assignees', []),
            'milestone': issue.get('milestone'),
            'html_url': issue.get('html_url') or issue.get('url'),
            'comments_count': issue.get('comments', 0),
            'indexed_at': datetime.utcnow().isoformat(),
            'last_synced': datetime.utcnow().isoformat(),
            'combined_text': combined_text[:10000],  # Limit for search
        }
        
        if embedding:
            doc['embedding'] = embedding
        
        return doc
    
    def store_issues(self, issues: List[Dict[str, Any]], tracker: str,
                     repo_owner: str = None, repo_name: str = None,
                     project_key: str = None, batch_size: int = 50) -> Dict[str, Any]:
        """
        Store multiple issues with embeddings in OpenSearch.
        
        Supports repository-level indexing:
        - GitHub: repo_owner/repo_name
        - Jira: project_key
        - TFS: project_key/repo_name
        
        Args:
            issues: List of issue dictionaries
            tracker: Tracker type (github, jira, tfs)
            repo_owner: Repository owner (for GitHub)
            repo_name: Repository name
            project_key: Project key (for Jira/TFS)
            batch_size: Number of issues to process per batch
            
        Returns:
            Summary of indexing operation
        """
        if not self.opensearch:
            return {"success": False, "error": "OpenSearch client not initialized"}
        
        self._ensure_index_exists()
        
        total_issues = len(issues)
        indexed = 0
        skipped = 0
        errors = 0
        
        # Build repo identifier for logging
        if tracker == 'github':
            repo_id = f"{repo_owner}/{repo_name}" if repo_owner else repo_name
        elif tracker == 'jira':
            repo_id = project_key or repo_name
        else:
            repo_id = f"{project_key}/{repo_name}" if project_key else repo_name
        
        logger.info(f"Starting to index {total_issues} issues from {tracker} ({repo_id})")
        
        # Process in batches
        for i in range(0, total_issues, batch_size):
            batch = issues[i:i + batch_size]
            documents = []
            
            for issue in batch:
                try:
                    doc = self._prepare_issue_document(
                        issue, tracker, repo_owner, repo_name, project_key
                    )
                    
                    # Check if issue already exists with same hash (skip if unchanged)
                    existing = self._check_existing_issue(doc['issue_hash'])
                    if existing:
                        skipped += 1
                        continue
                    
                    documents.append(doc)
                except Exception as e:
                    logger.error(f"Error preparing issue {issue.get('id')}: {e}")
                    errors += 1
            
            # Bulk index the batch
            if documents:
                try:
                    actions = [
                        {
                            '_index': self.INDEX_NAME,
                            '_id': doc['issue_hash'],  # Use hash as ID for upsert
                            '_source': doc
                        }
                        for doc in documents
                    ]
                    
                    from opensearchpy.helpers import bulk
                    success, failed = bulk(self.opensearch.client, actions, refresh=False)
                    indexed += success
                    errors += len(failed) if isinstance(failed, list) else 0
                except Exception as e:
                    logger.error(f"Error bulk indexing batch: {e}")
                    errors += len(documents)
            
            # Progress logging
            progress = min(i + batch_size, total_issues)
            logger.info(f"  Progress: {progress}/{total_issues} issues processed")
        
        # Refresh index
        try:
            self.opensearch.client.indices.refresh(index=self.INDEX_NAME)
        except:
            pass
        
        result = {
            "success": True,
            "total": total_issues,
            "indexed": indexed,
            "skipped": skipped,
            "errors": errors,
            "tracker": tracker,
            "repo": repo_id
        }
        
        logger.info(f"✓ Indexing complete for {repo_id}: {indexed} indexed, {skipped} skipped, {errors} errors")
        return result
    
    def _check_existing_issue(self, issue_hash: str) -> bool:
        """Check if an issue with the same hash already exists."""
        try:
            response = self.opensearch.client.exists(
                index=self.INDEX_NAME,
                id=issue_hash
            )
            return response
        except:
            return False
    
    def search_similar_issues(self, query: str, tracker: str = None,
                              state: str = None, repo_full_name: str = None,
                              limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar issues using semantic search.
        
        Args:
            query: Search query text
            tracker: Filter by tracker (optional)
            state: Filter by state (optional)
            repo_full_name: Filter by repository (optional, e.g., "owner/repo")
            limit: Maximum results
            
        Returns:
            List of similar issues with scores
        """
        if not self.opensearch or not self.embedding:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding.embed_text(query)
            
            # Build search query
            search_body = {
                'size': limit,
                'query': {
                    'bool': {
                        'must': [
                            {
                                'knn': {
                                    'embedding': {
                                        'vector': query_embedding,
                                        'k': limit * 2  # Get more candidates for filtering
                                    }
                                }
                            }
                        ],
                        'filter': []
                    }
                }
            }
            
            # Add filters
            if tracker:
                search_body['query']['bool']['filter'].append(
                    {'term': {'tracker': tracker}}
                )
            if state:
                search_body['query']['bool']['filter'].append(
                    {'term': {'state': state}}
                )
            if repo_full_name:
                search_body['query']['bool']['filter'].append(
                    {'term': {'repo_full_name': repo_full_name}}
                )
            
            response = self.opensearch.client.search(index=self.INDEX_NAME, body=search_body)
            
            results = []
            for hit in response['hits']['hits']:
                issue = hit['_source']
                issue['similarity_score'] = hit['_score']
                # Remove embedding from response to reduce payload
                issue.pop('embedding', None)
                issue.pop('combined_text', None)
                results.append(issue)
            
            return results
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def get_historical_context(self, bug_title: str, bug_description: str = "",
                                tracker: str = None, repo_full_name: str = None,
                                limit: int = 5) -> Dict[str, Any]:
        """
        Get historical context for a bug by finding similar past issues.
        
        Args:
            bug_title: Bug title
            bug_description: Bug description
            tracker: Filter by tracker (optional)
            repo_full_name: Filter by repository (optional, e.g., "owner/repo")
            limit: Maximum similar issues to return
            
        Returns:
            Historical context including similar issues and patterns
        """
        query = f"{bug_title} {bug_description}"
        similar_issues = self.search_similar_issues(
            query, tracker=tracker, repo_full_name=repo_full_name, limit=limit
        )
        
        if not similar_issues:
            return {
                "has_context": False,
                "message": "No similar historical issues found",
                "similar_issues": []
            }
        
        # Analyze patterns in similar issues
        patterns = {
            "common_labels": {},
            "resolution_states": {},
            "common_assignees": {}
        }
        
        for issue in similar_issues:
            # Count labels
            for label in issue.get('labels', []):
                patterns["common_labels"][label] = patterns["common_labels"].get(label, 0) + 1
            
            # Count states
            state = issue.get('state', 'unknown')
            patterns["resolution_states"][state] = patterns["resolution_states"].get(state, 0) + 1
            
            # Count assignees
            assignee = issue.get('assignee')
            if assignee:
                patterns["common_assignees"][assignee] = patterns["common_assignees"].get(assignee, 0) + 1
        
        # Sort patterns by frequency
        patterns["common_labels"] = dict(sorted(
            patterns["common_labels"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5])
        
        return {
            "has_context": True,
            "similar_issues_count": len(similar_issues),
            "similar_issues": similar_issues,
            "patterns": patterns,
            "message": f"Found {len(similar_issues)} similar historical issues"
        }
    
    def get_issue_stats(self, tracker: str = None) -> Dict[str, Any]:
        """
        Get statistics about stored issues.
        
        Args:
            tracker: Filter by tracker (optional)
            
        Returns:
            Statistics dictionary
        """
        if not self.opensearch:
            return {"error": "OpenSearch not initialized"}
        
        try:
            # Count total issues
            count_body = {'query': {'match_all': {}}}
            if tracker:
                count_body = {'query': {'term': {'tracker': tracker}}}
            
            count_response = self.opensearch.client.count(index=self.INDEX_NAME, body=count_body)
            total_count = count_response['count']
            
            # Get aggregations
            agg_body = {
                'size': 0,
                'aggs': {
                    'by_tracker': {'terms': {'field': 'tracker'}},
                    'by_state': {'terms': {'field': 'state'}},
                    'by_repo': {'terms': {'field': 'repo_name'}},
                    'date_range': {
                        'stats': {'field': 'created_at'}
                    }
                }
            }
            
            if tracker:
                agg_body['query'] = {'term': {'tracker': tracker}}
            
            agg_response = self.opensearch.client.search(index=self.INDEX_NAME, body=agg_body)
            
            return {
                "total_issues": total_count,
                "by_tracker": {
                    bucket['key']: bucket['doc_count'] 
                    for bucket in agg_response['aggregations']['by_tracker']['buckets']
                },
                "by_state": {
                    bucket['key']: bucket['doc_count'] 
                    for bucket in agg_response['aggregations']['by_state']['buckets']
                },
                "by_repo": {
                    bucket['key']: bucket['doc_count'] 
                    for bucket in agg_response['aggregations']['by_repo']['buckets']
                }
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
    
    def clear_tracker_issues(self, tracker: str) -> Dict[str, Any]:
        """
        Clear all issues for a specific tracker.
        
        Args:
            tracker: Tracker to clear (github, jira, tfs)
            
        Returns:
            Result of deletion
        """
        if not self.opensearch:
            return {"success": False, "error": "OpenSearch not initialized"}
        
        try:
            delete_body = {
                'query': {
                    'term': {'tracker': tracker}
                }
            }
            
            response = self.opensearch.client.delete_by_query(
                index=self.INDEX_NAME,
                body=delete_body
            )
            
            return {
                "success": True,
                "deleted": response['deleted'],
                "tracker": tracker
            }
        except Exception as e:
            logger.error(f"Error clearing issues: {e}")
            return {"success": False, "error": str(e)}

    # ==================== REPO-LEVEL OPERATIONS ====================
    
    def get_indexed_repos(self) -> Dict[str, Any]:
        """
        Get list of all indexed repositories with statistics.
        
        Returns:
            Dictionary with repo list and stats per repo
        """
        if not self.opensearch:
            return {"success": False, "error": "OpenSearch not initialized"}
        
        try:
            agg_body = {
                'size': 0,
                'aggs': {
                    'repos': {
                        'composite': {
                            'size': 100,
                            'sources': [
                                {'tracker': {'terms': {'field': 'tracker'}}},
                                {'repo_full_name': {'terms': {'field': 'repo_full_name'}}}
                            ]
                        },
                        'aggs': {
                            'issue_count': {'value_count': {'field': 'issue_id'}},
                            'states': {'terms': {'field': 'state'}},
                            'latest_sync': {'max': {'field': 'last_synced'}},
                            'oldest_issue': {'min': {'field': 'created_at'}},
                            'newest_issue': {'max': {'field': 'created_at'}}
                        }
                    }
                }
            }
            
            response = self.opensearch.client.search(index=self.INDEX_NAME, body=agg_body)
            
            repos = []
            for bucket in response['aggregations']['repos']['buckets']:
                repo_info = {
                    'tracker': bucket['key']['tracker'],
                    'repo_full_name': bucket['key']['repo_full_name'],
                    'issue_count': bucket['issue_count']['value'],
                    'states': {b['key']: b['doc_count'] for b in bucket['states']['buckets']},
                    'last_synced': bucket['latest_sync']['value_as_string'] if bucket['latest_sync']['value'] else None,
                    'oldest_issue': bucket['oldest_issue']['value_as_string'] if bucket['oldest_issue']['value'] else None,
                    'newest_issue': bucket['newest_issue']['value_as_string'] if bucket['newest_issue']['value'] else None
                }
                repos.append(repo_info)
            
            return {
                "success": True,
                "total_repos": len(repos),
                "repos": repos
            }
        except Exception as e:
            logger.error(f"Error getting indexed repos: {e}")
            return {"success": False, "error": str(e)}
    
    def get_repo_issues(self, repo_full_name: str = None, tracker: str = None,
                        repo_owner: str = None, repo_name: str = None,
                        state: str = None, limit: int = 100) -> Dict[str, Any]:
        """
        Get all issues for a specific repository.
        
        Args:
            repo_full_name: Full repo name (e.g., "owner/repo" or "PROJECT_KEY")
            tracker: Tracker type filter
            repo_owner: Repository owner (alternative to repo_full_name)
            repo_name: Repository name (alternative to repo_full_name)
            state: Filter by state (open, closed, etc.)
            limit: Maximum number of issues to return
            
        Returns:
            Dictionary with issues list
        """
        if not self.opensearch:
            return {"success": False, "error": "OpenSearch not initialized"}
        
        try:
            # Build filter
            filters = []
            
            if repo_full_name:
                filters.append({'term': {'repo_full_name': repo_full_name}})
            else:
                if repo_owner:
                    filters.append({'term': {'repo_owner': repo_owner}})
                if repo_name:
                    filters.append({'term': {'repo_name': repo_name}})
            
            if tracker:
                filters.append({'term': {'tracker': tracker}})
            if state:
                filters.append({'term': {'state': state}})
            
            search_body = {
                'size': limit,
                'query': {
                    'bool': {
                        'filter': filters
                    }
                },
                'sort': [{'created_at': {'order': 'desc'}}],
                '_source': {
                    'excludes': ['embedding', 'combined_text']
                }
            }
            
            response = self.opensearch.client.search(index=self.INDEX_NAME, body=search_body)
            
            issues = [hit['_source'] for hit in response['hits']['hits']]
            
            return {
                "success": True,
                "total": response['hits']['total']['value'],
                "returned": len(issues),
                "issues": issues
            }
        except Exception as e:
            logger.error(f"Error getting repo issues: {e}")
            return {"success": False, "error": str(e)}
    
    def get_repo_stats(self, repo_full_name: str = None, tracker: str = None) -> Dict[str, Any]:
        """
        Get detailed statistics for a specific repository.
        
        Args:
            repo_full_name: Full repo name (e.g., "owner/repo" or "PROJECT_KEY")
            tracker: Tracker type filter
            
        Returns:
            Dictionary with detailed stats
        """
        if not self.opensearch:
            return {"success": False, "error": "OpenSearch not initialized"}
        
        try:
            filters = []
            if repo_full_name:
                filters.append({'term': {'repo_full_name': repo_full_name}})
            if tracker:
                filters.append({'term': {'tracker': tracker}})
            
            agg_body = {
                'size': 0,
                'query': {'bool': {'filter': filters}} if filters else {'match_all': {}},
                'aggs': {
                    'total_issues': {'value_count': {'field': 'issue_id'}},
                    'by_state': {'terms': {'field': 'state', 'size': 20}},
                    'by_type': {'terms': {'field': 'issue_type', 'size': 20}},
                    'by_priority': {'terms': {'field': 'priority', 'size': 10}},
                    'by_label': {'terms': {'field': 'labels', 'size': 30}},
                    'by_assignee': {'terms': {'field': 'assignee', 'size': 20}},
                    'date_stats': {'stats': {'field': 'created_at'}},
                    'monthly_created': {
                        'date_histogram': {
                            'field': 'created_at',
                            'calendar_interval': 'month',
                            'min_doc_count': 1
                        }
                    }
                }
            }
            
            response = self.opensearch.client.search(index=self.INDEX_NAME, body=agg_body)
            aggs = response['aggregations']
            
            return {
                "success": True,
                "repo": repo_full_name,
                "tracker": tracker,
                "total_issues": aggs['total_issues']['value'],
                "by_state": {b['key']: b['doc_count'] for b in aggs['by_state']['buckets']},
                "by_type": {b['key']: b['doc_count'] for b in aggs['by_type']['buckets']},
                "by_priority": {b['key']: b['doc_count'] for b in aggs['by_priority']['buckets']},
                "top_labels": {b['key']: b['doc_count'] for b in aggs['by_label']['buckets'][:10]},
                "top_assignees": {b['key']: b['doc_count'] for b in aggs['by_assignee']['buckets'][:10]},
                "date_range": {
                    "oldest": aggs['date_stats']['min_as_string'] if aggs['date_stats']['min'] else None,
                    "newest": aggs['date_stats']['max_as_string'] if aggs['date_stats']['max'] else None
                },
                "monthly_trend": [
                    {'month': b['key_as_string'], 'count': b['doc_count']}
                    for b in aggs['monthly_created']['buckets'][-12:]  # Last 12 months
                ]
            }
        except Exception as e:
            logger.error(f"Error getting repo stats: {e}")
            return {"success": False, "error": str(e)}
    
    def clear_repo_issues(self, repo_full_name: str = None, tracker: str = None,
                          repo_owner: str = None, repo_name: str = None) -> Dict[str, Any]:
        """
        Clear all issues for a specific repository.
        
        Args:
            repo_full_name: Full repo name to clear
            tracker: Tracker type filter
            repo_owner: Repository owner (alternative)
            repo_name: Repository name (alternative)
            
        Returns:
            Result of deletion
        """
        if not self.opensearch:
            return {"success": False, "error": "OpenSearch not initialized"}
        
        try:
            filters = []
            
            if repo_full_name:
                filters.append({'term': {'repo_full_name': repo_full_name}})
            else:
                if repo_owner:
                    filters.append({'term': {'repo_owner': repo_owner}})
                if repo_name:
                    filters.append({'term': {'repo_name': repo_name}})
            
            if tracker:
                filters.append({'term': {'tracker': tracker}})
            
            if not filters:
                return {"success": False, "error": "Must specify repo_full_name, tracker, or repo_owner/repo_name"}
            
            delete_body = {
                'query': {
                    'bool': {
                        'filter': filters
                    }
                }
            }
            
            response = self.opensearch.client.delete_by_query(
                index=self.INDEX_NAME,
                body=delete_body
            )
            
            repo_id = repo_full_name or f"{repo_owner}/{repo_name}" if repo_owner else repo_name
            
            return {
                "success": True,
                "deleted": response['deleted'],
                "repo": repo_id,
                "tracker": tracker
            }
        except Exception as e:
            logger.error(f"Error clearing repo issues: {e}")
            return {"success": False, "error": str(e)}
    
    def search_repo_issues(self, query: str, repo_full_name: str = None,
                           tracker: str = None, use_semantic: bool = True,
                           limit: int = 20) -> Dict[str, Any]:
        """
        Search issues within a specific repository using text or semantic search.
        
        Args:
            query: Search query
            repo_full_name: Limit search to specific repo
            tracker: Limit search to specific tracker
            use_semantic: Use semantic (embedding) search if True, text search if False
            limit: Maximum results
            
        Returns:
            Dictionary with search results
        """
        if not self.opensearch:
            return {"success": False, "error": "OpenSearch not initialized"}
        
        try:
            filters = []
            if repo_full_name:
                filters.append({'term': {'repo_full_name': repo_full_name}})
            if tracker:
                filters.append({'term': {'tracker': tracker}})
            
            if use_semantic and self.embedding:
                # Semantic search using embeddings
                query_embedding = self.embedding.embed_text(query)
                
                search_body = {
                    'size': limit,
                    'query': {
                        'bool': {
                            'must': [
                                {
                                    'knn': {
                                        'embedding': {
                                            'vector': query_embedding,
                                            'k': limit * 2
                                        }
                                    }
                                }
                            ],
                            'filter': filters
                        }
                    },
                    '_source': {
                        'excludes': ['embedding', 'combined_text']
                    }
                }
            else:
                # Text search
                search_body = {
                    'size': limit,
                    'query': {
                        'bool': {
                            'must': [
                                {
                                    'multi_match': {
                                        'query': query,
                                        'fields': ['title^3', 'body', 'labels^2'],
                                        'type': 'best_fields'
                                    }
                                }
                            ],
                            'filter': filters
                        }
                    },
                    '_source': {
                        'excludes': ['embedding', 'combined_text']
                    }
                }
            
            response = self.opensearch.client.search(index=self.INDEX_NAME, body=search_body)
            
            results = []
            for hit in response['hits']['hits']:
                issue = hit['_source']
                issue['search_score'] = hit['_score']
                results.append(issue)
            
            return {
                "success": True,
                "query": query,
                "repo": repo_full_name,
                "search_type": "semantic" if use_semantic else "text",
                "total": len(results),
                "results": results
            }
        except Exception as e:
            logger.error(f"Error searching repo issues: {e}")
            return {"success": False, "error": str(e)}

