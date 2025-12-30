#!/usr/bin/env python
"""
Script to sync GitHub issues to OpenSearch for indexing and search.

Usage:
    python scripts/sync_github_issues.py [--state STATE] [--max MAX] [--embeddings]

Examples:
    # Sync all issues (default)
    python scripts/sync_github_issues.py
    
    # Sync only closed issues
    python scripts/sync_github_issues.py --state closed
    
    # Sync up to 1000 issues with embeddings
    python scripts/sync_github_issues.py --max 1000 --embeddings
"""
import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.trackers.github_client import GitHubMCPServer
from src.services.github_opensearch_sync import (
    GitHubOpenSearchSync, 
    sync_github_issues_to_opensearch
)


def main():
    parser = argparse.ArgumentParser(
        description='Sync GitHub issues to OpenSearch'
    )
    parser.add_argument(
        '--state', 
        choices=['open', 'closed', 'all'],
        default='all',
        help='Issue state filter (default: all)'
    )
    parser.add_argument(
        '--max', 
        type=int,
        default=500,
        help='Maximum number of issues to sync (default: 500)'
    )
    parser.add_argument(
        '--no-embeddings',
        action='store_true',
        help='Disable embeddings (embeddings are enabled by default)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-index existing issues (skip duplicate check)'
    )
    parser.add_argument(
        '--owner',
        type=str,
        default=None,
        help='Repository owner (default: from config)'
    )
    parser.add_argument(
        '--repo',
        type=str,
        default=None,
        help='Repository name (default: from config)'
    )
    parser.add_argument(
        '--opensearch-host',
        type=str,
        default=None,
        help='OpenSearch host (default: from config)'
    )
    parser.add_argument(
        '--opensearch-port',
        type=int,
        default=None,
        help='OpenSearch port (default: from config)'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Only show current index statistics, no sync'
    )
    parser.add_argument(
        '--search',
        type=str,
        default=None,
        help='Search indexed issues with query'
    )
    parser.add_argument(
        '--delete-repo',
        action='store_true',
        help='Delete all issues for the specified repository from index'
    )
    
    args = parser.parse_args()
    
    # Get configuration
    opensearch_host = args.opensearch_host or Config.OPENSEARCH_HOST
    opensearch_port = args.opensearch_port or Config.OPENSEARCH_PORT
    owner = args.owner or Config.GITHUB_OWNER
    repo = args.repo or Config.GITHUB_REPO
    
    print(f"\n🔧 Configuration:")
    print(f"   OpenSearch: {opensearch_host}:{opensearch_port}")
    print(f"   Repository: {owner}/{repo}")
    print()
    
    # Initialize sync service for stats/search/delete operations (no embeddings needed)
    if args.stats_only or args.search or args.delete_repo:
        sync_service = GitHubOpenSearchSync(
            host=opensearch_host,
            port=opensearch_port,
            enable_embeddings=False  # Don't need embeddings for these operations
        )
        
        if not sync_service.is_connected():
            print("❌ Failed to connect to OpenSearch")
            print("   Please ensure OpenSearch is running on", f"{opensearch_host}:{opensearch_port}")
            return 1
        
        if args.stats_only:
            print("📊 Index Statistics:")
            stats = sync_service.get_issues_stats(owner=owner, repo=repo)
            if 'error' in stats:
                print(f"   Error: {stats['error']}")
            else:
                print(f"   Total issues: {stats.get('total_issues', 0)}")
                print(f"   By state: {stats.get('by_state', {})}")
                print(f"   By repository: {stats.get('by_repository', {})}")
                print(f"   Top labels: {list(stats.get('top_labels', {}).keys())[:10]}")
                print(f"   Latest sync: {stats.get('latest_sync', 'N/A')}")
            
            sync_service.close()
            return 0
        
        if args.search:
            print(f"🔍 Searching for: {args.search}")
            results = sync_service.search_issues(
                query=args.search,
                owner=owner,
                repo=repo,
                size=20
            )
            
            if not results:
                print("   No results found")
            else:
                print(f"   Found {len(results)} issues:\n")
                for i, issue in enumerate(results, 1):
                    state_icon = "🟢" if issue['state'] == 'open' else "🔴"
                    labels = ', '.join(issue.get('labels', [])[:3])
                    print(f"   {i}. {state_icon} #{issue['number']}: {issue['title']}")
                    print(f"      Labels: {labels or 'none'}")
                    print(f"      Score: {issue.get('_score', 0):.2f}")
                    print(f"      URL: {issue['html_url']}")
                    print()
            
            sync_service.close()
            return 0
        
        if args.delete_repo:
            print(f"🗑️ Deleting issues for {owner}/{repo}...")
            result = sync_service.delete_repository_issues(owner, repo)
            if 'error' in result:
                print(f"   Error: {result['error']}")
            else:
                print(f"   Deleted {result['deleted']} issues")
            
            sync_service.close()
            return 0
    
    # Full sync operation
    try:
        # Initialize GitHub client
        print("🔌 Connecting to GitHub...")
        github_client = GitHubMCPServer()
        
        # Run sync (embeddings enabled by default)
        result = sync_github_issues_to_opensearch(
            github_client=github_client,
            opensearch_host=opensearch_host,
            opensearch_port=opensearch_port,
            owner=owner,
            repo=repo,
            state=args.state,
            max_issues=args.max,
            enable_embeddings=not args.no_embeddings,
            skip_duplicates=not args.force
        )
        
        if result.get('success'):
            print("✅ Sync completed successfully!")
            return 0
        else:
            print(f"❌ Sync failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
