"""Code Search Service - Retrieval-Augmented Generation for code analysis.

Combines semantic search with LLM analysis for intelligent code understanding.
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CodeSearchResult:
    """A single code search result."""
    file_path: str
    relative_path: str
    name: str
    chunk_type: str
    content: str
    start_line: int
    end_line: int
    language: str
    score: float
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parent_name: Optional[str] = None


class CodeSearchService:
    """Service for intelligent code search and retrieval."""
    
    def __init__(self, code_index_service=None, issue_history_service=None):
        """
        Initialize the code search service.
        
        Args:
            code_index_service: CodeIndexService instance
            issue_history_service: IssueHistoryService for historical context
        """
        self.code_index = code_index_service
        self.issue_history = issue_history_service
    
    def search_relevant_code(self, query: str, repo_full_name: str = None,
                              limit: int = 10, include_context: bool = True) -> Dict[str, Any]:
        """
        Search for code relevant to a query (bug description, feature request, etc.).
        
        Args:
            query: Natural language query
            repo_full_name: Filter by repository
            limit: Maximum results
            include_context: Include surrounding context
            
        Returns:
            Relevant code chunks with context
        """
        if not self.code_index:
            return {"success": False, "error": "Code index service not available"}
        
        # Semantic search for relevant code
        search_result = self.code_index.search_code(
            query=query,
            repo_full_name=repo_full_name,
            use_semantic=True,
            limit=limit
        )
        
        if not search_result.get("success"):
            return search_result
        
        results = search_result.get("results", [])
        
        # Enhance results with context
        enhanced_results = []
        for result in results:
            enhanced = {
                **result,
                "relevance_explanation": self._explain_relevance(query, result)
            }
            enhanced_results.append(enhanced)
        
        return {
            "success": True,
            "query": query,
            "total": len(enhanced_results),
            "results": enhanced_results
        }
    
    def _explain_relevance(self, query: str, result: Dict) -> str:
        """Generate a brief explanation of why this code is relevant."""
        explanations = []
        
        name = result.get('name', '')
        chunk_type = result.get('chunk_type', '')
        docstring = result.get('docstring', '')
        
        # Check name match
        query_words = query.lower().split()
        name_lower = name.lower()
        matched_words = [w for w in query_words if w in name_lower]
        if matched_words:
            explanations.append(f"Name contains: {', '.join(matched_words)}")
        
        # Check docstring match
        if docstring:
            doc_lower = docstring.lower()
            doc_matched = [w for w in query_words if w in doc_lower]
            if doc_matched:
                explanations.append(f"Documentation mentions: {', '.join(doc_matched[:3])}")
        
        # Add type context
        if chunk_type == 'class':
            explanations.append("This is a class definition")
        elif chunk_type == 'function':
            explanations.append("This is a function")
        elif chunk_type == 'method':
            parent = result.get('parent_name', '')
            explanations.append(f"Method of class {parent}" if parent else "This is a method")
        
        return "; ".join(explanations) if explanations else "Semantic similarity match"
    
    def find_code_for_bug(self, bug_title: str, bug_description: str = "",
                          repo_full_name: str = None, limit: int = 15) -> Dict[str, Any]:
        """
        Find code most likely related to a bug.
        
        Combines:
        1. Semantic search on bug description
        2. Symbol search for mentioned function/class names
        3. Historical context from similar bugs
        
        Args:
            bug_title: Bug title
            bug_description: Bug description
            repo_full_name: Repository to search
            limit: Maximum results per search type
            
        Returns:
            Consolidated relevant code with confidence scores
        """
        if not self.code_index:
            return {"success": False, "error": "Code index service not available"}
        
        all_results = {}
        combined_query = f"{bug_title} {bug_description}"
        
        # 1. Semantic search on full bug description
        semantic_results = self.code_index.search_code(
            query=combined_query,
            repo_full_name=repo_full_name,
            use_semantic=True,
            limit=limit
        )
        
        if semantic_results.get("success"):
            for result in semantic_results.get("results", []):
                chunk_id = result.get('chunk_id')
                if chunk_id not in all_results:
                    all_results[chunk_id] = {
                        **result,
                        "match_sources": ["semantic_search"],
                        "combined_score": result.get('score', 0)
                    }
                else:
                    all_results[chunk_id]["match_sources"].append("semantic_search")
                    all_results[chunk_id]["combined_score"] += result.get('score', 0)
        
        # 2. Extract and search for potential symbol names
        symbols = self._extract_potential_symbols(combined_query)
        for symbol in symbols[:5]:  # Limit symbol searches
            symbol_results = self.code_index.search_by_symbol(
                symbol_name=symbol,
                repo_full_name=repo_full_name
            )
            
            if symbol_results.get("success"):
                for result in symbol_results.get("results", []):
                    chunk_id = result.get('chunk_id')
                    if chunk_id not in all_results:
                        all_results[chunk_id] = {
                            **result,
                            "match_sources": [f"symbol:{symbol}"],
                            "combined_score": result.get('score', 0) * 1.5  # Boost symbol matches
                        }
                    else:
                        all_results[chunk_id]["match_sources"].append(f"symbol:{symbol}")
                        all_results[chunk_id]["combined_score"] += result.get('score', 0) * 0.5
        
        # 3. Get historical context if available
        historical_context = None
        if self.issue_history:
            try:
                historical_context = self.issue_history.get_historical_context(
                    bug_title=bug_title,
                    bug_description=bug_description,
                    repo_full_name=repo_full_name,
                    limit=5
                )
            except:
                pass
        
        # Sort by combined score
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x.get('combined_score', 0),
            reverse=True
        )[:limit]
        
        return {
            "success": True,
            "bug_title": bug_title,
            "total_results": len(sorted_results),
            "code_results": sorted_results,
            "historical_context": historical_context,
            "symbols_searched": symbols[:5]
        }
    
    def _extract_potential_symbols(self, text: str) -> List[str]:
        """Extract potential function/class names from text."""
        import re
        
        symbols = []
        
        # CamelCase words (likely class names)
        camel_case = re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b', text)
        symbols.extend(camel_case)
        
        # snake_case words (likely function names)
        snake_case = re.findall(r'\b([a-z]+(?:_[a-z]+)+)\b', text)
        symbols.extend(snake_case)
        
        # Words that look like method names
        method_like = re.findall(r'\b(get|set|create|update|delete|find|search|load|save|init|handle|process|validate|check|is|has|can|should)[A-Z]\w+', text)
        symbols.extend(method_like)
        
        # Quoted strings that might be function names
        quoted = re.findall(r'[`\'"](\w+)[`\'"]', text)
        symbols.extend([q for q in quoted if len(q) > 2])
        
        # Deduplicate while preserving order
        seen = set()
        unique_symbols = []
        for s in symbols:
            if s.lower() not in seen:
                seen.add(s.lower())
                unique_symbols.append(s)
        
        return unique_symbols
    
    def get_code_context(self, file_path: str, start_line: int, end_line: int,
                         context_lines: int = 10, repo_full_name: str = None) -> Dict[str, Any]:
        """
        Get code context around specified lines.
        
        Args:
            file_path: Path to file
            start_line: Starting line number
            end_line: Ending line number
            context_lines: Lines of context before/after
            repo_full_name: Repository filter
            
        Returns:
            Code with surrounding context
        """
        if not self.code_index:
            return {"success": False, "error": "Code index service not available"}
        
        # Search for chunks in this file around these lines
        search_body = {
            'size': 10,
            'query': {
                'bool': {
                    'must': [
                        {'term': {'relative_path': file_path}}
                    ],
                    'filter': [
                        {'range': {'start_line': {'lte': end_line + context_lines}}},
                        {'range': {'end_line': {'gte': start_line - context_lines}}}
                    ]
                }
            },
            'sort': [{'start_line': 'asc'}],
            '_source': {'excludes': ['embedding', 'searchable_text']}
        }
        
        if repo_full_name:
            search_body['query']['bool']['must'].append(
                {'term': {'repo_full_name': repo_full_name}}
            )
        
        try:
            response = self.code_index.opensearch.client.search(
                index=self.code_index.INDEX_NAME,
                body=search_body
            )
            
            chunks = [hit['_source'] for hit in response['hits']['hits']]
            
            return {
                "success": True,
                "file_path": file_path,
                "target_lines": f"{start_line}-{end_line}",
                "chunks": chunks
            }
        except Exception as e:
            logger.error(f"Context search error: {e}")
            return {"success": False, "error": str(e)}
    
    def find_related_code(self, chunk_id: str) -> Dict[str, Any]:
        """
        Find code related to a specific chunk (callers, callees, same class).
        
        Args:
            chunk_id: ID of the chunk to find relations for
            
        Returns:
            Related code chunks
        """
        if not self.code_index:
            return {"success": False, "error": "Code index service not available"}
        
        try:
            # Get the original chunk
            response = self.code_index.opensearch.client.get(
                index=self.code_index.INDEX_NAME,
                id=chunk_id
            )
            
            if not response.get('found'):
                return {"success": False, "error": "Chunk not found"}
            
            chunk = response['_source']
            related = {
                "callers": [],
                "callees": [],
                "same_class": [],
                "same_file": []
            }
            
            # Find callers (who calls this function)
            if chunk.get('name'):
                callers_result = self.code_index.get_function_calls(
                    function_name=chunk['name'],
                    repo_full_name=chunk.get('repo_full_name')
                )
                if callers_result.get("success"):
                    related["callers"] = callers_result.get("callers", [])
            
            # Find callees (what this function calls)
            calls = chunk.get('calls', [])
            for call in calls[:10]:
                symbol_result = self.code_index.search_by_symbol(
                    symbol_name=call,
                    repo_full_name=chunk.get('repo_full_name'),
                    exact_match=True
                )
                if symbol_result.get("success") and symbol_result.get("results"):
                    related["callees"].extend(symbol_result["results"][:2])
            
            # Find other methods in same class
            if chunk.get('parent_name'):
                class_search = {
                    'size': 20,
                    'query': {
                        'bool': {
                            'must': [
                                {'term': {'parent_name': chunk['parent_name']}},
                                {'term': {'repo_full_name': chunk.get('repo_full_name', '')}}
                            ]
                        }
                    },
                    '_source': ['name', 'chunk_type', 'signature', 'start_line', 'relative_path']
                }
                
                class_response = self.code_index.opensearch.client.search(
                    index=self.code_index.INDEX_NAME,
                    body=class_search
                )
                related["same_class"] = [
                    hit['_source'] for hit in class_response['hits']['hits']
                    if hit['_id'] != chunk_id
                ]
            
            return {
                "success": True,
                "chunk": {
                    "name": chunk.get('name'),
                    "chunk_type": chunk.get('chunk_type'),
                    "file": chunk.get('relative_path')
                },
                "related": related
            }
            
        except Exception as e:
            logger.error(f"Related code search error: {e}")
            return {"success": False, "error": str(e)}
    
    def prepare_analysis_context(self, bug_title: str, bug_description: str = "",
                                  repo_full_name: str = None,
                                  max_context_chars: int = 50000) -> Dict[str, Any]:
        """
        Prepare context for LLM-based code analysis.
        
        Gathers relevant code and formats it for analysis by an LLM.
        
        Args:
            bug_title: Bug title
            bug_description: Bug description
            repo_full_name: Repository to search
            max_context_chars: Maximum characters of context
            
        Returns:
            Formatted context ready for LLM analysis
        """
        # Find relevant code
        search_result = self.find_code_for_bug(
            bug_title=bug_title,
            bug_description=bug_description,
            repo_full_name=repo_full_name,
            limit=20
        )
        
        if not search_result.get("success"):
            return search_result
        
        code_results = search_result.get("code_results", [])
        historical_context = search_result.get("historical_context")
        
        # Format code for LLM
        formatted_code = []
        total_chars = 0
        
        for result in code_results:
            chunk_text = self._format_code_chunk(result)
            
            if total_chars + len(chunk_text) > max_context_chars:
                break
            
            formatted_code.append(chunk_text)
            total_chars += len(chunk_text)
        
        # Format historical context
        historical_text = ""
        if historical_context and historical_context.get("has_context"):
            historical_text = self._format_historical_context(historical_context)
        
        # Build final context
        context = {
            "success": True,
            "bug": {
                "title": bug_title,
                "description": bug_description
            },
            "code_context": "\n\n".join(formatted_code),
            "code_files_count": len(formatted_code),
            "historical_context": historical_text,
            "total_context_chars": total_chars + len(historical_text),
            "symbols_found": search_result.get("symbols_searched", [])
        }
        
        return context
    
    def _format_code_chunk(self, chunk: Dict) -> str:
        """Format a code chunk for LLM consumption."""
        lines = []
        
        # Header
        file_info = chunk.get('relative_path', chunk.get('file_path', 'unknown'))
        lines.append(f"### File: {file_info}")
        lines.append(f"### {chunk.get('chunk_type', 'code').title()}: {chunk.get('name', 'unknown')}")
        lines.append(f"### Lines: {chunk.get('start_line', '?')}-{chunk.get('end_line', '?')}")
        
        if chunk.get('signature'):
            lines.append(f"### Signature: {chunk['signature']}")
        
        if chunk.get('match_sources'):
            lines.append(f"### Match reasons: {', '.join(chunk['match_sources'])}")
        
        # Code
        language = chunk.get('language', '')
        content = chunk.get('content', '')
        
        # Truncate very long content
        if len(content) > 3000:
            content = content[:3000] + "\n... (truncated)"
        
        lines.append(f"```{language}")
        lines.append(content)
        lines.append("```")
        
        return "\n".join(lines)
    
    def _format_historical_context(self, context: Dict) -> str:
        """Format historical context for LLM consumption."""
        lines = ["## Historical Context from Similar Issues", ""]
        
        similar_issues = context.get("similar_issues", [])
        for i, issue in enumerate(similar_issues[:5], 1):
            score = issue.get('similarity_score', 0)
            lines.append(f"{i}. **{issue.get('issue_id', 'N/A')}** (Score: {score:.2f})")
            lines.append(f"   Title: {issue.get('title', 'N/A')}")
            if issue.get('state'):
                lines.append(f"   State: {issue['state']}")
            lines.append("")
        
        patterns = context.get("patterns", {})
        if patterns.get("common_labels"):
            lines.append(f"**Common Labels:** {', '.join(patterns['common_labels'].keys())}")
        if patterns.get("common_assignees"):
            lines.append(f"**Typical Assignees:** {', '.join(patterns['common_assignees'].keys())}")
        
        return "\n".join(lines)
