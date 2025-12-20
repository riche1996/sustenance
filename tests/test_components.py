"""
Test script to verify individual components.
Run this to test each component separately.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_config():
    """Test configuration loading."""
    print("\n=== Testing Configuration ===")
    try:
        from src.config import Config
        
        print(f"Jira URL: {Config.JIRA_URL}")
        print(f"Jira Project: {Config.JIRA_PROJECT_KEY}")
        print(f"Claude Model: {Config.CLAUDE_MODEL}")
        print(f"Repo Path: {Config.REPO_PATH}")
        print(f"Report Path: {Config.REPORT_OUTPUT_PATH}")
        
        Config.validate()
        print("\n✓ Configuration test passed")
        return True
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        return False


def test_jira_mcp():
    """Test Jira MCP server."""
    print("\n=== Testing Jira MCP Server ===")
    try:
        from src.trackers.jira_client import JiraMCPServer
        from src.config import Config
        
        jira = JiraMCPServer()
        
        # Try to fetch 1 bug
        print(f"Fetching bugs from project: {Config.JIRA_PROJECT_KEY}")
        bugs = jira.get_bugs(max_results=1)
        
        if bugs:
            bug = bugs[0]
            print(f"\nSample bug retrieved:")
            print(f"  Key: {bug.key}")
            print(f"  Summary: {bug.summary}")
            print(f"  Status: {bug.status}")
            print(f"  Priority: {bug.priority}")
        else:
            print("No bugs found (this is OK if project has no bugs)")
        
        print("\n✓ Jira MCP test passed")
        return True
    except Exception as e:
        print(f"\n❌ Jira MCP test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_code_analyzer():
    """Test code analyzer."""
    print("\n=== Testing Code Analyzer ===")
    try:
        from src.services.code_analyzer import CodeAnalysisAgent
        
        analyzer = CodeAnalysisAgent()
        
        # Scan repository
        print("Scanning repository...")
        code_files = analyzer.scan_repository(extensions=['.py', '.java'])
        
        print(f"Found {len(code_files)} code files")
        
        if code_files:
            print("\nSample files:")
            for f in code_files[:5]:
                print(f"  - {f.relative_path} ({len(f.content)} bytes)")
        
        print("\n✓ Code analyzer test passed")
        return True
    except Exception as e:
        print(f"\n❌ Code analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_claude_api():
    """Test Claude API connection with a simple request."""
    print("\n=== Testing Claude API ===")
    try:
        from anthropic import Anthropic
        from config import Config
        
        client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        
        print("Sending test message to Claude...")
        response = client.messages.create(
            model=Config.CLAUDE_MODEL,
            max_tokens=100,
            messages=[
                {
                    "role": "user",
                    "content": "Say 'API connection successful' and list 3 common Python bugs in one sentence each."
                }
            ]
        )
        
        response_text = response.content[0].text
        print(f"\nClaude's response:")
        print(response_text)
        
        print("\n✓ Claude API test passed")
        return True
    except Exception as e:
        print(f"\n❌ Claude API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_report_generator():
    """Test report generator."""
    print("\n=== Testing Report Generator ===")
    try:
        from src.services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        # Create sample data
        sample_results = [
            {
                "bug_key": "TEST-001",
                "bug_summary": "Test bug 1",
                "bug_description": "This is a test bug",
                "bug_status": "Open",
                "bug_priority": "High",
                "status": "analyzed",
                "total_files_analyzed": 5,
                "findings": [
                    {
                        "file": "test.py",
                        "lines": "10-15",
                        "issue": "Sample issue",
                        "severity": "Medium",
                        "resolution": "Sample resolution",
                        "code_fix": "# Sample fix"
                    }
                ]
            }
        ]
        
        print("Generating test report...")
        report_files = generator.generate_consolidated_report(
            analysis_results=sample_results,
            format="both"
        )
        
        print("\nGenerated reports:")
        for format_type, path in report_files.items():
            print(f"  {format_type}: {path}")
            if path.exists():
                print(f"    ✓ File exists ({path.stat().st_size} bytes)")
        
        print("\n✓ Report generator test passed")
        return True
    except Exception as e:
        print(f"\n❌ Report generator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_integration():
    """Test full integration with one bug."""
    print("\n=== Testing Full Integration ===")
    try:
        from main import BugTriageOrchestrator
        
        print("Initializing orchestrator...")
        orchestrator = BugTriageOrchestrator()
        
        print("\nAttempting to analyze 1 bug...")
        orchestrator.run(
            max_bugs=1,
            file_extensions=['.py']
        )
        
        print("\n✓ Full integration test passed")
        return True
    except Exception as e:
        print(f"\n❌ Full integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Component Test Suite")
    print("="*60)
    
    tests = [
        ("Configuration", test_config),
        ("Jira MCP Server", test_jira_mcp),
        ("Code Analyzer", test_code_analyzer),
        ("Claude API", test_claude_api),
        ("Report Generator", test_report_generator),
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except KeyboardInterrupt:
            print("\n\nTests interrupted by user.")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error in {name}: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if all(results.values()):
        print("\n🎉 All component tests passed!")
        
        # Ask if user wants to run full integration test
        print("\nWould you like to run a full integration test?")
        print("This will analyze 1 real bug from Jira. (y/n): ", end='')
        
        try:
            response = input().strip().lower()
            if response == 'y':
                test_full_integration()
        except KeyboardInterrupt:
            print("\nSkipped.")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before running the full system.")
        sys.exit(1)


if __name__ == "__main__":
    main()
