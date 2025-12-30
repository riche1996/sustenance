"""
GitHub Service - Unified interface for all GitHub operations.

Usage:
    from src.services.github_service import github
    
    # Get issues
    result = github("get_issues", state="open", max_results=10)
    
    # Create an issue
    result = github("create_issue", title="Bug fix", body="Description here")
    
    # Get pull requests
    result = github("get_pull_requests", state="open")
    
    # Search code
    result = github("search_code", query="def main")
"""

from typing import Any, Dict, List, Optional, Union
from src.trackers.github_client import GitHubMCPServer, GitHubIssue

# Singleton instance
_client: Optional[GitHubMCPServer] = None


def _get_client() -> GitHubMCPServer:
    """Get or create the GitHub client instance."""
    global _client
    if _client is None:
        _client = GitHubMCPServer()
    return _client


def github(action: str, **kwargs) -> Union[Dict, List, bool, str, None]:
    """
    Unified function to access all GitHub capabilities.
    
    Args:
        action: The GitHub action to perform (see available actions below)
        **kwargs: Arguments specific to each action
        
    Returns:
        Result of the action (varies by action type)
        
    Available Actions:
    
    ISSUES:
        - get_issues: Get repository issues
            params: owner, repo, state, labels, max_results
        - get_bugs: Get issues with bug label
            params: owner, repo, state, labels, max_results
        - get_issue: Get specific issue by number
            params: issue_number, owner, repo
        - create_issue: Create a new issue
            params: title, body, labels, assignees, milestone, owner, repo
        - update_issue: Update an existing issue
            params: issue_number, title, body, state, labels, owner, repo
        - search_issues: Search issues with filters
            params: query, author, assignee, labels, state, sort, order
        - add_comment: Add comment to an issue
            params: issue_number, comment, owner, repo
        - add_labels: Add labels to an issue
            params: issue_number, labels, owner, repo
        - remove_labels: Remove labels from an issue
            params: issue_number, labels, owner, repo
        - assign_issue: Assign users to an issue
            params: issue_number, assignees, owner, repo
        - update_issue_state: Update issue state (open/closed)
            params: issue_number, state, owner, repo
            
    PULL REQUESTS:
        - get_pull_requests: Get repository PRs
            params: state, sort, direction, owner, repo
        - get_pull_request: Get specific PR
            params: pr_number, owner, repo
        - create_pull_request: Create a new PR
            params: title, body, head, base, draft, owner, repo
        - merge_pull_request: Merge a PR
            params: pr_number, merge_method, commit_message, owner, repo
        - create_review: Add review to a PR
            params: pr_number, event, body, owner, repo
        - get_pull_request_diff: Get PR diff
            params: pr_number, owner, repo
        - get_pull_request_files: Get files changed in PR
            params: pr_number, owner, repo
            
    LABELS:
        - get_labels: Get all repository labels
            params: owner, repo
        - create_label: Create a new label
            params: name, color, description, owner, repo
        - update_label: Update a label
            params: name, new_name, color, description, owner, repo
        - delete_label: Delete a label
            params: name, owner, repo
            
    MILESTONES:
        - get_milestones: Get all milestones
            params: state, owner, repo
        - create_milestone: Create a milestone
            params: title, description, due_date, state, owner, repo
        - update_milestone: Update a milestone
            params: number, title, description, due_date, state, owner, repo
        - assign_milestone: Assign milestone to issue
            params: issue_number, milestone_number, owner, repo
            
    REPOSITORY:
        - get_repository_info: Get repo information
            params: owner, repo
        - get_contributors: Get repo contributors
            params: max_results, owner, repo
        - get_commits: Get commit history
            params: branch, max_results, author, owner, repo
        - get_file_contents: Get file content
            params: path, branch, owner, repo
        - search_code: Search code in repo
            params: query, path, language
            
    BRANCHES:
        - create_branch: Create a new branch
            params: branch_name, from_branch, owner, repo
        - delete_branch: Delete a branch
            params: branch_name, owner, repo
        - compare_branches: Compare two branches
            params: base, head, owner, repo
            
    COLLABORATORS:
        - get_collaborators: Get repo collaborators
            params: owner, repo
        - add_collaborator: Add a collaborator
            params: username, permission, owner, repo
        - remove_collaborator: Remove a collaborator
            params: username, owner, repo
            
    RELEASES & TAGS:
        - get_releases: Get all releases
            params: max_results, owner, repo
        - get_release_by_tag: Get release by tag
            params: tag, owner, repo
        - create_release: Create a release
            params: tag, name, body, draft, prerelease, target, owner, repo
        - get_tags: Get all tags
            params: max_results, owner, repo
        - create_tag: Create a tag
            params: tag, sha, message, owner, repo
            
    Examples:
        >>> github("get_issues", state="open", max_results=5)
        >>> github("create_issue", title="New bug", body="Description")
        >>> github("get_pull_requests", state="all")
        >>> github("search_code", query="def authenticate")
        >>> github("create_branch", branch_name="feature/new-feature")
    """
    client = _get_client()
    
    # Map actions to methods
    action_map = {
        # Issues
        "get_issues": client.get_issues,
        "get_bugs": client.get_bugs,
        "get_issue": client.get_issue,
        "create_issue": client.create_issue,
        "update_issue": client.update_issue,
        "search_issues": client.search_issues,
        "add_comment": client.add_comment,
        "add_labels": client.add_labels,
        "remove_labels": client.remove_labels,
        "assign_issue": client.assign_issue,
        "update_issue_state": client.update_issue_state,
        
        # Pull Requests
        "get_pull_requests": client.get_pull_requests,
        "get_prs": client.get_pull_requests,  # Alias
        "get_pull_request": client.get_pull_request,
        "get_pr": client.get_pull_request,  # Alias
        "create_pull_request": client.create_pull_request,
        "create_pr": client.create_pull_request,  # Alias
        "merge_pull_request": client.merge_pull_request,
        "merge_pr": client.merge_pull_request,  # Alias
        "create_review": client.create_review,
        "get_pull_request_diff": client.get_pull_request_diff,
        "get_pr_diff": client.get_pull_request_diff,  # Alias
        "get_pull_request_files": client.get_pull_request_files,
        "get_pr_files": client.get_pull_request_files,  # Alias
        
        # Labels
        "get_labels": client.get_labels,
        "create_label": client.create_label,
        "update_label": client.update_label,
        "delete_label": client.delete_label,
        
        # Milestones
        "get_milestones": client.get_milestones,
        "create_milestone": client.create_milestone,
        "update_milestone": client.update_milestone,
        "assign_milestone": client.assign_milestone_to_issue,
        
        # Repository
        "get_repository_info": client.get_repository_info,
        "get_repo_info": client.get_repository_info,  # Alias
        "get_contributors": client.get_contributors,
        "get_commits": client.get_commits,
        "get_file_contents": client.get_file_contents,
        "get_file": client.get_file_contents,  # Alias
        "search_code": client.search_code,
        
        # Branches
        "create_branch": client.create_branch,
        "delete_branch": client.delete_branch,
        "compare_branches": client.compare_branches,
        
        # Collaborators
        "get_collaborators": client.get_collaborators,
        "add_collaborator": client.add_collaborator,
        "remove_collaborator": client.remove_collaborator,
        
        # Releases & Tags
        "get_releases": client.get_releases,
        "get_release_by_tag": client.get_release_by_tag,
        "create_release": client.create_release,
        "get_tags": client.get_tags,
        "create_tag": client.create_tag,
    }
    
    if action not in action_map:
        available = ", ".join(sorted(set(action_map.keys())))
        raise ValueError(f"Unknown action: '{action}'. Available actions: {available}")
    
    try:
        return action_map[action](**kwargs)
    except TypeError as e:
        raise TypeError(f"Invalid arguments for action '{action}': {e}")


def list_actions() -> List[str]:
    """Return list of all available GitHub actions."""
    return [
        # Issues
        "get_issues", "get_bugs", "get_issue", "create_issue", "update_issue",
        "search_issues", "add_comment", "add_labels", "remove_labels",
        "assign_issue", "update_issue_state",
        # Pull Requests
        "get_pull_requests", "get_pull_request", "create_pull_request",
        "merge_pull_request", "create_review", "get_pull_request_diff",
        "get_pull_request_files",
        # Labels
        "get_labels", "create_label", "update_label", "delete_label",
        # Milestones
        "get_milestones", "create_milestone", "update_milestone", "assign_milestone",
        # Repository
        "get_repository_info", "get_contributors", "get_commits",
        "get_file_contents", "search_code",
        # Branches
        "create_branch", "delete_branch", "compare_branches",
        # Collaborators
        "get_collaborators", "add_collaborator", "remove_collaborator",
        # Releases & Tags
        "get_releases", "get_release_by_tag", "create_release",
        "get_tags", "create_tag",
    ]


def help(action: str = None) -> str:
    """
    Get help for GitHub actions.
    
    Args:
        action: Specific action to get help for, or None for general help
        
    Returns:
        Help text
    """
    if action is None:
        return github.__doc__
    
    action_help = {
        "get_issues": "Get repository issues.\nParams: owner, repo, state('open'|'closed'|'all'), labels, max_results",
        "get_bugs": "Get issues with bug label.\nParams: owner, repo, state, labels, max_results",
        "get_issue": "Get specific issue by number.\nParams: issue_number (required), owner, repo",
        "create_issue": "Create a new issue.\nParams: title (required), body, labels, assignees, milestone, owner, repo",
        "update_issue": "Update an issue.\nParams: issue_number (required), title, body, state, labels, owner, repo",
        "search_issues": "Search issues.\nParams: query (required), author, assignee, labels, state, sort, order",
        "add_comment": "Add comment to issue.\nParams: issue_number (required), comment (required), owner, repo",
        "add_labels": "Add labels to issue.\nParams: issue_number (required), labels (required), owner, repo",
        "remove_labels": "Remove labels from issue.\nParams: issue_number (required), labels (required), owner, repo",
        "assign_issue": "Assign users to issue.\nParams: issue_number (required), assignees (required), owner, repo",
        "update_issue_state": "Update issue state.\nParams: issue_number (required), state('open'|'closed') (required), owner, repo",
        
        "get_pull_requests": "Get repository PRs.\nParams: state, sort, direction, owner, repo",
        "get_pull_request": "Get specific PR.\nParams: pr_number (required), owner, repo",
        "create_pull_request": "Create a PR.\nParams: title (required), body (required), head (required), base, draft, owner, repo",
        "merge_pull_request": "Merge a PR.\nParams: pr_number (required), merge_method, commit_message, owner, repo",
        "create_review": "Add review to PR.\nParams: pr_number (required), event (required), body, owner, repo",
        "get_pull_request_diff": "Get PR diff.\nParams: pr_number (required), owner, repo",
        "get_pull_request_files": "Get PR changed files.\nParams: pr_number (required), owner, repo",
        
        "get_labels": "Get all labels.\nParams: owner, repo",
        "create_label": "Create label.\nParams: name (required), color (required), description, owner, repo",
        "update_label": "Update label.\nParams: name (required), new_name, color, description, owner, repo",
        "delete_label": "Delete label.\nParams: name (required), owner, repo",
        
        "get_milestones": "Get milestones.\nParams: state, owner, repo",
        "create_milestone": "Create milestone.\nParams: title (required), description, due_date, state, owner, repo",
        "update_milestone": "Update milestone.\nParams: number (required), title, description, due_date, state, owner, repo",
        "assign_milestone": "Assign milestone to issue.\nParams: issue_number (required), milestone_number (required), owner, repo",
        
        "get_repository_info": "Get repo info.\nParams: owner, repo",
        "get_contributors": "Get contributors.\nParams: max_results, owner, repo",
        "get_commits": "Get commits.\nParams: branch, max_results, author, owner, repo",
        "get_file_contents": "Get file content.\nParams: path (required), branch, owner, repo",
        "search_code": "Search code.\nParams: query (required), path, language",
        
        "create_branch": "Create branch.\nParams: branch_name (required), from_branch, owner, repo",
        "delete_branch": "Delete branch.\nParams: branch_name (required), owner, repo",
        "compare_branches": "Compare branches.\nParams: base (required), head (required), owner, repo",
        
        "get_collaborators": "Get collaborators.\nParams: owner, repo",
        "add_collaborator": "Add collaborator.\nParams: username (required), permission, owner, repo",
        "remove_collaborator": "Remove collaborator.\nParams: username (required), owner, repo",
        
        "get_releases": "Get releases.\nParams: max_results, owner, repo",
        "get_release_by_tag": "Get release by tag.\nParams: tag (required), owner, repo",
        "create_release": "Create release.\nParams: tag (required), name (required), body, draft, prerelease, target, owner, repo",
        "get_tags": "Get tags.\nParams: max_results, owner, repo",
        "create_tag": "Create tag.\nParams: tag (required), sha (required), message, owner, repo",
    }
    
    if action in action_help:
        return action_help[action]
    
    return f"No help available for action: {action}"


# Quick access functions for common operations
def get_issues(state: str = "open", max_results: int = 100, **kwargs) -> List[GitHubIssue]:
    """Quick access to get issues."""
    return github("get_issues", state=state, max_results=max_results, **kwargs)


def get_issue(issue_number: int, **kwargs) -> GitHubIssue:
    """Quick access to get a specific issue."""
    return github("get_issue", issue_number=issue_number, **kwargs)


def create_issue(title: str, body: str = "", **kwargs):
    """Quick access to create an issue."""
    return github("create_issue", title=title, body=body, **kwargs)


def get_prs(state: str = "open", **kwargs) -> List:
    """Quick access to get pull requests."""
    return github("get_pull_requests", state=state, **kwargs)


def search(query: str, **kwargs) -> List:
    """Quick access to search issues."""
    return github("search_issues", query=query, **kwargs)


def search_code(query: str, **kwargs) -> List[Dict]:
    """Quick access to search code."""
    return github("search_code", query=query, **kwargs)


if __name__ == "__main__":
    # Test the function
    print("Available GitHub Actions:")
    print("-" * 40)
    for action in list_actions():
        print(f"  - {action}")
    
    print("\n\nExample Usage:")
    print("-" * 40)
    print('github("get_issues", state="open", max_results=5)')
    print('github("create_issue", title="Bug", body="Description")')
    print('github("search_code", query="def main")')
