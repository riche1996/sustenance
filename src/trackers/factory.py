"""Bug Tracker Factory - Factory pattern to create bug tracker instances based on configuration."""
from typing import Union
from src.config import Config
from src.trackers.jira_client import JiraMCPServer, JiraIssue
from src.trackers.tfs_client import TfsMCPServer, TfsWorkItem
from src.trackers.github_client import GitHubMCPServer, GitHubIssue


# Type alias for all bug tracker issue types
BugIssue = Union[JiraIssue, TfsWorkItem, GitHubIssue]


class BugTrackerFactory:
    """Factory to create and manage bug tracker instances."""
    
    @staticmethod
    def create_tracker():
        """
        Create a bug tracker instance based on configuration.
        
        Returns:
            Bug tracker instance (JiraMCPServer, TfsMCPServer, or GitHubMCPServer)
        """
        tracker_type = Config.BUG_TRACKER.lower()
        
        if tracker_type == "jira":
            return JiraMCPServer()
        elif tracker_type == "tfs" or tracker_type == "azuredevops":
            return TfsMCPServer()
        elif tracker_type == "github":
            return GitHubMCPServer()
        else:
            raise ValueError(
                f"Unknown bug tracker type: {tracker_type}. "
                "Supported types: jira, tfs, github"
            )
    
    @staticmethod
    def get_tracker_name() -> str:
        """Get the configured tracker name."""
        return Config.BUG_TRACKER.lower()


class UnifiedBugTracker:
    """
    Unified interface for interacting with different bug tracking systems.
    Provides a common API regardless of the underlying tracker.
    """
    
    def __init__(self):
        """Initialize the unified bug tracker."""
        self.tracker = BugTrackerFactory.create_tracker()
        self.tracker_type = BugTrackerFactory.get_tracker_name()
    
    def get_bugs(self, max_results: int = 50, **kwargs):
        """
        Get bugs from the configured tracker.
        
        Args:
            max_results: Maximum number of bugs to retrieve
            **kwargs: Additional tracker-specific parameters
            
        Returns:
            List of bug issues (type depends on tracker)
        """
        if self.tracker_type == "jira":
            return self.tracker.get_bugs(
                status=kwargs.get('status'),
                max_results=max_results
            )
        elif self.tracker_type in ["tfs", "azuredevops"]:
            return self.tracker.get_bugs(
                state=kwargs.get('state'),
                max_results=max_results
            )
        elif self.tracker_type == "github":
            return self.tracker.get_bugs(
                state=kwargs.get('state', 'open'),
                labels=kwargs.get('labels'),
                max_results=max_results
            )
    
    def get_issue(self, issue_id):
        """
        Get a specific issue by ID.
        
        Args:
            issue_id: Issue identifier (key for Jira, ID for TFS, number for GitHub)
            
        Returns:
            Bug issue object
        """
        if self.tracker_type == "jira":
            return self.tracker.get_issue(issue_id)
        elif self.tracker_type in ["tfs", "azuredevops"]:
            return self.tracker.get_work_item(int(issue_id))
        elif self.tracker_type == "github":
            return self.tracker.get_issue(int(issue_id))
    
    def add_comment(self, issue_id, comment: str) -> bool:
        """
        Add a comment to an issue.
        
        Args:
            issue_id: Issue identifier
            comment: Comment text
            
        Returns:
            True if successful
        """
        if self.tracker_type == "jira":
            return self.tracker.add_comment(issue_id, comment)
        elif self.tracker_type in ["tfs", "azuredevops"]:
            return self.tracker.add_comment(int(issue_id), comment)
        elif self.tracker_type == "github":
            return self.tracker.add_comment(int(issue_id), comment)
    
    def update_status(self, issue_id, new_status: str) -> bool:
        """
        Update the status/state of an issue.
        
        Args:
            issue_id: Issue identifier
            new_status: New status/state
            
        Returns:
            True if successful
        """
        if self.tracker_type == "jira":
            return self.tracker.update_issue_status(issue_id, new_status)
        elif self.tracker_type in ["tfs", "azuredevops"]:
            return self.tracker.update_work_item_state(int(issue_id), new_status)
        elif self.tracker_type == "github":
            return self.tracker.update_issue_state(int(issue_id), new_status)
    
    def format_bug_description(self, bug) -> str:
        """
        Format bug information into a consistent description string.
        
        Args:
            bug: Bug issue object (any tracker type)
            
        Returns:
            Formatted bug description
        """
        if self.tracker_type == "jira":
            return f"""
Bug Key: {bug.key}
Summary: {bug.summary}
Status: {bug.status}
Priority: {bug.priority or 'N/A'}
Description: {bug.description or 'No description provided'}
Created: {bug.created}
Reporter: {bug.reporter or 'Unknown'}
"""
        elif self.tracker_type in ["tfs", "azuredevops"]:
            return f"""
Work Item ID: {bug.id}
Title: {bug.title}
State: {bug.state}
Priority: {bug.priority or 'N/A'}
Severity: {bug.severity or 'N/A'}
Description: {bug.description or 'No description provided'}
Created: {bug.created_date}
Created By: {bug.created_by or 'Unknown'}
"""
        elif self.tracker_type == "github":
            return f"""
Issue Number: #{bug.number}
Title: {bug.title}
State: {bug.state}
Labels: {', '.join(bug.labels)}
Body: {bug.body or 'No description provided'}
Created: {bug.created_at}
Created By: {bug.created_by or 'Unknown'}
URL: {bug.html_url}
"""
        else:
            return str(bug)
    
    def get_bug_identifier(self, bug) -> str:
        """
        Get the unique identifier for a bug.
        
        Args:
            bug: Bug issue object (any tracker type)
            
        Returns:
            Bug identifier as string
        """
        if self.tracker_type == "jira":
            return bug.key
        elif self.tracker_type in ["tfs", "azuredevops"]:
            return str(bug.id)
        elif self.tracker_type == "github":
            return f"#{bug.number}"
        else:
            return str(bug)
    
    def get_bug_summary(self, bug) -> str:
        """
        Get the summary/title of a bug.
        
        Args:
            bug: Bug issue object (any tracker type)
            
        Returns:
            Bug summary/title
        """
        if self.tracker_type == "jira":
            return bug.summary
        elif self.tracker_type in ["tfs", "azuredevops"]:
            return bug.title
        elif self.tracker_type == "github":
            return bug.title
        else:
            return str(bug)
