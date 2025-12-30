"""GitHub MCP Server - Model Context Protocol server for GitHub integration."""
from typing import Any, List, Dict, Optional, Callable
from pydantic import BaseModel, Field
from src.config import Config
import requests
from requests.auth import HTTPBasicAuth

# Type alias for progress callback
ProgressCallback = Callable[[str], None]


class GitHubIssue(BaseModel):
    """Represents a GitHub issue."""
    number: int
    title: str
    body: Optional[str] = None
    state: str
    labels: List[str] = Field(default_factory=list)
    assignee: Optional[str] = None
    assignees: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    milestone: Optional[str] = None
    html_url: str
    
    class Config:
        arbitrary_types_allowed = True


class GitHubMCPServer:
    """MCP Server for GitHub integration."""
    
    def __init__(self):
        """Initialize the GitHub MCP server."""
        self.base_url = "https://api.github.com"
        self.owner = Config.GITHUB_OWNER
        self.repo = Config.GITHUB_REPO
        self.token = Config.GITHUB_TOKEN
        self.progress_callback: Optional[ProgressCallback] = None
        
        # Set up authentication
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        self._validate_connection()
    
    def set_progress_callback(self, callback: Optional[ProgressCallback]):
        """Set a callback function for progress updates."""
        self.progress_callback = callback
    
    def _report_progress(self, message: str):
        """Report progress via callback if set, otherwise print."""
        if self.progress_callback:
            self.progress_callback(message)
        print(message)
    
    def _validate_connection(self):
        """Validate connection to GitHub."""
        try:
            # Test connection by fetching repo details
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            print(f"✓ Connected to GitHub: {self.owner}/{self.repo}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to GitHub: {str(e)}")
    
    def get_issues(
        self, 
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        state: str = "open",
        labels: Optional[List[str]] = None,
        max_results: int = 100
    ) -> List[GitHubIssue]:
        """
        Retrieve issues from GitHub with pagination support for large results.
        
        Args:
            owner: Repository owner (default from config)
            repo: Repository name (default from config)
            state: Issue state ('open', 'closed', 'all')
            labels: Labels to filter by (optional)
            max_results: Maximum number of issues to return (supports >100 via pagination)
            
        Returns:
            List of GitHubIssue objects
        """
        import time
        
        owner = owner or self.owner
        repo = repo or self.repo
        
        all_issues = []
        page = 1
        per_page = min(100, max_results)  # GitHub max per page is 100
        
        self._report_progress(f"📥 Fetching up to {max_results} {state} issues from GitHub: {owner}/{repo}")
        
        while len(all_issues) < max_results:
            try:
                # Build query parameters
                params = {
                    'state': state,
                    'per_page': per_page,
                    'page': page,
                    'sort': 'created',
                    'direction': 'desc'
                }
                
                if labels:
                    params['labels'] = ','.join(labels)
                
                # Fetch issues with timeout
                url = f"{self.base_url}/repos/{owner}/{repo}/issues"
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                # Check for rate limiting
                if response.status_code == 403:
                    remaining = response.headers.get('X-RateLimit-Remaining', '0')
                    reset_time = response.headers.get('X-RateLimit-Reset', '0')
                    if remaining == '0':
                        reset_dt = time.strftime('%H:%M:%S', time.localtime(int(reset_time)))
                        self._report_progress(f"  ⚠️ Rate limit reached. Resets at {reset_dt}. Returning {len(all_issues)} issues collected so far.")
                        break
                
                response.raise_for_status()
                
                issues_data = response.json()
                
                # No more issues
                if not issues_data:
                    break
                
                # Convert to GitHubIssue objects
                for issue in issues_data:
                    # Skip pull requests (they appear in issues endpoint)
                    if 'pull_request' in issue:
                        continue
                    
                    github_issue = GitHubIssue(
                        number=issue['number'],
                        title=issue['title'],
                        body=issue.get('body', None),
                        state=issue['state'],
                        labels=[label['name'] for label in issue.get('labels', [])],
                        assignee=issue['assignee']['login'] if issue.get('assignee') else None,
                        assignees=[a['login'] for a in issue.get('assignees', [])],
                        created_by=issue['user']['login'] if issue.get('user') else None,
                        created_at=issue['created_at'],
                        updated_at=issue['updated_at'],
                        closed_at=issue.get('closed_at', None),
                        milestone=issue['milestone']['title'] if issue.get('milestone') else None,
                        html_url=issue['html_url']
                    )
                    all_issues.append(github_issue)
                    
                    # Stop if we've reached max_results
                    if len(all_issues) >= max_results:
                        break
                
                # If we got fewer than per_page, no more pages
                if len(issues_data) < per_page:
                    break
                
                page += 1
                # Calculate and report progress percentage
                progress_pct = min(100, int((len(all_issues) / max_results) * 100))
                self._report_progress(f"  📊 Fetched page {page-1}: {len(all_issues)}/{max_results} issues ({progress_pct}%)")
                
            except requests.exceptions.Timeout:
                self._report_progress(f"  ⚠️ Request timeout on page {page}. Returning {len(all_issues)} issues collected so far.")
                break
            except requests.exceptions.RequestException as e:
                self._report_progress(f"  ⚠️ Request error: {e}. Returning {len(all_issues)} issues collected so far.")
                break
        
        self._report_progress(f"✅ Retrieved {len(all_issues)} issues from GitHub (100%)")
        return all_issues
    
    def get_bugs(
        self,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        state: str = "open",
        labels: Optional[List[str]] = None,
        max_results: int = 50
    ) -> List[GitHubIssue]:
        """
        Retrieve bugs (issues with 'bug' label) from GitHub.
        
        Args:
            owner: Repository owner (default from config)
            repo: Repository name (default from config)
            state: Issue state ('open', 'closed', 'all')
            labels: Additional labels to filter by
            max_results: Maximum number of issues to return
            
        Returns:
            List of GitHubIssue objects
        """
        owner = owner or self.owner
        repo = repo or self.repo
        
        # Build query parameters
        params = {
            'state': state,
            'per_page': min(max_results, 100),  # GitHub max is 100
            'sort': 'created',
            'direction': 'desc'
        }
        
        # Add bug-related labels to filters (try common variations)
        label_list = labels or []
        bug_label_found = any(
            'bug' in l.lower() for l in label_list
        )
        
        # If no bug label specified, add common bug label patterns
        if not bug_label_found:
            # Try to detect which bug label the repo uses
            # Common patterns: 'bug', 'type: bug', 'type/bug', 'Bug', etc.
            label_list.append('type: bug')  # Common in enterprise repos
        
        params['labels'] = ','.join(label_list)
        
        print(f"Fetching bugs from GitHub: {owner}/{repo}")
        
        # Fetch issues
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        issues_data = response.json()
        
        # Convert to GitHubIssue objects
        github_issues = []
        for issue in issues_data:
            # Skip pull requests (they appear in issues endpoint)
            if 'pull_request' in issue:
                continue
            
            github_issue = GitHubIssue(
                number=issue['number'],
                title=issue['title'],
                body=issue.get('body', None),
                state=issue['state'],
                labels=[label['name'] for label in issue.get('labels', [])],
                assignee=issue['assignee']['login'] if issue.get('assignee') else None,
                assignees=[a['login'] for a in issue.get('assignees', [])],
                created_by=issue['user']['login'] if issue.get('user') else None,
                created_at=issue['created_at'],
                updated_at=issue['updated_at'],
                closed_at=issue.get('closed_at', None),
                milestone=issue['milestone']['title'] if issue.get('milestone') else None,
                html_url=issue['html_url']
            )
            github_issues.append(github_issue)
        
        print(f"✓ Retrieved {len(github_issues)} bugs from GitHub")
        return github_issues
    
    def get_issue(self, issue_number: int, owner: Optional[str] = None, repo: Optional[str] = None) -> GitHubIssue:
        """
        Get a specific issue by number.
        
        Args:
            issue_number: The issue number
            owner: Repository owner (default from config)
            repo: Repository name (default from config)
            
        Returns:
            GitHubIssue object
        """
        owner = owner or self.owner
        repo = repo or self.repo
        
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        issue = response.json()
        
        return GitHubIssue(
            number=issue['number'],
            title=issue['title'],
            body=issue.get('body', None),
            state=issue['state'],
            labels=[label['name'] for label in issue.get('labels', [])],
            assignee=issue['assignee']['login'] if issue.get('assignee') else None,
            assignees=[a['login'] for a in issue.get('assignees', [])],
            created_by=issue['user']['login'] if issue.get('user') else None,
            created_at=issue['created_at'],
            updated_at=issue['updated_at'],
            closed_at=issue.get('closed_at', None),
            milestone=issue['milestone']['title'] if issue.get('milestone') else None,
            html_url=issue['html_url']
        )
    
    def add_comment(self, issue_number: int, comment: str, owner: Optional[str] = None, repo: Optional[str] = None) -> bool:
        """
        Add a comment to a GitHub issue.
        
        Args:
            issue_number: The issue number
            comment: Comment text to add
            owner: Repository owner (default from config)
            repo: Repository name (default from config)
            
        Returns:
            True if successful
        """
        owner = owner or self.owner
        repo = repo or self.repo
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
            body = {"body": comment}
            
            response = requests.post(url, json=body, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to add comment to issue #{issue_number}: {str(e)}")
            return False
    
    def update_issue_state(self, issue_number: int, state: str, owner: Optional[str] = None, repo: Optional[str] = None) -> bool:
        """
        Update the state of a GitHub issue.
        
        Args:
            issue_number: The issue number
            state: New state ('open' or 'closed')
            owner: Repository owner (default from config)
            repo: Repository name (default from config)
            
        Returns:
            True if successful
        """
        owner = owner or self.owner
        repo = repo or self.repo
        
        if state not in ['open', 'closed']:
            print(f"Invalid state: {state}. Must be 'open' or 'closed'")
            return False
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
            body = {"state": state}
            
            response = requests.patch(url, json=body, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to update state for issue #{issue_number}: {str(e)}")
            return False
    
    def add_labels(self, issue_number: int, labels: List[str], owner: Optional[str] = None, repo: Optional[str] = None) -> bool:
        """
        Add labels to a GitHub issue.
        
        Args:
            issue_number: The issue number
            labels: List of label names to add
            owner: Repository owner (default from config)
            repo: Repository name (default from config)
            
        Returns:
            True if successful
        """
        owner = owner or self.owner
        repo = repo or self.repo
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/labels"
            body = {"labels": labels}
            
            response = requests.post(url, json=body, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to add labels to issue #{issue_number}: {str(e)}")
            return False
    
    def assign_issue(self, issue_number: int, assignees: List[str], owner: Optional[str] = None, repo: Optional[str] = None) -> bool:
        """
        Assign users to a GitHub issue.
        
        Args:
            issue_number: The issue number
            assignees: List of usernames to assign
            owner: Repository owner (default from config)
            repo: Repository name (default from config)
            
        Returns:
            True if successful
        """
        owner = owner or self.owner
        repo = repo or self.repo
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/assignees"
            body = {"assignees": assignees}
            
            response = requests.post(url, json=body, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to assign issue #{issue_number}: {str(e)}")
            return False
    
    # ==== NEW GITHUB CAPABILITIES ====
    
    # Issue Management Extensions
    def create_issue(self, title: str, body: str = "", labels: List[str] = None, 
                     assignees: List[str] = None, milestone: int = None,
                     owner: Optional[str] = None, repo: Optional[str] = None):
        """Create a new GitHub issue."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues"
            data = {"title": title, "body": body}
            if labels:
                data["labels"] = labels
            if assignees:
                data["assignees"] = assignees
            if milestone:
                data["milestone"] = milestone
            
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            issue_data = response.json()
            return True, self._parse_issue(issue_data)
        except Exception as e:
            print(f"Failed to create issue: {str(e)}")
            return False, None
    
    def update_issue(self, issue_number: int, title: str = None, body: str = None,
                    state: str = None, labels: List[str] = None,
                    owner: Optional[str] = None, repo: Optional[str] = None) -> bool:
        """Update an existing issue."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
            data = {}
            if title:
                data["title"] = title
            if body:
                data["body"] = body
            if state:
                data["state"] = state
            if labels:
                data["labels"] = labels
            
            response = requests.patch(url, json=data, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to update issue: {str(e)}")
            return False
    
    def remove_labels(self, issue_number: int, labels: List[str],
                     owner: Optional[str] = None, repo: Optional[str] = None) -> bool:
        """Remove labels from an issue."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            for label in labels:
                url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/labels/{label}"
                response = requests.delete(url, headers=self.headers)
                response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to remove labels: {str(e)}")
            return False
    
    def search_issues(self, query: str, author: str = None, assignee: str = None,
                     labels: List[str] = None, state: str = "open",
                     sort: str = "created", order: str = "desc") -> List[GitHubIssue]:
        """Search issues with advanced filters."""
        try:
            # Build search query
            search_query = f"repo:{self.owner}/{self.repo} {query}"
            if author:
                search_query += f" author:{author}"
            if assignee:
                search_query += f" assignee:{assignee}"
            if labels:
                for label in labels:
                    search_query += f" label:\"{label}\""
            if state != "all":
                search_query += f" state:{state}"
            
            url = f"{self.base_url}/search/issues"
            params = {"q": search_query, "sort": sort, "order": order}
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            return [self._parse_issue(item) for item in data.get('items', [])]
        except Exception as e:
            print(f"Failed to search issues: {str(e)}")
            return []
    
    # Pull Requests
    def get_pull_requests(self, state: str = "open", sort: str = "created",
                         direction: str = "desc", owner: Optional[str] = None,
                         repo: Optional[str] = None) -> List:
        """Get repository pull requests."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
            params = {"state": state, "sort": sort, "direction": direction, "per_page": 30}
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return [self._parse_pr(pr) for pr in response.json()]
        except Exception as e:
            print(f"Failed to get pull requests: {str(e)}")
            return []
    
    def get_pull_request(self, pr_number: int, owner: Optional[str] = None,
                        repo: Optional[str] = None):
        """Get specific pull request details."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return self._parse_pr(response.json())
        except Exception as e:
            print(f"Failed to get pull request: {str(e)}")
            return None
    
    def create_pull_request(self, title: str, body: str, head: str, base: str = "main",
                           draft: bool = False, owner: Optional[str] = None,
                           repo: Optional[str] = None):
        """Create a new pull request."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
            data = {
                "title": title,
                "body": body,
                "head": head,
                "base": base,
                "draft": draft
            }
            
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return True, self._parse_pr(response.json())
        except Exception as e:
            print(f"Failed to create pull request: {str(e)}")
            return False, None
    
    def merge_pull_request(self, pr_number: int, merge_method: str = "merge",
                          commit_message: str = None, owner: Optional[str] = None,
                          repo: Optional[str] = None) -> bool:
        """Merge a pull request."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/merge"
            data = {"merge_method": merge_method}
            if commit_message:
                data["commit_message"] = commit_message
            
            response = requests.put(url, json=data, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to merge pull request: {str(e)}")
            return False
    
    def create_review(self, pr_number: int, event: str, body: str = "",
                     owner: Optional[str] = None, repo: Optional[str] = None) -> bool:
        """Add a review to a pull request."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
            data = {"event": event, "body": body}
            
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to create review: {str(e)}")
            return False
    
    def get_pull_request_diff(self, pr_number: int, owner: Optional[str] = None,
                             repo: Optional[str] = None) -> str:
        """Get the diff for a pull request."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
            headers = {**self.headers, 'Accept': 'application/vnd.github.v3.diff'}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Failed to get PR diff: {str(e)}")
            return None
    
    def get_pull_request_files(self, pr_number: int, owner: Optional[str] = None,
                               repo: Optional[str] = None) -> List[Dict]:
        """Get list of files changed in a PR."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            files = []
            for file in response.json():
                files.append({
                    "filename": file.get("filename"),
                    "status": file.get("status"),
                    "additions": file.get("additions"),
                    "deletions": file.get("deletions"),
                    "changes": file.get("changes")
                })
            return files
        except Exception as e:
            print(f"Failed to get PR files: {str(e)}")
            return []
    
    # Labels Management
    def get_labels(self, owner: Optional[str] = None, repo: Optional[str] = None) -> List[Dict]:
        """Get all repository labels."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/labels"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return [{
                "name": label.get("name"),
                "color": label.get("color"),
                "description": label.get("description")
            } for label in response.json()]
        except Exception as e:
            print(f"Failed to get labels: {str(e)}")
            return []
    
    def create_label(self, name: str, color: str, description: str = "",
                    owner: Optional[str] = None, repo: Optional[str] = None):
        """Create a new label."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/labels"
            data = {"name": name, "color": color.lstrip('#'), "description": description}
            
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            label_data = response.json()
            return True, {
                "name": label_data.get("name"),
                "color": label_data.get("color"),
                "description": label_data.get("description")
            }
        except Exception as e:
            print(f"Failed to create label: {str(e)}")
            return False, None
    
    def update_label(self, name: str, new_name: str = None, color: str = None,
                    description: str = None, owner: Optional[str] = None,
                    repo: Optional[str] = None) -> bool:
        """Update an existing label."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/labels/{name}"
            data = {}
            if new_name:
                data["new_name"] = new_name
            if color:
                data["color"] = color.lstrip('#')
            if description:
                data["description"] = description
            
            response = requests.patch(url, json=data, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to update label: {str(e)}")
            return False
    
    def delete_label(self, name: str, owner: Optional[str] = None,
                    repo: Optional[str] = None) -> bool:
        """Delete a label."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/labels/{name}"
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to delete label: {str(e)}")
            return False
    
    # Milestones
    def get_milestones(self, state: str = "open", owner: Optional[str] = None,
                      repo: Optional[str] = None) -> List[Dict]:
        """Get all milestones."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/milestones"
            params = {"state": state}
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            return [{
                "number": m.get("number"),
                "title": m.get("title"),
                "description": m.get("description"),
                "state": m.get("state"),
                "due_on": m.get("due_on")
            } for m in response.json()]
        except Exception as e:
            print(f"Failed to get milestones: {str(e)}")
            return []
    
    def create_milestone(self, title: str, description: str = "", due_date: str = None,
                        state: str = "open", owner: Optional[str] = None,
                        repo: Optional[str] = None):
        """Create a new milestone."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/milestones"
            data = {"title": title, "state": state}
            if description:
                data["description"] = description
            if due_date:
                data["due_on"] = due_date
            
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            m = response.json()
            return True, {
                "number": m.get("number"),
                "title": m.get("title"),
                "description": m.get("description"),
                "state": m.get("state")
            }
        except Exception as e:
            print(f"Failed to create milestone: {str(e)}")
            return False, None
    
    def update_milestone(self, number: int, title: str = None, description: str = None,
                        due_date: str = None, state: str = None,
                        owner: Optional[str] = None, repo: Optional[str] = None) -> bool:
        """Update a milestone."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/milestones/{number}"
            data = {}
            if title:
                data["title"] = title
            if description:
                data["description"] = description
            if due_date:
                data["due_on"] = due_date
            if state:
                data["state"] = state
            
            response = requests.patch(url, json=data, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to update milestone: {str(e)}")
            return False
    
    def assign_milestone_to_issue(self, issue_number: int, milestone_number: int,
                                  owner: Optional[str] = None, repo: Optional[str] = None) -> bool:
        """Assign a milestone to an issue."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
            data = {"milestone": milestone_number}
            
            response = requests.patch(url, json=data, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to assign milestone: {str(e)}")
            return False
    
    # Repository Info
    def get_repository_info(self, owner: Optional[str] = None, repo: Optional[str] = None) -> Dict:
        """Get repository information."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            return {
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
            }
        except Exception as e:
            print(f"Failed to get repository info: {str(e)}")
            return None
    
    def get_contributors(self, max_results: int = 30, owner: Optional[str] = None,
                        repo: Optional[str] = None) -> List[Dict]:
        """Get repository contributors."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contributors"
            params = {"per_page": max_results}
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            return [{
                "username": c.get("login"),
                "contributions": c.get("contributions"),
                "avatar_url": c.get("avatar_url"),
                "profile_url": c.get("html_url")
            } for c in response.json()]
        except Exception as e:
            print(f"Failed to get contributors: {str(e)}")
            return []
    
    def get_commits(self, branch: str = None, max_results: int = 10,
                   author: str = None, owner: Optional[str] = None,
                   repo: Optional[str] = None) -> List[Dict]:
        """Get commit history."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/commits"
            params = {"per_page": max_results}
            if branch:
                params["sha"] = branch
            if author:
                params["author"] = author
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            return [{
                "sha": c.get("sha"),
                "message": c.get("commit", {}).get("message"),
                "author": c.get("commit", {}).get("author", {}).get("name"),
                "date": c.get("commit", {}).get("author", {}).get("date"),
                "url": c.get("html_url")
            } for c in response.json()]
        except Exception as e:
            print(f"Failed to get commits: {str(e)}")
            return []
    
    def get_file_contents(self, path: str, branch: str = None,
                         owner: Optional[str] = None, repo: Optional[str] = None) -> str:
        """Get file content from repository."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
            params = {}
            if branch:
                params["ref"] = branch
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            import base64
            content = response.json().get("content", "")
            return base64.b64decode(content).decode('utf-8')
        except Exception as e:
            print(f"Failed to get file content: {str(e)}")
            return None
    
    def search_code(self, query: str, path: str = None, language: str = None) -> List[Dict]:
        """Search code in repository."""
        try:
            search_query = f"repo:{self.owner}/{self.repo} {query}"
            if path:
                search_query += f" path:{path}"
            if language:
                search_query += f" language:{language}"
            
            url = f"{self.base_url}/search/code"
            params = {"q": search_query, "per_page": 30}
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            return [{
                "name": item.get("name"),
                "path": item.get("path"),
                "url": item.get("html_url"),
                "repository": item.get("repository", {}).get("full_name")
            } for item in data.get('items', [])]
        except Exception as e:
            print(f"Failed to search code: {str(e)}")
            return []
    
    # Branch Operations
    def create_branch(self, branch_name: str, from_branch: str = None,
                     owner: Optional[str] = None, repo: Optional[str] = None) -> bool:
        """Create a new branch."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            # Get SHA of the source branch
            if not from_branch:
                repo_info = self.get_repository_info(owner, repo)
                from_branch = repo_info.get("default_branch", "main")
            
            # Get the SHA of the source branch
            url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{from_branch}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            sha = response.json().get("object", {}).get("sha")
            
            # Create new branch
            url = f"{self.base_url}/repos/{owner}/{repo}/git/refs"
            data = {
                "ref": f"refs/heads/{branch_name}",
                "sha": sha
            }
            
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to create branch: {str(e)}")
            return False
    
    def delete_branch(self, branch_name: str, owner: Optional[str] = None,
                     repo: Optional[str] = None) -> bool:
        """Delete a remote branch."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{branch_name}"
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to delete branch: {str(e)}")
            return False
    
    def compare_branches(self, base: str, head: str, owner: Optional[str] = None,
                        repo: Optional[str] = None) -> Dict:
        """Compare two branches."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/compare/{base}...{head}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            return {
                "status": data.get("status"),
                "ahead_by": data.get("ahead_by"),
                "behind_by": data.get("behind_by"),
                "total_commits": data.get("total_commits"),
                "commits": [{
                    "sha": c.get("sha"),
                    "message": c.get("commit", {}).get("message"),
                    "author": c.get("commit", {}).get("author", {}).get("name")
                } for c in data.get("commits", [])]
            }
        except Exception as e:
            print(f"Failed to compare branches: {str(e)}")
            return None
    
    # Collaborators
    def get_collaborators(self, owner: Optional[str] = None, repo: Optional[str] = None) -> List[Dict]:
        """Get repository collaborators."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/collaborators"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return [{
                "username": c.get("login"),
                "permissions": c.get("permissions"),
                "avatar_url": c.get("avatar_url")
            } for c in response.json()]
        except Exception as e:
            print(f"Failed to get collaborators: {str(e)}")
            return []
    
    def add_collaborator(self, username: str, permission: str = "push",
                        owner: Optional[str] = None, repo: Optional[str] = None) -> bool:
        """Add a collaborator to the repository."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/collaborators/{username}"
            data = {"permission": permission}
            
            response = requests.put(url, json=data, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to add collaborator: {str(e)}")
            return False
    
    def remove_collaborator(self, username: str, owner: Optional[str] = None,
                           repo: Optional[str] = None) -> bool:
        """Remove a collaborator."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/collaborators/{username}"
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to remove collaborator: {str(e)}")
            return False
    
    # Releases & Tags
    def get_releases(self, max_results: int = 10, owner: Optional[str] = None,
                    repo: Optional[str] = None) -> List[Dict]:
        """Get all releases."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/releases"
            params = {"per_page": max_results}
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            return [{
                "tag_name": r.get("tag_name"),
                "name": r.get("name"),
                "body": r.get("body"),
                "draft": r.get("draft"),
                "prerelease": r.get("prerelease"),
                "created_at": r.get("created_at"),
                "published_at": r.get("published_at"),
                "url": r.get("html_url")
            } for r in response.json()]
        except Exception as e:
            print(f"Failed to get releases: {str(e)}")
            return []
    
    def get_release_by_tag(self, tag: str, owner: Optional[str] = None,
                          repo: Optional[str] = None) -> Dict:
        """Get a specific release by tag."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/releases/tags/{tag}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            r = response.json()
            
            return {
                "tag_name": r.get("tag_name"),
                "name": r.get("name"),
                "body": r.get("body"),
                "draft": r.get("draft"),
                "prerelease": r.get("prerelease"),
                "created_at": r.get("created_at"),
                "published_at": r.get("published_at"),
                "url": r.get("html_url")
            }
        except Exception as e:
            print(f"Failed to get release: {str(e)}")
            return None
    
    def create_release(self, tag: str, name: str, body: str = "", draft: bool = False,
                      prerelease: bool = False, target: str = None,
                      owner: Optional[str] = None, repo: Optional[str] = None):
        """Create a new release."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/releases"
            data = {
                "tag_name": tag,
                "name": name,
                "body": body,
                "draft": draft,
                "prerelease": prerelease
            }
            if target:
                data["target_commitish"] = target
            
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            r = response.json()
            
            return True, {
                "tag_name": r.get("tag_name"),
                "name": r.get("name"),
                "url": r.get("html_url")
            }
        except Exception as e:
            print(f"Failed to create release: {str(e)}")
            return False, None
    
    def get_tags(self, max_results: int = 30, owner: Optional[str] = None,
                repo: Optional[str] = None) -> List[Dict]:
        """Get all tags."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/tags"
            params = {"per_page": max_results}
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            
            return [{
                "name": t.get("name"),
                "sha": t.get("commit", {}).get("sha"),
                "url": t.get("commit", {}).get("url")
            } for t in response.json()]
        except Exception as e:
            print(f"Failed to get tags: {str(e)}")
            return []
    
    def create_tag(self, tag: str, sha: str, message: str = "",
                  owner: Optional[str] = None, repo: Optional[str] = None) -> bool:
        """Create a new tag."""
        owner, repo = owner or self.owner, repo or self.repo
        try:
            # First create the tag object
            url = f"{self.base_url}/repos/{owner}/{repo}/git/tags"
            data = {
                "tag": tag,
                "message": message or f"Tag {tag}",
                "object": sha,
                "type": "commit"
            }
            
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            tag_sha = response.json().get("sha")
            
            # Then create the reference
            url = f"{self.base_url}/repos/{owner}/{repo}/git/refs"
            data = {
                "ref": f"refs/tags/{tag}",
                "sha": tag_sha
            }
            
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to create tag: {str(e)}")
            return False
    
    # Helper methods
    def _parse_pr(self, pr_data: Dict) -> Any:
        """Parse pull request data into a simple object."""
        class PR:
            def __init__(self, data):
                self.number = data.get("number")
                self.title = data.get("title")
                self.body = data.get("body")
                self.state = data.get("state")
                self.user = type('obj', (object,), {'login': data.get("user", {}).get("login")})() if data.get("user") else None
                self.head = type('obj', (object,), {'ref': data.get("head", {}).get("ref")})() if data.get("head") else None
                self.base = type('obj', (object,), {'ref': data.get("base", {}).get("ref")})() if data.get("base") else None
                self.mergeable = data.get("mergeable")
                self.merged = data.get("merged", False)
                self.draft = data.get("draft", False)
                self.created_at = data.get("created_at")
                self.updated_at = data.get("updated_at")
                self.html_url = data.get("html_url")
        
        return PR(pr_data)
