"""Code analysis agent using Claude SDK with RAG-based code retrieval."""
import os
import ssl
import httpx
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from anthropic import Anthropic
from src.config import Config

# Type alias for progress callback
ProgressCallback = Callable[[str], None]


class CodeFile:
    """Represents a code file for analysis."""
    
    def __init__(self, path: Path, content: str):
        self.path = path
        self.relative_path = path.relative_to(Config.REPO_PATH) if path.is_relative_to(Config.REPO_PATH) else path
        self.content = content
        self.extension = path.suffix


class CodeAnalysisAgent:
    """Agent for analyzing code using Claude with RAG-based code retrieval.
    
    This agent supports two modes:
    1. Traditional Mode: Scans all files in the repository (good for small repos)
    2. RAG Mode: Uses indexed code for semantic search (required for large repos)
    
    RAG Mode Flow:
    - Uses CodeSearchService to find relevant code chunks
    - Combines semantic search with symbol-based search
    - Integrates historical context from similar issues
    - Only sends relevant code snippets to Claude (not entire files)
    """
    
    def __init__(self, use_rag: bool = True):
        """Initialize the code analysis agent.
        
        Args:
            use_rag: If True, uses RAG-based code retrieval (recommended for large repos)
        """
        # Create HTTP client with SSL verification disabled and timeout
        http_client = httpx.Client(verify=False, timeout=60.0)
        self.client = Anthropic(
            api_key=Config.ANTHROPIC_API_KEY,
            http_client=http_client
        )
        self.model = Config.CLAUDE_MODEL
        self.use_rag = use_rag
        self.progress_callback: Optional[ProgressCallback] = None
        
        # Initialize RAG services if enabled
        self._code_search_service = None
        self._code_index_service = None
    
    def set_progress_callback(self, callback: Optional[ProgressCallback]):
        """Set a callback function for progress updates.
        
        Args:
            callback: Function that receives progress message strings
        """
        self.progress_callback = callback
    
    def _report_progress(self, message: str):
        """Report progress via callback if set, otherwise print."""
        if self.progress_callback:
            self.progress_callback(message)
        print(message)
        
    @property
    def code_search_service(self):
        """Lazy load CodeSearchService."""
        if self._code_search_service is None:
            try:
                from src.services.code_search_service import CodeSearchService
                self._code_search_service = CodeSearchService()
            except Exception as e:
                print(f"Warning: Could not initialize CodeSearchService: {e}")
                self._code_search_service = None
        return self._code_search_service
    
    @property
    def code_index_service(self):
        """Lazy load CodeIndexService."""
        if self._code_index_service is None:
            try:
                from src.services.code_index_service import CodeIndexService
                self._code_index_service = CodeIndexService()
            except Exception as e:
                print(f"Warning: Could not initialize CodeIndexService: {e}")
                self._code_index_service = None
        return self._code_index_service
    
    def scan_repository(self, extensions: Optional[List[str]] = None) -> List[CodeFile]:
        """
        Scan the repository for code files.
        
        Args:
            extensions: List of file extensions to include (e.g., ['.py', '.java'])
                       If None, includes common code files
        
        Returns:
            List of CodeFile objects
        """
        if extensions is None:
            extensions = ['.py', '.java', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.cpp', '.c', '.h']
        
        code_files = []
        repo_path = Config.REPO_PATH
        
        if not repo_path.exists():
            self._report_progress(f"Repository path does not exist: {repo_path}")
            return code_files
        
        for ext in extensions:
            for file_path in repo_path.rglob(f'*{ext}'):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        code_files.append(CodeFile(file_path, content))
                    except Exception as e:
                        self._report_progress(f"Warning: Could not read {file_path}: {str(e)}")
        
        self._report_progress(f"✓ Scanned repository: found {len(code_files)} code files")
        return code_files
    
    def analyze_bug(
        self, 
        bug_description: str,
        bug_key: str,
        code_files: List[CodeFile],
        max_files_per_analysis: int = 3,  # Reduced from 10 to 3 for faster processing
        historical_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze code files to identify potential bug locations and fixes.
        
        Args:
            bug_description: Description of the bug from Jira
            bug_key: Jira issue key
            code_files: List of code files to analyze
            max_files_per_analysis: Maximum files to analyze in one request
            
        Returns:
            Analysis results dictionary
        """
        if not code_files:
            return {
                "bug_key": bug_key,
                "status": "no_files",
                "message": "No code files found to analyze"
            }
        
        self._report_progress(f"\n{'='*60}")
        self._report_progress(f"Analyzing bug: {bug_key}")
        self._report_progress(f"{'='*60}")
        
        # Group files by language/extension for better analysis
        files_by_type = {}
        for code_file in code_files:
            ext = code_file.extension
            if ext not in files_by_type:
                files_by_type[ext] = []
            files_by_type[ext].append(code_file)
        
        all_findings = []
        
        # Analyze files in batches
        for ext, files in files_by_type.items():
            self._report_progress(f"\nAnalyzing {len(files)} {ext} files...")
            
            for i in range(0, len(files), max_files_per_analysis):
                batch = files[i:i + max_files_per_analysis]
                findings = self._analyze_batch(bug_description, bug_key, batch, historical_context)
                all_findings.extend(findings)
        
        return {
            "bug_key": bug_key,
            "status": "analyzed",
            "total_files_analyzed": len(code_files),
            "findings": all_findings
        }
    
    def _analyze_batch(
        self, 
        bug_description: str,
        bug_key: str,
        code_files: List[CodeFile],
        historical_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Analyze a batch of code files."""
        # Build the analysis prompt with size limits
        files_content = []
        max_file_size = 5000  # Limit each file to 5000 chars
        
        for idx, code_file in enumerate(code_files):
            content = code_file.content
            if len(content) > max_file_size:
                content = content[:max_file_size] + f"\n... (truncated, total {len(code_file.content)} chars)"
            
            files_content.append(
                f"File {idx + 1}: {code_file.relative_path}\n"
                f"```{code_file.extension[1:]}\n"
                f"{content}\n"
                f"```\n"
            )
        
        # Format historical context for prompt
        context_section = ""
        if historical_context and historical_context.get("has_context"):
            context_section = "\n📚 HISTORICAL CONTEXT FROM SIMILAR PAST ISSUES:\n"
            context_section += "=" * 50 + "\n"
            
            if historical_context.get("similar_issues"):
                context_section += f"Found {historical_context.get('similar_issues_count', 0)} similar issues:\n\n"
                for i, issue in enumerate(historical_context.get("similar_issues", [])[:5], 1):
                    similarity = issue.get("similarity", 0) * 100
                    context_section += f"{i}. [{issue.get('key', 'N/A')}] (Similarity: {similarity:.1f}%)\n"
                    context_section += f"   Title: {issue.get('title', 'N/A')}\n"
                    if issue.get("resolution"):
                        context_section += f"   Resolution: {issue.get('resolution')}\n"
                    context_section += "\n"
            
            if historical_context.get("common_themes"):
                context_section += "\nCommon Themes in Similar Issues:\n"
                for theme in historical_context.get("common_themes", [])[:5]:
                    context_section += f"  • {theme}\n"
            
            context_section += "\n" + "=" * 50 + "\n"
            context_section += "Use this historical context to guide your analysis.\n\n"
        
        prompt = f"""You are a senior software engineer analyzing code to identify and fix bugs.

Bug Report ({bug_key}):
{bug_description}
{context_section}

Below are {len(code_files)} code files from the repository. Please analyze them to:
1. Identify which files are likely related to this bug
2. Pinpoint the exact line numbers where issues exist
3. Explain what the problem is
4. Suggest specific fixes with code examples

Code Files:
{chr(10).join(files_content)}

Provide your analysis in the following structured format:

For each relevant finding:
- File: <relative file path>
- Lines: <line numbers or range>
- Issue: <description of the problem>
- Severity: <Critical/High/Medium/Low>
- Resolution: <detailed fix explanation>
- Code Fix: <actual code changes needed>

If no relevant code is found in these files, state "NO ISSUES FOUND IN THIS BATCH"."""

        try:
            self._report_progress(f"  Sending {len(code_files)} files to Claude for analysis...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            analysis_text = response.content[0].text
            self._report_progress(f"  ✓ Received analysis from Claude")
            
            # Parse the response into structured findings
            findings = self._parse_analysis(analysis_text, code_files)
            
            return findings
            
        except Exception as e:
            self._report_progress(f"Error during Claude API call: {str(e)}")
            return [{
                "file": "ERROR",
                "lines": "N/A",
                "issue": f"Analysis failed: {str(e)}",
                "severity": "Unknown",
                "resolution": "Unable to complete analysis",
                "code_fix": ""
            }]
    
    def _parse_analysis(self, analysis_text: str, code_files: List[CodeFile]) -> List[Dict[str, Any]]:
        """Parse Claude's analysis into structured findings."""
        findings = []
        
        # Check if no issues found
        if "NO ISSUES FOUND" in analysis_text.upper():
            return findings
        
        # Split by file sections (this is a simple parser)
        lines = analysis_text.split('\n')
        current_finding = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('- File:'):
                if current_finding:
                    findings.append(current_finding)
                current_finding = {'file': line.replace('- File:', '').strip()}
            elif line.startswith('- Lines:'):
                current_finding['lines'] = line.replace('- Lines:', '').strip()
            elif line.startswith('- Issue:'):
                current_finding['issue'] = line.replace('- Issue:', '').strip()
            elif line.startswith('- Severity:'):
                current_finding['severity'] = line.replace('- Severity:', '').strip()
            elif line.startswith('- Resolution:'):
                current_finding['resolution'] = line.replace('- Resolution:', '').strip()
            elif line.startswith('- Code Fix:'):
                current_finding['code_fix'] = line.replace('- Code Fix:', '').strip()
        
        # Add last finding
        if current_finding and 'file' in current_finding:
            findings.append(current_finding)
        
        # If parsing failed, return raw analysis
        if not findings and analysis_text.strip():
            findings.append({
                'file': 'Multiple files',
                'lines': 'See analysis',
                'issue': 'See detailed analysis below',
                'severity': 'Unknown',
                'resolution': analysis_text,
                'code_fix': ''
            })
        
        return findings

    # ============================================================================
    # RAG-Based Analysis Methods (for large repositories)
    # ============================================================================
    
    def analyze_bug_with_rag(
        self,
        bug_description: str,
        bug_key: str,
        repo_full_name: str,
        historical_context: Optional[Dict[str, Any]] = None,
        max_code_chunks: int = 15
    ) -> Dict[str, Any]:
        """
        Analyze a bug using RAG-based code retrieval.
        
        This method is designed for large repositories where scanning all files
        is not practical. It uses semantic search to find relevant code.
        
        Args:
            bug_description: Description of the bug
            bug_key: Bug issue key
            repo_full_name: Repository name (e.g., "owner/repo")
            historical_context: Historical context from similar issues
            max_code_chunks: Maximum number of code chunks to retrieve
            
        Returns:
            Analysis results dictionary
        """
        if not self.code_search_service:
            return {
                "bug_key": bug_key,
                "status": "error",
                "message": "CodeSearchService not available. Please ensure code is indexed."
            }
        
        print(f"\n{'='*60}")
        print(f"🔍 RAG-Based Analysis for: {bug_key}")
        print(f"{'='*60}")
        
        # Step 1: Prepare analysis context using RAG
        print("\n📚 Retrieving relevant code using semantic search...")
        analysis_context = self.code_search_service.prepare_analysis_context(
            bug_title=bug_key,
            bug_description=bug_description,
            repo_full_name=repo_full_name,
            historical_context=historical_context,
            max_chunks=max_code_chunks
        )
        
        if not analysis_context.get("has_code_context"):
            return {
                "bug_key": bug_key,
                "status": "no_code",
                "message": "No relevant code found in index. Repository may not be indexed."
            }
        
        code_chunks_count = analysis_context.get("code_chunks_count", 0)
        print(f"  ✓ Retrieved {code_chunks_count} relevant code chunks")
        
        # Step 2: Build the RAG-enhanced prompt
        prompt = self._build_rag_prompt(
            bug_key=bug_key,
            bug_description=bug_description,
            formatted_context=analysis_context.get("formatted_context", ""),
            historical_context=historical_context
        )
        
        # Step 3: Send to Claude for analysis
        print("\n🤖 Sending to Claude for analysis...")
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            analysis_text = response.content[0].text
            print(f"  ✓ Received analysis from Claude")
            
            # Parse the response
            findings = self._parse_rag_analysis(analysis_text)
            
            return {
                "bug_key": bug_key,
                "status": "analyzed",
                "mode": "rag",
                "code_chunks_analyzed": code_chunks_count,
                "files_referenced": analysis_context.get("files_referenced", []),
                "historical_issues_used": analysis_context.get("historical_issues_used", 0),
                "findings": findings,
                "raw_analysis": analysis_text
            }
            
        except Exception as e:
            self._report_progress(f"Error during Claude API call: {str(e)}")
            return {
                "bug_key": bug_key,
                "status": "error",
                "message": f"Analysis failed: {str(e)}"
            }
    
    def _build_rag_prompt(
        self,
        bug_key: str,
        bug_description: str,
        formatted_context: str,
        historical_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the prompt for RAG-based analysis."""
        
        historical_section = ""
        if historical_context and historical_context.get("has_context"):
            historical_section = "\n📚 HISTORICAL CONTEXT FROM SIMILAR PAST ISSUES:\n"
            historical_section += "=" * 50 + "\n"
            
            if historical_context.get("similar_issues"):
                historical_section += f"Found {historical_context.get('similar_issues_count', 0)} similar issues:\n\n"
                for i, issue in enumerate(historical_context.get("similar_issues", [])[:5], 1):
                    similarity = issue.get("similarity", 0) * 100
                    historical_section += f"{i}. [{issue.get('key', 'N/A')}] (Similarity: {similarity:.1f}%)\n"
                    historical_section += f"   Title: {issue.get('title', 'N/A')}\n"
                    if issue.get("resolution"):
                        historical_section += f"   Resolution: {issue.get('resolution')}\n"
                    historical_section += "\n"
            
            if historical_context.get("common_themes"):
                historical_section += "\nCommon Resolution Patterns:\n"
                for theme in historical_context.get("common_themes", [])[:5]:
                    historical_section += f"  • {theme}\n"
            
            historical_section += "\n" + "=" * 50 + "\n"
        
        prompt = f"""You are a senior software engineer analyzing code to identify and fix bugs.
Your analysis is powered by RAG (Retrieval-Augmented Generation) - you're seeing 
the most relevant code snippets retrieved via semantic search, not the entire codebase.

🐛 BUG REPORT: {bug_key}
{'='*60}
{bug_description}
{'='*60}
{historical_section}

📂 RELEVANT CODE (Retrieved via Semantic Search):
{formatted_context}

Based on the code snippets above, please provide your analysis:

1. **Root Cause Analysis**: Identify the most likely cause of this bug
2. **Affected Files**: List the files that need to be modified
3. **Detailed Findings**: For each issue found, provide:

For each finding use this format:
- File: <file path>
- Lines: <line numbers or range>
- Issue: <what's wrong>
- Severity: <Critical/High/Medium/Low>
- Root Cause: <why this bug occurs>
- Resolution: <how to fix it>
- Code Fix: <actual code changes>

4. **Additional Recommendations**: Any other suggestions

If the retrieved code doesn't seem relevant to the bug, state that clearly and suggest 
what files or code patterns should be searched for instead.
"""
        return prompt
    
    def _parse_rag_analysis(self, analysis_text: str) -> List[Dict[str, Any]]:
        """Parse Claude's RAG analysis into structured findings."""
        findings = []
        
        # Check for "not relevant" indicators
        if "NOT RELEVANT" in analysis_text.upper() or "NO ISSUES FOUND" in analysis_text.upper():
            return [{
                'file': 'N/A',
                'lines': 'N/A',
                'issue': 'Retrieved code may not be relevant to this bug',
                'severity': 'Unknown',
                'resolution': analysis_text,
                'code_fix': ''
            }]
        
        # Parse structured findings
        lines = analysis_text.split('\n')
        current_finding = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('- File:'):
                if current_finding and 'file' in current_finding:
                    findings.append(current_finding)
                current_finding = {'file': line.replace('- File:', '').strip()}
            elif line.startswith('- Lines:'):
                current_finding['lines'] = line.replace('- Lines:', '').strip()
            elif line.startswith('- Issue:'):
                current_finding['issue'] = line.replace('- Issue:', '').strip()
            elif line.startswith('- Severity:'):
                current_finding['severity'] = line.replace('- Severity:', '').strip()
            elif line.startswith('- Root Cause:'):
                current_finding['root_cause'] = line.replace('- Root Cause:', '').strip()
            elif line.startswith('- Resolution:'):
                current_finding['resolution'] = line.replace('- Resolution:', '').strip()
            elif line.startswith('- Code Fix:'):
                current_finding['code_fix'] = line.replace('- Code Fix:', '').strip()
        
        # Add last finding
        if current_finding and 'file' in current_finding:
            findings.append(current_finding)
        
        # If parsing failed, return raw analysis
        if not findings and analysis_text.strip():
            findings.append({
                'file': 'Multiple files',
                'lines': 'See analysis',
                'issue': 'See detailed analysis below',
                'severity': 'Unknown',
                'resolution': analysis_text,
                'code_fix': ''
            })
        
        return findings
    
    def index_repository(
        self,
        repo_path: str,
        repo_full_name: str,
        extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Index a repository for RAG-based analysis.
        
        Args:
            repo_path: Path to the repository
            repo_full_name: Repository name (e.g., "owner/repo")
            extensions: File extensions to index
            
        Returns:
            Indexing statistics
        """
        if not self.code_index_service:
            return {
                "status": "error",
                "message": "CodeIndexService not available"
            }
        
        print(f"\n📁 Indexing repository: {repo_full_name}")
        print(f"   Path: {repo_path}")
        
        try:
            result = self.code_index_service.index_repository(
                repo_path=repo_path,
                repo_full_name=repo_full_name,
                extensions=extensions,
                incremental=True
            )
            
            return {
                "status": "success",
                "repo_full_name": repo_full_name,
                **result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Indexing failed: {str(e)}"
            }
    
    def get_index_stats(self, repo_full_name: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about indexed code."""
        if not self.code_index_service:
            return {"status": "error", "message": "CodeIndexService not available"}
        
        return self.code_index_service.get_index_stats(repo_full_name)
    
    def smart_analyze_bug(
        self,
        bug_description: str,
        bug_key: str,
        repo_full_name: Optional[str] = None,
        historical_context: Optional[Dict[str, Any]] = None,
        force_scan: bool = False
    ) -> Dict[str, Any]:
        """
        Smart analysis that chooses between RAG and traditional scanning.
        
        Uses RAG if:
        - Repository is indexed
        - use_rag is True
        - force_scan is False
        
        Falls back to traditional scanning if:
        - Repository is not indexed
        - use_rag is False
        - force_scan is True
        
        Args:
            bug_description: Description of the bug
            bug_key: Bug issue key
            repo_full_name: Repository name for RAG mode
            historical_context: Historical context
            force_scan: If True, always use traditional scanning
            
        Returns:
            Analysis results
        """
        # Check if we should use RAG
        use_rag_mode = (
            self.use_rag 
            and not force_scan 
            and repo_full_name 
            and self.code_index_service
        )
        
        if use_rag_mode:
            # Check if repo is indexed
            stats = self.code_index_service.get_index_stats(repo_full_name)
            if stats.get("total_chunks", 0) > 0:
                print(f"🚀 Using RAG mode (found {stats['total_chunks']} indexed chunks)")
                return self.analyze_bug_with_rag(
                    bug_description=bug_description,
                    bug_key=bug_key,
                    repo_full_name=repo_full_name,
                    historical_context=historical_context
                )
            else:
                print("⚠️ Repository not indexed, falling back to traditional scan")
        
        # Fall back to traditional scanning
        print("📁 Using traditional file scan mode")
        code_files = self.scan_repository()
        return self.analyze_bug(
            bug_description=bug_description,
            bug_key=bug_key,
            code_files=code_files,
            historical_context=historical_context
        )
