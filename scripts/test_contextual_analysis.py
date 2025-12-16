"""
Test script for contextual bug analysis feature.
Tests the integration of log history with bug analysis.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import Config
from log_history_manager import LogHistoryManager
from jira_mcp import JiraIssue
from datetime import datetime


def test_contextual_lookup():
    """Test searching for similar bugs in history."""
    print("="*60)
    print("Testing Contextual Analysis Feature")
    print("="*60)
    
    # Initialize log history manager
    print("\n1. Initializing Log History Manager...")
    try:
        log_manager = LogHistoryManager(
            opensearch_host=Config.OPENSEARCH_HOST,
            opensearch_port=Config.OPENSEARCH_PORT,
            index_name=Config.OPENSEARCH_INDEX,
            embedding_model=Config.EMBEDDING_MODEL
        )
        print("   ✓ Connected to OpenSearch")
    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}")
        return False
    
    # Test 1: Add a mock bug analysis to history
    print("\n2. Adding mock bug to history...")
    mock_bug = JiraIssue(
        key="TEST-001",
        summary="NullPointerException in user authentication",
        description="User login fails when email is null",
        issue_type="Bug",
        status="Done",
        priority="High",
        created="2025-12-01T10:00:00.000+0000",
        updated="2025-12-10T15:30:00.000+0000",
        labels=["backend", "authentication"]
    )
    
    mock_analysis = {
        "bug_key": "TEST-001",
        "status": "analyzed",
        "total_files_analyzed": 5,
        "findings": [
            {
                "file": "src/auth/UserService.java",
                "lines": "45-48",
                "issue": "Missing null check before accessing user.getEmail()",
                "severity": "High",
                "resolution": "Add null validation before property access",
                "code_fix": "if (user != null && user.getEmail() != null) { ... }"
            }
        ]
    }
    
    try:
        log_manager.log_analysis(
            bug=mock_bug,
            analysis_result=mock_analysis,
            files_analyzed=["UserService.java", "AuthController.java"],
            metadata={"test": True}
        )
        print("   ✓ Mock bug logged successfully")
    except Exception as e:
        print(f"   ✗ Failed to log: {e}")
        return False
    
    # Test 2: Search for similar bugs
    print("\n3. Searching for similar bugs...")
    test_queries = [
        "NullPointerException during authentication",
        "Login fails with null email",
        "User authentication error"
    ]
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        try:
            similar_bugs = log_manager.search_similar_bugs(
                query=query,
                limit=3,
                min_score=0.5  # Lower threshold for testing
            )
            
            if similar_bugs:
                print(f"   ✓ Found {len(similar_bugs)} similar bug(s)")
                for idx, bug in enumerate(similar_bugs, 1):
                    score = bug.get('score', 0)
                    bug_data = bug.get('bug', {})
                    print(f"      {idx}. {bug_data.get('key')} - {bug_data.get('summary')}")
                    print(f"         Similarity: {score:.2%}")
            else:
                print("   ℹ No similar bugs found")
        except Exception as e:
            print(f"   ✗ Search failed: {e}")
    
    # Test 3: Format historical context (like main.py does)
    print("\n4. Testing context formatting...")
    try:
        similar_bugs = log_manager.search_similar_bugs(
            query="authentication null pointer",
            limit=2,
            min_score=0.7
        )
        
        if similar_bugs:
            # This mimics the _format_historical_context method
            context_parts = ["\n=== HISTORICAL CONTEXT: Similar Bugs Previously Analyzed ==="]
            
            for idx, bug in enumerate(similar_bugs, 1):
                score = bug.get('score', 0)
                bug_data = bug.get('bug', {})
                analysis = bug.get('analysis_result', {})
                
                context_parts.append(f"\n--- Similar Bug #{idx} (Similarity: {score:.2%}) ---")
                context_parts.append(f"Bug ID: {bug_data.get('key', 'N/A')}")
                context_parts.append(f"Summary: {bug_data.get('summary', 'N/A')}")
                
                findings = analysis.get('findings', [])
                if findings:
                    context_parts.append(f"\nFindings:")
                    for f in findings[:1]:  # Show first finding
                        context_parts.append(f"  - File: {f.get('file')}")
                        context_parts.append(f"    Resolution: {f.get('resolution')}")
            
            context = "\n".join(context_parts)
            print("   ✓ Context formatted successfully")
            print("\n   Preview:")
            print("   " + "\n   ".join(context.split("\n")[:10]))
            print("   ...")
        else:
            print("   ℹ No bugs with similarity ≥70% found (this is normal for new systems)")
    except Exception as e:
        print(f"   ✗ Context formatting failed: {e}")
    
    # Test 4: Statistics
    print("\n5. Log History Statistics...")
    try:
        stats = log_manager.get_statistics()
        print(f"   Total logs: {stats.get('total_logs', 0)}")
        print(f"   Index: {stats.get('index_name', 'N/A')}")
        print(f"   Storage: {stats.get('index_size', 'N/A')}")
        print("   ✓ Statistics retrieved")
    except Exception as e:
        print(f"   ℹ Statistics unavailable: {e}")
    
    print("\n" + "="*60)
    print("Contextual Analysis Test Complete!")
    print("="*60)
    print("\nKey Points:")
    print("1. Log history stores all bug analyses with embeddings")
    print("2. When analyzing new bugs, system searches for similar ones")
    print("3. Claude receives historical context for consistent fixes")
    print("4. Minimum similarity threshold: 70% (configurable)")
    print("\nNext: Run 'python main.py' to see it in action!")
    print("="*60)
    
    return True


if __name__ == "__main__":
    success = test_contextual_lookup()
    sys.exit(0 if success else 1)
