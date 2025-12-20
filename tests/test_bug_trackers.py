"""Test script for bug tracker connectors (Jira, TFS, GitHub)."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import Config
from src.trackers.factory import UnifiedBugTracker, BugTrackerFactory


def test_jira_connector():
    """Test Jira connector."""
    print("\n" + "="*60)
    print("Testing JIRA Connector")
    print("="*60)
    
    try:
        from src.trackers.jira_client import JiraMCPServer
        
        jira = JiraMCPServer()
        print(f"✓ Connected to Jira: {Config.JIRA_URL}")
        
        # Fetch bugs
        bugs = jira.get_bugs(max_results=3)
        print(f"✓ Retrieved {len(bugs)} bugs\n")
        
        for bug in bugs:
            print(f"  {bug.key}: {bug.summary}")
            print(f"    Status: {bug.status}, Priority: {bug.priority}")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_tfs_connector():
    """Test TFS/Azure DevOps connector."""
    print("\n" + "="*60)
    print("Testing TFS/Azure DevOps Connector")
    print("="*60)
    
    try:
        from src.trackers.tfs_client import TfsMCPServer
        
        tfs = TfsMCPServer()
        print(f"✓ Connected to Azure DevOps: {Config.TFS_URL}/{Config.TFS_ORGANIZATION}")
        
        # Fetch bugs
        bugs = tfs.get_bugs(max_results=3)
        print(f"✓ Retrieved {len(bugs)} bugs\n")
        
        for bug in bugs:
            print(f"  #{bug.id}: {bug.title}")
            print(f"    State: {bug.state}, Priority: {bug.priority}, Severity: {bug.severity}")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_github_connector():
    """Test GitHub connector."""
    print("\n" + "="*60)
    print("Testing GitHub Connector")
    print("="*60)
    
    try:
        from src.trackers.github_client import GitHubMCPServer
        
        github = GitHubMCPServer()
        print(f"✓ Connected to GitHub: {Config.GITHUB_OWNER}/{Config.GITHUB_REPO}")
        
        # Fetch bugs
        bugs = github.get_bugs(max_results=3)
        print(f"✓ Retrieved {len(bugs)} bugs\n")
        
        for bug in bugs:
            print(f"  #{bug.number}: {bug.title}")
            print(f"    State: {bug.state}, Labels: {', '.join(bug.labels)}")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_unified_tracker():
    """Test unified bug tracker interface."""
    print("\n" + "="*60)
    print("Testing Unified Bug Tracker")
    print("="*60)
    
    try:
        tracker = UnifiedBugTracker()
        print(f"✓ Using tracker: {tracker.tracker_type}")
        
        # Fetch bugs
        bugs = tracker.get_bugs(max_results=3)
        print(f"✓ Retrieved {len(bugs)} bugs\n")
        
        for bug in bugs:
            identifier = tracker.get_bug_identifier(bug)
            summary = tracker.get_bug_summary(bug)
            print(f"  {identifier}: {summary}")
        
        # Test formatting
        if bugs:
            print("\n" + "-"*60)
            print("Sample bug description format:")
            print("-"*60)
            print(tracker.format_bug_description(bugs[0]))
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def main():
    """Main test function."""
    print("\n" + "="*70)
    print("BUG TRACKER CONNECTORS TEST")
    print("="*70)
    
    print(f"\nConfigured Bug Tracker: {Config.BUG_TRACKER}")
    
    results = {}
    
    # Test based on configured tracker
    if Config.BUG_TRACKER.lower() == "jira":
        results['jira'] = test_jira_connector()
    elif Config.BUG_TRACKER.lower() in ["tfs", "azuredevops"]:
        results['tfs'] = test_tfs_connector()
    elif Config.BUG_TRACKER.lower() == "github":
        results['github'] = test_github_connector()
    
    # Always test unified interface
    results['unified'] = test_unified_tracker()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check configuration and credentials.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
