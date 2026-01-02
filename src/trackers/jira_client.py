"""Jira MCP Server - Model Context Protocol server for Jira integration."""
from typing import Any, List, Dict, Optional, Callable
from jira import JIRA
from pydantic import BaseModel, Field
from src.config import Config
import urllib3

# Disable SSL warnings for Jira connection
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Type alias for progress callback
ProgressCallback = Callable[[str], None]


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
        self.progress_callback: Optional[ProgressCallback] = None
        self._connect()
    
    def set_progress_callback(self, callback: Optional[ProgressCallback]):
        """Set a callback function for progress updates."""
        self.progress_callback = callback
    
    def _report_progress(self, message: str):
        """Report progress via callback if set, otherwise print."""
        if self.progress_callback:
            self.progress_callback(message)
        print(message)
    
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
        max_results: int = 50,
        issue_type: Optional[str] = None
    ) -> List[JiraIssue]:
        """
        Retrieve issues from Jira (bugs, stories, tasks, etc.).
        
        Args:
            project_key: Project key to filter by (default from config)
            status: List of statuses to filter by (e.g., ['Open', 'In Progress'])
            max_results: Maximum number of issues to return
            issue_type: Type of issue to fetch (Bug, Story, Task, Epic, etc.). If None, fetches all types.
            
        Returns:
            List of JiraIssue objects
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        project_key = project_key or Config.JIRA_PROJECT_KEY
        
        # Build JQL query
        jql_parts = [
            f'project = "{project_key}"'
        ]
        
        # Add issue type filter if specified
        if issue_type:
            # Map common variations to Jira issue types
            issue_type_map = {
                'bug': 'Bug',
                'bugs': 'Bug',
                'story': 'Story',
                'stories': 'Story',
                'user story': 'Story',
                'user stories': 'Story',
                'task': 'Task',
                'tasks': 'Task',
                'epic': 'Epic',
                'epics': 'Epic',
                'sub-task': 'Sub-task',
                'subtask': 'Sub-task'
            }
            mapped_type = issue_type_map.get(issue_type.lower(), issue_type)
            jql_parts.append(f'type = "{mapped_type}"')
        
        if status:
            status_str = ', '.join(f'"{s}"' for s in status)
            jql_parts.append(f'status IN ({status_str})')
        
        jql_query = ' AND '.join(jql_parts)
        jql_query += ' ORDER BY created DESC'
        
        self._report_progress(f"📥 Executing JQL: {jql_query}")
        
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
        
        issue_label = issue_type if issue_type else "issues"
        self._report_progress(f"✅ Retrieved {len(jira_issues)} {issue_label} from Jira (100%)")
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
            
        Note:
            Jira uses transitions (workflow steps), not direct status changes.
            Will try to find best matching transition automatically.
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            issue = self.jira_client.issue(issue_key)
            transitions = self.jira_client.transitions(issue)
            
            # Normalize the requested transition (lowercase, strip whitespace)
            requested = transition_name.lower().strip()
            
            # Try exact match first (case-insensitive)
            for t in transitions:
                if t['name'].lower().strip() == requested:
                    self.jira_client.transition_issue(issue, t['id'])
                    print(f"✓ Transitioned {issue_key} to '{t['name']}'")
                    return True
            
            # Try partial match (requested is contained in transition name)
            for t in transitions:
                if requested in t['name'].lower().strip():
                    self.jira_client.transition_issue(issue, t['id'])
                    print(f"✓ Transitioned {issue_key} to '{t['name']}' (partial match)")
                    return True
            
            # Try reverse partial match (transition name is contained in requested)
            for t in transitions:
                if t['name'].lower().strip() in requested:
                    self.jira_client.transition_issue(issue, t['id'])
                    print(f"✓ Transitioned {issue_key} to '{t['name']}' (reverse match)")
                    return True
            
            # Map common status names to transitions
            status_mapping = {
                'open': ['to do', 'open', 'new', 'backlog', 'reopen'],
                'todo': ['to do'],
                'in progress': ['in progress', 'start progress', 'in development'],
                'inprogress': ['in progress', 'start progress'],
                'started': ['in progress', 'start progress'],
                'done': ['done', 'close', 'closed', 'resolve', 'resolved', 'complete'],
                'closed': ['done', 'close', 'closed', 'resolve', 'resolved'],
                'resolved': ['done', 'resolve', 'resolved', 'close'],
                'complete': ['done', 'complete', 'close'],
                'reopen': ['reopen', 'to do', 'open'],
                'reopened': ['reopen', 'to do', 'open'],
            }
            
            # Try to find a matching transition from the mapping
            if requested in status_mapping:
                for possible in status_mapping[requested]:
                    for t in transitions:
                        if possible in t['name'].lower().strip():
                            self.jira_client.transition_issue(issue, t['id'])
                            print(f"✓ Transitioned {issue_key} to '{t['name']}' (mapped from '{transition_name}')")
                            return True
            
            # Show available transitions
            available = [t['name'] for t in transitions]
            raise Exception(f"Transition '{transition_name}' not found. Available: {available}")
        except Exception as e:
            error_msg = str(e)
            print(f"Failed to update status for {issue_key}: {error_msg}")
            raise Exception(f"Cannot transition {issue_key}: {error_msg}")

    # ==== NEW JIRA CAPABILITIES ====
    
    # Issue Management
    def create_issue(
        self,
        summary: str,
        issue_type: str = "Bug",
        description: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        components: Optional[List[str]] = None,
        project_key: Optional[str] = None
    ) -> Optional[JiraIssue]:
        """
        Create a new Jira issue.
        
        Args:
            summary: Issue summary/title
            issue_type: Type of issue (Bug, Story, Task, Epic, Sub-task)
            description: Issue description
            priority: Priority name (Highest, High, Medium, Low, Lowest)
            assignee: Username to assign
            labels: List of labels
            components: List of component names
            project_key: Project key (default from config)
            
        Returns:
            JiraIssue object if successful, None otherwise
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        project_key = project_key or Config.JIRA_PROJECT_KEY
        
        try:
            # Build issue fields
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'issuetype': {'name': issue_type}
            }
            
            if description:
                issue_dict['description'] = description
            if priority:
                issue_dict['priority'] = {'name': priority}
            if assignee:
                issue_dict['assignee'] = {'name': assignee}
            if labels:
                issue_dict['labels'] = labels
            if components:
                issue_dict['components'] = [{'name': c} for c in components]
            
            new_issue = self.jira_client.create_issue(fields=issue_dict)
            print(f"✓ Created issue: {new_issue.key}")
            return self.get_issue(new_issue.key)
        except Exception as e:
            print(f"Failed to create issue: {str(e)}")
            return None
    
    def update_issue(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        components: Optional[List[str]] = None
    ) -> bool:
        """
        Update an existing Jira issue.
        
        Args:
            issue_key: The Jira issue key
            summary: New summary
            description: New description
            priority: New priority
            assignee: New assignee username
            labels: New labels (replaces existing)
            components: New components (replaces existing)
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            issue = self.jira_client.issue(issue_key)
            fields = {}
            
            if summary:
                fields['summary'] = summary
            if description is not None:
                fields['description'] = description
            if priority:
                fields['priority'] = {'name': priority}
            if assignee is not None:
                fields['assignee'] = {'name': assignee} if assignee else None
            if labels is not None:
                fields['labels'] = labels
            if components is not None:
                fields['components'] = [{'name': c} for c in components]
            
            if fields:
                issue.update(fields=fields)
                print(f"✓ Updated issue: {issue_key}")
                return True
            return False
        except Exception as e:
            print(f"Failed to update issue {issue_key}: {str(e)}")
            return False
    
    def delete_issue(self, issue_key: str) -> bool:
        """
        Delete a Jira issue.
        
        Args:
            issue_key: The Jira issue key
            
        Returns:
            True if successful
            
        Note:
            Requires 'Delete Issues' permission in Jira project settings.
            Most users don't have this permission by default.
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            issue = self.jira_client.issue(issue_key)
            issue.delete()
            print(f"✓ Deleted issue: {issue_key}")
            return True
        except Exception as e:
            error_msg = str(e)
            if "permission" in error_msg.lower() or "403" in error_msg or "401" in error_msg:
                print(f"Permission denied: Cannot delete issue {issue_key}. You need 'Delete Issues' permission in Jira.")
            else:
                print(f"Failed to delete issue {issue_key}: {error_msg}")
            raise Exception(f"Cannot delete {issue_key}: {error_msg}")
    
    def assign_issue(self, issue_key: str, assignee: Optional[str]) -> bool:
        """
        Assign or unassign a user to/from an issue.
        
        Args:
            issue_key: The Jira issue key
            assignee: Username to assign (None to unassign)
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            self.jira_client.assign_issue(issue_key, assignee)
            action = f"assigned to {assignee}" if assignee else "unassigned"
            print(f"✓ Issue {issue_key} {action}")
            return True
        except Exception as e:
            print(f"Failed to assign issue {issue_key}: {str(e)}")
            return False
    
    def get_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get available workflow transitions for an issue.
        
        Args:
            issue_key: The Jira issue key
            
        Returns:
            List of available transitions with id and name
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            issue = self.jira_client.issue(issue_key)
            transitions = self.jira_client.transitions(issue)
            return [{'id': t['id'], 'name': t['name']} for t in transitions]
        except Exception as e:
            print(f"Failed to get transitions for {issue_key}: {str(e)}")
            return []
    
    def add_watchers(self, issue_key: str, usernames: List[str]) -> bool:
        """
        Add watchers to an issue.
        
        Args:
            issue_key: The Jira issue key
            usernames: List of usernames to add as watchers
            
        Returns:
            True if all watchers added successfully
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            for username in usernames:
                self.jira_client.add_watcher(issue_key, username)
            print(f"✓ Added {len(usernames)} watcher(s) to {issue_key}")
            return True
        except Exception as e:
            print(f"Failed to add watchers to {issue_key}: {str(e)}")
            return False
    
    def remove_watchers(self, issue_key: str, usernames: List[str]) -> bool:
        """
        Remove watchers from an issue.
        
        Args:
            issue_key: The Jira issue key
            usernames: List of usernames to remove
            
        Returns:
            True if all watchers removed successfully
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            for username in usernames:
                self.jira_client.remove_watcher(issue_key, username)
            print(f"✓ Removed {len(usernames)} watcher(s) from {issue_key}")
            return True
        except Exception as e:
            print(f"Failed to remove watchers from {issue_key}: {str(e)}")
            return False
    
    def get_watchers(self, issue_key: str) -> List[str]:
        """
        Get watchers of an issue.
        
        Args:
            issue_key: The Jira issue key
            
        Returns:
            List of watcher usernames
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            watchers = self.jira_client.watchers(issue_key)
            return [w.name for w in watchers.watchers]
        except Exception as e:
            print(f"Failed to get watchers for {issue_key}: {str(e)}")
            return []
    
    def link_issues(
        self,
        issue_key: str,
        target_issue_key: str,
        link_type: str = "Relates"
    ) -> bool:
        """
        Create a link between two issues.
        
        Args:
            issue_key: Source issue key
            target_issue_key: Target issue key
            link_type: Link type name (Relates, Blocks, Cloners, Duplicate, etc.)
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            self.jira_client.create_issue_link(
                type=link_type,
                inwardIssue=issue_key,
                outwardIssue=target_issue_key
            )
            print(f"✓ Linked {issue_key} → {target_issue_key} ({link_type})")
            return True
        except Exception as e:
            print(f"Failed to link issues: {str(e)}")
            return False
    
    def get_issue_links(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get all links for an issue.
        
        Args:
            issue_key: The Jira issue key
            
        Returns:
            List of issue links
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            issue = self.jira_client.issue(issue_key)
            links = []
            for link in issue.fields.issuelinks:
                link_info = {'type': link.type.name}
                if hasattr(link, 'outwardIssue'):
                    link_info['direction'] = 'outward'
                    link_info['issue'] = link.outwardIssue.key
                elif hasattr(link, 'inwardIssue'):
                    link_info['direction'] = 'inward'
                    link_info['issue'] = link.inwardIssue.key
                links.append(link_info)
            return links
        except Exception as e:
            print(f"Failed to get links for {issue_key}: {str(e)}")
            return []
    
    # Labels Management
    def add_labels(self, issue_key: str, labels: List[str]) -> bool:
        """
        Add labels to an issue.
        
        Args:
            issue_key: The Jira issue key
            labels: List of label names to add
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            issue = self.jira_client.issue(issue_key)
            existing_labels = issue.fields.labels or []
            new_labels = list(set(existing_labels + labels))
            issue.update(fields={'labels': new_labels})
            print(f"✓ Added labels to {issue_key}: {labels}")
            return True
        except Exception as e:
            print(f"Failed to add labels to {issue_key}: {str(e)}")
            return False
    
    def remove_labels(self, issue_key: str, labels: List[str]) -> bool:
        """
        Remove labels from an issue.
        
        Args:
            issue_key: The Jira issue key
            labels: List of label names to remove
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            issue = self.jira_client.issue(issue_key)
            existing_labels = issue.fields.labels or []
            new_labels = [l for l in existing_labels if l not in labels]
            issue.update(fields={'labels': new_labels})
            print(f"✓ Removed labels from {issue_key}: {labels}")
            return True
        except Exception as e:
            print(f"Failed to remove labels from {issue_key}: {str(e)}")
            return False
    
    # Comments Management
    def get_comments(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get all comments for an issue.
        
        Args:
            issue_key: The Jira issue key
            
        Returns:
            List of comments with id, author, body, created
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            comments = self.jira_client.comments(issue_key)
            return [{
                'id': c.id,
                'author': c.author.displayName,
                'body': c.body,
                'created': str(c.created),
                'updated': str(c.updated) if hasattr(c, 'updated') else None
            } for c in comments]
        except Exception as e:
            print(f"Failed to get comments for {issue_key}: {str(e)}")
            return []
    
    def edit_comment(self, issue_key: str, comment_id: str, new_body: str) -> bool:
        """
        Edit an existing comment.
        
        Args:
            issue_key: The Jira issue key
            comment_id: The comment ID
            new_body: New comment text
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            comment = self.jira_client.comment(issue_key, comment_id)
            comment.update(body=new_body)
            print(f"✓ Updated comment {comment_id} on {issue_key}")
            return True
        except Exception as e:
            print(f"Failed to edit comment on {issue_key}: {str(e)}")
            return False
    
    def delete_comment(self, issue_key: str, comment_id: str) -> bool:
        """
        Delete a comment.
        
        Args:
            issue_key: The Jira issue key
            comment_id: The comment ID
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            comment = self.jira_client.comment(issue_key, comment_id)
            comment.delete()
            print(f"✓ Deleted comment {comment_id} from {issue_key}")
            return True
        except Exception as e:
            print(f"Failed to delete comment on {issue_key}: {str(e)}")
            return False
    
    # Attachments
    def add_attachment(self, issue_key: str, file_path: str) -> bool:
        """
        Add an attachment to an issue.
        
        Args:
            issue_key: The Jira issue key
            file_path: Path to the file to attach
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            self.jira_client.add_attachment(issue=issue_key, attachment=file_path)
            print(f"✓ Added attachment to {issue_key}")
            return True
        except Exception as e:
            print(f"Failed to add attachment to {issue_key}: {str(e)}")
            return False
    
    def get_attachments(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get all attachments for an issue.
        
        Args:
            issue_key: The Jira issue key
            
        Returns:
            List of attachments with id, filename, size, created, author
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            issue = self.jira_client.issue(issue_key)
            attachments = issue.fields.attachment or []
            return [{
                'id': a.id,
                'filename': a.filename,
                'size': a.size,
                'created': str(a.created),
                'author': a.author.displayName,
                'content_url': a.content,
                'mime_type': getattr(a, 'mimeType', None)
            } for a in attachments]
        except Exception as e:
            print(f"Failed to get attachments for {issue_key}: {str(e)}")
            return []
    
    def download_attachment(self, attachment_id: str) -> Optional[bytes]:
        """
        Download attachment content by ID.
        
        Args:
            attachment_id: The attachment ID
            
        Returns:
            Attachment content as bytes, or None on failure
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            attachment = self.jira_client.attachment(attachment_id)
            content = attachment.get()
            return content
        except Exception as e:
            print(f"Failed to download attachment {attachment_id}: {str(e)}")
            return None
    
    def get_attachment_auth_header(self) -> Dict[str, str]:
        """
        Get authentication header for downloading attachments.
        
        Returns:
            Dictionary with Authorization header
        """
        import base64
        auth_string = f"{Config.JIRA_EMAIL}:{Config.JIRA_API_TOKEN}"
        encoded = base64.b64encode(auth_string.encode()).decode()
        return {'Authorization': f'Basic {encoded}'}
    
    def delete_attachment(self, attachment_id: str) -> bool:
        """
        Delete an attachment.
        
        Args:
            attachment_id: The attachment ID
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            attachment = self.jira_client.attachment(attachment_id)
            attachment.delete()
            print(f"✓ Deleted attachment {attachment_id}")
            return True
        except Exception as e:
            print(f"Failed to delete attachment {attachment_id}: {str(e)}")
            return False
    
    # Components
    def get_components(self, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all components for a project.
        
        Args:
            project_key: Project key (default from config)
            
        Returns:
            List of components with id, name, description
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        project_key = project_key or Config.JIRA_PROJECT_KEY
        
        try:
            components = self.jira_client.project_components(project_key)
            return [{
                'id': c.id,
                'name': c.name,
                'description': getattr(c, 'description', None),
                'lead': c.lead.displayName if hasattr(c, 'lead') and c.lead else None
            } for c in components]
        except Exception as e:
            print(f"Failed to get components for {project_key}: {str(e)}")
            return []
    
    def create_component(
        self,
        name: str,
        description: Optional[str] = None,
        lead_username: Optional[str] = None,
        project_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new component in a project.
        
        Args:
            name: Component name
            description: Component description
            lead_username: Component lead username
            project_key: Project key (default from config)
            
        Returns:
            Component info if successful, None otherwise
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        project_key = project_key or Config.JIRA_PROJECT_KEY
        
        try:
            component_dict = {
                'project': project_key,
                'name': name
            }
            if description:
                component_dict['description'] = description
            if lead_username:
                component_dict['leadUserName'] = lead_username
            
            component = self.jira_client.create_component(**component_dict)
            print(f"✓ Created component: {name}")
            return {
                'id': component.id,
                'name': component.name,
                'description': getattr(component, 'description', None)
            }
        except Exception as e:
            print(f"Failed to create component: {str(e)}")
            return None
    
    def add_components_to_issue(self, issue_key: str, components: List[str]) -> bool:
        """
        Add components to an issue.
        
        Args:
            issue_key: The Jira issue key
            components: List of component names to add
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            issue = self.jira_client.issue(issue_key)
            existing = [c.name for c in issue.fields.components] if issue.fields.components else []
            new_components = list(set(existing + components))
            issue.update(fields={'components': [{'name': c} for c in new_components]})
            print(f"✓ Added components to {issue_key}: {components}")
            return True
        except Exception as e:
            print(f"Failed to add components to {issue_key}: {str(e)}")
            return False
    
    def remove_components_from_issue(self, issue_key: str, components: List[str]) -> bool:
        """
        Remove components from an issue.
        
        Args:
            issue_key: The Jira issue key
            components: List of component names to remove
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            issue = self.jira_client.issue(issue_key)
            existing = [c.name for c in issue.fields.components] if issue.fields.components else []
            new_components = [c for c in existing if c not in components]
            issue.update(fields={'components': [{'name': c} for c in new_components]})
            print(f"✓ Removed components from {issue_key}: {components}")
            return True
        except Exception as e:
            print(f"Failed to remove components from {issue_key}: {str(e)}")
            return False
    
    # Versions / Releases
    def get_versions(self, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all versions for a project.
        
        Args:
            project_key: Project key (default from config)
            
        Returns:
            List of versions with id, name, description, released, releaseDate
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        project_key = project_key or Config.JIRA_PROJECT_KEY
        
        try:
            versions = self.jira_client.project_versions(project_key)
            return [{
                'id': v.id,
                'name': v.name,
                'description': getattr(v, 'description', None),
                'released': getattr(v, 'released', False),
                'releaseDate': getattr(v, 'releaseDate', None),
                'archived': getattr(v, 'archived', False)
            } for v in versions]
        except Exception as e:
            print(f"Failed to get versions for {project_key}: {str(e)}")
            return []
    
    def create_version(
        self,
        name: str,
        description: Optional[str] = None,
        release_date: Optional[str] = None,
        project_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new version/release in a project.
        
        Args:
            name: Version name
            description: Version description
            release_date: Release date (YYYY-MM-DD format)
            project_key: Project key (default from config)
            
        Returns:
            Version info if successful, None otherwise
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        project_key = project_key or Config.JIRA_PROJECT_KEY
        
        try:
            version_dict = {
                'project': project_key,
                'name': name
            }
            if description:
                version_dict['description'] = description
            if release_date:
                version_dict['releaseDate'] = release_date
            
            version = self.jira_client.create_version(**version_dict)
            print(f"✓ Created version: {name}")
            return {
                'id': version.id,
                'name': version.name,
                'description': getattr(version, 'description', None)
            }
        except Exception as e:
            print(f"Failed to create version: {str(e)}")
            return None
    
    def release_version(self, version_id: str) -> bool:
        """
        Mark a version as released.
        
        Args:
            version_id: The version ID
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            version = self.jira_client.version(version_id)
            version.update(released=True)
            print(f"✓ Released version {version_id}")
            return True
        except Exception as e:
            print(f"Failed to release version {version_id}: {str(e)}")
            return False
    
    def set_fix_version(self, issue_key: str, versions: List[str]) -> bool:
        """
        Set fix version(s) for an issue.
        
        Args:
            issue_key: The Jira issue key
            versions: List of version names
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            issue = self.jira_client.issue(issue_key)
            issue.update(fields={'fixVersions': [{'name': v} for v in versions]})
            print(f"✓ Set fix versions for {issue_key}: {versions}")
            return True
        except Exception as e:
            print(f"Failed to set fix version for {issue_key}: {str(e)}")
            return False
    
    def set_affects_version(self, issue_key: str, versions: List[str]) -> bool:
        """
        Set affects version(s) for an issue.
        
        Args:
            issue_key: The Jira issue key
            versions: List of version names
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            issue = self.jira_client.issue(issue_key)
            issue.update(fields={'versions': [{'name': v} for v in versions]})
            print(f"✓ Set affects versions for {issue_key}: {versions}")
            return True
        except Exception as e:
            print(f"Failed to set affects version for {issue_key}: {str(e)}")
            return False
    
    # Sprints & Agile (for Jira Software)
    def get_boards(self) -> List[Dict[str, Any]]:
        """
        Get all Agile boards.
        
        Returns:
            List of boards with id, name, type
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            boards = self.jira_client.boards()
            return [{
                'id': b.id,
                'name': b.name,
                'type': b.type
            } for b in boards]
        except Exception as e:
            print(f"Failed to get boards: {str(e)}")
            return []
    
    def get_sprints(self, board_id: int, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get sprints for a board.
        
        Args:
            board_id: The board ID
            state: Filter by state (active, future, closed)
            
        Returns:
            List of sprints with id, name, state, startDate, endDate
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            sprints = self.jira_client.sprints(board_id, state=state)
            return [{
                'id': s.id,
                'name': s.name,
                'state': s.state,
                'startDate': getattr(s, 'startDate', None),
                'endDate': getattr(s, 'endDate', None)
            } for s in sprints]
        except Exception as e:
            print(f"Failed to get sprints for board {board_id}: {str(e)}")
            return []
    
    def add_to_sprint(self, sprint_id: int, issue_keys: List[str]) -> bool:
        """
        Add issues to a sprint.
        
        Args:
            sprint_id: The sprint ID
            issue_keys: List of issue keys to add
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            self.jira_client.add_issues_to_sprint(sprint_id, issue_keys)
            print(f"✓ Added {len(issue_keys)} issues to sprint {sprint_id}")
            return True
        except Exception as e:
            print(f"Failed to add issues to sprint: {str(e)}")
            return False
    
    def get_sprint_issues(self, sprint_id: int) -> List[JiraIssue]:
        """
        Get all issues in a sprint.
        
        Args:
            sprint_id: The sprint ID
            
        Returns:
            List of JiraIssue objects
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            jql = f'Sprint = {sprint_id}'
            issues = self.jira_client.search_issues(
                jql,
                maxResults=100,
                fields='summary,description,issuetype,status,priority,assignee,reporter,created,updated,labels,components'
            )
            
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
            
            print(f"✓ Retrieved {len(jira_issues)} issues from sprint {sprint_id}")
            return jira_issues
        except Exception as e:
            print(f"Failed to get sprint issues: {str(e)}")
            return []
    
    # Users
    def search_users(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for users by name or email.
        
        Args:
            query: Search query (name or email)
            max_results: Maximum results to return
            
        Returns:
            List of users with accountId, displayName, emailAddress
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            users = self.jira_client.search_users(query, maxResults=max_results)
            return [{
                'accountId': getattr(u, 'accountId', None),
                'name': getattr(u, 'name', None),
                'displayName': u.displayName,
                'emailAddress': getattr(u, 'emailAddress', None),
                'active': getattr(u, 'active', True)
            } for u in users]
        except Exception as e:
            print(f"Failed to search users: {str(e)}")
            return []
    
    def get_assignable_users(
        self,
        issue_key: Optional[str] = None,
        project_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get users who can be assigned to issues.
        
        Args:
            issue_key: Specific issue key (optional)
            project_key: Project key (default from config)
            
        Returns:
            List of assignable users
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        project_key = project_key or Config.JIRA_PROJECT_KEY
        
        try:
            if issue_key:
                users = self.jira_client.search_assignable_users_for_issues(
                    '', issue_key=issue_key
                )
            else:
                users = self.jira_client.search_assignable_users_for_projects(
                    '', project_key=project_key
                )
            
            return [{
                'accountId': getattr(u, 'accountId', None),
                'name': getattr(u, 'name', None),
                'displayName': u.displayName,
                'emailAddress': getattr(u, 'emailAddress', None)
            } for u in users]
        except Exception as e:
            print(f"Failed to get assignable users: {str(e)}")
            return []
    
    # Projects
    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get all accessible projects.
        
        Returns:
            List of projects with key, name, id
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            projects = self.jira_client.projects()
            return [{
                'key': p.key,
                'name': p.name,
                'id': p.id
            } for p in projects]
        except Exception as e:
            print(f"Failed to get projects: {str(e)}")
            return []
    
    def get_project(self, project_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get detailed project information.
        
        Args:
            project_key: Project key (default from config)
            
        Returns:
            Project details if found
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        project_key = project_key or Config.JIRA_PROJECT_KEY
        
        try:
            project = self.jira_client.project(project_key)
            return {
                'key': project.key,
                'name': project.name,
                'id': project.id,
                'description': getattr(project, 'description', None),
                'lead': project.lead.displayName if hasattr(project, 'lead') and project.lead else None,
                'url': getattr(project, 'url', None)
            }
        except Exception as e:
            print(f"Failed to get project {project_key}: {str(e)}")
            return None
    
    # Advanced Search
    def jql_search(
        self,
        jql: str,
        max_results: int = 50,
        fields: Optional[List[str]] = None
    ) -> List[JiraIssue]:
        """
        Execute a custom JQL query.
        
        Args:
            jql: JQL query string
            max_results: Maximum results to return
            fields: List of fields to retrieve (default: standard fields)
            
        Returns:
            List of JiraIssue objects
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        default_fields = 'summary,description,issuetype,status,priority,assignee,reporter,created,updated,labels,components'
        
        try:
            print(f"Executing JQL: {jql}")
            issues = self.jira_client.search_issues(
                jql,
                maxResults=max_results,
                fields=','.join(fields) if fields else default_fields
            )
            
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
            
            print(f"✓ JQL returned {len(jira_issues)} issues")
            return jira_issues
        except Exception as e:
            print(f"JQL query failed: {str(e)}")
            return []
    
    # Meta Information
    def get_issue_types(self, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available issue types for a project.
        
        Args:
            project_key: Project key (default from config)
            
        Returns:
            List of issue types with id, name, description
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        project_key = project_key or Config.JIRA_PROJECT_KEY
        
        try:
            project = self.jira_client.project(project_key)
            return [{
                'id': it.id,
                'name': it.name,
                'description': getattr(it, 'description', None),
                'subtask': getattr(it, 'subtask', False)
            } for it in project.issueTypes]
        except Exception as e:
            print(f"Failed to get issue types: {str(e)}")
            return []
    
    def get_priorities(self) -> List[Dict[str, Any]]:
        """
        Get all available priorities.
        
        Returns:
            List of priorities with id, name, description
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            priorities = self.jira_client.priorities()
            return [{
                'id': p.id,
                'name': p.name,
                'description': getattr(p, 'description', None)
            } for p in priorities]
        except Exception as e:
            print(f"Failed to get priorities: {str(e)}")
            return []
    
    def get_statuses(self, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all available statuses for a project.
        
        Args:
            project_key: Project key (default from config)
            
        Returns:
            List of statuses with id, name, category
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            statuses = self.jira_client.statuses()
            return [{
                'id': s.id,
                'name': s.name,
                'description': getattr(s, 'description', None),
                'category': s.statusCategory.name if hasattr(s, 'statusCategory') else None
            } for s in statuses]
        except Exception as e:
            print(f"Failed to get statuses: {str(e)}")
            return []
    
    def get_link_types(self) -> List[Dict[str, Any]]:
        """
        Get all available issue link types.
        
        Returns:
            List of link types with name, inward, outward
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            link_types = self.jira_client.issue_link_types()
            return [{
                'id': lt.id,
                'name': lt.name,
                'inward': lt.inward,
                'outward': lt.outward
            } for lt in link_types]
        except Exception as e:
            print(f"Failed to get link types: {str(e)}")
            return []
    
    # Work Log
    def add_worklog(
        self,
        issue_key: str,
        time_spent: str,
        comment: Optional[str] = None
    ) -> bool:
        """
        Add a work log entry to an issue.
        
        Args:
            issue_key: The Jira issue key
            time_spent: Time spent (e.g., '2h', '30m', '1d')
            comment: Optional work log comment
            
        Returns:
            True if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            self.jira_client.add_worklog(
                issue=issue_key,
                timeSpent=time_spent,
                comment=comment
            )
            print(f"✓ Added worklog to {issue_key}: {time_spent}")
            return True
        except Exception as e:
            print(f"Failed to add worklog to {issue_key}: {str(e)}")
            return False
    
    def get_worklogs(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get all work logs for an issue.
        
        Args:
            issue_key: The Jira issue key
            
        Returns:
            List of work logs with author, timeSpent, comment, created
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            worklogs = self.jira_client.worklogs(issue_key)
            return [{
                'id': w.id,
                'author': w.author.displayName,
                'timeSpent': w.timeSpent,
                'timeSpentSeconds': w.timeSpentSeconds,
                'comment': getattr(w, 'comment', None),
                'created': str(w.created),
                'updated': str(w.updated)
            } for w in worklogs]
        except Exception as e:
            print(f"Failed to get worklogs for {issue_key}: {str(e)}")
            return []
    
    # Subtasks
    def create_subtask(
        self,
        parent_key: str,
        summary: str,
        description: Optional[str] = None,
        assignee: Optional[str] = None
    ) -> Optional[JiraIssue]:
        """
        Create a subtask under a parent issue.
        
        Args:
            parent_key: Parent issue key
            summary: Subtask summary
            description: Subtask description
            assignee: Assignee username
            
        Returns:
            JiraIssue object if successful
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            parent = self.jira_client.issue(parent_key)
            project_key = parent.fields.project.key
            
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'issuetype': {'name': 'Sub-task'},
                'parent': {'key': parent_key}
            }
            
            if description:
                issue_dict['description'] = description
            if assignee:
                issue_dict['assignee'] = {'name': assignee}
            
            new_issue = self.jira_client.create_issue(fields=issue_dict)
            print(f"✓ Created subtask: {new_issue.key} under {parent_key}")
            return self.get_issue(new_issue.key)
        except Exception as e:
            print(f"Failed to create subtask: {str(e)}")
            return None
    
    def get_subtasks(self, issue_key: str) -> List[JiraIssue]:
        """
        Get all subtasks of an issue.
        
        Args:
            issue_key: Parent issue key
            
        Returns:
            List of subtask JiraIssue objects
        """
        if not self.jira_client:
            raise ConnectionError("Not connected to Jira")
        
        try:
            issue = self.jira_client.issue(issue_key)
            subtasks = []
            
            if hasattr(issue.fields, 'subtasks') and issue.fields.subtasks:
                for st in issue.fields.subtasks:
                    subtasks.append(self.get_issue(st.key))
            
            return subtasks
        except Exception as e:
            print(f"Failed to get subtasks for {issue_key}: {str(e)}")
            return []
