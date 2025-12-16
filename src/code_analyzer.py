"""Code analysis agent using Claude SDK."""
import os
import ssl
import httpx
from pathlib import Path
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from config import Config


class CodeFile:
    """Represents a code file for analysis."""
    
    def __init__(self, path: Path, content: str):
        self.path = path
        self.relative_path = path.relative_to(Config.REPO_PATH) if path.is_relative_to(Config.REPO_PATH) else path
        self.content = content
        self.extension = path.suffix


class CodeAnalysisAgent:
    """Agent for analyzing code using Claude."""
    
    def __init__(self):
        """Initialize the code analysis agent."""
        # Create HTTP client with SSL verification disabled and timeout
        http_client = httpx.Client(verify=False, timeout=60.0)
        self.client = Anthropic(
            api_key=Config.ANTHROPIC_API_KEY,
            http_client=http_client
        )
        self.model = Config.CLAUDE_MODEL
    
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
            print(f"Repository path does not exist: {repo_path}")
            return code_files
        
        for ext in extensions:
            for file_path in repo_path.rglob(f'*{ext}'):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        code_files.append(CodeFile(file_path, content))
                    except Exception as e:
                        print(f"Warning: Could not read {file_path}: {str(e)}")
        
        print(f"✓ Scanned repository: found {len(code_files)} code files")
        return code_files
    
    def analyze_bug(
        self, 
        bug_description: str,
        bug_key: str,
        code_files: List[CodeFile],
        max_files_per_analysis: int = 3,  # Reduced from 10 to 3 for faster processing
        historical_context: Optional[str] = None
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
        
        print(f"\n{'='*60}")
        print(f"Analyzing bug: {bug_key}")
        print(f"{'='*60}")
        
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
            print(f"\nAnalyzing {len(files)} {ext} files...")
            
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
        historical_context: Optional[str] = None
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
        
        prompt = f"""You are a senior software engineer analyzing code to identify and fix bugs.

Bug Report ({bug_key}):
{bug_description}
{historical_context if historical_context else ''}

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
            print(f"  Sending {len(code_files)} files to Claude for analysis...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            analysis_text = response.content[0].text
            print(f"  ✓ Received analysis from Claude")
            
            # Parse the response into structured findings
            findings = self._parse_analysis(analysis_text, code_files)
            
            return findings
            
        except Exception as e:
            print(f"Error during Claude API call: {str(e)}")
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
