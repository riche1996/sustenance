"""TFS/Azure DevOps MCP Server - Model Context Protocol server for Azure DevOps integration."""
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field
from src.config import Config
import requests
from requests.auth import HTTPBasicAuth
import base64
import urllib3
import json
import os

# Disable SSL warnings for on-premises TFS servers
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TfsWorkItem(BaseModel):
    """Represents a TFS/Azure DevOps work item."""
    id: int
    title: str
    description: Optional[str] = None
    work_item_type: str
    state: str
    priority: Optional[int] = None
    severity: Optional[str] = None
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    created_date: str
    changed_date: str
    tags: List[str] = Field(default_factory=list)
    area_path: Optional[str] = None
    iteration_path: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class TfsComment(BaseModel):
    """Represents a TFS work item comment."""
    id: int
    text: str
    created_by: Optional[str] = None
    created_date: str
    modified_date: Optional[str] = None


class TfsAttachment(BaseModel):
    """Represents a TFS work item attachment."""
    id: str
    name: str
    url: str
    size: int
    created_date: str
    created_by: Optional[str] = None


class TfsIteration(BaseModel):
    """Represents a TFS iteration/sprint."""
    id: str
    name: str
    path: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    state: Optional[str] = None


class TfsArea(BaseModel):
    """Represents a TFS area."""
    id: str
    name: str
    path: str


class TfsTeam(BaseModel):
    """Represents a TFS team."""
    id: str
    name: str
    description: Optional[str] = None
    url: str


class TfsQuery(BaseModel):
    """Represents a TFS saved query."""
    id: str
    name: str
    path: str
    query_type: str
    is_folder: bool


class TfsMCPServer:
    """MCP Server for TFS/Azure DevOps integration."""
    
    def __init__(self):
        """Initialize the TFS MCP server."""
        self.base_url = Config.TFS_URL.rstrip('/')
        self.project = Config.TFS_PROJECT
        self.pat = Config.TFS_PAT
        self.organization = Config.TFS_ORGANIZATION
        
        # Detect if it's cloud (dev.azure.com) or on-premises TFS
        self.is_cloud = 'dev.azure.com' in self.base_url.lower()
        
        # Set up authentication
        self.auth = HTTPBasicAuth('', self.pat)
        self.headers = {
            'Content-Type': 'application/json'
        }
        
        self._validate_connection()
    
    def _validate_connection(self):
        """Validate connection to TFS/Azure DevOps."""
        try:
            # Test connection with a simple API call
            if self.is_cloud:
                # Azure DevOps Cloud format: https://dev.azure.com/{org}/{project}/_apis/...
                url = f"{self.base_url}/{self.organization}/{self.project}/_apis/projects/{self.project}?api-version=7.1"
            else:
                # On-premises TFS format: https://{server}/{collection}/_apis/projects/{project}
                # The organization is the collection name in on-premises TFS
                url = f"{self.base_url}/{self.organization}/_apis/projects/{self.project}?api-version=5.0"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            server_type = "Azure DevOps Cloud" if self.is_cloud else "TFS On-Premises"
            print(f"✓ Connected to {server_type}: {self.base_url}/{self.organization}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to TFS/Azure DevOps: {str(e)}")
    
    def get_bugs(
        self, 
        project: Optional[str] = None,
        state: Optional[List[str]] = None,
        max_results: int = 50
    ) -> List[TfsWorkItem]:
        """
        Retrieve bugs from TFS/Azure DevOps.
        
        Args:
            project: Project name to filter by (default from config)
            state: List of states to filter by (e.g., ['New', 'Active', 'Resolved'])
            max_results: Maximum number of work items to return
            
        Returns:
            List of TfsWorkItem objects
        """
        project = project or self.project
        
        # Build WIQL query - use only standard fields available in all projects
        # Note: Some fields like Priority/Severity may not exist in all project templates
        wiql_query = """
        SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [System.CreatedBy],
               [System.CreatedDate], [System.ChangedDate], [System.Tags],
               [System.AreaPath], [System.IterationPath], [System.Description]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Bug'
        """
        
        if state:
            state_values = "', '".join(state)
            wiql_query += f" AND [System.State] IN ('{state_values}')"
        
        wiql_query += " ORDER BY [System.CreatedDate] DESC"
        
        print(f"Executing WIQL query for project: {project}")
        
        # Execute WIQL query - use project in URL path for both cloud and on-premises
        api_version = "7.1" if self.is_cloud else "5.0"
        url = f"{self.base_url}/{self.organization}/{project}/_apis/wit/wiql?api-version={api_version}"
        wiql_body = {"query": wiql_query}
        
        response = requests.post(url, json=wiql_body, auth=self.auth, headers=self.headers, verify=False)
        response.raise_for_status()
        
        work_items_refs = response.json().get('workItems', [])[:max_results]
        
        if not work_items_refs:
            print("✓ No bugs found")
            return []
        
        # Get full work item details
        work_item_ids = [str(item['id']) for item in work_items_refs]
        ids_param = ','.join(work_item_ids)
        
        # Use project in URL path for work items API
        api_version = "7.1" if self.is_cloud else "5.0"
        url = f"{self.base_url}/{self.organization}/{project}/_apis/wit/workitems?ids={ids_param}&api-version={api_version}"
        response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
        response.raise_for_status()
        
        work_items_data = response.json().get('value', [])
        
        # Convert to TfsWorkItem objects
        tfs_work_items = []
        for item in work_items_data:
            fields = item.get('fields', {})
            
            # Extract assigned to and created by (handle complex objects)
            assigned_to = fields.get('System.AssignedTo', {})
            if isinstance(assigned_to, dict):
                assigned_to = assigned_to.get('displayName', None)
            
            created_by = fields.get('System.CreatedBy', {})
            if isinstance(created_by, dict):
                created_by = created_by.get('displayName', None)
            
            # Parse tags
            tags_str = fields.get('System.Tags', '')
            tags = [tag.strip() for tag in tags_str.split(';') if tag.strip()] if tags_str else []
            
            work_item = TfsWorkItem(
                id=item['id'],
                title=fields.get('System.Title', ''),
                description=fields.get('System.Description', None),
                work_item_type=fields.get('System.WorkItemType', 'Bug'),
                state=fields.get('System.State', ''),
                priority=fields.get('System.Priority', None),
                severity=fields.get('Microsoft.VSTS.Common.Severity', None),
                assigned_to=assigned_to,
                created_by=created_by,
                created_date=fields.get('System.CreatedDate', ''),
                changed_date=fields.get('System.ChangedDate', ''),
                tags=tags,
                area_path=fields.get('System.AreaPath', None),
                iteration_path=fields.get('System.IterationPath', None)
            )
            tfs_work_items.append(work_item)
        
        print(f"✓ Retrieved {len(tfs_work_items)} bugs from Azure DevOps")
        return tfs_work_items
    
    def get_work_item(self, work_item_id: int) -> TfsWorkItem:
        """
        Get a specific work item by ID.
        
        Args:
            work_item_id: The work item ID
            
        Returns:
            TfsWorkItem object
        """
        api_version = "7.1" if self.is_cloud else "5.0"
        url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}?api-version={api_version}"
        response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
        response.raise_for_status()
        
        item = response.json()
        fields = item.get('fields', {})
        
        # Extract assigned to and created by
        assigned_to = fields.get('System.AssignedTo', {})
        if isinstance(assigned_to, dict):
            assigned_to = assigned_to.get('displayName', None)
        
        created_by = fields.get('System.CreatedBy', {})
        if isinstance(created_by, dict):
            created_by = created_by.get('displayName', None)
        
        # Parse tags
        tags_str = fields.get('System.Tags', '')
        tags = [tag.strip() for tag in tags_str.split(';') if tag.strip()] if tags_str else []
        
        return TfsWorkItem(
            id=item['id'],
            title=fields.get('System.Title', ''),
            description=fields.get('System.Description', None),
            work_item_type=fields.get('System.WorkItemType', 'Bug'),
            state=fields.get('System.State', ''),
            priority=fields.get('System.Priority', None),
            severity=fields.get('Microsoft.VSTS.Common.Severity', None),
            assigned_to=assigned_to,
            created_by=created_by,
            created_date=fields.get('System.CreatedDate', ''),
            changed_date=fields.get('System.ChangedDate', ''),
            tags=tags,
            area_path=fields.get('System.AreaPath', None),
            iteration_path=fields.get('System.IterationPath', None)
        )
    
    def add_comment(self, work_item_id: int, comment: str) -> bool:
        """
        Add a comment to a work item.
        
        Args:
            work_item_id: The work item ID
            comment: Comment text to add
            
        Returns:
            True if successful
        """
        try:
            api_version = "7.1-preview.3" if self.is_cloud else "5.0-preview.3"
            url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}/comments?api-version={api_version}"
            body = {"text": comment}
            
            response = requests.post(url, json=body, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to add comment to work item {work_item_id}: {str(e)}")
            return False
    
    def update_work_item_state(self, work_item_id: int, new_state: str) -> bool:
        """
        Update the state of a work item.
        
        Args:
            work_item_id: The work item ID
            new_state: New state (e.g., 'Active', 'Resolved', 'Closed')
            
        Returns:
            True if successful
        """
        try:
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}?api-version={api_version}"
            
            # Azure DevOps uses JSON Patch format
            patch_document = [
                {
                    "op": "add",
                    "path": "/fields/System.State",
                    "value": new_state
                }
            ]
            
            headers = self.headers.copy()
            headers['Content-Type'] = 'application/json-patch+json'
            
            response = requests.patch(url, json=patch_document, auth=self.auth, headers=headers, verify=False)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to update state for work item {work_item_id}: {str(e)}")
            return False

    # ==================== WORK ITEM CRUD ====================
    
    def create_work_item(
        self,
        title: str,
        work_item_type: str = "Bug",
        description: Optional[str] = None,
        assigned_to: Optional[str] = None,
        area_path: Optional[str] = None,
        iteration_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[int] = None,
        project: Optional[str] = None
    ) -> Optional[TfsWorkItem]:
        """
        Create a new work item.
        
        Args:
            title: Work item title
            work_item_type: Type of work item (Bug, Task, User Story, etc.)
            description: Work item description (HTML allowed)
            assigned_to: User to assign to
            area_path: Area path
            iteration_path: Iteration path
            tags: List of tags
            priority: Priority (1-4)
            project: Project name (default from config)
            
        Returns:
            Created TfsWorkItem or None
        """
        try:
            project = project or self.project
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/{project}/_apis/wit/workitems/${work_item_type}?api-version={api_version}"
            
            patch_document = [
                {"op": "add", "path": "/fields/System.Title", "value": title}
            ]
            
            if description:
                patch_document.append({"op": "add", "path": "/fields/System.Description", "value": description})
            if assigned_to:
                patch_document.append({"op": "add", "path": "/fields/System.AssignedTo", "value": assigned_to})
            if area_path:
                patch_document.append({"op": "add", "path": "/fields/System.AreaPath", "value": area_path})
            if iteration_path:
                patch_document.append({"op": "add", "path": "/fields/System.IterationPath", "value": iteration_path})
            if tags:
                patch_document.append({"op": "add", "path": "/fields/System.Tags", "value": "; ".join(tags)})
            if priority:
                patch_document.append({"op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": priority})
            
            headers = self.headers.copy()
            headers['Content-Type'] = 'application/json-patch+json'
            
            response = requests.post(url, json=patch_document, auth=self.auth, headers=headers, verify=False)
            response.raise_for_status()
            
            item = response.json()
            return self._parse_work_item(item)
        except Exception as e:
            print(f"Failed to create work item: {str(e)}")
            return None
    
    def update_work_item(
        self,
        work_item_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        assigned_to: Optional[str] = None,
        state: Optional[str] = None,
        area_path: Optional[str] = None,
        iteration_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[int] = None
    ) -> bool:
        """
        Update a work item.
        
        Args:
            work_item_id: Work item ID
            title: New title
            description: New description
            assigned_to: New assignee
            state: New state
            area_path: New area path
            iteration_path: New iteration path
            tags: New tags (replaces existing)
            priority: New priority
            
        Returns:
            True if successful
        """
        try:
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}?api-version={api_version}"
            
            patch_document = []
            
            if title is not None:
                patch_document.append({"op": "add", "path": "/fields/System.Title", "value": title})
            if description is not None:
                patch_document.append({"op": "add", "path": "/fields/System.Description", "value": description})
            if assigned_to is not None:
                patch_document.append({"op": "add", "path": "/fields/System.AssignedTo", "value": assigned_to})
            if state is not None:
                patch_document.append({"op": "add", "path": "/fields/System.State", "value": state})
            if area_path is not None:
                patch_document.append({"op": "add", "path": "/fields/System.AreaPath", "value": area_path})
            if iteration_path is not None:
                patch_document.append({"op": "add", "path": "/fields/System.IterationPath", "value": iteration_path})
            if tags is not None:
                patch_document.append({"op": "add", "path": "/fields/System.Tags", "value": "; ".join(tags)})
            if priority is not None:
                patch_document.append({"op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": priority})
            
            if not patch_document:
                return True  # Nothing to update
            
            headers = self.headers.copy()
            headers['Content-Type'] = 'application/json-patch+json'
            
            response = requests.patch(url, json=patch_document, auth=self.auth, headers=headers, verify=False)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to update work item {work_item_id}: {str(e)}")
            return False
    
    def delete_work_item(self, work_item_id: int, destroy: bool = False) -> bool:
        """
        Delete a work item (moves to recycle bin or permanently deletes).
        
        Args:
            work_item_id: Work item ID
            destroy: If True, permanently delete. If False, move to recycle bin.
            
        Returns:
            True if successful
        """
        try:
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}?api-version={api_version}"
            if destroy:
                url += "&destroy=true"
            
            response = requests.delete(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to delete work item {work_item_id}: {str(e)}")
            return False
    
    # ==================== COMMENTS ====================
    
    def get_comments(self, work_item_id: int) -> List[TfsComment]:
        """
        Get all comments on a work item.
        
        Args:
            work_item_id: Work item ID
            
        Returns:
            List of TfsComment objects
        """
        try:
            api_version = "7.1-preview.3" if self.is_cloud else "5.0-preview.3"
            url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}/comments?api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            comments_data = response.json().get('comments', [])
            comments = []
            for c in comments_data:
                created_by = c.get('createdBy', {})
                if isinstance(created_by, dict):
                    created_by = created_by.get('displayName', None)
                
                comments.append(TfsComment(
                    id=c['id'],
                    text=c.get('text', ''),
                    created_by=created_by,
                    created_date=c.get('createdDate', ''),
                    modified_date=c.get('modifiedDate')
                ))
            return comments
        except Exception as e:
            print(f"Failed to get comments for work item {work_item_id}: {str(e)}")
            return []
    
    def update_comment(self, work_item_id: int, comment_id: int, text: str) -> bool:
        """
        Update a comment on a work item.
        
        Args:
            work_item_id: Work item ID
            comment_id: Comment ID
            text: New comment text
            
        Returns:
            True if successful
        """
        try:
            api_version = "7.1-preview.3" if self.is_cloud else "5.0-preview.3"
            url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}/comments/{comment_id}?api-version={api_version}"
            body = {"text": text}
            
            response = requests.patch(url, json=body, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to update comment {comment_id}: {str(e)}")
            return False
    
    def delete_comment(self, work_item_id: int, comment_id: int) -> bool:
        """
        Delete a comment from a work item.
        
        Args:
            work_item_id: Work item ID
            comment_id: Comment ID
            
        Returns:
            True if successful
        """
        try:
            api_version = "7.1-preview.3" if self.is_cloud else "5.0-preview.3"
            url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}/comments/{comment_id}?api-version={api_version}"
            
            response = requests.delete(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to delete comment {comment_id}: {str(e)}")
            return False
    
    # ==================== ATTACHMENTS ====================
    
    def get_attachments(self, work_item_id: int) -> List[TfsAttachment]:
        """
        Get all attachments on a work item.
        
        Args:
            work_item_id: Work item ID
            
        Returns:
            List of TfsAttachment objects
        """
        try:
            # Get work item with relations to find attachments
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}?$expand=relations&api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            item = response.json()
            relations = item.get('relations', [])
            
            attachments = []
            for rel in relations:
                if rel.get('rel') == 'AttachedFile':
                    attrs = rel.get('attributes', {})
                    attachments.append(TfsAttachment(
                        id=attrs.get('id', ''),
                        name=attrs.get('name', ''),
                        url=rel.get('url', ''),
                        size=attrs.get('resourceSize', 0),
                        created_date=attrs.get('resourceCreatedDate', ''),
                        created_by=attrs.get('authorizedDate')
                    ))
            return attachments
        except Exception as e:
            print(f"Failed to get attachments for work item {work_item_id}: {str(e)}")
            return []
    
    def add_attachment(self, work_item_id: int, file_path: str) -> bool:
        """
        Add an attachment to a work item.
        
        Args:
            work_item_id: Work item ID
            file_path: Path to the file to attach
            
        Returns:
            True if successful
        """
        try:
            # First upload the attachment
            file_name = os.path.basename(file_path)
            api_version = "7.1" if self.is_cloud else "5.0"
            upload_url = f"{self.base_url}/{self.organization}/_apis/wit/attachments?fileName={file_name}&api-version={api_version}"
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            upload_headers = self.headers.copy()
            upload_headers['Content-Type'] = 'application/octet-stream'
            
            response = requests.post(upload_url, data=file_content, auth=self.auth, headers=upload_headers, verify=False)
            response.raise_for_status()
            
            attachment_url = response.json().get('url')
            
            # Then link it to the work item
            patch_url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}?api-version={api_version}"
            patch_document = [
                {
                    "op": "add",
                    "path": "/relations/-",
                    "value": {
                        "rel": "AttachedFile",
                        "url": attachment_url
                    }
                }
            ]
            
            patch_headers = self.headers.copy()
            patch_headers['Content-Type'] = 'application/json-patch+json'
            
            response = requests.patch(patch_url, json=patch_document, auth=self.auth, headers=patch_headers, verify=False)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to add attachment to work item {work_item_id}: {str(e)}")
            return False
    
    def delete_attachment(self, work_item_id: int, attachment_url: str) -> bool:
        """
        Remove an attachment from a work item.
        
        Args:
            work_item_id: Work item ID
            attachment_url: URL of the attachment to remove
            
        Returns:
            True if successful
        """
        try:
            # Get current relations
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}?$expand=relations&api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            item = response.json()
            relations = item.get('relations', [])
            
            # Find the index of the attachment
            for idx, rel in enumerate(relations):
                if rel.get('url') == attachment_url:
                    patch_url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}?api-version={api_version}"
                    patch_document = [
                        {"op": "remove", "path": f"/relations/{idx}"}
                    ]
                    
                    patch_headers = self.headers.copy()
                    patch_headers['Content-Type'] = 'application/json-patch+json'
                    
                    response = requests.patch(patch_url, json=patch_document, auth=self.auth, headers=patch_headers, verify=False)
                    response.raise_for_status()
                    return True
            
            return False
        except Exception as e:
            print(f"Failed to delete attachment from work item {work_item_id}: {str(e)}")
            return False
    
    def download_attachment(self, attachment_url: str) -> Optional[bytes]:
        """
        Download attachment content from TFS/Azure DevOps.
        
        Args:
            attachment_url: URL of the attachment to download
            
        Returns:
            Attachment content as bytes, or None if failed
        """
        try:
            response = requests.get(attachment_url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Failed to download attachment from {attachment_url}: {str(e)}")
            return None
    
    def get_attachment_auth_header(self) -> Optional[Dict[str, str]]:
        """
        Get authentication header for downloading TFS attachments.
        
        Returns:
            Dictionary with Authorization header, or None if not available
        """
        try:
            if self.auth:
                # Use Basic auth for TFS
                import base64
                if isinstance(self.auth, tuple):
                    username, password = self.auth
                    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                    return {"Authorization": f"Basic {credentials}"}
                elif hasattr(self.auth, '__call__'):
                    # HTTPBasicAuth object
                    credentials = base64.b64encode(f":{self.pat}".encode()).decode()
                    return {"Authorization": f"Basic {credentials}"}
            return None
        except Exception as e:
            print(f"Failed to get TFS auth header: {str(e)}")
            return None
    
    # ==================== WORK ITEM LINKS ====================
    
    def get_work_item_links(self, work_item_id: int) -> List[Dict[str, Any]]:
        """
        Get all links on a work item.
        
        Args:
            work_item_id: Work item ID
            
        Returns:
            List of link dictionaries
        """
        try:
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}?$expand=relations&api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            item = response.json()
            relations = item.get('relations', [])
            
            links = []
            for rel in relations:
                if rel.get('rel') != 'AttachedFile':  # Exclude attachments
                    links.append({
                        "type": rel.get('rel'),
                        "url": rel.get('url'),
                        "attributes": rel.get('attributes', {})
                    })
            return links
        except Exception as e:
            print(f"Failed to get links for work item {work_item_id}: {str(e)}")
            return []
    
    def link_work_items(self, source_id: int, target_id: int, link_type: str = "System.LinkTypes.Related") -> bool:
        """
        Link two work items.
        
        Args:
            source_id: Source work item ID
            target_id: Target work item ID
            link_type: Link type (e.g., System.LinkTypes.Related, System.LinkTypes.Hierarchy-Forward)
            
        Returns:
            True if successful
        """
        try:
            api_version = "7.1" if self.is_cloud else "5.0"
            
            # Get target URL
            target_url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{target_id}"
            
            patch_url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{source_id}?api-version={api_version}"
            patch_document = [
                {
                    "op": "add",
                    "path": "/relations/-",
                    "value": {
                        "rel": link_type,
                        "url": target_url
                    }
                }
            ]
            
            headers = self.headers.copy()
            headers['Content-Type'] = 'application/json-patch+json'
            
            response = requests.patch(patch_url, json=patch_document, auth=self.auth, headers=headers, verify=False)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to link work items {source_id} -> {target_id}: {str(e)}")
            return False
    
    def get_link_types(self) -> List[Dict[str, Any]]:
        """
        Get all available work item link types.
        
        Returns:
            List of link type dictionaries
        """
        try:
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/_apis/wit/workitemrelationtypes?api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            return response.json().get('value', [])
        except Exception as e:
            print(f"Failed to get link types: {str(e)}")
            return []
    
    # ==================== TAGS ====================
    
    def add_tags(self, work_item_id: int, tags: List[str]) -> bool:
        """
        Add tags to a work item.
        
        Args:
            work_item_id: Work item ID
            tags: List of tags to add
            
        Returns:
            True if successful
        """
        try:
            # Get current tags
            item = self.get_work_item(work_item_id)
            current_tags = item.tags if item else []
            
            # Merge tags
            all_tags = list(set(current_tags + tags))
            
            return self.update_work_item(work_item_id, tags=all_tags)
        except Exception as e:
            print(f"Failed to add tags to work item {work_item_id}: {str(e)}")
            return False
    
    def remove_tags(self, work_item_id: int, tags: List[str]) -> bool:
        """
        Remove tags from a work item.
        
        Args:
            work_item_id: Work item ID
            tags: List of tags to remove
            
        Returns:
            True if successful
        """
        try:
            # Get current tags
            item = self.get_work_item(work_item_id)
            current_tags = item.tags if item else []
            
            # Remove specified tags
            new_tags = [t for t in current_tags if t not in tags]
            
            return self.update_work_item(work_item_id, tags=new_tags)
        except Exception as e:
            print(f"Failed to remove tags from work item {work_item_id}: {str(e)}")
            return False
    
    # ==================== ITERATIONS & AREAS ====================
    
    def get_iterations(self, project: Optional[str] = None, depth: int = 2) -> List[TfsIteration]:
        """
        Get iterations/sprints for a project.
        
        Args:
            project: Project name (default from config)
            depth: Depth of iteration hierarchy to return
            
        Returns:
            List of TfsIteration objects
        """
        try:
            project = project or self.project
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/{project}/_apis/wit/classificationnodes/Iterations?$depth={depth}&api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            def parse_iterations(node, path=""):
                iterations = []
                current_path = f"{path}\\{node['name']}" if path else node['name']
                
                attrs = node.get('attributes', {})
                iterations.append(TfsIteration(
                    id=str(node.get('id', '')),
                    name=node.get('name', ''),
                    path=current_path,
                    start_date=attrs.get('startDate'),
                    end_date=attrs.get('finishDate'),
                    state=attrs.get('timeFrame')
                ))
                
                for child in node.get('children', []):
                    iterations.extend(parse_iterations(child, current_path))
                
                return iterations
            
            root = response.json()
            return parse_iterations(root)
        except Exception as e:
            print(f"Failed to get iterations: {str(e)}")
            return []
    
    def get_areas(self, project: Optional[str] = None, depth: int = 2) -> List[TfsArea]:
        """
        Get areas for a project.
        
        Args:
            project: Project name (default from config)
            depth: Depth of area hierarchy to return
            
        Returns:
            List of TfsArea objects
        """
        try:
            project = project or self.project
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/{project}/_apis/wit/classificationnodes/Areas?$depth={depth}&api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            def parse_areas(node, path=""):
                areas = []
                current_path = f"{path}\\{node['name']}" if path else node['name']
                
                areas.append(TfsArea(
                    id=str(node.get('id', '')),
                    name=node.get('name', ''),
                    path=current_path
                ))
                
                for child in node.get('children', []):
                    areas.extend(parse_areas(child, current_path))
                
                return areas
            
            root = response.json()
            return parse_areas(root)
        except Exception as e:
            print(f"Failed to get areas: {str(e)}")
            return []
    
    def set_iteration(self, work_item_id: int, iteration_path: str) -> bool:
        """
        Set the iteration path for a work item.
        
        Args:
            work_item_id: Work item ID
            iteration_path: Full iteration path
            
        Returns:
            True if successful
        """
        return self.update_work_item(work_item_id, iteration_path=iteration_path)
    
    def set_area(self, work_item_id: int, area_path: str) -> bool:
        """
        Set the area path for a work item.
        
        Args:
            work_item_id: Work item ID
            area_path: Full area path
            
        Returns:
            True if successful
        """
        return self.update_work_item(work_item_id, area_path=area_path)
    
    # ==================== TEAMS ====================
    
    def get_teams(self, project: Optional[str] = None) -> List[TfsTeam]:
        """
        Get teams for a project.
        
        Args:
            project: Project name (default from config)
            
        Returns:
            List of TfsTeam objects
        """
        try:
            project = project or self.project
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/_apis/projects/{project}/teams?api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            teams = []
            for t in response.json().get('value', []):
                teams.append(TfsTeam(
                    id=t.get('id', ''),
                    name=t.get('name', ''),
                    description=t.get('description'),
                    url=t.get('url', '')
                ))
            return teams
        except Exception as e:
            print(f"Failed to get teams: {str(e)}")
            return []
    
    def get_team_members(self, team_id: str, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get members of a team.
        
        Args:
            team_id: Team ID or name
            project: Project name (default from config)
            
        Returns:
            List of team member dictionaries
        """
        try:
            project = project or self.project
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/_apis/projects/{project}/teams/{team_id}/members?api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            members = []
            for m in response.json().get('value', []):
                identity = m.get('identity', {})
                members.append({
                    "id": identity.get('id'),
                    "display_name": identity.get('displayName'),
                    "unique_name": identity.get('uniqueName'),
                    "is_team_admin": m.get('isTeamAdmin', False)
                })
            return members
        except Exception as e:
            print(f"Failed to get team members: {str(e)}")
            return []
    
    # ==================== QUERIES ====================
    
    def get_queries(self, project: Optional[str] = None, folder: str = "Shared Queries") -> List[TfsQuery]:
        """
        Get saved queries.
        
        Args:
            project: Project name (default from config)
            folder: Query folder path
            
        Returns:
            List of TfsQuery objects
        """
        try:
            project = project or self.project
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/{project}/_apis/wit/queries/{folder}?$depth=2&api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            def parse_queries(node, path=""):
                queries = []
                current_path = f"{path}/{node['name']}" if path else node['name']
                
                queries.append(TfsQuery(
                    id=node.get('id', ''),
                    name=node.get('name', ''),
                    path=current_path,
                    query_type=node.get('queryType', ''),
                    is_folder=node.get('isFolder', False)
                ))
                
                for child in node.get('children', []):
                    queries.extend(parse_queries(child, current_path))
                
                return queries
            
            root = response.json()
            return parse_queries(root)
        except Exception as e:
            print(f"Failed to get queries: {str(e)}")
            return []
    
    def run_query(self, query_id: str, project: Optional[str] = None) -> List[TfsWorkItem]:
        """
        Run a saved query.
        
        Args:
            query_id: Query ID
            project: Project name (default from config)
            
        Returns:
            List of TfsWorkItem objects
        """
        try:
            project = project or self.project
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/{project}/_apis/wit/wiql/{query_id}?api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            work_items_refs = response.json().get('workItems', [])
            
            if not work_items_refs:
                return []
            
            # Get full work item details
            work_item_ids = [str(item['id']) for item in work_items_refs[:200]]  # Limit to 200
            ids_param = ','.join(work_item_ids)
            
            items_url = f"{self.base_url}/{self.organization}/{project}/_apis/wit/workitems?ids={ids_param}&api-version={api_version}"
            response = requests.get(items_url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            return [self._parse_work_item(item) for item in response.json().get('value', [])]
        except Exception as e:
            print(f"Failed to run query {query_id}: {str(e)}")
            return []
    
    def run_wiql(self, wiql: str, project: Optional[str] = None, max_results: int = 50) -> List[TfsWorkItem]:
        """
        Run a WIQL query.
        
        Args:
            wiql: WIQL query string
            project: Project name (default from config)
            max_results: Maximum results to return
            
        Returns:
            List of TfsWorkItem objects
        """
        try:
            project = project or self.project
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/{project}/_apis/wit/wiql?api-version={api_version}"
            
            response = requests.post(url, json={"query": wiql}, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            work_items_refs = response.json().get('workItems', [])[:max_results]
            
            if not work_items_refs:
                return []
            
            # Get full work item details
            work_item_ids = [str(item['id']) for item in work_items_refs]
            ids_param = ','.join(work_item_ids)
            
            items_url = f"{self.base_url}/{self.organization}/{project}/_apis/wit/workitems?ids={ids_param}&api-version={api_version}"
            response = requests.get(items_url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            return [self._parse_work_item(item) for item in response.json().get('value', [])]
        except Exception as e:
            print(f"Failed to run WIQL query: {str(e)}")
            return []
    
    # ==================== PROJECTS ====================
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get all projects in the organization/collection.
        
        Returns:
            List of project dictionaries
        """
        try:
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/_apis/projects?api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            return response.json().get('value', [])
        except Exception as e:
            print(f"Failed to get projects: {str(e)}")
            return []
    
    def get_project(self, project: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific project.
        
        Args:
            project: Project name (default from config)
            
        Returns:
            Project dictionary or None
        """
        try:
            project = project or self.project
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/_apis/projects/{project}?api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            print(f"Failed to get project {project}: {str(e)}")
            return None
    
    # ==================== WORK ITEM TYPES ====================
    
    def get_work_item_types(self, project: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available work item types for a project.
        
        Args:
            project: Project name (default from config)
            
        Returns:
            List of work item type dictionaries
        """
        try:
            project = project or self.project
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/{project}/_apis/wit/workitemtypes?api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            return response.json().get('value', [])
        except Exception as e:
            print(f"Failed to get work item types: {str(e)}")
            return []
    
    def get_work_item_states(self, work_item_type: str = "Bug", project: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available states for a work item type.
        
        Args:
            work_item_type: Work item type name
            project: Project name (default from config)
            
        Returns:
            List of state dictionaries
        """
        try:
            project = project or self.project
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/{project}/_apis/wit/workitemtypes/{work_item_type}/states?api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            return response.json().get('value', [])
        except Exception as e:
            print(f"Failed to get states for {work_item_type}: {str(e)}")
            return []
    
    # ==================== SEARCH ====================
    
    def search_work_items(
        self,
        search_text: str,
        work_item_types: Optional[List[str]] = None,
        states: Optional[List[str]] = None,
        assigned_to: Optional[str] = None,
        project: Optional[str] = None,
        max_results: int = 50
    ) -> List[TfsWorkItem]:
        """
        Search for work items.
        
        Args:
            search_text: Text to search for in title/description
            work_item_types: Filter by work item types
            states: Filter by states
            assigned_to: Filter by assignee
            project: Project name (default from config)
            max_results: Maximum results to return
            
        Returns:
            List of TfsWorkItem objects
        """
        project = project or self.project
        
        # Build WIQL query
        conditions = []
        
        if search_text:
            conditions.append(f"([System.Title] CONTAINS '{search_text}' OR [System.Description] CONTAINS '{search_text}')")
        
        if work_item_types:
            types_str = "', '".join(work_item_types)
            conditions.append(f"[System.WorkItemType] IN ('{types_str}')")
        
        if states:
            states_str = "', '".join(states)
            conditions.append(f"[System.State] IN ('{states_str}')")
        
        if assigned_to:
            conditions.append(f"[System.AssignedTo] = '{assigned_to}'")
        
        wiql = """
        SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo],
               [System.CreatedDate], [System.ChangedDate], [System.Description]
        FROM WorkItems
        """
        
        if conditions:
            wiql += " WHERE " + " AND ".join(conditions)
        
        wiql += " ORDER BY [System.ChangedDate] DESC"
        
        return self.run_wiql(wiql, project, max_results)
    
    # ==================== HISTORY ====================
    
    def get_work_item_history(self, work_item_id: int) -> List[Dict[str, Any]]:
        """
        Get the revision history of a work item.
        
        Args:
            work_item_id: Work item ID
            
        Returns:
            List of revision dictionaries
        """
        try:
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}/revisions?api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            return response.json().get('value', [])
        except Exception as e:
            print(f"Failed to get history for work item {work_item_id}: {str(e)}")
            return []
    
    def get_work_item_updates(self, work_item_id: int) -> List[Dict[str, Any]]:
        """
        Get the update history of a work item (shows field changes).
        
        Args:
            work_item_id: Work item ID
            
        Returns:
            List of update dictionaries
        """
        try:
            api_version = "7.1" if self.is_cloud else "5.0"
            url = f"{self.base_url}/{self.organization}/_apis/wit/workitems/{work_item_id}/updates?api-version={api_version}"
            
            response = requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            response.raise_for_status()
            
            return response.json().get('value', [])
        except Exception as e:
            print(f"Failed to get updates for work item {work_item_id}: {str(e)}")
            return []
    
    # ==================== HELPER METHODS ====================
    
    def _parse_work_item(self, item: Dict[str, Any]) -> TfsWorkItem:
        """Parse API response into TfsWorkItem object."""
        fields = item.get('fields', {})
        
        # Extract assigned to and created by
        assigned_to = fields.get('System.AssignedTo', {})
        if isinstance(assigned_to, dict):
            assigned_to = assigned_to.get('displayName', None)
        
        created_by = fields.get('System.CreatedBy', {})
        if isinstance(created_by, dict):
            created_by = created_by.get('displayName', None)
        
        # Parse tags
        tags_str = fields.get('System.Tags', '')
        tags = [tag.strip() for tag in tags_str.split(';') if tag.strip()] if tags_str else []
        
        return TfsWorkItem(
            id=item['id'],
            title=fields.get('System.Title', ''),
            description=fields.get('System.Description', None),
            work_item_type=fields.get('System.WorkItemType', 'Bug'),
            state=fields.get('System.State', ''),
            priority=fields.get('Microsoft.VSTS.Common.Priority', None),
            severity=fields.get('Microsoft.VSTS.Common.Severity', None),
            assigned_to=assigned_to,
            created_by=created_by,
            created_date=fields.get('System.CreatedDate', ''),
            changed_date=fields.get('System.ChangedDate', ''),
            tags=tags,
            area_path=fields.get('System.AreaPath', None),
            iteration_path=fields.get('System.IterationPath', None)
        )
    
    @property
    def connected(self) -> bool:
        """Check if connected to TFS/Azure DevOps."""
        try:
            self._validate_connection()
            return True
        except:
            return False
