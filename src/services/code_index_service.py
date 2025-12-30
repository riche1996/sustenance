"""Code Index Service - Indexes code chunks with embeddings in OpenSearch.

Provides:
- Incremental indexing (only changed files)
- Code-aware embeddings
- Symbol search
- Semantic code search
"""
import os
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import json

from .code_chunker import CodeChunker, CodeChunk, ChunkType

logger = logging.getLogger(__name__)


class CodeIndexService:
    """Service for indexing code in OpenSearch with embeddings."""
    
    INDEX_NAME = "code_index"
    FILE_HASH_INDEX = "code_file_hashes"
    
    def __init__(self, opensearch_client=None, embedding_service=None):
        """
        Initialize the code index service.
        
        Args:
            opensearch_client: OpenSearch client instance
            embedding_service: Embedding service for generating vectors
        """
        self.opensearch = opensearch_client
        self.embedding = embedding_service
        self.chunker = CodeChunker()
        self._index_created = False
        
        if self.opensearch:
            self._ensure_indices_exist()
    
    def _ensure_indices_exist(self):
        """Create indices if they don't exist."""
        if self._index_created:
            return
        
        try:
            # Main code index
            if not self.opensearch.client.indices.exists(index=self.INDEX_NAME):
                index_body = {
                    'settings': {
                        'index': {
                            'number_of_shards': 2,
                            'number_of_replicas': 0,
                            'knn': True
                        }
                    },
                    'mappings': {
                        'properties': {
                            # Identifiers
                            'chunk_id': {'type': 'keyword'},
                            'file_path': {'type': 'keyword'},
                            'relative_path': {'type': 'keyword'},
                            'repo_name': {'type': 'keyword'},
                            'repo_owner': {'type': 'keyword'},
                            'repo_full_name': {'type': 'keyword'},
                            
                            # Code structure
                            'chunk_type': {'type': 'keyword'},  # class, function, method, block
                            'name': {'type': 'keyword'},  # Function/class name
                            'parent_name': {'type': 'keyword'},  # Class name for methods
                            'language': {'type': 'keyword'},
                            'signature': {'type': 'text'},
                            
                            # Content
                            'content': {'type': 'text', 'analyzer': 'standard'},
                            'docstring': {'type': 'text', 'analyzer': 'standard'},
                            
                            # Location
                            'start_line': {'type': 'integer'},
                            'end_line': {'type': 'integer'},
                            'line_count': {'type': 'integer'},
                            
                            # References
                            'imports': {'type': 'keyword'},
                            'calls': {'type': 'keyword'},  # Functions called
                            
                            # Metadata
                            'indexed_at': {'type': 'date'},
                            'file_hash': {'type': 'keyword'},
                            
                            # Embedding for semantic search
                            'embedding': {
                                'type': 'knn_vector',
                                'dimension': 384  # all-MiniLM-L6-v2
                            },
                            
                            # Combined text for search
                            'searchable_text': {'type': 'text', 'analyzer': 'standard'}
                        }
                    }
                }
                
                self.opensearch.client.indices.create(index=self.INDEX_NAME, body=index_body)
                logger.info(f"✓ Created code index: {self.INDEX_NAME}")
            
            # File hash index for incremental updates
            if not self.opensearch.client.indices.exists(index=self.FILE_HASH_INDEX):
                hash_index_body = {
                    'mappings': {
                        'properties': {
                            'file_path': {'type': 'keyword'},
                            'repo_full_name': {'type': 'keyword'},
                            'file_hash': {'type': 'keyword'},
                            'last_indexed': {'type': 'date'},
                            'chunk_count': {'type': 'integer'}
                        }
                    }
                }
                self.opensearch.client.indices.create(index=self.FILE_HASH_INDEX, body=hash_index_body)
                logger.info(f"✓ Created file hash index: {self.FILE_HASH_INDEX}")
            
            self._index_created = True
            
        except Exception as e:
            logger.error(f"Error creating indices: {e}")
            raise
    
    def _compute_file_hash(self, content: str) -> str:
        """Compute hash of file content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_stored_hash(self, file_path: str, repo_full_name: str) -> Optional[str]:
        """Get stored hash for a file."""
        try:
            doc_id = hashlib.md5(f"{repo_full_name}:{file_path}".encode()).hexdigest()
            result = self.opensearch.client.get(
                index=self.FILE_HASH_INDEX,
                id=doc_id,
                ignore=[404]
            )
            if result and result.get('found'):
                return result['_source'].get('file_hash')
        except:
            pass
        return None
    
    def _store_file_hash(self, file_path: str, repo_full_name: str, 
                         file_hash: str, chunk_count: int):
        """Store file hash for incremental updates."""
        try:
            doc_id = hashlib.md5(f"{repo_full_name}:{file_path}".encode()).hexdigest()
            self.opensearch.client.index(
                index=self.FILE_HASH_INDEX,
                id=doc_id,
                body={
                    'file_path': file_path,
                    'repo_full_name': repo_full_name,
                    'file_hash': file_hash,
                    'last_indexed': datetime.utcnow().isoformat(),
                    'chunk_count': chunk_count
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store file hash: {e}")
    
    def _prepare_chunk_document(self, chunk: CodeChunk, repo_owner: str = None,
                                 repo_name: str = None, file_hash: str = None) -> Dict[str, Any]:
        """Prepare a chunk document for indexing."""
        # Build repo_full_name
        repo_full_name = f"{repo_owner}/{repo_name}" if repo_owner and repo_name else repo_name
        
        # Create searchable text for embedding
        searchable_parts = [chunk.name]
        if chunk.signature:
            searchable_parts.append(chunk.signature)
        if chunk.docstring:
            searchable_parts.append(chunk.docstring)
        searchable_parts.append(chunk.content[:2000])  # First 2000 chars of content
        
        searchable_text = ' '.join(searchable_parts)
        
        # Generate embedding
        embedding = None
        if self.embedding and searchable_text.strip():
            try:
                embedding = self.embedding.embed_text(searchable_text[:8000])
            except Exception as e:
                logger.warning(f"Failed to generate embedding for {chunk.name}: {e}")
        
        doc = {
            'chunk_id': chunk.chunk_id,
            'file_path': chunk.file_path,
            'relative_path': chunk.relative_path,
            'repo_name': repo_name,
            'repo_owner': repo_owner,
            'repo_full_name': repo_full_name,
            'chunk_type': chunk.chunk_type.value,
            'name': chunk.name,
            'parent_name': chunk.parent_name,
            'language': chunk.language,
            'signature': chunk.signature,
            'content': chunk.content,
            'docstring': chunk.docstring,
            'start_line': chunk.start_line,
            'end_line': chunk.end_line,
            'line_count': chunk.end_line - chunk.start_line + 1,
            'imports': chunk.imports,
            'calls': chunk.calls,
            'indexed_at': datetime.utcnow().isoformat(),
            'file_hash': file_hash,
            'searchable_text': searchable_text
        }
        
        if embedding:
            doc['embedding'] = embedding
        
        return doc
    
    def index_file(self, file_path: str, content: str,
                   repo_owner: str = None, repo_name: str = None,
                   repo_root: str = None, force: bool = False) -> Dict[str, Any]:
        """
        Index a single file.
        
        Args:
            file_path: Path to the file
            content: File content
            repo_owner: Repository owner
            repo_name: Repository name
            repo_root: Repository root path
            force: Force re-indexing even if unchanged
            
        Returns:
            Indexing result
        """
        if not self.opensearch:
            return {"success": False, "error": "OpenSearch not initialized"}
        
        self._ensure_indices_exist()
        
        repo_full_name = f"{repo_owner}/{repo_name}" if repo_owner and repo_name else repo_name
        file_hash = self._compute_file_hash(content)
        
        # Check if file has changed
        if not force:
            stored_hash = self._get_stored_hash(file_path, repo_full_name)
            if stored_hash == file_hash:
                return {
                    "success": True,
                    "status": "unchanged",
                    "message": "File unchanged, skipping"
                }
        
        # Delete existing chunks for this file
        try:
            self.opensearch.client.delete_by_query(
                index=self.INDEX_NAME,
                body={
                    'query': {
                        'bool': {
                            'must': [
                                {'term': {'file_path': file_path}},
                                {'term': {'repo_full_name': repo_full_name}}
                            ]
                        }
                    }
                },
                ignore=[404]
            )
        except:
            pass
        
        # Chunk the file
        chunks = self.chunker.chunk_file(file_path, content, repo_root)
        
        if not chunks:
            return {
                "success": True,
                "status": "no_chunks",
                "message": "No chunks generated from file"
            }
        
        # Index chunks
        indexed = 0
        errors = 0
        
        for chunk in chunks:
            try:
                doc = self._prepare_chunk_document(chunk, repo_owner, repo_name, file_hash)
                self.opensearch.client.index(
                    index=self.INDEX_NAME,
                    id=chunk.chunk_id,
                    body=doc
                )
                indexed += 1
            except Exception as e:
                logger.error(f"Error indexing chunk {chunk.chunk_id}: {e}")
                errors += 1
        
        # Store file hash
        self._store_file_hash(file_path, repo_full_name, file_hash, len(chunks))
        
        return {
            "success": True,
            "status": "indexed",
            "chunks_indexed": indexed,
            "errors": errors,
            "file_path": file_path
        }
    
    def index_repository(self, repo_path: str, repo_owner: str = None,
                         repo_name: str = None, extensions: List[str] = None,
                         exclude_patterns: List[str] = None,
                         incremental: bool = True,
                         batch_size: int = 50) -> Dict[str, Any]:
        """
        Index an entire repository.
        
        Args:
            repo_path: Path to repository root
            repo_owner: Repository owner
            repo_name: Repository name (defaults to folder name)
            extensions: File extensions to include
            exclude_patterns: Patterns to exclude
            incremental: Only index changed files
            batch_size: Batch size for bulk indexing
            
        Returns:
            Indexing results summary
        """
        if not self.opensearch:
            return {"success": False, "error": "OpenSearch not initialized"}
        
        self._ensure_indices_exist()
        
        repo_path = Path(repo_path)
        if not repo_path.exists():
            return {"success": False, "error": f"Repository path not found: {repo_path}"}
        
        if repo_name is None:
            repo_name = repo_path.name
        
        repo_full_name = f"{repo_owner}/{repo_name}" if repo_owner else repo_name
        
        logger.info(f"Starting repository indexing: {repo_full_name}")
        logger.info(f"  Path: {repo_path}")
        logger.info(f"  Incremental: {incremental}")
        
        # Default exclusions
        if exclude_patterns is None:
            exclude_patterns = [
                'node_modules', '.git', '__pycache__', '.venv', 'venv',
                'dist', 'build', '.idea', '.vscode', 'target', 'bin', 'obj',
                '.next', '.nuxt', 'coverage', '.pytest_cache', '.mypy_cache',
                'vendor', 'packages', '.tox', 'eggs', '*.egg-info'
            ]
        
        # Default extensions
        if extensions is None:
            extensions = list(self.chunker.LANGUAGE_MAP.keys())
        
        # Collect files
        files_to_process = []
        files_skipped = 0
        files_unchanged = 0
        
        for ext in extensions:
            for file_path in repo_path.rglob(f'*{ext}'):
                # Check exclusions
                if any(excl in str(file_path) for excl in exclude_patterns):
                    files_skipped += 1
                    continue
                
                # Check file size (skip files > 1MB)
                try:
                    if file_path.stat().st_size > 1_000_000:
                        files_skipped += 1
                        continue
                except:
                    continue
                
                files_to_process.append(file_path)
        
        logger.info(f"  Found {len(files_to_process)} files to process, {files_skipped} excluded")
        
        # Process files
        total_chunks = 0
        files_indexed = 0
        errors = 0
        documents = []
        
        for i, file_path in enumerate(files_to_process):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                file_hash = self._compute_file_hash(content)
                relative_path = str(file_path.relative_to(repo_path))
                
                # Check if unchanged (incremental mode)
                if incremental:
                    stored_hash = self._get_stored_hash(str(file_path), repo_full_name)
                    if stored_hash == file_hash:
                        files_unchanged += 1
                        continue
                
                # Chunk the file
                chunks = self.chunker.chunk_file(str(file_path), content, str(repo_path))
                
                for chunk in chunks:
                    doc = self._prepare_chunk_document(chunk, repo_owner, repo_name, file_hash)
                    documents.append({
                        '_index': self.INDEX_NAME,
                        '_id': chunk.chunk_id,
                        '_source': doc
                    })
                
                # Store file hash
                self._store_file_hash(str(file_path), repo_full_name, file_hash, len(chunks))
                files_indexed += 1
                total_chunks += len(chunks)
                
                # Bulk index when batch is full
                if len(documents) >= batch_size:
                    self._bulk_index(documents)
                    documents = []
                
                # Progress logging
                if (i + 1) % 50 == 0:
                    logger.info(f"  Progress: {i + 1}/{len(files_to_process)} files")
                    
            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")
                errors += 1
        
        # Index remaining documents
        if documents:
            self._bulk_index(documents)
        
        # Refresh index
        try:
            self.opensearch.client.indices.refresh(index=self.INDEX_NAME)
        except:
            pass
        
        result = {
            "success": True,
            "repo_full_name": repo_full_name,
            "files_processed": len(files_to_process),
            "files_indexed": files_indexed,
            "files_unchanged": files_unchanged,
            "files_skipped": files_skipped,
            "total_chunks": total_chunks,
            "errors": errors
        }
        
        logger.info(f"✓ Indexing complete: {files_indexed} files, {total_chunks} chunks")
        return result
    
    def _bulk_index(self, documents: List[Dict]):
        """Bulk index documents."""
        try:
            from opensearchpy.helpers import bulk
            success, failed = bulk(self.opensearch.client, documents, refresh=False)
            if failed:
                logger.warning(f"Bulk index had {len(failed)} failures")
        except Exception as e:
            logger.error(f"Bulk index error: {e}")
    
    def search_code(self, query: str, repo_full_name: str = None,
                    language: str = None, chunk_type: str = None,
                    use_semantic: bool = True, limit: int = 20) -> Dict[str, Any]:
        """
        Search for code using text or semantic search.
        
        Args:
            query: Search query
            repo_full_name: Filter by repository
            language: Filter by language
            chunk_type: Filter by chunk type (class, function, method, block)
            use_semantic: Use semantic search if True
            limit: Maximum results
            
        Returns:
            Search results
        """
        if not self.opensearch:
            return {"success": False, "error": "OpenSearch not initialized"}
        
        filters = []
        if repo_full_name:
            filters.append({'term': {'repo_full_name': repo_full_name}})
        if language:
            filters.append({'term': {'language': language}})
        if chunk_type:
            filters.append({'term': {'chunk_type': chunk_type}})
        
        if use_semantic and self.embedding:
            # Semantic search
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
                    'excludes': ['embedding', 'searchable_text']
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
                                    'fields': ['name^3', 'signature^2', 'docstring^2', 'content', 'searchable_text'],
                                    'type': 'best_fields'
                                }
                            }
                        ],
                        'filter': filters
                    }
                },
                '_source': {
                    'excludes': ['embedding', 'searchable_text']
                }
            }
        
        try:
            response = self.opensearch.client.search(index=self.INDEX_NAME, body=search_body)
            
            results = []
            for hit in response['hits']['hits']:
                result = hit['_source']
                result['score'] = hit['_score']
                results.append(result)
            
            return {
                "success": True,
                "query": query,
                "total": len(results),
                "results": results
            }
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"success": False, "error": str(e)}
    
    def search_by_symbol(self, symbol_name: str, repo_full_name: str = None,
                         exact_match: bool = False) -> Dict[str, Any]:
        """
        Search for code by symbol name (function, class, method).
        
        Args:
            symbol_name: Name to search for
            repo_full_name: Filter by repository
            exact_match: Require exact name match
            
        Returns:
            Search results
        """
        if not self.opensearch:
            return {"success": False, "error": "OpenSearch not initialized"}
        
        filters = []
        if repo_full_name:
            filters.append({'term': {'repo_full_name': repo_full_name}})
        
        if exact_match:
            must = [{'term': {'name': symbol_name}}]
        else:
            must = [
                {
                    'bool': {
                        'should': [
                            {'term': {'name': {'value': symbol_name, 'boost': 3}}},
                            {'wildcard': {'name': f'*{symbol_name}*'}},
                            {'match': {'signature': symbol_name}}
                        ]
                    }
                }
            ]
        
        search_body = {
            'size': 50,
            'query': {
                'bool': {
                    'must': must,
                    'filter': filters
                }
            },
            '_source': {
                'excludes': ['embedding', 'searchable_text', 'content']
            }
        }
        
        try:
            response = self.opensearch.client.search(index=self.INDEX_NAME, body=search_body)
            
            results = []
            for hit in response['hits']['hits']:
                result = hit['_source']
                result['score'] = hit['_score']
                results.append(result)
            
            return {
                "success": True,
                "symbol": symbol_name,
                "total": len(results),
                "results": results
            }
        except Exception as e:
            logger.error(f"Symbol search error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_function_calls(self, function_name: str, repo_full_name: str = None) -> Dict[str, Any]:
        """
        Find all places where a function is called.
        
        Args:
            function_name: Function name to search for
            repo_full_name: Filter by repository
            
        Returns:
            List of code chunks that call this function
        """
        if not self.opensearch:
            return {"success": False, "error": "OpenSearch not initialized"}
        
        filters = [{'term': {'calls': function_name}}]
        if repo_full_name:
            filters.append({'term': {'repo_full_name': repo_full_name}})
        
        search_body = {
            'size': 100,
            'query': {
                'bool': {
                    'filter': filters
                }
            },
            '_source': ['relative_path', 'name', 'chunk_type', 'start_line', 'end_line', 'signature']
        }
        
        try:
            response = self.opensearch.client.search(index=self.INDEX_NAME, body=search_body)
            
            callers = []
            for hit in response['hits']['hits']:
                callers.append(hit['_source'])
            
            return {
                "success": True,
                "function": function_name,
                "callers_count": len(callers),
                "callers": callers
            }
        except Exception as e:
            logger.error(f"Call search error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_index_stats(self, repo_full_name: str = None) -> Dict[str, Any]:
        """Get statistics about indexed code."""
        if not self.opensearch:
            return {"success": False, "error": "OpenSearch not initialized"}
        
        try:
            filters = []
            if repo_full_name:
                filters.append({'term': {'repo_full_name': repo_full_name}})
            
            agg_body = {
                'size': 0,
                'query': {'bool': {'filter': filters}} if filters else {'match_all': {}},
                'aggs': {
                    'total_chunks': {'value_count': {'field': 'chunk_id'}},
                    'by_repo': {'terms': {'field': 'repo_full_name', 'size': 50}},
                    'by_language': {'terms': {'field': 'language', 'size': 20}},
                    'by_type': {'terms': {'field': 'chunk_type', 'size': 10}},
                    'total_lines': {'sum': {'field': 'line_count'}}
                }
            }
            
            response = self.opensearch.client.search(index=self.INDEX_NAME, body=agg_body)
            aggs = response['aggregations']
            
            return {
                "success": True,
                "total_chunks": int(aggs['total_chunks']['value']),
                "total_lines": int(aggs['total_lines']['value']),
                "by_repository": {b['key']: b['doc_count'] for b in aggs['by_repo']['buckets']},
                "by_language": {b['key']: b['doc_count'] for b in aggs['by_language']['buckets']},
                "by_type": {b['key']: b['doc_count'] for b in aggs['by_type']['buckets']}
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"success": False, "error": str(e)}
    
    def clear_repository(self, repo_full_name: str) -> Dict[str, Any]:
        """Clear all indexed code for a repository."""
        if not self.opensearch:
            return {"success": False, "error": "OpenSearch not initialized"}
        
        try:
            # Delete chunks
            result = self.opensearch.client.delete_by_query(
                index=self.INDEX_NAME,
                body={'query': {'term': {'repo_full_name': repo_full_name}}}
            )
            chunks_deleted = result.get('deleted', 0)
            
            # Delete file hashes
            self.opensearch.client.delete_by_query(
                index=self.FILE_HASH_INDEX,
                body={'query': {'term': {'repo_full_name': repo_full_name}}},
                ignore=[404]
            )
            
            return {
                "success": True,
                "repo": repo_full_name,
                "chunks_deleted": chunks_deleted
            }
        except Exception as e:
            logger.error(f"Clear error: {e}")
            return {"success": False, "error": str(e)}
