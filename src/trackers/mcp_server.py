"""
MCP Server for Bug Tracker Connectors
Exposes GitHub, JIRA, and TFS connectors as MCP tools.
"""
import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =======================
# Configuration
# =======================
class Config:
    """Configuration for all connectors."""
    # GitHub Config
    GITHUB_BASE_URL = "https://api.github.com"
    GITHUB_OWNER = "spring-projects"
    GITHUB_REPO = "spring-framework"
    GITHUB_TOKEN = "your-github-token-here"  # Set via environment variable
    
    # JIRA Config (update with your values)
    JIRA_URL = "https://your-jira-instance.atlassian.net"
    JIRA_EMAIL = "your-email@example.com"
    JIRA_API_TOKEN = "your-jira-api-token"
    JIRA_PROJECT_KEY = "PROJECT"
    
    # TFS/Azure DevOps Config (update with your values)
    TFS_URL = "https://dev.azure.com/your-org"
    TFS_PROJECT = "your-project"
    TFS_PAT = "your-pat-token"
    TFS_ORGANIZATION = "your-org"


# =======================
# GitHub Connector
# =======================
def get_github_issues(
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    state: str = "open",
    labels: Optional[List[str]] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Fetch GitHub issues for the configured repository (excluding PRs).
    
    Args:
        owner: Repository owner (default from config)
        repo: Repository name (default from config)
        state: Issue state ('open', 'closed', 'all')
        labels: Labels to filter by
        max_results: Maximum number of issues to return
    
    Returns:
        Dict with success status and issue data
    """
    owner = owner or Config.GITHUB_OWNER
    repo = repo or Config.GITHUB_REPO
    
    headers = {
        "Authorization": f"token {Config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    all_issues = []
    page = 1
    per_page = min(100, max_results)

    try:
        while len(all_issues) < max_results:
            params = {
                "state": state,
                "per_page": per_page,
                "page": page,
                "sort": "created",
                "direction": "desc"
            }

            if labels:
                params["labels"] = ",".join(labels)

            url = f"{Config.GITHUB_BASE_URL}/repos/{owner}/{repo}/issues"
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                return {
                    "success": False,
                    "action": "get_github_issues",
                    "data": [],
                    "error": "GitHub API rate limit exceeded"
                }

            response.raise_for_status()
            issues_data = response.json()

            if not issues_data:
                break

            for issue in issues_data:
                if "pull_request" in issue:
                    continue

                all_issues.append({
                    "number": issue.get("number"),
                    "title": issue.get("title"),
                    "body": issue.get("body"),
                    "state": issue.get("state"),
                    "labels": [l.get("name") for l in issue.get("labels", [])],
                    "assignee": issue.get("assignee", {}).get("login") if issue.get("assignee") else None,
                    "assignees": [a.get("login") for a in issue.get("assignees", [])],
                    "created_by": issue.get("user", {}).get("login") if issue.get("user") else None,
                    "created_at": issue.get("created_at"),
                    "updated_at": issue.get("updated_at"),
                    "closed_at": issue.get("closed_at"),
                    "milestone": issue.get("milestone", {}).get("title") if issue.get("milestone") else None,
                    "html_url": issue.get("html_url")
                })

                if len(all_issues) >= max_results:
                    break

            if len(issues_data) < per_page:
                break

            page += 1

        return {
            "success": True,
            "action": "get_github_issues",
            "data": all_issues,
            "message": f"Retrieved {len(all_issues)} issues from {owner}/{repo}"
        }

    except Exception as e:
        return {
            "success": False,
            "action": "get_github_issues",
            "data": [],
            "error": str(e)
        }


def get_github_issue_details(
    issue_number: int,
    owner: Optional[str] = None,
    repo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get detailed information about a specific GitHub issue.
    
    Args:
        issue_number: The issue number
        owner: Repository owner (default from config)
        repo: Repository name (default from config)
    
    Returns:
        Dict with issue details
    """
    owner = owner or Config.GITHUB_OWNER
    repo = repo or Config.GITHUB_REPO
    
    headers = {
        "Authorization": f"token {Config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        url = f"{Config.GITHUB_BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        issue = response.json()
        
        # Get comments
        comments_url = f"{url}/comments"
        comments_response = requests.get(comments_url, headers=headers, timeout=30)
        comments = comments_response.json() if comments_response.status_code == 200 else []
        
        return {
            "success": True,
            "action": "get_github_issue_details",
            "data": {
                "number": issue.get("number"),
                "title": issue.get("title"),
                "body": issue.get("body"),
                "state": issue.get("state"),
                "labels": [l.get("name") for l in issue.get("labels", [])],
                "assignee": issue.get("assignee", {}).get("login") if issue.get("assignee") else None,
                "created_by": issue.get("user", {}).get("login") if issue.get("user") else None,
                "created_at": issue.get("created_at"),
                "updated_at": issue.get("updated_at"),
                "closed_at": issue.get("closed_at"),
                "html_url": issue.get("html_url"),
                "comments": [
                    {
                        "id": c.get("id"),
                        "body": c.get("body"),
                        "user": c.get("user", {}).get("login"),
                        "created_at": c.get("created_at")
                    }
                    for c in comments
                ]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "action": "get_github_issue_details",
            "data": None,
            "error": str(e)
        }


def search_github_issues(
    query: str,
    owner: Optional[str] = None,
    repo: Optional[str] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Search GitHub issues using keywords.
    
    Args:
        query: Search query string
        owner: Repository owner (default from config)
        repo: Repository name (default from config)
        max_results: Maximum number of results
    
    Returns:
        Dict with search results
    """
    owner = owner or Config.GITHUB_OWNER
    repo = repo or Config.GITHUB_REPO
    
    headers = {
        "Authorization": f"token {Config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        search_query = f"{query} repo:{owner}/{repo} is:issue"
        url = f"{Config.GITHUB_BASE_URL}/search/issues"
        params = {
            "q": search_query,
            "per_page": min(100, max_results),
            "sort": "created",
            "order": "desc"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        issues = []
        for issue in data.get("items", [])[:max_results]:
            issues.append({
                "number": issue.get("number"),
                "title": issue.get("title"),
                "body": issue.get("body"),
                "state": issue.get("state"),
                "labels": [l.get("name") for l in issue.get("labels", [])],
                "created_at": issue.get("created_at"),
                "html_url": issue.get("html_url")
            })
        
        return {
            "success": True,
            "action": "search_github_issues",
            "data": issues,
            "message": f"Found {len(issues)} issues matching '{query}'"
        }
    except Exception as e:
        return {
            "success": False,
            "action": "search_github_issues",
            "data": [],
            "error": str(e)
        }


# =======================
# JIRA Connector
# =======================
def get_jira_issues(
    project_key: Optional[str] = None,
    issue_type: Optional[str] = None,
    status: Optional[List[str]] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Fetch JIRA issues for the configured project.
    
    Args:
        project_key: JIRA project key (default from config)
        issue_type: Type of issue (Bug, Story, Task, etc.)
        status: List of statuses to filter by
        max_results: Maximum number of issues to return
    
    Returns:
        Dict with success status and issue data
    """
    try:
        from jira import JIRA
        
        project_key = project_key or Config.JIRA_PROJECT_KEY
        
        options = {
            'server': Config.JIRA_URL,
            'verify': False
        }
        
        jira_client = JIRA(
            options=options,
            basic_auth=(Config.JIRA_EMAIL, Config.JIRA_API_TOKEN)
        )
        
        # Build JQL query
        jql_parts = [f'project = "{project_key}"']
        
        if issue_type:
            jql_parts.append(f'issuetype = "{issue_type}"')
        
        if status:
            status_str = ', '.join([f'"{s}"' for s in status])
            jql_parts.append(f'status IN ({status_str})')
        
        jql = ' AND '.join(jql_parts) + ' ORDER BY created DESC'
        
        issues = jira_client.search_issues(jql, maxResults=max_results)
        
        issue_list = []
        for issue in issues:
            issue_list.append({
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "issue_type": issue.fields.issuetype.name,
                "status": issue.fields.status.name,
                "priority": issue.fields.priority.name if issue.fields.priority else None,
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
                "reporter": issue.fields.reporter.displayName if issue.fields.reporter else None,
                "created": str(issue.fields.created),
                "updated": str(issue.fields.updated)
            })
        
        return {
            "success": True,
            "action": "get_jira_issues",
            "data": issue_list,
            "message": f"Retrieved {len(issue_list)} issues from JIRA project {project_key}"
        }
    except ImportError:
        return {
            "success": False,
            "action": "get_jira_issues",
            "data": [],
            "error": "JIRA library not installed. Run: pip install jira"
        }
    except Exception as e:
        return {
            "success": False,
            "action": "get_jira_issues",
            "data": [],
            "error": str(e)
        }


def search_jira_issues(
    query: str,
    project_key: Optional[str] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Search JIRA issues using JQL or text search.
    
    Args:
        query: Search query (text or JQL)
        project_key: JIRA project key (default from config)
        max_results: Maximum number of results
    
    Returns:
        Dict with search results
    """
    try:
        from jira import JIRA
        
        project_key = project_key or Config.JIRA_PROJECT_KEY
        
        options = {
            'server': Config.JIRA_URL,
            'verify': False
        }
        
        jira_client = JIRA(
            options=options,
            basic_auth=(Config.JIRA_EMAIL, Config.JIRA_API_TOKEN)
        )
        
        # Build JQL with text search
        jql = f'project = "{project_key}" AND text ~ "{query}" ORDER BY created DESC'
        
        issues = jira_client.search_issues(jql, maxResults=max_results)
        
        issue_list = []
        for issue in issues:
            issue_list.append({
                "key": issue.key,
                "summary": issue.fields.summary,
                "issue_type": issue.fields.issuetype.name,
                "status": issue.fields.status.name,
                "created": str(issue.fields.created)
            })
        
        return {
            "success": True,
            "action": "search_jira_issues",
            "data": issue_list,
            "message": f"Found {len(issue_list)} issues matching '{query}'"
        }
    except ImportError:
        return {
            "success": False,
            "action": "search_jira_issues",
            "data": [],
            "error": "JIRA library not installed. Run: pip install jira"
        }
    except Exception as e:
        return {
            "success": False,
            "action": "search_jira_issues",
            "data": [],
            "error": str(e)
        }


# =======================
# TFS/Azure DevOps Connector
# =======================
def get_tfs_work_items(
    project: Optional[str] = None,
    work_item_type: Optional[str] = None,
    state: Optional[str] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Fetch TFS/Azure DevOps work items.
    
    Args:
        project: TFS project name (default from config)
        work_item_type: Type of work item (Bug, Task, User Story, etc.)
        state: State to filter by (Active, Resolved, Closed, etc.)
        max_results: Maximum number of work items to return
    
    Returns:
        Dict with success status and work item data
    """
    project = project or Config.TFS_PROJECT
    
    # Detect if cloud or on-premises
    is_cloud = "dev.azure.com" in Config.TFS_URL or "visualstudio.com" in Config.TFS_URL
    
    if is_cloud:
        base_url = f"{Config.TFS_URL}/{Config.TFS_ORGANIZATION}"
    else:
        base_url = Config.TFS_URL
    
    # Set up authentication
    auth_string = f":{Config.TFS_PAT}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/json"
    }
    
    try:
        # Build WIQL query
        wiql_parts = [f"SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = '{project}'"]
        
        if work_item_type:
            wiql_parts.append(f"AND [System.WorkItemType] = '{work_item_type}'")
        
        if state:
            wiql_parts.append(f"AND [System.State] = '{state}'")
        
        wiql_parts.append("ORDER BY [System.CreatedDate] DESC")
        
        wiql = " ".join(wiql_parts)
        
        # Execute WIQL query
        wiql_url = f"{base_url}/{project}/_apis/wit/wiql?api-version=6.0"
        response = requests.post(
            wiql_url,
            headers=headers,
            json={"query": wiql},
            verify=False,
            timeout=30
        )
        response.raise_for_status()
        
        work_item_refs = response.json().get("workItems", [])[:max_results]
        
        if not work_item_refs:
            return {
                "success": True,
                "action": "get_tfs_work_items",
                "data": [],
                "message": "No work items found"
            }
        
        # Get work item details
        ids = [str(wi["id"]) for wi in work_item_refs]
        ids_str = ",".join(ids)
        
        details_url = f"{base_url}/_apis/wit/workitems?ids={ids_str}&api-version=6.0"
        details_response = requests.get(details_url, headers=headers, verify=False, timeout=30)
        details_response.raise_for_status()
        
        work_items = []
        for wi in details_response.json().get("value", []):
            fields = wi.get("fields", {})
            work_items.append({
                "id": wi.get("id"),
                "title": fields.get("System.Title"),
                "description": fields.get("System.Description"),
                "work_item_type": fields.get("System.WorkItemType"),
                "state": fields.get("System.State"),
                "priority": fields.get("Microsoft.VSTS.Common.Priority"),
                "assigned_to": fields.get("System.AssignedTo", {}).get("displayName") if isinstance(fields.get("System.AssignedTo"), dict) else fields.get("System.AssignedTo"),
                "created_date": fields.get("System.CreatedDate"),
                "changed_date": fields.get("System.ChangedDate"),
                "area_path": fields.get("System.AreaPath"),
                "iteration_path": fields.get("System.IterationPath")
            })
        
        return {
            "success": True,
            "action": "get_tfs_work_items",
            "data": work_items,
            "message": f"Retrieved {len(work_items)} work items from TFS project {project}"
        }
    except Exception as e:
        return {
            "success": False,
            "action": "get_tfs_work_items",
            "data": [],
            "error": str(e)
        }


def search_tfs_work_items(
    query: str,
    project: Optional[str] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Search TFS/Azure DevOps work items by text.
    
    Args:
        query: Search query text
        project: TFS project name (default from config)
        max_results: Maximum number of results
    
    Returns:
        Dict with search results
    """
    project = project or Config.TFS_PROJECT
    
    is_cloud = "dev.azure.com" in Config.TFS_URL or "visualstudio.com" in Config.TFS_URL
    
    if is_cloud:
        base_url = f"{Config.TFS_URL}/{Config.TFS_ORGANIZATION}"
    else:
        base_url = Config.TFS_URL
    
    auth_string = f":{Config.TFS_PAT}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/json"
    }
    
    try:
        # Build WIQL query with text search
        wiql = f"""
        SELECT [System.Id] FROM WorkItems 
        WHERE [System.TeamProject] = '{project}' 
        AND ([System.Title] CONTAINS '{query}' OR [System.Description] CONTAINS '{query}')
        ORDER BY [System.CreatedDate] DESC
        """
        
        wiql_url = f"{base_url}/{project}/_apis/wit/wiql?api-version=6.0"
        response = requests.post(
            wiql_url,
            headers=headers,
            json={"query": wiql},
            verify=False,
            timeout=30
        )
        response.raise_for_status()
        
        work_item_refs = response.json().get("workItems", [])[:max_results]
        
        if not work_item_refs:
            return {
                "success": True,
                "action": "search_tfs_work_items",
                "data": [],
                "message": f"No work items found matching '{query}'"
            }
        
        # Get work item details
        ids = [str(wi["id"]) for wi in work_item_refs]
        ids_str = ",".join(ids)
        
        details_url = f"{base_url}/_apis/wit/workitems?ids={ids_str}&api-version=6.0"
        details_response = requests.get(details_url, headers=headers, verify=False, timeout=30)
        details_response.raise_for_status()
        
        work_items = []
        for wi in details_response.json().get("value", []):
            fields = wi.get("fields", {})
            work_items.append({
                "id": wi.get("id"),
                "title": fields.get("System.Title"),
                "work_item_type": fields.get("System.WorkItemType"),
                "state": fields.get("System.State"),
                "created_date": fields.get("System.CreatedDate")
            })
        
        return {
            "success": True,
            "action": "search_tfs_work_items",
            "data": work_items,
            "message": f"Found {len(work_items)} work items matching '{query}'"
        }
    except Exception as e:
        return {
            "success": False,
            "action": "search_tfs_work_items",
            "data": [],
            "error": str(e)
        }


# =======================
# MCP Server Implementation
# =======================
import base64

# Tool definitions for MCP
TOOLS = [
    {
        "name": "get_github_issues",
        "description": "Fetch GitHub issues from a repository. Returns list of issues with details like title, body, labels, assignee, etc.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner (optional, uses default from config)"},
                "repo": {"type": "string", "description": "Repository name (optional, uses default from config)"},
                "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open", "description": "Issue state filter"},
                "labels": {"type": "array", "items": {"type": "string"}, "description": "Labels to filter by"},
                "max_results": {"type": "integer", "default": 10, "description": "Maximum number of issues to return"}
            }
        }
    },
    {
        "name": "get_github_issue_details",
        "description": "Get detailed information about a specific GitHub issue including comments.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "issue_number": {"type": "integer", "description": "The issue number"},
                "owner": {"type": "string", "description": "Repository owner (optional)"},
                "repo": {"type": "string", "description": "Repository name (optional)"}
            },
            "required": ["issue_number"]
        }
    },
    {
        "name": "search_github_issues",
        "description": "Search GitHub issues using keywords.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
                "owner": {"type": "string", "description": "Repository owner (optional)"},
                "repo": {"type": "string", "description": "Repository name (optional)"},
                "max_results": {"type": "integer", "default": 10, "description": "Maximum number of results"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_jira_issues",
        "description": "Fetch JIRA issues from a project. Returns list of issues with details.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_key": {"type": "string", "description": "JIRA project key (optional, uses default from config)"},
                "issue_type": {"type": "string", "description": "Issue type filter (Bug, Story, Task, etc.)"},
                "status": {"type": "array", "items": {"type": "string"}, "description": "Status filter list"},
                "max_results": {"type": "integer", "default": 10, "description": "Maximum number of issues to return"}
            }
        }
    },
    {
        "name": "search_jira_issues",
        "description": "Search JIRA issues using text search.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text"},
                "project_key": {"type": "string", "description": "JIRA project key (optional)"},
                "max_results": {"type": "integer", "default": 10, "description": "Maximum number of results"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_tfs_work_items",
        "description": "Fetch TFS/Azure DevOps work items from a project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "TFS project name (optional, uses default from config)"},
                "work_item_type": {"type": "string", "description": "Work item type filter (Bug, Task, User Story, etc.)"},
                "state": {"type": "string", "description": "State filter (Active, Resolved, Closed, etc.)"},
                "max_results": {"type": "integer", "default": 10, "description": "Maximum number of work items to return"}
            }
        }
    },
    {
        "name": "search_tfs_work_items",
        "description": "Search TFS/Azure DevOps work items by text.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text"},
                "project": {"type": "string", "description": "TFS project name (optional)"},
                "max_results": {"type": "integer", "default": 10, "description": "Maximum number of results"}
            },
            "required": ["query"]
        }
    }
]


def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Route tool calls to appropriate connector functions."""
    tool_handlers = {
        "get_github_issues": get_github_issues,
        "get_github_issue_details": get_github_issue_details,
        "search_github_issues": search_github_issues,
        "get_jira_issues": get_jira_issues,
        "search_jira_issues": search_jira_issues,
        "get_tfs_work_items": get_tfs_work_items,
        "search_tfs_work_items": search_tfs_work_items
    }
    
    handler = tool_handlers.get(name)
    if handler:
        return handler(**arguments)
    else:
        return {"success": False, "error": f"Unknown tool: {name}"}


async def run_stdio_server():
    """Run the MCP server using stdio transport."""
    print("Bug Tracker MCP Server started", file=sys.stderr)
    print("Available tools:", file=sys.stderr)
    for tool in TOOLS:
        print(f"  - {tool['name']}: {tool['description']}", file=sys.stderr)
    
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            request = json.loads(line.strip())
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "bug-tracker-mcp",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": TOOLS
                    }
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = handle_tool_call(tool_name, tool_args)
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            print(json.dumps(response), flush=True)
            
        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode - run a quick test of GitHub connector
        print("Testing GitHub connector...")
        result = get_github_issues(max_results=5)
        
        if result["success"]:
            print(f"✓ {result['message']}\n")
            for issue in result["data"]:
                print(f"#{issue['number']}: {issue['title']}")
        else:
            print(f"✗ Error: {result.get('error', 'Unknown error')}")
    else:
        # Run as MCP server
        asyncio.run(run_stdio_server())


if __name__ == "__main__":
    main()
