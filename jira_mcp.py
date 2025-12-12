"""Jira MCP Server - Model Context Protocol server for Jira integration."""
from typing import Any, List, Dict, Optional
from jira import JIRA
from pydantic import BaseModel, Field
from config import Config
import urllib3

# Disable SSL warnings for Jira connection
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class JiraIssue(BaseModel):
    """Represents a Jira issue."""
    key: str
    summary: str
    description: Optional[str] = None
    issue_type: str
    status: str
    priority: Optional[str] = None
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    created: str
    updated: str
    labels: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


class JiraMCPServer:
    """MCP Server for Jira integration."""
    
    def __init__(self):
        """Initialize the Jira MCP server."""
        self.jira_client: Optional[JIRA] = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Jira."""
        try:
            # Create options with SSL verification disabled
            options = {
                'server': Config.JIRA_URL,
                'verify': False
            }
            
            self.jira_client = JIRA(
                options=options,
                basic_auth=(Config.JIRA_EMAIL, Config.JIRA_API_TOKEN)
            )
            print(f"✓ Connected to Jira: {Config.JIRA_URL}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Jira: {str(e)}")
    
    def get_bugs(
        self, 
        project_key: Optional[str] = None,
        status: Optional[List[str]] = None,
        max_results: int = 50
    ) -> List[JiraIssue]:
        """
        Retrieve bugs from Jira.
        
        Args:
            project_key: Project key to filter by (default from config)
            status: List of statuses to filter by (e.g., ['Open', 'In Progress'])
            max_results: Maximum number of issues to return
            
        Returns:
            List of JiraIssue objects
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        project_key = project_key or Config.JIRA_PROJECT_KEY
        
        # Build JQL query
        jql_parts = [
            f'project = "{project_key}"',
            'type = Bug'
        ]
        
        if status:
            status_str = ', '.join(f'"{s}"' for s in status)
            jql_parts.append(f'status IN ({status_str})')
        
        jql_query = ' AND '.join(jql_parts)
        jql_query += ' ORDER BY created DESC'
        
        print(f"Executing JQL: {jql_query}")
        
        # Fetch issues
        issues = self.jira_client.search_issues(
            jql_query,
            maxResults=max_results,
            fields='summary,description,issuetype,status,priority,assignee,reporter,created,updated,labels,components'
        )
        
        # Convert to JiraIssue objects
        jira_issues = []
        for issue in issues:
            jira_issue = JiraIssue(
                key=issue.key,
                summary=issue.fields.summary,
                description=getattr(issue.fields, 'description', None),
                issue_type=issue.fields.issuetype.name,
                status=issue.fields.status.name,
                priority=issue.fields.priority.name if issue.fields.priority else None,
                assignee=issue.fields.assignee.displayName if issue.fields.assignee else None,
                reporter=issue.fields.reporter.displayName if issue.fields.reporter else None,
                created=str(issue.fields.created),
                updated=str(issue.fields.updated),
                labels=issue.fields.labels or [],
                components=[c.name for c in issue.fields.components] or []
            )
            jira_issues.append(jira_issue)
        
        print(f"✓ Retrieved {len(jira_issues)} bugs from Jira")
        return jira_issues
    
    def get_issue(self, issue_key: str) -> JiraIssue:
        """
        Get a specific issue by key.
        
        Args:
            issue_key: The Jira issue key (e.g., 'PROJ-123')
            
        Returns:
            JiraIssue object
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        issue = self.jira_client.issue(issue_key)
        
        return JiraIssue(
            key=issue.key,
            summary=issue.fields.summary,
            description=getattr(issue.fields, 'description', None),
            issue_type=issue.fields.issuetype.name,
            status=issue.fields.status.name,
            priority=issue.fields.priority.name if issue.fields.priority else None,
            assignee=issue.fields.assignee.displayName if issue.fields.assignee else None,
            reporter=issue.fields.reporter.displayName if issue.fields.reporter else None,
            created=str(issue.fields.created),
            updated=str(issue.fields.updated),
            labels=issue.fields.labels or [],
            components=[c.name for c in issue.fields.components] or []
        )
    
    def add_comment(self, issue_key: str, comment: str) -> bool:
        """
        Add a comment to a Jira issue.
        
        Args:
            issue_key: The Jira issue key
            comment: Comment text to add
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            self.jira_client.add_comment(issue_key, comment)
            return True
        except Exception as e:
            print(f"Failed to add comment to {issue_key}: {str(e)}")
            return False
    
    def update_issue_status(self, issue_key: str, transition_name: str) -> bool:
        """
        Update the status of a Jira issue.
        
        Args:
            issue_key: The Jira issue key
            transition_name: Name of the transition (e.g., 'In Progress', 'Done')
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            issue = self.jira_client.issue(issue_key)
            transitions = self.jira_client.transitions(issue)
            
            for t in transitions:
                if t['name'].lower() == transition_name.lower():
                    self.jira_client.transition_issue(issue, t['id'])
                    return True
            
            print(f"Transition '{transition_name}' not found for {issue_key}")
            return False
        except Exception as e:
            print(f"Failed to update status for {issue_key}: {str(e)}")
            return False
