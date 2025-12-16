"""Utility script for querying and managing log history."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import Config
from log_history_manager import LogHistoryManager
import json


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(title)
    print('='*60)


def main():
    """Main entry point for log history queries."""
    print("\n" + "="*60)
    print("Bug Analysis Log History Query Tool")
    print("="*60 + "\n")
    
    # Initialize log history manager
    try:
        log_manager = LogHistoryManager(
            opensearch_host=Config.OPENSEARCH_HOST,
            opensearch_port=Config.OPENSEARCH_PORT,
            index_name=Config.OPENSEARCH_INDEX,
            embedding_model=Config.EMBEDDING_MODEL
        )
        print("✓ Connected to OpenSearch\n")
    except Exception as e:
        print(f"❌ Failed to connect to OpenSearch: {e}")
        print("\nMake sure OpenSearch is running at http://localhost:9200/")
        return
    
    # Display menu
    while True:
        print("\nAvailable Commands:")
        print("  1. View statistics")
        print("  2. Search similar bugs")
        print("  3. Get bug history")
        print("  4. View recent analyses")
        print("  5. Find duplicate bugs")
        print("  6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            view_statistics(log_manager)
        elif choice == "2":
            search_similar_bugs(log_manager)
        elif choice == "3":
            get_bug_history(log_manager)
        elif choice == "4":
            view_recent_analyses(log_manager)
        elif choice == "5":
            find_duplicates(log_manager)
        elif choice == "6":
            print("\nGoodbye!")
            log_manager.close()
            break
        else:
            print("Invalid choice. Please try again.")


def view_statistics(log_manager: LogHistoryManager):
    """Display statistics about logged analyses."""
    print_section("Log Statistics")
    
    stats = log_manager.get_statistics()
    
    if stats:
        print(f"Total analyses: {stats.get('total_analyses', 0)}")
        print(f"Unique bugs analyzed: {stats.get('bugs_analyzed', 0)}")
        print(f"Total findings: {stats.get('total_findings', 0)}")
        print(f"Avg findings per bug: {stats.get('avg_findings_per_bug', 0)}")
        print(f"Recent errors: {stats.get('recent_errors', 0)}")
    else:
        print("No statistics available")


def search_similar_bugs(log_manager: LogHistoryManager):
    """Search for similar bugs using semantic search."""
    print_section("Search Similar Bugs")
    
    query = input("\nEnter bug description or symptoms: ").strip()
    if not query:
        print("No query provided")
        return
    
    limit = input("Number of results (default 10): ").strip()
    limit = int(limit) if limit.isdigit() else 10
    
    print(f"\nSearching for bugs similar to: '{query}'...\n")
    
    results = log_manager.search_similar_bugs(query, limit=limit)
    
    if not results:
        print("No similar bugs found")
        return
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Bug: {result.get('bug_id', 'Unknown')}")
        print(f"   Summary: {result.get('bug_summary', 'N/A')}")
        print(f"   Similarity Score: {result.get('score', 0):.4f}")
        print(f"   Status: {result.get('bug_status', 'N/A')}")
        print(f"   Priority: {result.get('bug_priority', 'N/A')}")
        print(f"   Findings: {result.get('total_findings', 0)}")
        print(f"   Timestamp: {result.get('timestamp', 'N/A')}")


def get_bug_history(log_manager: LogHistoryManager):
    """Get complete history for a specific bug."""
    print_section("Bug Analysis History")
    
    bug_id = input("\nEnter bug ID (e.g., ABC-123): ").strip()
    if not bug_id:
        print("No bug ID provided")
        return
    
    print(f"\nFetching history for {bug_id}...\n")
    
    history = log_manager.get_bug_history(bug_id)
    
    if not history:
        print(f"No history found for bug {bug_id}")
        return
    
    print(f"Found {len(history)} analysis record(s):\n")
    
    for i, record in enumerate(history, 1):
        print(f"\n{i}. Analysis at {record.get('timestamp', 'N/A')}")
        print(f"   Status: {record.get('bug_status', 'N/A')}")
        print(f"   Priority: {record.get('bug_priority', 'N/A')}")
        print(f"   Files analyzed: {len(record.get('files_analyzed', []))}")
        print(f"   Findings: {record.get('total_findings', 0)}")
        
        # Show first few findings
        findings = record.get('findings', [])
        if findings:
            print(f"   Top findings:")
            for j, finding in enumerate(findings[:3], 1):
                if isinstance(finding, dict):
                    print(f"     {j}. {finding.get('file', 'N/A')} - {finding.get('issue', 'N/A')[:50]}...")


def view_recent_analyses(log_manager: LogHistoryManager):
    """View most recent analyses."""
    print_section("Recent Analyses")
    
    limit = input("\nNumber of recent analyses to show (default 10): ").strip()
    limit = int(limit) if limit.isdigit() else 10
    
    print(f"\nFetching {limit} most recent analyses...\n")
    
    recent = log_manager.get_recent_analyses(limit=limit)
    
    if not recent:
        print("No analyses found")
        return
    
    for i, analysis in enumerate(recent, 1):
        print(f"\n{i}. Bug: {analysis.get('bug_id', 'Unknown')}")
        print(f"   Summary: {analysis.get('bug_summary', 'N/A')[:60]}...")
        print(f"   Status: {analysis.get('bug_status', 'N/A')}")
        print(f"   Priority: {analysis.get('bug_priority', 'N/A')}")
        print(f"   Findings: {analysis.get('total_findings', 0)}")
        print(f"   Timestamp: {analysis.get('timestamp', 'N/A')}")


def find_duplicates(log_manager: LogHistoryManager):
    """Find potential duplicate bugs."""
    print_section("Find Duplicate Bugs")
    
    bug_id = input("\nEnter bug ID to check for duplicates: ").strip()
    if not bug_id:
        print("No bug ID provided")
        return
    
    threshold = input("Similarity threshold (0-1, default 0.85): ").strip()
    try:
        threshold = float(threshold) if threshold else 0.85
    except ValueError:
        threshold = 0.85
    
    print(f"\nSearching for duplicates of {bug_id} (threshold: {threshold})...\n")
    
    # This requires fetching the bug first - for demo, we'll use a workaround
    print("Note: This feature requires the bug object. Use 'Search similar bugs' instead.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
