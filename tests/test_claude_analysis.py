"""
Test script to verify Claude API analysis with actual code files.
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx
from anthropic import Anthropic
from src.trackers.jira_client import JiraMCPServer
from src.services.code_analyzer import CodeAnalysisAgent
from src.config import Config

def test_single_file_analysis():
    """Test analysis with just one code file."""
    print("Testing single file analysis with Claude API...\n")
    
    # Get a bug from Jira
    jira = JiraMCPServer()
    bugs = jira.get_bugs(max_results=1)
    
    if not bugs:
        print("No bugs found!")
        return
    
    bug = bugs[0]
    print(f"Bug: {bug.key} - {bug.summary}")
    print(f"Description: {bug.description[:200]}...\n")
    
    # Get code files
    analyzer = CodeAnalysisAgent()
    code_files = analyzer.scan_repository(extensions=['.py'])
    
    if not code_files:
        print("No code files found!")
        return
    
    # Test with just the first file
    test_file = code_files[0]
    print(f"Testing with: {test_file.relative_path} ({len(test_file.content)} chars)\n")
    
    # Prepare simple prompt
    prompt = f"""Analyze this code file for the bug: {bug.summary}

Bug Description:
{bug.description}

Code File: {test_file.relative_path}
```python
{test_file.content[:2000]}
```

Provide analysis in this format:
- File: {test_file.relative_path}
- Lines: <line numbers>
- Issue: <what's wrong>
- Severity: <level>
- Resolution: <how to fix>
- Code Fix: <code example>

If not related, say "NO ISSUES FOUND"."""

    # Call Claude
    try:
        print("Calling Claude API...")
        http_client = httpx.Client(verify=False, timeout=120.0)
        client = Anthropic(api_key=Config.ANTHROPIC_API_KEY, http_client=http_client)
        
        response = client.messages.create(
            model=Config.CLAUDE_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        print("\n" + "="*60)
        print("CLAUDE ANALYSIS RESULT:")
        print("="*60)
        print(response.content[0].text)
        print("="*60)
        print(f"\nModel: {response.model}")
        print(f"Tokens used: Input={response.usage.input_tokens}, Output={response.usage.output_tokens}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_file_analysis()
