"""
GitHub All-In-One Function
===========================
A single comprehensive function to perform all GitHub capabilities.
This script provides a unified interface to all GitHub operations without modifying existing code.

Usage:
    from scripts.github_all_in_one import github_action
    
    # Examples:
    result = github_action("get_issues", state="open", max_results=10)
    result = github_action("create_issue", title="Bug Report", body="Description", labels=["bug"])
    result = github_action("get_pull_requests", state="open")
"""

import os
import sys
import time
import base64
import requests
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class GitHubConfig:
    """Configuration for GitHub API."""
    token: str = ""
    owner: str = ""
    repo: str = ""
    base_url: str = "https://api.github.com"
    
    def __post_init__(self):
        """Load from environment if not provided."""
        if not self.token:
            self.token = os.getenv("GITHUB_TOKEN", "")
        if not self.owner:
            self.owner = os.getenv("GITHUB_OWNER", "")
        if not self.repo:
            self.repo = os.getenv("GITHUB_REPO", "")


@dataclass
class ActionResult:
    """Standard result object for all GitHub actions."""
    success: bool
    action: str
    data: Any = None
    message: str = ""
    error: str = ""
    metadata: Dict = field(default_factory=dict)


def github_action(
    action: str,
    # Common parameters
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    # Issue parameters
    issue_number: Optional[int] = None,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: Optional[str] = None,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
    milestone: Optional[int] = None,
    comment: Optional[str] = None,
    # Search parameters
    query: Optional[str] = None,
    author: Optional[str] = None,
    assignee: Optional[str] = None,
    sort: Optional[str] = None,
    order: Optional[str] = None,
    # PR parameters
    pr_number: Optional[int] = None,
    head: Optional[str] = None,
    base: Optional[str] = None,
    draft: Optional[bool] = None,
    merge_method: Optional[str] = None,
    commit_message: Optional[str] = None,
    event: Optional[str] = None,
    # Label parameters
    name: Optional[str] = None,
    new_name: Optional[str] = None,
    color: Optional[str] = None,
    description: Optional[str] = None,
    # Branch parameters
    branch_name: Optional[str] = None,
    branch: Optional[str] = None,
    from_branch: Optional[str] = None,
    # File parameters
    path: Optional[str] = None,
    language: Optional[str] = None,
    # Collaborator parameters
    username: Optional[str] = None,
    permission: Optional[str] = None,
    # Release/Tag parameters
    tag: Optional[str] = None,
    sha: Optional[str] = None,
    prerelease: Optional[bool] = None,
    target: Optional[str] = None,
    # Milestone parameters
    due_date: Optional[str] = None,
    milestone_number: Optional[int] = None,
    # General parameters
    max_results: int = 50,
    direction: Optional[str] = None,
    # Configuration
    config: Optional[GitHubConfig] = None,
    **kwargs
) -> ActionResult:
    """
    Unified GitHub action function that performs all GitHub capabilities.
    All helper functions are encapsulated inside this single function.
    
    SUPPORTED ACTIONS:
    
    === ISSUE MANAGEMENT ===
    - get_issues          : Retrieve issues with filtering
    - get_bugs            : Get issues with 'bug' label
    - get_issue           : Get specific issue details
    - create_issue        : Create a new issue
    - update_issue        : Update an existing issue
    - add_comment         : Add comment to an issue
    - update_issue_state  : Change issue state (open/closed)
    - add_labels          : Add labels to an issue
    - remove_labels       : Remove labels from an issue
    - assign_issue        : Assign users to an issue
    - search_issues       : Search issues with advanced filters
    
    === PULL REQUEST MANAGEMENT ===
    - get_pull_requests   : List pull requests
    - get_pull_request    : Get specific PR details
    - create_pull_request : Create a new PR
    - merge_pull_request  : Merge a PR
    - create_review       : Add review to PR
    - get_pr_diff         : Get PR diff
    - get_pr_files        : Get files changed in PR
    
    === LABEL MANAGEMENT ===
    - get_labels          : List all labels
    - create_label        : Create a new label
    - update_label        : Update existing label
    - delete_label        : Delete a label
    
    === MILESTONE MANAGEMENT ===
    - get_milestones      : List milestones
    - create_milestone    : Create a milestone
    - update_milestone    : Update a milestone
    - assign_milestone    : Assign milestone to issue
    
    === REPOSITORY INFO ===
    - get_repo_info       : Get repository information
    - get_contributors    : List contributors
    - get_commits         : Get commit history
    - get_file_content    : Read file from repo
    - search_code         : Search code in repo
    
    === BRANCH MANAGEMENT ===
    - get_branches        : List all branches
    - create_branch       : Create a new branch
    - delete_branch       : Delete a branch
    - compare_branches    : Compare two branches
    
    === COLLABORATOR MANAGEMENT ===
    - get_collaborators   : List collaborators
    - add_collaborator    : Add collaborator
    - remove_collaborator : Remove collaborator
    
    === RELEASE & TAG MANAGEMENT ===
    - get_releases        : List releases
    - get_release         : Get release by tag
    - create_release      : Create a release
    - get_tags            : List tags
    - create_tag          : Create a tag
    
    Args:
        action: The action to perform (see list above)
        owner: Repository owner (uses config default if not provided)
        repo: Repository name (uses config default if not provided)
        ... (see parameter list above for action-specific parameters)
        config: GitHubConfig object (optional, creates default if not provided)
    
    Returns:
        ActionResult object with success status, data, and any error messages
    
    Examples:
        # Get open issues
        result = github_action("get_issues", state="open", max_results=10)
        
        # Create an issue
        result = github_action("create_issue", title="Bug", body="Details", labels=["bug"])
        
        # Merge a PR
        result = github_action("merge_pull_request", pr_number=123, merge_method="squash")
        
        # Create a branch
        result = github_action("create_branch", branch_name="feature-x", from_branch="main")
    """
    
    # ==================== HELPER FUNCTIONS (ALL NESTED INSIDE) ====================
    
    def parse_issue(issue_data: Dict) -> Dict:
        """Parse issue data into a standardized dict."""
        return {
            "number": issue_data.get("number"),
            "title": issue_data.get("title"),
            "body": issue_data.get("body"),
            "state": issue_data.get("state"),
            "labels": [l.get("name") for l in issue_data.get("labels", [])],
            "assignee": issue_data.get("assignee", {}).get("login") if issue_data.get("assignee") else None,
            "assignees": [a.get("login") for a in issue_data.get("assignees", [])],
            "created_by": issue_data.get("user", {}).get("login") if issue_data.get("user") else None,
            "created_at": issue_data.get("created_at"),
            "updated_at": issue_data.get("updated_at"),
            "closed_at": issue_data.get("closed_at"),
            "milestone": issue_data.get("milestone", {}).get("title") if issue_data.get("milestone") else None,
            "html_url": issue_data.get("html_url")
        }

    def parse_pr(pr_data: Dict) -> Dict:
        """Parse PR data into a standardized dict."""
        return {
            "number": pr_data.get("number"),
            "title": pr_data.get("title"),
            "body": pr_data.get("body"),
            "state": pr_data.get("state"),
            "user": pr_data.get("user", {}).get("login") if pr_data.get("user") else None,
            "head": pr_data.get("head", {}).get("ref") if pr_data.get("head") else None,
            "base": pr_data.get("base", {}).get("ref") if pr_data.get("base") else None,
            "mergeable": pr_data.get("mergeable"),
            "merged": pr_data.get("merged", False),
            "draft": pr_data.get("draft", False),
            "created_at": pr_data.get("created_at"),
            "updated_at": pr_data.get("updated_at"),
            "html_url": pr_data.get("html_url")
        }

    # ==================== ISSUE FUNCTIONS ====================

    def get_issues_impl(base_url, headers, owner, repo, state, labels, max_results):
        all_issues = []
        page = 1
        per_page = min(100, max_results)
        
        while len(all_issues) < max_results:
            params = {
                'state': state,
                'per_page': per_page,
                'page': page,
                'sort': 'created',
                'direction': 'desc'
            }
            if labels:
                params['labels'] = ','.join(labels)
            
            url = f"{base_url}/repos/{owner}/{repo}/issues"
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 403:
                remaining = response.headers.get('X-RateLimit-Remaining', '0')
                if remaining == '0':
                    break
            
            response.raise_for_status()
            issues_data = response.json()
            
            if not issues_data:
                break
            
            for issue in issues_data:
                if 'pull_request' in issue:
                    continue
                all_issues.append(parse_issue(issue))
                if len(all_issues) >= max_results:
                    break
            
            if len(issues_data) < per_page:
                break
            page += 1
        
        return ActionResult(True, "get_issues", data=all_issues, message=f"Retrieved {len(all_issues)} issues")

    def get_issue_impl(base_url, headers, owner, repo, issue_number):
        url = f"{base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "get_issue", data=parse_issue(response.json()))

    def create_issue_impl(base_url, headers, owner, repo, title, body, labels, assignees, milestone):
        url = f"{base_url}/repos/{owner}/{repo}/issues"
        data = {"title": title, "body": body}
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees
        if milestone:
            data["milestone"] = milestone
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        issue = parse_issue(response.json())
        return ActionResult(True, "create_issue", data=issue, message=f"Created issue #{issue['number']}")

    def update_issue_impl(base_url, headers, owner, repo, issue_number, title, body, state, labels):
        url = f"{base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        data = {}
        if title:
            data["title"] = title
        if body:
            data["body"] = body
        if state:
            data["state"] = state
        if labels:
            data["labels"] = labels
        
        response = requests.patch(url, json=data, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "update_issue", data=parse_issue(response.json()), message=f"Updated issue #{issue_number}")

    def add_comment_impl(base_url, headers, owner, repo, issue_number, comment):
        url = f"{base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        response = requests.post(url, json={"body": comment}, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "add_comment", message=f"Added comment to issue #{issue_number}")

    def update_issue_state_impl(base_url, headers, owner, repo, issue_number, state):
        if state not in ['open', 'closed']:
            return ActionResult(False, "update_issue_state", error="State must be 'open' or 'closed'")
        
        url = f"{base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        response = requests.patch(url, json={"state": state}, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "update_issue_state", message=f"Issue #{issue_number} state changed to {state}")

    def add_labels_impl(base_url, headers, owner, repo, issue_number, labels):
        url = f"{base_url}/repos/{owner}/{repo}/issues/{issue_number}/labels"
        response = requests.post(url, json={"labels": labels}, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "add_labels", message=f"Added labels to issue #{issue_number}")

    def remove_labels_impl(base_url, headers, owner, repo, issue_number, labels):
        for label in labels:
            url = f"{base_url}/repos/{owner}/{repo}/issues/{issue_number}/labels/{label}"
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
        return ActionResult(True, "remove_labels", message=f"Removed labels from issue #{issue_number}")

    def assign_issue_impl(base_url, headers, owner, repo, issue_number, assignees):
        url = f"{base_url}/repos/{owner}/{repo}/issues/{issue_number}/assignees"
        response = requests.post(url, json={"assignees": assignees}, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "assign_issue", message=f"Assigned users to issue #{issue_number}")

    def search_issues_impl(base_url, headers, owner, repo, query, author, assignee, labels, state, sort, order):
        search_query = f"repo:{owner}/{repo} {query}"
        if author:
            search_query += f" author:{author}"
        if assignee:
            search_query += f" assignee:{assignee}"
        if labels:
            for label in labels:
                search_query += f' label:"{label}"'
        if state != "all":
            search_query += f" state:{state}"
        
        url = f"{base_url}/search/issues"
        params = {"q": search_query, "sort": sort, "order": order}
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        issues = [parse_issue(item) for item in data.get('items', [])]
        return ActionResult(True, "search_issues", data=issues, message=f"Found {len(issues)} matching issues")

    # ==================== PULL REQUEST FUNCTIONS ====================

    def get_pull_requests_impl(base_url, headers, owner, repo, state, sort, direction, max_results):
        url = f"{base_url}/repos/{owner}/{repo}/pulls"
        params = {"state": state, "sort": sort, "direction": direction, "per_page": min(max_results, 100)}
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        prs = [parse_pr(pr) for pr in response.json()]
        return ActionResult(True, "get_pull_requests", data=prs, message=f"Retrieved {len(prs)} pull requests")

    def get_pull_request_impl(base_url, headers, owner, repo, pr_number):
        url = f"{base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "get_pull_request", data=parse_pr(response.json()))

    def create_pull_request_impl(base_url, headers, owner, repo, title, body, head, base, draft):
        url = f"{base_url}/repos/{owner}/{repo}/pulls"
        data = {"title": title, "body": body, "head": head, "base": base, "draft": draft}
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        pr = parse_pr(response.json())
        return ActionResult(True, "create_pull_request", data=pr, message=f"Created PR #{pr['number']}")

    def merge_pull_request_impl(base_url, headers, owner, repo, pr_number, merge_method, commit_message):
        url = f"{base_url}/repos/{owner}/{repo}/pulls/{pr_number}/merge"
        data = {"merge_method": merge_method}
        if commit_message:
            data["commit_message"] = commit_message
        
        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "merge_pull_request", message=f"Merged PR #{pr_number}")

    def create_review_impl(base_url, headers, owner, repo, pr_number, event, body):
        url = f"{base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        data = {"event": event, "body": body}
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "create_review", message=f"Added review to PR #{pr_number}")

    def get_pr_diff_impl(base_url, headers, owner, repo, pr_number):
        url = f"{base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        diff_headers = {**headers, 'Accept': 'application/vnd.github.v3.diff'}
        
        response = requests.get(url, headers=diff_headers)
        response.raise_for_status()
        return ActionResult(True, "get_pr_diff", data=response.text)

    def get_pr_files_impl(base_url, headers, owner, repo, pr_number):
        url = f"{base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        files = [{
            "filename": f.get("filename"),
            "status": f.get("status"),
            "additions": f.get("additions"),
            "deletions": f.get("deletions"),
            "changes": f.get("changes")
        } for f in response.json()]
        
        return ActionResult(True, "get_pr_files", data=files, message=f"Found {len(files)} changed files")

    # ==================== LABEL FUNCTIONS ====================

    def get_labels_impl(base_url, headers, owner, repo):
        url = f"{base_url}/repos/{owner}/{repo}/labels"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        labels_list = [{
            "name": l.get("name"),
            "color": l.get("color"),
            "description": l.get("description")
        } for l in response.json()]
        
        return ActionResult(True, "get_labels", data=labels_list, message=f"Found {len(labels_list)} labels")

    def create_label_impl(base_url, headers, owner, repo, name, color, description):
        url = f"{base_url}/repos/{owner}/{repo}/labels"
        data = {"name": name, "color": color.lstrip('#'), "description": description}
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        label = response.json()
        return ActionResult(True, "create_label", data={
            "name": label.get("name"),
            "color": label.get("color"),
            "description": label.get("description")
        }, message=f"Created label '{name}'")

    def update_label_impl(base_url, headers, owner, repo, name, new_name, color, description):
        url = f"{base_url}/repos/{owner}/{repo}/labels/{name}"
        data = {}
        if new_name:
            data["new_name"] = new_name
        if color:
            data["color"] = color.lstrip('#')
        if description:
            data["description"] = description
        
        response = requests.patch(url, json=data, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "update_label", message=f"Updated label '{name}'")

    def delete_label_impl(base_url, headers, owner, repo, name):
        url = f"{base_url}/repos/{owner}/{repo}/labels/{name}"
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "delete_label", message=f"Deleted label '{name}'")

    # ==================== MILESTONE FUNCTIONS ====================

    def get_milestones_impl(base_url, headers, owner, repo, state):
        url = f"{base_url}/repos/{owner}/{repo}/milestones"
        params = {"state": state}
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        milestones = [{
            "number": m.get("number"),
            "title": m.get("title"),
            "description": m.get("description"),
            "state": m.get("state"),
            "due_on": m.get("due_on")
        } for m in response.json()]
        
        return ActionResult(True, "get_milestones", data=milestones, message=f"Found {len(milestones)} milestones")

    def create_milestone_impl(base_url, headers, owner, repo, title, description, due_date, state):
        url = f"{base_url}/repos/{owner}/{repo}/milestones"
        data = {"title": title, "state": state}
        if description:
            data["description"] = description
        if due_date:
            data["due_on"] = due_date
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        m = response.json()
        return ActionResult(True, "create_milestone", data={
            "number": m.get("number"),
            "title": m.get("title"),
            "description": m.get("description"),
            "state": m.get("state")
        }, message=f"Created milestone '{title}'")

    def update_milestone_impl(base_url, headers, owner, repo, number, title, description, due_date, state):
        url = f"{base_url}/repos/{owner}/{repo}/milestones/{number}"
        data = {}
        if title:
            data["title"] = title
        if description:
            data["description"] = description
        if due_date:
            data["due_on"] = due_date
        if state:
            data["state"] = state
        
        response = requests.patch(url, json=data, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "update_milestone", message=f"Updated milestone #{number}")

    def assign_milestone_impl(base_url, headers, owner, repo, issue_number, milestone_number):
        url = f"{base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        data = {"milestone": milestone_number}
        
        response = requests.patch(url, json=data, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "assign_milestone", message=f"Assigned milestone to issue #{issue_number}")

    # ==================== REPOSITORY INFO FUNCTIONS ====================

    def get_repo_info_impl(base_url, headers, owner, repo):
        url = f"{base_url}/repos/{owner}/{repo}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        return ActionResult(True, "get_repo_info", data={
            "name": data.get("name"),
            "full_name": data.get("full_name"),
            "description": data.get("description"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "open_issues": data.get("open_issues_count"),
            "language": data.get("language"),
            "size": data.get("size"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "default_branch": data.get("default_branch"),
            "url": data.get("html_url")
        })

    def get_contributors_impl(base_url, headers, owner, repo, max_results):
        url = f"{base_url}/repos/{owner}/{repo}/contributors"
        params = {"per_page": max_results}
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        contributors = [{
            "username": c.get("login"),
            "contributions": c.get("contributions"),
            "avatar_url": c.get("avatar_url"),
            "profile_url": c.get("html_url")
        } for c in response.json()]
        
        return ActionResult(True, "get_contributors", data=contributors, message=f"Found {len(contributors)} contributors")

    def get_commits_impl(base_url, headers, owner, repo, branch, max_results, author):
        url = f"{base_url}/repos/{owner}/{repo}/commits"
        params = {"per_page": max_results}
        if branch:
            params["sha"] = branch
        if author:
            params["author"] = author
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        commits = [{
            "sha": c.get("sha"),
            "message": c.get("commit", {}).get("message"),
            "author": c.get("commit", {}).get("author", {}).get("name"),
            "date": c.get("commit", {}).get("author", {}).get("date"),
            "url": c.get("html_url")
        } for c in response.json()]
        
        return ActionResult(True, "get_commits", data=commits, message=f"Retrieved {len(commits)} commits")

    def get_file_content_impl(base_url, headers, owner, repo, path, branch):
        url = f"{base_url}/repos/{owner}/{repo}/contents/{path}"
        params = {}
        if branch:
            params["ref"] = branch
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        content = response.json().get("content", "")
        decoded = base64.b64decode(content).decode('utf-8')
        return ActionResult(True, "get_file_content", data=decoded)

    def search_code_impl(base_url, headers, owner, repo, query, path, language):
        search_query = f"repo:{owner}/{repo} {query}"
        if path:
            search_query += f" path:{path}"
        if language:
            search_query += f" language:{language}"
        
        url = f"{base_url}/search/code"
        params = {"q": search_query, "per_page": 30}
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        results = [{
            "name": item.get("name"),
            "path": item.get("path"),
            "url": item.get("html_url"),
            "repository": item.get("repository", {}).get("full_name")
        } for item in data.get('items', [])]
        
        return ActionResult(True, "search_code", data=results, message=f"Found {len(results)} code matches")

    # ==================== BRANCH FUNCTIONS ====================

    def get_branches_impl(base_url, headers, owner, repo, max_results):
        url = f"{base_url}/repos/{owner}/{repo}/branches"
        params = {"per_page": max_results}
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        branches = [{
            "name": b.get("name"),
            "sha": b.get("commit", {}).get("sha"),
            "protected": b.get("protected")
        } for b in response.json()]
        
        return ActionResult(True, "get_branches", data=branches, message=f"Found {len(branches)} branches")

    def create_branch_impl(base_url, headers, owner, repo, branch_name, from_branch):
        # Get SHA of source branch
        if not from_branch:
            repo_info = get_repo_info_impl(base_url, headers, owner, repo)
            from_branch = repo_info.data.get("default_branch", "main") if repo_info.success else "main"
        
        # Get the SHA
        url = f"{base_url}/repos/{owner}/{repo}/git/refs/heads/{from_branch}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        sha = response.json().get("object", {}).get("sha")
        
        # Create new branch
        url = f"{base_url}/repos/{owner}/{repo}/git/refs"
        data = {"ref": f"refs/heads/{branch_name}", "sha": sha}
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "create_branch", message=f"Created branch '{branch_name}' from '{from_branch}'")

    def delete_branch_impl(base_url, headers, owner, repo, branch_name):
        url = f"{base_url}/repos/{owner}/{repo}/git/refs/heads/{branch_name}"
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "delete_branch", message=f"Deleted branch '{branch_name}'")

    def compare_branches_impl(base_url, headers, owner, repo, base, head):
        url = f"{base_url}/repos/{owner}/{repo}/compare/{base}...{head}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        return ActionResult(True, "compare_branches", data={
            "status": data.get("status"),
            "ahead_by": data.get("ahead_by"),
            "behind_by": data.get("behind_by"),
            "total_commits": data.get("total_commits"),
            "commits": [{
                "sha": c.get("sha"),
                "message": c.get("commit", {}).get("message"),
                "author": c.get("commit", {}).get("author", {}).get("name")
            } for c in data.get("commits", [])]
        })

    # ==================== COLLABORATOR FUNCTIONS ====================

    def get_collaborators_impl(base_url, headers, owner, repo):
        url = f"{base_url}/repos/{owner}/{repo}/collaborators"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        collaborators = [{
            "username": c.get("login"),
            "permissions": c.get("permissions"),
            "avatar_url": c.get("avatar_url")
        } for c in response.json()]
        
        return ActionResult(True, "get_collaborators", data=collaborators, message=f"Found {len(collaborators)} collaborators")

    def add_collaborator_impl(base_url, headers, owner, repo, username, permission):
        url = f"{base_url}/repos/{owner}/{repo}/collaborators/{username}"
        data = {"permission": permission}
        
        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "add_collaborator", message=f"Added '{username}' as collaborator")

    def remove_collaborator_impl(base_url, headers, owner, repo, username):
        url = f"{base_url}/repos/{owner}/{repo}/collaborators/{username}"
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "remove_collaborator", message=f"Removed collaborator '{username}'")

    # ==================== RELEASE & TAG FUNCTIONS ====================

    def get_releases_impl(base_url, headers, owner, repo, max_results):
        url = f"{base_url}/repos/{owner}/{repo}/releases"
        params = {"per_page": max_results}
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        releases = [{
            "tag_name": r.get("tag_name"),
            "name": r.get("name"),
            "body": r.get("body"),
            "draft": r.get("draft"),
            "prerelease": r.get("prerelease"),
            "created_at": r.get("created_at"),
            "published_at": r.get("published_at"),
            "url": r.get("html_url")
        } for r in response.json()]
        
        return ActionResult(True, "get_releases", data=releases, message=f"Found {len(releases)} releases")

    def get_release_by_tag_impl(base_url, headers, owner, repo, tag):
        url = f"{base_url}/repos/{owner}/{repo}/releases/tags/{tag}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        r = response.json()
        
        return ActionResult(True, "get_release", data={
            "tag_name": r.get("tag_name"),
            "name": r.get("name"),
            "body": r.get("body"),
            "draft": r.get("draft"),
            "prerelease": r.get("prerelease"),
            "created_at": r.get("created_at"),
            "published_at": r.get("published_at"),
            "url": r.get("html_url")
        })

    def create_release_impl(base_url, headers, owner, repo, tag, name, body, draft, prerelease, target):
        url = f"{base_url}/repos/{owner}/{repo}/releases"
        data = {
            "tag_name": tag,
            "name": name,
            "body": body,
            "draft": draft,
            "prerelease": prerelease
        }
        if target:
            data["target_commitish"] = target
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        r = response.json()
        
        return ActionResult(True, "create_release", data={
            "tag_name": r.get("tag_name"),
            "name": r.get("name"),
            "url": r.get("html_url")
        }, message=f"Created release '{name}'")

    def get_tags_impl(base_url, headers, owner, repo, max_results):
        url = f"{base_url}/repos/{owner}/{repo}/tags"
        params = {"per_page": max_results}
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        tags = [{
            "name": t.get("name"),
            "sha": t.get("commit", {}).get("sha"),
            "url": t.get("commit", {}).get("url")
        } for t in response.json()]
        
        return ActionResult(True, "get_tags", data=tags, message=f"Found {len(tags)} tags")

    def create_tag_impl(base_url, headers, owner, repo, tag, sha, message):
        # Create tag object
        url = f"{base_url}/repos/{owner}/{repo}/git/tags"
        data = {
            "tag": tag,
            "message": message or f"Tag {tag}",
            "object": sha,
            "type": "commit"
        }
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        tag_sha = response.json().get("sha")
        
        # Create reference
        url = f"{base_url}/repos/{owner}/{repo}/git/refs"
        data = {"ref": f"refs/tags/{tag}", "sha": tag_sha}
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "create_tag", message=f"Created tag '{tag}'")

    # ==================== UTILITY FUNCTIONS ====================

    def test_connection_impl(base_url, headers, owner, repo):
        url = f"{base_url}/repos/{owner}/{repo}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return ActionResult(True, "test_connection", message=f"Connected to {owner}/{repo}")

    def list_available_actions_impl():
        actions = {
            "Issue Management": [
                "get_issues", "get_bugs", "get_issue", "create_issue", "update_issue",
                "add_comment", "update_issue_state", "add_labels", "remove_labels",
                "assign_issue", "search_issues"
            ],
            "Pull Request Management": [
                "get_pull_requests", "get_pull_request", "create_pull_request",
                "merge_pull_request", "create_review", "get_pr_diff", "get_pr_files"
            ],
            "Label Management": [
                "get_labels", "create_label", "update_label", "delete_label"
            ],
            "Milestone Management": [
                "get_milestones", "create_milestone", "update_milestone", "assign_milestone"
            ],
            "Repository Info": [
                "get_repo_info", "get_contributors", "get_commits", "get_file_content", "search_code"
            ],
            "Branch Management": [
                "get_branches", "create_branch", "delete_branch", "compare_branches"
            ],
            "Collaborator Management": [
                "get_collaborators", "add_collaborator", "remove_collaborator"
            ],
            "Release & Tag Management": [
                "get_releases", "get_release", "create_release", "get_tags", "create_tag"
            ],
            "Utility": [
                "test_connection", "list_actions", "help"
            ]
        }
        return ActionResult(True, "list_actions", data=actions, message="Available GitHub actions by category")

    def get_help_impl(action_name):
        help_text = """
GitHub All-In-One Function Help
===============================

Usage:
    result = github_action(action, **parameters)

Configuration:
    Set environment variables or pass GitHubConfig:
    - GITHUB_TOKEN: Your GitHub personal access token
    - GITHUB_OWNER: Repository owner
    - GITHUB_REPO: Repository name

Examples:
    # Get issues
    result = github_action("get_issues", state="open", max_results=10)
    
    # Create issue
    result = github_action("create_issue", title="Bug Report", body="Details", labels=["bug"])
    
    # Search issues
    result = github_action("search_issues", query="login error", author="user123")
    
    # Create PR
    result = github_action("create_pull_request", title="Feature", head="feature-branch", base="main")
    
    # Merge PR
    result = github_action("merge_pull_request", pr_number=123, merge_method="squash")
    
    # Create branch
    result = github_action("create_branch", branch_name="feature-x", from_branch="main")
    
    # Get repo info
    result = github_action("get_repo_info")

Use action='list_actions' to see all available actions.
"""
        return ActionResult(True, "help", data=help_text)

    # ==================== MAIN ACTION DISPATCHER ====================
    
    # Initialize configuration
    if config is None:
        config = GitHubConfig()
    
    owner = owner or config.owner
    repo = repo or config.repo
    
    # Set up headers
    headers = {
        'Authorization': f'token {config.token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    base_url = config.base_url
    
    # Action handlers
    try:
        # ==================== ISSUE MANAGEMENT ====================
        
        if action == "get_issues":
            return get_issues_impl(base_url, headers, owner, repo, state or "open", labels, max_results)
        
        elif action == "get_bugs":
            bug_labels = labels or []
            if not any('bug' in l.lower() for l in bug_labels):
                bug_labels.append('type: bug')
            return get_issues_impl(base_url, headers, owner, repo, state or "open", bug_labels, max_results)
        
        elif action == "get_issue":
            if not issue_number:
                return ActionResult(False, action, error="issue_number is required")
            return get_issue_impl(base_url, headers, owner, repo, issue_number)
        
        elif action == "create_issue":
            if not title:
                return ActionResult(False, action, error="title is required")
            return create_issue_impl(base_url, headers, owner, repo, title, body or "", labels, assignees, milestone)
        
        elif action == "update_issue":
            if not issue_number:
                return ActionResult(False, action, error="issue_number is required")
            return update_issue_impl(base_url, headers, owner, repo, issue_number, title, body, state, labels)
        
        elif action == "add_comment":
            if not issue_number or not comment:
                return ActionResult(False, action, error="issue_number and comment are required")
            return add_comment_impl(base_url, headers, owner, repo, issue_number, comment)
        
        elif action == "update_issue_state":
            if not issue_number or not state:
                return ActionResult(False, action, error="issue_number and state are required")
            return update_issue_state_impl(base_url, headers, owner, repo, issue_number, state)
        
        elif action == "add_labels":
            if not issue_number or not labels:
                return ActionResult(False, action, error="issue_number and labels are required")
            return add_labels_impl(base_url, headers, owner, repo, issue_number, labels)
        
        elif action == "remove_labels":
            if not issue_number or not labels:
                return ActionResult(False, action, error="issue_number and labels are required")
            return remove_labels_impl(base_url, headers, owner, repo, issue_number, labels)
        
        elif action == "assign_issue":
            if not issue_number or not assignees:
                return ActionResult(False, action, error="issue_number and assignees are required")
            return assign_issue_impl(base_url, headers, owner, repo, issue_number, assignees)
        
        elif action == "search_issues":
            if not query:
                return ActionResult(False, action, error="query is required")
            return search_issues_impl(base_url, headers, owner, repo, query, author, assignee, labels, state or "open", sort or "created", order or "desc")
        
        # ==================== PULL REQUEST MANAGEMENT ====================
        
        elif action == "get_pull_requests":
            return get_pull_requests_impl(base_url, headers, owner, repo, state or "open", sort or "created", direction or "desc", max_results)
        
        elif action == "get_pull_request":
            if not pr_number:
                return ActionResult(False, action, error="pr_number is required")
            return get_pull_request_impl(base_url, headers, owner, repo, pr_number)
        
        elif action == "create_pull_request":
            if not title or not head:
                return ActionResult(False, action, error="title and head are required")
            return create_pull_request_impl(base_url, headers, owner, repo, title, body or "", head, base or "main", draft or False)
        
        elif action == "merge_pull_request":
            if not pr_number:
                return ActionResult(False, action, error="pr_number is required")
            return merge_pull_request_impl(base_url, headers, owner, repo, pr_number, merge_method or "merge", commit_message)
        
        elif action == "create_review":
            if not pr_number or not event:
                return ActionResult(False, action, error="pr_number and event are required")
            return create_review_impl(base_url, headers, owner, repo, pr_number, event, body or "")
        
        elif action == "get_pr_diff":
            if not pr_number:
                return ActionResult(False, action, error="pr_number is required")
            return get_pr_diff_impl(base_url, headers, owner, repo, pr_number)
        
        elif action == "get_pr_files":
            if not pr_number:
                return ActionResult(False, action, error="pr_number is required")
            return get_pr_files_impl(base_url, headers, owner, repo, pr_number)
        
        # ==================== LABEL MANAGEMENT ====================
        
        elif action == "get_labels":
            return get_labels_impl(base_url, headers, owner, repo)
        
        elif action == "create_label":
            if not name or not color:
                return ActionResult(False, action, error="name and color are required")
            return create_label_impl(base_url, headers, owner, repo, name, color, description or "")
        
        elif action == "update_label":
            if not name:
                return ActionResult(False, action, error="name is required")
            return update_label_impl(base_url, headers, owner, repo, name, new_name, color, description)
        
        elif action == "delete_label":
            if not name:
                return ActionResult(False, action, error="name is required")
            return delete_label_impl(base_url, headers, owner, repo, name)
        
        # ==================== MILESTONE MANAGEMENT ====================
        
        elif action == "get_milestones":
            return get_milestones_impl(base_url, headers, owner, repo, state or "open")
        
        elif action == "create_milestone":
            if not title:
                return ActionResult(False, action, error="title is required")
            return create_milestone_impl(base_url, headers, owner, repo, title, description or "", due_date, state or "open")
        
        elif action == "update_milestone":
            if not milestone_number:
                return ActionResult(False, action, error="milestone_number is required")
            return update_milestone_impl(base_url, headers, owner, repo, milestone_number, title, description, due_date, state)
        
        elif action == "assign_milestone":
            if not issue_number or not milestone_number:
                return ActionResult(False, action, error="issue_number and milestone_number are required")
            return assign_milestone_impl(base_url, headers, owner, repo, issue_number, milestone_number)
        
        # ==================== REPOSITORY INFO ====================
        
        elif action == "get_repo_info":
            return get_repo_info_impl(base_url, headers, owner, repo)
        
        elif action == "get_contributors":
            return get_contributors_impl(base_url, headers, owner, repo, max_results)
        
        elif action == "get_commits":
            return get_commits_impl(base_url, headers, owner, repo, branch, max_results, author)
        
        elif action == "get_file_content":
            if not path:
                return ActionResult(False, action, error="path is required")
            return get_file_content_impl(base_url, headers, owner, repo, path, branch)
        
        elif action == "search_code":
            if not query:
                return ActionResult(False, action, error="query is required")
            return search_code_impl(base_url, headers, owner, repo, query, path, language)
        
        # ==================== BRANCH MANAGEMENT ====================
        
        elif action == "get_branches":
            return get_branches_impl(base_url, headers, owner, repo, max_results)
        
        elif action == "create_branch":
            if not branch_name:
                return ActionResult(False, action, error="branch_name is required")
            return create_branch_impl(base_url, headers, owner, repo, branch_name, from_branch)
        
        elif action == "delete_branch":
            if not branch_name:
                return ActionResult(False, action, error="branch_name is required")
            return delete_branch_impl(base_url, headers, owner, repo, branch_name)
        
        elif action == "compare_branches":
            if not base or not head:
                return ActionResult(False, action, error="base and head are required")
            return compare_branches_impl(base_url, headers, owner, repo, base, head)
        
        # ==================== COLLABORATOR MANAGEMENT ====================
        
        elif action == "get_collaborators":
            return get_collaborators_impl(base_url, headers, owner, repo)
        
        elif action == "add_collaborator":
            if not username:
                return ActionResult(False, action, error="username is required")
            return add_collaborator_impl(base_url, headers, owner, repo, username, permission or "push")
        
        elif action == "remove_collaborator":
            if not username:
                return ActionResult(False, action, error="username is required")
            return remove_collaborator_impl(base_url, headers, owner, repo, username)
        
        # ==================== RELEASE & TAG MANAGEMENT ====================
        
        elif action == "get_releases":
            return get_releases_impl(base_url, headers, owner, repo, max_results)
        
        elif action == "get_release":
            if not tag:
                return ActionResult(False, action, error="tag is required")
            return get_release_by_tag_impl(base_url, headers, owner, repo, tag)
        
        elif action == "create_release":
            if not tag or not name:
                return ActionResult(False, action, error="tag and name are required")
            return create_release_impl(base_url, headers, owner, repo, tag, name, body or "", draft or False, prerelease or False, target)
        
        elif action == "get_tags":
            return get_tags_impl(base_url, headers, owner, repo, max_results)
        
        elif action == "create_tag":
            if not tag or not sha:
                return ActionResult(False, action, error="tag and sha are required")
            return create_tag_impl(base_url, headers, owner, repo, tag, sha, comment or "")
        
        # ==================== UTILITY ACTIONS ====================
        
        elif action == "test_connection":
            return test_connection_impl(base_url, headers, owner, repo)
        
        elif action == "list_actions":
            return list_available_actions_impl()
        
        elif action == "help":
            return get_help_impl(kwargs.get("help_action"))
        
        else:
            return ActionResult(
                False, action,
                error=f"Unknown action: {action}. Use action='list_actions' to see available actions."
            )
    
    except requests.exceptions.HTTPError as e:
        return ActionResult(False, action, error=f"HTTP Error: {str(e)}")
    except requests.exceptions.ConnectionError as e:
        return ActionResult(False, action, error=f"Connection Error: {str(e)}")
    except Exception as e:
        return ActionResult(False, action, error=f"Error: {str(e)}")


# ==================== MAIN (for testing) ====================

if __name__ == "__main__":
    print("=" * 60)
    print("GitHub All-In-One Function")
    print("=" * 60)
    
    # List all available actions
    result = github_action("list_actions")
    
    if result.success:
        print("\n✓ Available Actions:\n")
        for category, actions in result.data.items():
            print(f"\n{category}:")
            for action in actions:
                print(f"  - {action}")
    
    print("\n" + "=" * 60)
    print("Usage Example:")
    print("=" * 60)
    print("""
from scripts.github_all_in_one import github_action

# Test connection
result = github_action("test_connection")
print(result.message)

# Get open issues
result = github_action("get_issues", state="open", max_results=5)
for issue in result.data:
    print(f"#{issue['number']}: {issue['title']}")

# Create an issue
result = github_action(
    "create_issue",
    title="New Feature Request",
    body="Please add this feature",
    labels=["enhancement"]
)
print(result.message)
""")
