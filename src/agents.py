"""Agent system for Sustenance - Multi-tracker issue management."""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from bug_tracker_factory import UnifiedBugTracker
from jira_mcp import JiraMCPServer
from tfs_mcp import TfsMCPServer
from github_mcp import GitHubMCPServer
from config import Config
from code_analyzer import CodeAnalysisAgent
import httpx


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.capabilities = []
    
    @abstractmethod
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute an action."""
        pass
    
    def get_capabilities(self) -> List[str]:
        """Get list of agent capabilities."""
        return self.capabilities


class JiraAgent(BaseAgent):
    """Agent for Jira interactions."""
    
    def __init__(self):
        super().__init__("JiraAgent")
        self.jira = JiraMCPServer()
        self.capabilities = [
            # Issue Management (12)
            "fetch_bugs",
            "get_bug_details",
            "create_issue",
            "edit_issue",
            "delete_issue",
            "assign_issue",
            "add_comment",
            "edit_comment",
            "delete_comment",
            "get_comments",
            "update_status",
            "get_transitions",
            # Labels (2)
            "add_labels",
            "remove_labels",
            # Watchers (3)
            "add_watchers",
            "remove_watchers",
            "get_watchers",
            # Issue Links (3)
            "link_issues",
            "get_issue_links",
            "get_link_types",
            # Attachments (3)
            "add_attachment",
            "get_attachments",
            "delete_attachment",
            # Components (4)
            "get_components",
            "create_component",
            "add_components",
            "remove_components",
            # Versions/Releases (5)
            "get_versions",
            "create_version",
            "release_version",
            "set_fix_version",
            "set_affects_version",
            # Sprints & Agile (4)
            "get_boards",
            "get_sprints",
            "add_to_sprint",
            "get_sprint_issues",
            # Users (2)
            "search_users",
            "get_assignable_users",
            # Projects (2)
            "get_projects",
            "get_project",
            # Search (2)
            "search_bugs",
            "jql_search",
            # Meta (4)
            "get_issue_types",
            "get_priorities",
            "get_statuses",
            # Work Logs (2)
            "add_worklog",
            "get_worklogs",
            # Subtasks (2)
            "create_subtask",
            "get_subtasks"
        ]
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute Jira-specific action."""
        try:
            # ==== ISSUE MANAGEMENT ====
            if action == "fetch_bugs":
                bugs = self.jira.get_bugs(
                    status=kwargs.get('status'),
                    max_results=kwargs.get('max_results', 10),
                    issue_type=kwargs.get('issue_type')
                )
                return {
                    "success": True,
                    "data": [self._format_bug(bug) for bug in bugs],
                    "count": len(bugs)
                }
            
            elif action == "get_bug_details":
                bug = self.jira.get_issue(kwargs['bug_id'])
                return {
                    "success": True,
                    "data": self._format_bug(bug)
                }
            
            elif action == "create_issue":
                issue = self.jira.create_issue(
                    summary=kwargs['summary'],
                    issue_type=kwargs.get('issue_type', 'Bug'),
                    description=kwargs.get('description'),
                    priority=kwargs.get('priority'),
                    assignee=kwargs.get('assignee'),
                    labels=kwargs.get('labels'),
                    components=kwargs.get('components')
                )
                if issue:
                    return {
                        "success": True,
                        "data": self._format_bug(issue),
                        "message": f"Issue {issue.key} created successfully"
                    }
                return {"success": False, "error": "Failed to create issue"}
            
            elif action == "edit_issue":
                success = self.jira.update_issue(
                    issue_key=kwargs['bug_id'],
                    summary=kwargs.get('summary'),
                    description=kwargs.get('description'),
                    priority=kwargs.get('priority'),
                    assignee=kwargs.get('assignee'),
                    labels=kwargs.get('labels'),
                    components=kwargs.get('components')
                )
                return {
                    "success": success,
                    "message": f"Issue {kwargs['bug_id']} updated" if success else "Failed to update issue"
                }
            
            elif action == "delete_issue":
                success = self.jira.delete_issue(kwargs['bug_id'])
                return {
                    "success": success,
                    "message": f"Issue {kwargs['bug_id']} deleted" if success else "Failed to delete issue"
                }
            
            elif action == "assign_issue":
                success = self.jira.assign_issue(
                    kwargs['bug_id'],
                    kwargs.get('assignee')
                )
                return {
                    "success": success,
                    "message": f"Issue {kwargs['bug_id']} assigned" if success else "Failed to assign issue"
                }
            
            elif action == "add_comment":
                success = self.jira.add_comment(
                    kwargs['bug_id'],
                    kwargs['comment']
                )
                return {
                    "success": success,
                    "message": "Comment added" if success else "Failed to add comment"
                }
            
            elif action == "edit_comment":
                success = self.jira.edit_comment(
                    kwargs['bug_id'],
                    kwargs['comment_id'],
                    kwargs['new_body']
                )
                return {
                    "success": success,
                    "message": "Comment updated" if success else "Failed to update comment"
                }
            
            elif action == "delete_comment":
                success = self.jira.delete_comment(
                    kwargs['bug_id'],
                    kwargs['comment_id']
                )
                return {
                    "success": success,
                    "message": "Comment deleted" if success else "Failed to delete comment"
                }
            
            elif action == "get_comments":
                comments = self.jira.get_comments(kwargs['bug_id'])
                return {
                    "success": True,
                    "data": comments,
                    "count": len(comments)
                }
            
            elif action == "update_status":
                success = self.jira.update_issue_status(
                    kwargs['bug_id'],
                    kwargs['new_status']
                )
                return {
                    "success": success,
                    "message": "Status updated" if success else "Failed to update status"
                }
            
            elif action == "get_transitions":
                transitions = self.jira.get_transitions(kwargs['bug_id'])
                return {
                    "success": True,
                    "data": transitions,
                    "count": len(transitions)
                }
            
            # ==== LABELS ====
            elif action == "add_labels":
                success = self.jira.add_labels(
                    kwargs['bug_id'],
                    kwargs['labels']
                )
                return {
                    "success": success,
                    "message": "Labels added" if success else "Failed to add labels"
                }
            
            elif action == "remove_labels":
                success = self.jira.remove_labels(
                    kwargs['bug_id'],
                    kwargs['labels']
                )
                return {
                    "success": success,
                    "message": "Labels removed" if success else "Failed to remove labels"
                }
            
            # ==== WATCHERS ====
            elif action == "add_watchers":
                success = self.jira.add_watchers(
                    kwargs['bug_id'],
                    kwargs['usernames']
                )
                return {
                    "success": success,
                    "message": "Watchers added" if success else "Failed to add watchers"
                }
            
            elif action == "remove_watchers":
                success = self.jira.remove_watchers(
                    kwargs['bug_id'],
                    kwargs['usernames']
                )
                return {
                    "success": success,
                    "message": "Watchers removed" if success else "Failed to remove watchers"
                }
            
            elif action == "get_watchers":
                watchers = self.jira.get_watchers(kwargs['bug_id'])
                return {
                    "success": True,
                    "data": watchers,
                    "count": len(watchers)
                }
            
            # ==== ISSUE LINKS ====
            elif action == "link_issues":
                success = self.jira.link_issues(
                    kwargs['bug_id'],
                    kwargs['target_issue'],
                    kwargs.get('link_type', 'Relates')
                )
                return {
                    "success": success,
                    "message": "Issues linked" if success else "Failed to link issues"
                }
            
            elif action == "get_issue_links":
                links = self.jira.get_issue_links(kwargs['bug_id'])
                return {
                    "success": True,
                    "data": links,
                    "count": len(links)
                }
            
            elif action == "get_link_types":
                link_types = self.jira.get_link_types()
                return {
                    "success": True,
                    "data": link_types,
                    "count": len(link_types)
                }
            
            # ==== ATTACHMENTS ====
            elif action == "add_attachment":
                success = self.jira.add_attachment(
                    kwargs['bug_id'],
                    kwargs['file_path']
                )
                return {
                    "success": success,
                    "message": "Attachment added" if success else "Failed to add attachment"
                }
            
            elif action == "get_attachments":
                attachments = self.jira.get_attachments(kwargs['bug_id'])
                return {
                    "success": True,
                    "data": attachments,
                    "count": len(attachments)
                }
            
            elif action == "delete_attachment":
                success = self.jira.delete_attachment(kwargs['attachment_id'])
                return {
                    "success": success,
                    "message": "Attachment deleted" if success else "Failed to delete attachment"
                }
            
            # ==== COMPONENTS ====
            elif action == "get_components":
                components = self.jira.get_components(kwargs.get('project_key'))
                return {
                    "success": True,
                    "data": components,
                    "count": len(components)
                }
            
            elif action == "create_component":
                component = self.jira.create_component(
                    name=kwargs['name'],
                    description=kwargs.get('description'),
                    lead_username=kwargs.get('lead_username')
                )
                return {
                    "success": component is not None,
                    "data": component,
                    "message": f"Component '{kwargs['name']}' created" if component else "Failed to create component"
                }
            
            elif action == "add_components":
                success = self.jira.add_components_to_issue(
                    kwargs['bug_id'],
                    kwargs['components']
                )
                return {
                    "success": success,
                    "message": "Components added" if success else "Failed to add components"
                }
            
            elif action == "remove_components":
                success = self.jira.remove_components_from_issue(
                    kwargs['bug_id'],
                    kwargs['components']
                )
                return {
                    "success": success,
                    "message": "Components removed" if success else "Failed to remove components"
                }
            
            # ==== VERSIONS/RELEASES ====
            elif action == "get_versions":
                versions = self.jira.get_versions(kwargs.get('project_key'))
                return {
                    "success": True,
                    "data": versions,
                    "count": len(versions)
                }
            
            elif action == "create_version":
                version = self.jira.create_version(
                    name=kwargs['name'],
                    description=kwargs.get('description'),
                    release_date=kwargs.get('release_date')
                )
                return {
                    "success": version is not None,
                    "data": version,
                    "message": f"Version '{kwargs['name']}' created" if version else "Failed to create version"
                }
            
            elif action == "release_version":
                success = self.jira.release_version(kwargs['version_id'])
                return {
                    "success": success,
                    "message": "Version released" if success else "Failed to release version"
                }
            
            elif action == "set_fix_version":
                success = self.jira.set_fix_version(
                    kwargs['bug_id'],
                    kwargs['versions']
                )
                return {
                    "success": success,
                    "message": "Fix version set" if success else "Failed to set fix version"
                }
            
            elif action == "set_affects_version":
                success = self.jira.set_affects_version(
                    kwargs['bug_id'],
                    kwargs['versions']
                )
                return {
                    "success": success,
                    "message": "Affects version set" if success else "Failed to set affects version"
                }
            
            # ==== SPRINTS & AGILE ====
            elif action == "get_boards":
                boards = self.jira.get_boards()
                return {
                    "success": True,
                    "data": boards,
                    "count": len(boards)
                }
            
            elif action == "get_sprints":
                sprints = self.jira.get_sprints(
                    board_id=kwargs['board_id'],
                    state=kwargs.get('state')
                )
                return {
                    "success": True,
                    "data": sprints,
                    "count": len(sprints)
                }
            
            elif action == "add_to_sprint":
                success = self.jira.add_to_sprint(
                    kwargs['sprint_id'],
                    kwargs['issue_keys']
                )
                return {
                    "success": success,
                    "message": "Issues added to sprint" if success else "Failed to add to sprint"
                }
            
            elif action == "get_sprint_issues":
                issues = self.jira.get_sprint_issues(kwargs['sprint_id'])
                return {
                    "success": True,
                    "data": [self._format_bug(bug) for bug in issues],
                    "count": len(issues)
                }
            
            # ==== USERS ====
            elif action == "search_users":
                users = self.jira.search_users(
                    query=kwargs['query'],
                    max_results=kwargs.get('max_results', 10)
                )
                return {
                    "success": True,
                    "data": users,
                    "count": len(users)
                }
            
            elif action == "get_assignable_users":
                users = self.jira.get_assignable_users(
                    issue_key=kwargs.get('bug_id'),
                    project_key=kwargs.get('project_key')
                )
                return {
                    "success": True,
                    "data": users,
                    "count": len(users)
                }
            
            # ==== PROJECTS ====
            elif action == "get_projects":
                projects = self.jira.get_projects()
                return {
                    "success": True,
                    "data": projects,
                    "count": len(projects)
                }
            
            elif action == "get_project":
                project = self.jira.get_project(kwargs.get('project_key'))
                return {
                    "success": project is not None,
                    "data": project
                }
            
            # ==== SEARCH ====
            elif action == "search_bugs":
                issues = self.jira.jql_search(
                    jql=kwargs.get('jql', f'project = "{kwargs.get("project_key", "")}"'),
                    max_results=kwargs.get('max_results', 50)
                )
                return {
                    "success": True,
                    "data": [self._format_bug(bug) for bug in issues],
                    "count": len(issues)
                }
            
            elif action == "jql_search":
                issues = self.jira.jql_search(
                    jql=kwargs['jql'],
                    max_results=kwargs.get('max_results', 50)
                )
                return {
                    "success": True,
                    "data": [self._format_bug(bug) for bug in issues],
                    "count": len(issues)
                }
            
            # ==== META ====
            elif action == "get_issue_types":
                issue_types = self.jira.get_issue_types(kwargs.get('project_key'))
                return {
                    "success": True,
                    "data": issue_types,
                    "count": len(issue_types)
                }
            
            elif action == "get_priorities":
                priorities = self.jira.get_priorities()
                return {
                    "success": True,
                    "data": priorities,
                    "count": len(priorities)
                }
            
            elif action == "get_statuses":
                statuses = self.jira.get_statuses(kwargs.get('project_key'))
                return {
                    "success": True,
                    "data": statuses,
                    "count": len(statuses)
                }
            
            # ==== WORK LOGS ====
            elif action == "add_worklog":
                success = self.jira.add_worklog(
                    issue_key=kwargs['bug_id'],
                    time_spent=kwargs['time_spent'],
                    comment=kwargs.get('comment')
                )
                return {
                    "success": success,
                    "message": "Worklog added" if success else "Failed to add worklog"
                }
            
            elif action == "get_worklogs":
                worklogs = self.jira.get_worklogs(kwargs['bug_id'])
                return {
                    "success": True,
                    "data": worklogs,
                    "count": len(worklogs)
                }
            
            # ==== SUBTASKS ====
            elif action == "create_subtask":
                subtask = self.jira.create_subtask(
                    parent_key=kwargs['parent_key'],
                    summary=kwargs['summary'],
                    description=kwargs.get('description'),
                    assignee=kwargs.get('assignee')
                )
                if subtask:
                    return {
                        "success": True,
                        "data": self._format_bug(subtask),
                        "message": f"Subtask {subtask.key} created"
                    }
                return {"success": False, "error": "Failed to create subtask"}
            
            elif action == "get_subtasks":
                subtasks = self.jira.get_subtasks(kwargs['bug_id'])
                return {
                    "success": True,
                    "data": [self._format_bug(st) for st in subtasks],
                    "count": len(subtasks)
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_bug(self, bug) -> Dict[str, Any]:
        """Format Jira bug for response."""
        return {
            "id": bug.key,
            "title": bug.summary,
            "description": bug.description,
            "status": bug.status,
            "priority": bug.priority,
            "assignee": bug.assignee,
            "created": bug.created
        }


class TfsAgent(BaseAgent):
    """Agent for TFS/Azure DevOps interactions."""
    
    def __init__(self):
        super().__init__("TfsAgent")
        self.tfs = TfsMCPServer()
        self.capabilities = [
            "fetch_bugs",
            "get_bug_details",
            "add_comment",
            "update_state",
            "search_bugs"
        ]
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute TFS-specific action."""
        try:
            if action == "fetch_bugs":
                bugs = self.tfs.get_bugs(
                    state=kwargs.get('state'),
                    max_results=kwargs.get('max_results', 10)
                )
                return {
                    "success": True,
                    "data": [self._format_bug(bug) for bug in bugs],
                    "count": len(bugs)
                }
            
            elif action == "get_bug_details":
                bug = self.tfs.get_work_item(int(kwargs['bug_id']))
                return {
                    "success": True,
                    "data": self._format_bug(bug)
                }
            
            elif action == "add_comment":
                success = self.tfs.add_comment(
                    int(kwargs['bug_id']),
                    kwargs['comment']
                )
                return {
                    "success": success,
                    "message": "Comment added" if success else "Failed to add comment"
                }
            
            elif action == "update_state":
                success = self.tfs.update_work_item_state(
                    int(kwargs['bug_id']),
                    kwargs['new_state']
                )
                return {
                    "success": success,
                    "message": "State updated" if success else "Failed to update state"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_bug(self, bug) -> Dict[str, Any]:
        """Format TFS bug for response."""
        return {
            "id": str(bug.id),
            "title": bug.title,
            "description": bug.description,
            "state": bug.state,
            "priority": bug.priority,
            "severity": bug.severity,
            "assigned_to": bug.assigned_to,
            "created": bug.created_date
        }


class GitHubAgent(BaseAgent):
    """Agent for GitHub interactions."""
    
    def __init__(self):
        super().__init__("GitHubAgent")
        self.github = GitHubMCPServer()
        self.capabilities = [
            # Issue Management
            "fetch_bugs",
            "get_bug_details",
            "create_issue",
            "edit_issue",
            "add_comment",
            "update_state",
            "add_labels",
            "remove_labels",
            "assign_users",
            "search_issues",
            # Pull Requests
            "list_pull_requests",
            "get_pull_request",
            "create_pull_request",
            "merge_pull_request",
            "add_review",
            "get_pr_diff",
            "get_pr_files",
            # Labels & Milestones
            "list_labels",
            "create_label",
            "edit_label",
            "delete_label",
            "list_milestones",
            "create_milestone",
            "update_milestone",
            "assign_milestone",
            # Repository Management
            "list_branches",
            "clone_repo",
            "check_repo_status",
            "list_cloned_repos",
            "get_repo_info",
            "list_contributors",
            "get_commit_history",
            "get_file_content",
            "search_code",
            "create_branch",
            "delete_branch",
            "compare_branches",
            # Collaborators
            "list_collaborators",
            "add_collaborator",
            "remove_collaborator",
            # Releases & Tags
            "list_releases",
            "get_release",
            "create_release",
            "list_tags",
            "create_tag"
        ]
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute GitHub-specific action."""
        try:
            if action == "fetch_bugs":
                bugs = self.github.get_bugs(
                    state=kwargs.get('state', 'open'),
                    labels=kwargs.get('labels'),
                    max_results=kwargs.get('max_results', 10)
                )
                return {
                    "success": True,
                    "data": [self._format_bug(bug) for bug in bugs],
                    "count": len(bugs)
                }
            
            elif action == "get_bug_details":
                bug = self.github.get_issue(int(kwargs['bug_id']))
                return {
                    "success": True,
                    "data": self._format_bug(bug)
                }
            
            elif action == "add_comment":
                success = self.github.add_comment(
                    int(kwargs['bug_id']),
                    kwargs['comment']
                )
                return {
                    "success": success,
                    "message": "Comment added" if success else "Failed to add comment"
                }
            
            elif action == "update_state":
                success = self.github.update_issue_state(
                    int(kwargs['bug_id']),
                    kwargs['new_state']
                )
                return {
                    "success": success,
                    "message": "State updated" if success else "Failed to update state"
                }
            
            elif action == "add_labels":
                success = self.github.add_labels(
                    int(kwargs['bug_id']),
                    kwargs['labels']
                )
                return {
                    "success": success,
                    "message": "Labels added" if success else "Failed to add labels"
                }
            
            elif action == "assign_users":
                success = self.github.assign_issue(
                    int(kwargs['bug_id']),
                    kwargs['assignees']
                )
                return {
                    "success": success,
                    "message": "Users assigned" if success else "Failed to assign users"
                }
            
            elif action == "list_branches":
                import subprocess
                
                repo_url = kwargs.get('repo_url')
                
                # If no repo_url provided, use configured GitHub repository
                if not repo_url:
                    if self.github.owner and self.github.repo:
                        repo_url = f"https://github.com/{self.github.owner}/{self.github.repo}.git"
                    else:
                        return {
                            "success": False,
                            "error": "Repository URL is required. Either provide a URL or configure GITHUB_OWNER and GITHUB_REPO in .env"
                        }
                
                # Support owner/repo format (convert to full URL)
                if repo_url and not repo_url.startswith('http'):
                    # Assume it's owner/repo format
                    repo_url = f"https://github.com/{repo_url}.git"
                
                try:
                    # Use git ls-remote to list branches without cloning
                    result = subprocess.run(
                        ['git', 'ls-remote', '--heads', repo_url],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        # Parse the output to extract branch names
                        branches = []
                        for line in result.stdout.strip().split('\n'):
                            if line:
                                # Format: <hash>\trefs/heads/<branch-name>
                                parts = line.split('\t')
                                if len(parts) == 2 and 'refs/heads/' in parts[1]:
                                    branch_name = parts[1].replace('refs/heads/', '')
                                    branches.append(branch_name)
                        
                        return {
                            "success": True,
                            "message": f"Found {len(branches)} branches",
                            "data": {
                                "branches": branches,
                                "count": len(branches)
                            }
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Failed to list branches: {result.stderr}"
                        }
                except subprocess.TimeoutExpired:
                    return {
                        "success": False,
                        "error": "Branch listing operation timed out"
                    }
                except FileNotFoundError:
                    return {
                        "success": False,
                        "error": "Git is not installed or not in PATH"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to list branches: {str(e)}"
                    }
            
            elif action == "clone_repo":
                import subprocess
                import os
                
                repo_url = kwargs.get('repo_url')
                target_dir = kwargs.get('target_dir', './data/repos')
                branch = kwargs.get('branch')  # Optional specific branch
                shallow = kwargs.get('shallow', False)  # Shallow clone option
                
                # If no repo_url provided, use configured GitHub repository
                if not repo_url:
                    if self.github.owner and self.github.repo:
                        repo_url = f"https://github.com/{self.github.owner}/{self.github.repo}.git"
                    else:
                        return {
                            "success": False,
                            "error": "Repository URL is required. Either provide a URL or configure GITHUB_OWNER and GITHUB_REPO in .env"
                        }
                
                # Support owner/repo format (convert to full URL)
                if repo_url and not repo_url.startswith('http'):
                    # Assume it's owner/repo format
                    repo_url = f"https://github.com/{repo_url}.git"
                
                # Create target directory if it doesn't exist
                os.makedirs(target_dir, exist_ok=True)
                
                # Extract repo name from URL
                repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
                repo_path = os.path.join(target_dir, repo_name)
                
                try:
                    # Check if repo already exists
                    if os.path.exists(repo_path):
                        # Repo exists - fetch and checkout/pull
                        if branch:
                            # First, clean any untracked files that might interfere
                            clean_result = subprocess.run(
                                ['git', '-C', repo_path, 'clean', '-fd'],
                                capture_output=True,
                                text=True,
                                timeout=30
                            )
                            
                            # Reset any local changes
                            reset_result = subprocess.run(
                                ['git', '-C', repo_path, 'reset', '--hard'],
                                capture_output=True,
                                text=True,
                                timeout=30
                            )
                            
                            # Fetch all branches
                            fetch_result = subprocess.run(
                                ['git', '-C', repo_path, 'fetch', 'origin'],
                                capture_output=True,
                                text=True,
                                timeout=900
                            )
                            
                            if fetch_result.returncode != 0:
                                return {
                                    "success": False,
                                    "error": f"Failed to fetch from origin: {fetch_result.stderr}"
                                }
                            
                            # Try to checkout the branch (it may already exist locally)
                            checkout_result = subprocess.run(
                                ['git', '-C', repo_path, 'checkout', branch],
                                capture_output=True,
                                text=True,
                                timeout=30
                            )
                            
                            if checkout_result.returncode != 0:
                                # Branch doesn't exist locally, create it tracking the remote
                                checkout_result = subprocess.run(
                                    ['git', '-C', repo_path, 'checkout', '-b', branch, f'origin/{branch}'],
                                    capture_output=True,
                                    text=True,
                                    timeout=30
                                )
                                
                                if checkout_result.returncode != 0:
                                    return {
                                        "success": False,
                                        "error": f"Failed to checkout branch '{branch}': {checkout_result.stderr}"
                                    }
                            
                            # Pull latest changes for the branch
                            result = subprocess.run(
                                ['git', '-C', repo_path, 'pull'],
                                capture_output=True,
                                text=True,
                                timeout=900
                            )
                            
                            if result.returncode != 0:
                                return {
                                    "success": False,
                                    "error": f"Failed to pull latest changes: {result.stderr}"
                                }
                            
                            action_type = f"updated (branch: {branch})"
                        else:
                            # Just pull latest changes on current branch
                            result = subprocess.run(
                                ['git', '-C', repo_path, 'pull'],
                                capture_output=True,
                                text=True,
                                timeout=900
                            )
                            
                            if result.returncode != 0:
                                return {
                                    "success": False,
                                    "error": f"Failed to pull latest changes: {result.stderr}"
                                }
                            
                            action_type = "updated"
                    else:
                        # Enable long paths on Windows before cloning
                        subprocess.run(['git', 'config', '--global', 'core.longpaths', 'true'], 
                                     capture_output=True, timeout=10)
                        
                        # For new clones with specific branch
                        if branch and branch.lower() not in ['main', 'master']:
                            # Clone with specific branch - don't use --no-checkout with --depth
                            # Instead, clone the branch directly and handle checkout separately if needed
                            clone_cmd = ['git', 'clone']
                            
                            if shallow:
                                clone_cmd.extend(['--depth', '1', '--single-branch'])
                            
                            clone_cmd.extend(['--branch', branch, repo_url, repo_path])
                            
                            # Clone the repository with the specific branch
                            result = subprocess.run(
                                clone_cmd,
                                capture_output=True,
                                text=True,
                                timeout=900
                            )
                            
                            if result.returncode != 0:
                                # If direct clone with branch fails, try the two-step approach
                                # Step 1: Clone without specific branch
                                clone_cmd_fallback = ['git', 'clone']
                                if shallow:
                                    clone_cmd_fallback.extend(['--depth', '1'])
                                clone_cmd_fallback.extend([repo_url, repo_path])
                                
                                result = subprocess.run(
                                    clone_cmd_fallback,
                                    capture_output=True,
                                    text=True,
                                    timeout=900
                                )
                                
                                if result.returncode != 0:
                                    return {
                                        "success": False,
                                        "error": f"Failed to clone repository: {result.stderr}"
                                    }
                                
                                # Step 2: Fetch and checkout the branch
                                fetch_result = subprocess.run(
                                    ['git', '-C', repo_path, 'fetch', 'origin', branch],
                                    capture_output=True,
                                    text=True,
                                    timeout=900
                                )
                                
                                if fetch_result.returncode != 0:
                                    return {
                                        "success": False,
                                        "error": f"Failed to fetch branch '{branch}': {fetch_result.stderr}"
                                    }
                                
                                # Checkout the branch
                                checkout_result = subprocess.run(
                                    ['git', '-C', repo_path, 'checkout', branch],
                                    capture_output=True,
                                    text=True,
                                    timeout=30
                                )
                                
                                if checkout_result.returncode != 0:
                                    # Try creating new branch tracking remote
                                    checkout_result = subprocess.run(
                                        ['git', '-C', repo_path, 'checkout', '-b', branch, f'origin/{branch}'],
                                        capture_output=True,
                                        text=True,
                                        timeout=30
                                    )
                                    
                                    if checkout_result.returncode != 0:
                                        return {
                                            "success": False,
                                            "error": f"Failed to checkout branch '{branch}': {checkout_result.stderr}"
                                        }
                            
                            action_type = f"cloned (branch: {branch})"
                        else:
                            # Standard clone for main/master or when no branch specified
                            clone_cmd = ['git', 'clone']
                            
                            if shallow:
                                clone_cmd.extend(['--depth', '1'])
                            
                            if branch:
                                clone_cmd.extend(['-b', branch])
                            
                            clone_cmd.extend([repo_url, repo_path])
                            
                            # Clone the repository
                            result = subprocess.run(
                                clone_cmd,
                                capture_output=True,
                                text=True,
                                timeout=900
                            )
                            
                            if result.returncode != 0:
                                return {
                                    "success": False,
                                    "error": f"Failed to clone repository: {result.stderr}"
                                }
                            
                            action_type = f"cloned{' (branch: ' + branch + ')' if branch else ''}"
                    
                    # Success - repository is ready
                    return {
                        "success": True,
                        "message": f"Repository {action_type} successfully",
                        "data": {
                            "repo_name": repo_name,
                            "path": repo_path,
                            "action": action_type,
                            "branch": branch if branch else "default"
                        }
                    }
                except subprocess.TimeoutExpired:
                    return {
                        "success": False,
                        "error": "Repository clone/pull operation timed out (>5 minutes)"
                    }
                except FileNotFoundError:
                    return {
                        "success": False,
                        "error": "Git is not installed or not in PATH. Please install Git from https://git-scm.com/"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Clone failed: {str(e)}"
                    }
            
            elif action == "check_repo_status":
                import subprocess
                import os
                
                target_dir = kwargs.get('target_dir', './data/repos')
                repo_name = kwargs.get('repo_name')
                
                # If no repo_name provided, use configured repository
                if not repo_name:
                    if self.github.owner and self.github.repo:
                        repo_name = self.github.repo
                    else:
                        return {
                            "success": False,
                            "error": "Repository name is required"
                        }
                
                repo_path = os.path.join(target_dir, repo_name)
                
                # Check if repository exists
                if not os.path.exists(repo_path):
                    return {
                        "success": False,
                        "error": f"Repository not found at {repo_path}"
                    }
                
                try:
                    # Get current branch
                    branch_result = subprocess.run(
                        ['git', '-C', repo_path, 'branch', '--show-current'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if branch_result.returncode != 0:
                        return {
                            "success": False,
                            "error": f"Failed to get branch info: {branch_result.stderr}"
                        }
                    
                    current_branch = branch_result.stdout.strip()
                    
                    # Get last commit info
                    commit_result = subprocess.run(
                        ['git', '-C', repo_path, 'log', '-1', '--pretty=format:%h - %s (%cr)'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    last_commit = commit_result.stdout.strip() if commit_result.returncode == 0 else "N/A"
                    
                    # Get status (any uncommitted changes)
                    status_result = subprocess.run(
                        ['git', '-C', repo_path, 'status', '--short'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    has_changes = bool(status_result.stdout.strip())
                    
                    return {
                        "success": True,
                        "data": {
                            "repo_name": repo_name,
                            "path": repo_path,
                            "current_branch": current_branch,
                            "last_commit": last_commit,
                            "has_uncommitted_changes": has_changes
                        },
                        "message": f"Repository status retrieved"
                    }
                    
                except subprocess.TimeoutExpired:
                    return {
                        "success": False,
                        "error": "Git command timed out"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to get repository status: {str(e)}"
                    }
            
            elif action == "list_cloned_repos":
                import subprocess
                import os
                
                target_dir = kwargs.get('target_dir', './data/repos')
                
                # Check if directory exists
                if not os.path.exists(target_dir):
                    return {
                        "success": False,
                        "error": f"Directory not found: {target_dir}"
                    }
                
                try:
                    # Get all subdirectories
                    repos = []
                    for item in os.listdir(target_dir):
                        item_path = os.path.join(target_dir, item)
                        if os.path.isdir(item_path):
                            # Check if it's a git repository
                            git_dir = os.path.join(item_path, '.git')
                            if os.path.exists(git_dir):
                                # Get current branch
                                branch_result = subprocess.run(
                                    ['git', '-C', item_path, 'branch', '--show-current'],
                                    capture_output=True,
                                    text=True,
                                    timeout=10
                                )
                                
                                current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "N/A"
                                
                                # Get last commit
                                commit_result = subprocess.run(
                                    ['git', '-C', item_path, 'log', '-1', '--pretty=format:%h - %s (%cr)'],
                                    capture_output=True,
                                    text=True,
                                    timeout=10
                                )
                                
                                last_commit = commit_result.stdout.strip() if commit_result.returncode == 0 else "N/A"
                                
                                repos.append({
                                    "name": item,
                                    "path": item_path,
                                    "current_branch": current_branch,
                                    "last_commit": last_commit
                                })
                    
                    if not repos:
                        return {
                            "success": True,
                            "data": {"repositories": []},
                            "message": f"No git repositories found in {target_dir}"
                        }
                    
                    return {
                        "success": True,
                        "data": {"repositories": repos},
                        "message": f"Found {len(repos)} cloned repository/repositories"
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to list repositories: {str(e)}"
                    }
            
            # ==== NEW GITHUB CAPABILITIES ====
            
            # Issue Management Extensions
            elif action == "create_issue":
                title = kwargs.get('title')
                if not title:
                    return {"success": False, "error": "Issue title is required"}
                
                success, data = self.github.create_issue(
                    title=title,
                    body=kwargs.get('body', ''),
                    labels=kwargs.get('labels', []),
                    assignees=kwargs.get('assignees', []),
                    milestone=kwargs.get('milestone')
                )
                
                if success:
                    return {
                        "success": True,
                        "data": self._format_bug(data),
                        "message": f"Issue #{data.number} created successfully"
                    }
                return {"success": False, "error": "Failed to create issue"}
            
            elif action == "edit_issue":
                issue_number = kwargs.get('issue_number')
                if not issue_number:
                    return {"success": False, "error": "Issue number is required"}
                
                success = self.github.update_issue(
                    int(issue_number),
                    title=kwargs.get('title'),
                    body=kwargs.get('body'),
                    state=kwargs.get('state'),
                    labels=kwargs.get('labels')
                )
                return {
                    "success": success,
                    "message": f"Issue #{issue_number} updated" if success else "Failed to update issue"
                }
            
            elif action == "remove_labels":
                issue_number = kwargs.get('issue_number')
                labels = kwargs.get('labels', [])
                if not issue_number:
                    return {"success": False, "error": "Issue number is required"}
                
                success = self.github.remove_labels(int(issue_number), labels)
                return {
                    "success": success,
                    "message": f"Labels removed from #{issue_number}" if success else "Failed to remove labels"
                }
            
            elif action == "search_issues":
                query = kwargs.get('query', '')
                filters = {
                    'author': kwargs.get('author'),
                    'assignee': kwargs.get('assignee'),
                    'labels': kwargs.get('labels'),
                    'state': kwargs.get('state', 'open'),
                    'sort': kwargs.get('sort', 'created'),
                    'order': kwargs.get('order', 'desc')
                }
                
                issues = self.github.search_issues(query, **filters)
                return {
                    "success": True,
                    "data": [self._format_bug(issue) for issue in issues],
                    "count": len(issues)
                }
            
            # Pull Requests
            elif action == "list_pull_requests":
                prs = self.github.get_pull_requests(
                    state=kwargs.get('state', 'open'),
                    sort=kwargs.get('sort', 'created'),
                    direction=kwargs.get('direction', 'desc')
                )
                return {
                    "success": True,
                    "data": [self._format_pr(pr) for pr in prs],
                    "count": len(prs)
                }
            
            elif action == "get_pull_request":
                pr_number = kwargs.get('pr_number')
                if not pr_number:
                    return {"success": False, "error": "PR number is required"}
                
                pr = self.github.get_pull_request(int(pr_number))
                if pr:
                    return {"success": True, "data": self._format_pr(pr)}
                return {"success": False, "error": f"PR #{pr_number} not found"}
            
            elif action == "create_pull_request":
                title = kwargs.get('title')
                head = kwargs.get('head')
                if not title or not head:
                    return {"success": False, "error": "Title and head branch are required"}
                
                success, pr = self.github.create_pull_request(
                    title=title,
                    body=kwargs.get('body', ''),
                    head=head,
                    base=kwargs.get('base', 'main'),
                    draft=kwargs.get('draft', False)
                )
                
                if success:
                    return {
                        "success": True,
                        "data": self._format_pr(pr),
                        "message": f"PR #{pr.number} created successfully"
                    }
                return {"success": False, "error": "Failed to create pull request"}
            
            elif action == "merge_pull_request":
                pr_number = kwargs.get('pr_number')
                if not pr_number:
                    return {"success": False, "error": "PR number is required"}
                
                success = self.github.merge_pull_request(
                    int(pr_number),
                    merge_method=kwargs.get('merge_method', 'merge'),
                    commit_message=kwargs.get('commit_message')
                )
                return {
                    "success": success,
                    "message": f"PR #{pr_number} merged successfully" if success else "Failed to merge PR"
                }
            
            elif action == "add_review":
                pr_number = kwargs.get('pr_number')
                event = kwargs.get('event', 'COMMENT')
                if not pr_number:
                    return {"success": False, "error": "PR number is required"}
                
                success = self.github.create_review(
                    int(pr_number),
                    event=event,
                    body=kwargs.get('body', '')
                )
                return {
                    "success": success,
                    "message": f"Review added to PR #{pr_number}" if success else "Failed to add review"
                }
            
            elif action == "get_pr_diff":
                pr_number = kwargs.get('pr_number')
                if not pr_number:
                    return {"success": False, "error": "PR number is required"}
                
                diff = self.github.get_pull_request_diff(int(pr_number))
                if diff:
                    return {"success": True, "data": {"diff": diff}}
                return {"success": False, "error": "Failed to get PR diff"}
            
            elif action == "get_pr_files":
                pr_number = kwargs.get('pr_number')
                if not pr_number:
                    return {"success": False, "error": "PR number is required"}
                
                files = self.github.get_pull_request_files(int(pr_number))
                return {
                    "success": True,
                    "data": {"files": files, "count": len(files)}
                }
            
            # Labels Management
            elif action == "list_labels":
                labels = self.github.get_labels()
                return {
                    "success": True,
                    "data": {"labels": labels, "count": len(labels)}
                }
            
            elif action == "create_label":
                name = kwargs.get('name')
                color = kwargs.get('color')
                if not name or not color:
                    return {"success": False, "error": "Label name and color are required"}
                
                success, label = self.github.create_label(
                    name=name,
                    color=color,
                    description=kwargs.get('description', '')
                )
                return {
                    "success": success,
                    "message": f"Label '{name}' created" if success else "Failed to create label",
                    "data": label if success else None
                }
            
            elif action == "edit_label":
                name = kwargs.get('name')
                if not name:
                    return {"success": False, "error": "Label name is required"}
                
                success = self.github.update_label(
                    name=name,
                    new_name=kwargs.get('new_name'),
                    color=kwargs.get('color'),
                    description=kwargs.get('description')
                )
                return {
                    "success": success,
                    "message": f"Label '{name}' updated" if success else "Failed to update label"
                }
            
            elif action == "delete_label":
                name = kwargs.get('name')
                if not name:
                    return {"success": False, "error": "Label name is required"}
                
                success = self.github.delete_label(name)
                return {
                    "success": success,
                    "message": f"Label '{name}' deleted" if success else "Failed to delete label"
                }
            
            # Milestones Management
            elif action == "list_milestones":
                milestones = self.github.get_milestones(
                    state=kwargs.get('state', 'open')
                )
                return {
                    "success": True,
                    "data": {"milestones": milestones, "count": len(milestones)}
                }
            
            elif action == "create_milestone":
                title = kwargs.get('title')
                if not title:
                    return {"success": False, "error": "Milestone title is required"}
                
                success, milestone = self.github.create_milestone(
                    title=title,
                    description=kwargs.get('description', ''),
                    due_date=kwargs.get('due_date'),
                    state=kwargs.get('state', 'open')
                )
                return {
                    "success": success,
                    "message": f"Milestone '{title}' created" if success else "Failed to create milestone",
                    "data": milestone if success else None
                }
            
            elif action == "update_milestone":
                number = kwargs.get('number')
                if not number:
                    return {"success": False, "error": "Milestone number is required"}
                
                success = self.github.update_milestone(
                    int(number),
                    title=kwargs.get('title'),
                    description=kwargs.get('description'),
                    due_date=kwargs.get('due_date'),
                    state=kwargs.get('state')
                )
                return {
                    "success": success,
                    "message": f"Milestone {number} updated" if success else "Failed to update milestone"
                }
            
            elif action == "assign_milestone":
                issue_number = kwargs.get('issue_number')
                milestone_number = kwargs.get('milestone_number')
                if not issue_number or not milestone_number:
                    return {"success": False, "error": "Issue and milestone numbers are required"}
                
                success = self.github.assign_milestone_to_issue(
                    int(issue_number),
                    int(milestone_number)
                )
                return {
                    "success": success,
                    "message": f"Milestone assigned to issue #{issue_number}" if success else "Failed to assign milestone"
                }
            
            # Repository Info
            elif action == "get_repo_info":
                info = self.github.get_repository_info()
                if info:
                    return {"success": True, "data": info}
                return {"success": False, "error": "Failed to get repository info"}
            
            elif action == "list_contributors":
                max_results = kwargs.get('max_results', 30)
                contributors = self.github.get_contributors(max_results=max_results)
                return {
                    "success": True,
                    "data": {"contributors": contributors, "count": len(contributors)}
                }
            
            elif action == "get_commit_history":
                commits = self.github.get_commits(
                    branch=kwargs.get('branch'),
                    max_results=kwargs.get('max_results', 10),
                    author=kwargs.get('author')
                )
                return {
                    "success": True,
                    "data": {"commits": commits, "count": len(commits)}
                }
            
            elif action == "get_file_content":
                path = kwargs.get('path')
                if not path:
                    return {"success": False, "error": "File path is required"}
                
                content = self.github.get_file_contents(
                    path=path,
                    branch=kwargs.get('branch')
                )
                if content:
                    return {"success": True, "data": {"content": content, "path": path}}
                return {"success": False, "error": f"Failed to get file content for {path}"}
            
            elif action == "search_code":
                query = kwargs.get('query')
                if not query:
                    return {"success": False, "error": "Search query is required"}
                
                results = self.github.search_code(
                    query=query,
                    path=kwargs.get('path'),
                    language=kwargs.get('language')
                )
                return {
                    "success": True,
                    "data": {"results": results, "count": len(results)}
                }
            
            # Branch Operations
            elif action == "create_branch":
                branch_name = kwargs.get('branch_name')
                if not branch_name:
                    return {"success": False, "error": "Branch name is required"}
                
                success = self.github.create_branch(
                    branch_name=branch_name,
                    from_branch=kwargs.get('from_branch')
                )
                return {
                    "success": success,
                    "message": f"Branch '{branch_name}' created" if success else "Failed to create branch"
                }
            
            elif action == "delete_branch":
                branch_name = kwargs.get('branch_name')
                if not branch_name:
                    return {"success": False, "error": "Branch name is required"}
                
                success = self.github.delete_branch(branch_name)
                return {
                    "success": success,
                    "message": f"Branch '{branch_name}' deleted" if success else "Failed to delete branch"
                }
            
            elif action == "compare_branches":
                base = kwargs.get('base')
                head = kwargs.get('head')
                if not base or not head:
                    return {"success": False, "error": "Base and head branches are required"}
                
                comparison = self.github.compare_branches(base=base, head=head)
                if comparison:
                    return {"success": True, "data": comparison}
                return {"success": False, "error": "Failed to compare branches"}
            
            # Collaborators
            elif action == "list_collaborators":
                collaborators = self.github.get_collaborators()
                return {
                    "success": True,
                    "data": {"collaborators": collaborators, "count": len(collaborators)}
                }
            
            elif action == "add_collaborator":
                username = kwargs.get('username')
                if not username:
                    return {"success": False, "error": "Username is required"}
                
                success = self.github.add_collaborator(
                    username=username,
                    permission=kwargs.get('permission', 'push')
                )
                return {
                    "success": success,
                    "message": f"User '{username}' added as collaborator" if success else "Failed to add collaborator"
                }
            
            elif action == "remove_collaborator":
                username = kwargs.get('username')
                if not username:
                    return {"success": False, "error": "Username is required"}
                
                success = self.github.remove_collaborator(username)
                return {
                    "success": success,
                    "message": f"User '{username}' removed from collaborators" if success else "Failed to remove collaborator"
                }
            
            # Releases & Tags
            elif action == "list_releases":
                max_results = kwargs.get('max_results', 10)
                releases = self.github.get_releases(max_results=max_results)
                return {
                    "success": True,
                    "data": {"releases": releases, "count": len(releases)}
                }
            
            elif action == "get_release":
                tag = kwargs.get('tag')
                if not tag:
                    return {"success": False, "error": "Release tag is required"}
                
                release = self.github.get_release_by_tag(tag)
                if release:
                    return {"success": True, "data": release}
                return {"success": False, "error": f"Release '{tag}' not found"}
            
            elif action == "create_release":
                tag = kwargs.get('tag')
                name = kwargs.get('name')
                if not tag or not name:
                    return {"success": False, "error": "Tag and name are required"}
                
                success, release = self.github.create_release(
                    tag=tag,
                    name=name,
                    body=kwargs.get('body', ''),
                    draft=kwargs.get('draft', False),
                    prerelease=kwargs.get('prerelease', False),
                    target=kwargs.get('target')
                )
                return {
                    "success": success,
                    "message": f"Release '{name}' created" if success else "Failed to create release",
                    "data": release if success else None
                }
            
            elif action == "list_tags":
                max_results = kwargs.get('max_results', 30)
                tags = self.github.get_tags(max_results=max_results)
                return {
                    "success": True,
                    "data": {"tags": tags, "count": len(tags)}
                }
            
            elif action == "create_tag":
                tag = kwargs.get('tag')
                sha = kwargs.get('sha')
                if not tag or not sha:
                    return {"success": False, "error": "Tag name and SHA are required"}
                
                success = self.github.create_tag(
                    tag=tag,
                    sha=sha,
                    message=kwargs.get('message', '')
                )
                return {
                    "success": success,
                    "message": f"Tag '{tag}' created" if success else "Failed to create tag"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_bug(self, bug) -> Dict[str, Any]:
        """Format GitHub bug for response."""
        return {
            "id": str(bug.number),
            "title": bug.title,
            "description": bug.body,
            "state": bug.state,
            "labels": bug.labels,
            "assignee": bug.assignee,
            "created": bug.created_at,
            "url": bug.html_url
        }
    
    def _format_pr(self, pr) -> Dict[str, Any]:
        """Format GitHub pull request for response."""
        return {
            "number": pr.number,
            "title": pr.title,
            "description": pr.body,
            "state": pr.state,
            "author": pr.user.login if pr.user else None,
            "head": pr.head.ref if pr.head else None,
            "base": pr.base.ref if pr.base else None,
            "mergeable": getattr(pr, 'mergeable', None),
            "merged": pr.merged,
            "draft": pr.draft,
            "created": pr.created_at,
            "updated": pr.updated_at,
            "url": pr.html_url
        }


class CodeAnalysisAgentWrapper(BaseAgent):
    """Agent for analyzing code based on bug information."""
    
    def __init__(self):
        super().__init__("CodeAnalysisAgent")
        self.analyzer = CodeAnalysisAgent()
        self.capabilities = [
            "analyze_bug",
            "scan_repository",
            "analyze_with_context"
        ]
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute code analysis action."""
        try:
            if action == "scan_repository":
                extensions = kwargs.get('extensions', ['.py', '.java', '.js', '.ts'])
                code_files = self.analyzer.scan_repository(extensions=extensions)
                return {
                    "success": True,
                    "data": {
                        "total_files": len(code_files),
                        "files": [str(f.relative_path) for f in code_files[:20]]  # First 20 files
                    },
                    "message": f"Found {len(code_files)} code files"
                }
            
            elif action == "analyze_bug":
                bug_description = kwargs.get('bug_description', '')
                bug_id = kwargs.get('bug_id', '')
                extensions = kwargs.get('extensions', ['.py', '.java', '.js', '.ts'])
                
                # Scan repository
                code_files = self.analyzer.scan_repository(extensions=extensions)
                
                if not code_files:
                    return {
                        "success": False,
                        "error": "No code files found in repository",
                        "message": f"Please check repository path: {Config.REPO_PATH}"
                    }
                
                # Analyze bug
                result = self.analyzer.analyze_bug(
                    bug_description=bug_description,
                    bug_key=bug_id,
                    code_files=code_files,
                    max_files_per_analysis=3
                )
                
                return {
                    "success": True,
                    "data": result,
                    "message": f"Analysis complete for bug {bug_id}"
                }
            
            elif action == "analyze_with_context":
                bug_description = kwargs.get('bug_description', '')
                bug_id = kwargs.get('bug_id', '')
                historical_context = kwargs.get('historical_context', None)
                extensions = kwargs.get('extensions', ['.py', '.java', '.js', '.ts'])
                
                # Scan repository
                code_files = self.analyzer.scan_repository(extensions=extensions)
                
                if not code_files:
                    return {
                        "success": False,
                        "error": "No code files found in repository"
                    }
                
                # Analyze with historical context
                result = self.analyzer.analyze_bug(
                    bug_description=bug_description,
                    bug_key=bug_id,
                    code_files=code_files,
                    max_files_per_analysis=3,
                    historical_context=historical_context
                )
                
                return {
                    "success": True,
                    "data": result,
                    "message": f"Analysis complete with context for bug {bug_id}"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Code analysis failed: {str(e)}"
            }


class SuperAgent:
    """
    Super agent that routes requests to appropriate connector agents.
    Acts as the main orchestrator for Sustenance - managing issue tracking across multiple systems.
    Supports natural language chat interface for intuitive interaction.
    """
    
    def __init__(self):
        # No hardcoded default - Claude will decide based on available trackers and user intent
        self.tracker_type = None
        self.agents: Dict[str, BaseAgent] = {}
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}  # session_id -> messages
        self.session_metadata: Dict[str, Dict[str, str]] = {}  # session_id -> {title, created_at, updated_at}
        self.session_file = "./chat_sessions.json"  # Persistent storage file
        self.metadata_file = "./chat_metadata.json"  # Session metadata file
        print(f"DEBUG: SuperAgent __init__ called (no default tracker - will be decided dynamically)", flush=True)
        self._load_conversation_history()  # Load persisted sessions
        self._initialize_agents()
        # Set default to first available tracker after initialization
        available = [k for k in ["jira", "tfs", "github"] if k in self.agents]
        self.tracker_type = available[0] if available else None
        if self.tracker_type:
            print(f"✓ Dynamic default set to: {self.tracker_type.upper()}", flush=True)
    
    def _load_conversation_history(self):
        """Load conversation history from disk."""
        import json
        import os
        
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    self.conversation_history = json.load(f)
                print(f"✓ Loaded {len(self.conversation_history)} chat session(s) from disk", flush=True)
            except Exception as e:
                print(f"⚠️  Failed to load chat sessions: {e}", flush=True)
                self.conversation_history = {}
        else:
            print(f"ℹ️  No existing chat sessions found", flush=True)
        
        # Load session metadata
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.session_metadata = json.load(f)
            except Exception as e:
                print(f"⚠️  Failed to load session metadata: {e}", flush=True)
                self.session_metadata = {}
    
    def _save_conversation_history(self):
        """Save conversation history to disk."""
        import json
        
        try:
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
            
            # Also save metadata
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Failed to save chat sessions: {e}", flush=True)
    
    def _initialize_agents(self):
        """Initialize all available agents based on configured credentials."""
        import sys
        print("\n" + "="*70, flush=True)
        print("INITIALIZING SUSTENANCE AGENTS", flush=True)
        print("="*70, flush=True)
        
        # Try to initialize Jira if credentials are available
        print(f"\nChecking Jira credentials...", flush=True)
        print(f"  JIRA_URL: {Config.JIRA_URL}", flush=True)
        print(f"  JIRA_API_TOKEN: {'*' * 20 if Config.JIRA_API_TOKEN else 'NOT SET'}", flush=True)
        
        if Config.JIRA_URL and Config.JIRA_API_TOKEN:
            print(f"  → Attempting to initialize Jira agent...", flush=True)
            try:
                self.agents["jira"] = JiraAgent()
                print(f"  ✓ Initialized JiraAgent", flush=True)
            except Exception as e:
                print(f"  ⚠️  Jira agent initialization failed: {e}", flush=True)
                import traceback
                traceback.print_exc(file=sys.stderr)
        else:
            print(f"  ℹ️  Jira not configured (missing JIRA_URL or JIRA_API_TOKEN)", flush=True)
        
        # Try to initialize TFS if credentials are available
        if Config.TFS_URL and Config.TFS_PAT:
            try:
                self.agents["tfs"] = TfsAgent()
                self.agents["azuredevops"] = self.agents["tfs"]  # Alias
                print(f"✓ Initialized TfsAgent", flush=True)
            except Exception as e:
                print(f"⚠️  TFS agent initialization failed: {e}", flush=True)
        else:
            print(f"ℹ️  TFS not configured (missing TFS_URL or TFS_PAT)", flush=True)
        
        # Try to initialize GitHub if credentials are available
        if Config.GITHUB_TOKEN and Config.GITHUB_OWNER:
            try:
                self.agents["github"] = GitHubAgent()
                print(f"✓ Initialized GitHubAgent", flush=True)
            except Exception as e:
                print(f"⚠️  GitHub agent initialization failed: {e}", flush=True)
        else:
            print(f"ℹ️  GitHub not configured (missing GITHUB_TOKEN or GITHUB_OWNER)", flush=True)
        
        # Always initialize code analysis agent
        try:
            self.agents["code_analysis"] = CodeAnalysisAgentWrapper()
            print(f"✓ Initialized CodeAnalysisAgent", flush=True)
        except Exception as e:
            print(f"⚠️  Code analysis agent not available: {e}", flush=True)
        
        if not any(k in self.agents for k in ["jira", "tfs", "github"]):
            print(f"⚠️  Warning: No tracker agents initialized!", flush=True)
        else:
            available = [k for k in ["jira", "tfs", "github"] if k in self.agents]
            print(f"\n✓ Available trackers: {', '.join(available).upper()}", flush=True)
            print(f"ℹ️  Tracker selection will be dynamic based on your query", flush=True)
    
    def chat_stream(self, message: str, session_id: str = "default"):
        """Process natural language message with streaming response.
        
        Args:
            message: Natural language message from user
            session_id: Session identifier for conversation history tracking
            
        Yields:
            JSON chunks of the streaming response
        """
        import json
        from anthropic import Anthropic
        
        try:
            # First, quickly parse intent to determine if we need streaming
            result = self.chat(message, session_id=session_id)
            
            # For now, send the complete message in chunks to simulate streaming
            # In a future enhancement, we can stream Claude's actual responses
            if result.get("success"):
                response_text = result.get("message", "")
                metadata = result.get("metadata")
                
                # Stream the response in small chunks for better UX
                chunk_size = 20  # characters per chunk
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i+chunk_size]
                    chunk_data = {"chunk": chunk}
                    if metadata and i == 0:  # Send metadata with first chunk
                        chunk_data["metadata"] = metadata
                    yield json.dumps(chunk_data)
                    import time
                    time.sleep(0.02)  # Small delay for smooth streaming effect
                
                # Send final complete message with metadata
                final_data = {"message": response_text, "success": True}
                if metadata:
                    final_data["metadata"] = metadata
                yield json.dumps(final_data)
            else:
                # Send error immediately
                yield json.dumps(result)
                
        except Exception as e:
            yield json.dumps({"success": False, "error": str(e)})
    
    def chat(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """Process natural language message and route to appropriate agent.
        
        Args:
            message: Natural language message from user
            session_id: Session identifier for conversation history tracking
            
        Returns:
            Response with agent's action results
        """
        # Initialize conversation history for this session if not exists
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        # Use Claude LLM to understand intent and extract parameters
        try:
            from anthropic import Anthropic
            import json
            
            # Create HTTP client with SSL verification disabled
            http_client = httpx.Client(verify=False, timeout=60.0)
            client = Anthropic(api_key=Config.ANTHROPIC_API_KEY, http_client=http_client)
            
            # Get list of actually available trackers
            available_trackers = [k for k in ["jira", "tfs", "github"] if k in self.agents]
            
            # If no trackers available, return error
            if not available_trackers:
                return {
                    "success": False,
                    "message": "❌ No trackers are configured. Please check your .env file and ensure at least one tracker (Jira, TFS, or GitHub) has valid credentials."
                }
            
            available_trackers_str = ', '.join(available_trackers)
            default_tracker_desc = f"Default tracker: {self.tracker_type}" if self.tracker_type else "No default set (will be chosen dynamically)"
            
            system_prompt = f"""You are Sustenance - an intelligent assistant for managing issues across multiple tracking systems (Jira, GitHub, TFS).

**Available Trackers:** {available_trackers_str}
{default_tracker_desc}

**Your Capabilities:**
You can help users with:
- **Issue Management**: Fetch, list, create, edit, search bugs/issues, add/remove labels, assign users
- **Pull Requests**: List, create, merge, review PRs, view diffs
- **Labels & Milestones**: Create, update, delete labels and milestones
- **Repository Management**: List/create/delete branches, clone repos, check status
- **Repository Info**: Get repo details, contributors, commits, file contents
- **Collaborators**: List, add, remove collaborators
- **Releases & Tags**: List, create releases and tags
- **Code Search**: Search code within repositories
- **Code Analysis**: Analyze code related to bugs

**How to Respond:**
Analyze the user's request and respond naturally. If you need to perform an action:

1. **For listing/fetching issues:** Respond ONLY with JSON (no explanation):
   {{"action": "fetch_bugs", "tracker": "jira|github|tfs", "max_results": 10, "issue_type": "Bug|Story|Task|Epic", "state": "open|closed|all"}}

2. **For creating issues:** Respond ONLY with JSON:
   {{"action": "create_issue", "tracker": "github", "title": "Bug title", "body": "description", "labels": ["bug", "urgent"], "assignees": ["username"]}}

3. **For editing issues:** Respond ONLY with JSON:
   {{"action": "edit_issue", "tracker": "github", "issue_number": 123, "title": "New title", "state": "closed"}}

4. **For searching issues:** Respond ONLY with JSON:
   {{"action": "search_issues", "tracker": "github", "query": "search text", "author": "username", "labels": ["bug"], "state": "open"}}

5. **For bug details:** Respond ONLY with JSON:
   {{"action": "get_bug_details", "bug_id": "ABC-123", "tracker": "jira|github|tfs"}}

6. **For adding comments:** Respond ONLY with JSON:
   {{"action": "add_comment", "bug_id": "ABC-123", "comment": "text", "tracker": "jira|github|tfs"}}

7. **For updating status:** Respond ONLY with JSON:
   {{"action": "update_status", "bug_id": "ABC-123", "status": "open|closed", "tracker": "jira|github|tfs"}}

8. **For labels management:**
   - Add: {{"action": "add_labels", "bug_id": "123", "labels": ["bug", "urgent"], "tracker": "github"}}
   - Remove: {{"action": "remove_labels", "issue_number": 123, "labels": ["wontfix"], "tracker": "github"}}
   - List: {{"action": "list_labels", "tracker": "github"}}
   - Create: {{"action": "create_label", "name": "needs-review", "color": "yellow", "tracker": "github"}}

9. **For milestones management:**
   - List: {{"action": "list_milestones", "tracker": "github", "state": "open"}}
   - Create: {{"action": "create_milestone", "title": "v2.0", "tracker": "github"}}
   - Assign: {{"action": "assign_milestone", "issue_number": 123, "milestone_number": 1, "tracker": "github"}}

10. **For pull requests:**
    - List: {{"action": "list_pull_requests", "tracker": "github", "state": "open"}}
    - Details: {{"action": "get_pull_request", "pr_number": 45, "tracker": "github"}}
    - Create: {{"action": "create_pull_request", "title": "Feature", "head": "feature-branch", "base": "main", "tracker": "github"}}
    - Merge: {{"action": "merge_pull_request", "pr_number": 45, "merge_method": "squash", "tracker": "github"}}
    - Review: {{"action": "add_review", "pr_number": 45, "event": "APPROVE", "body": "LGTM", "tracker": "github"}}
    - Diff: {{"action": "get_pr_diff", "pr_number": 45, "tracker": "github"}}
    - Files: {{"action": "get_pr_files", "pr_number": 45, "tracker": "github"}}

11. **For repository operations:**
    - Branches: {{"action": "list_branches", "repo_url": "https://github.com/owner/repo"}}
    - Clone: {{"action": "clone_repo", "branch": "6.2.x", "shallow": true}}
    - Status: {{"action": "check_repo_status", "repo_name": "spring-framework"}}
    - List Cloned: {{"action": "list_cloned_repos", "target_dir": "./data/repos"}}
    - Repo Info: {{"action": "get_repo_info", "tracker": "github"}}
    - Contributors: {{"action": "list_contributors", "max_results": 30, "tracker": "github"}}
    - Commits: {{"action": "get_commit_history", "branch": "main", "max_results": 10, "tracker": "github"}}
    - Create Branch: {{"action": "create_branch", "branch_name": "feature-x", "from_branch": "main", "tracker": "github"}}
    - Delete Branch: {{"action": "delete_branch", "branch_name": "old-feature", "tracker": "github"}}
    - Compare: {{"action": "compare_branches", "base": "main", "head": "develop", "tracker": "github"}}

12. **For file operations:**
    - Get File: {{"action": "get_file_content", "path": "README.md", "branch": "main", "tracker": "github"}}
    - Search Code: {{"action": "search_code", "query": "authentication", "path": "src", "tracker": "github"}}

13. **For collaborators:**
    - List: {{"action": "list_collaborators", "tracker": "github"}}
    - Add: {{"action": "add_collaborator", "username": "johndoe", "permission": "push", "tracker": "github"}}
    - Remove: {{"action": "remove_collaborator", "username": "johndoe", "tracker": "github"}}

14. **For releases & tags:**
    - List Releases: {{"action": "list_releases", "max_results": 10, "tracker": "github"}}
    - Get Release: {{"action": "get_release", "tag": "v2.0", "tracker": "github"}}
    - Create Release: {{"action": "create_release", "tag": "v2.0", "name": "Version 2.0", "body": "Release notes", "tracker": "github"}}
    - List Tags: {{"action": "list_tags", "max_results": 30, "tracker": "github"}}
    - Create Tag: {{"action": "create_tag", "tag": "v2.0.1", "sha": "abc123", "tracker": "github"}}

15. **For code analysis:** Respond ONLY with JSON:
   {{"action": "analyze_bug", "bug_id": "ABC-123", "tracker": "jira|github|tfs"}}

16. **For extracting IDs from conversation:** Respond ONLY with JSON:
   {{"action": "list_ids", "tracker": "jira|github", "issue_type": "Bug|Story"}}

17. **For conversational responses (greetings, help, clarifications):** Just respond naturally in plain text.

**CRITICAL RULES:**
- When you decide to perform an action (1-16 above), return ONLY the JSON object
- Do NOT include any explanatory text, greetings, or conversation before or after the JSON
- Do NOT wrap JSON in markdown code blocks
- The response must start with {{ and end with }}
- If you're just chatting (greetings, help, clarifications), respond in plain text only
- NEVER mix plain text with JSON in the same response
- When user implies an action, respond with ONLY the JSON action
- Do NOT say "let me check", "I'll do that", "I don't have a function", or "I can only" - just return the JSON
- NEVER say you can't do something when an action exists - execute it instead

**Context & Intelligence:**
- Understand context from conversation history
- Remember repos, branches, bugs, PRs recently mentioned
- Infer missing details intelligently:
  * "show bugs" → fetch_bugs from Jira (default)
  * "create issue 'Bug in login'" → create_issue with that title
  * "list open PRs" → list_pull_requests with state="open"
  * "merge PR #45" → merge_pull_request with pr_number=45
  * "approve PR 45" → add_review with event="APPROVE"
  * "show contributors" → list_contributors
  * "get README" → get_file_content with path="README.md"
  * "create branch feature-x from develop" → create_branch
  * "list releases" → list_releases
  * "compare main and develop" → compare_branches

**JIRA-SPECIFIC ACTIONS (50 total):**

18. **Jira Issue Creation:**
   {{"action": "create_issue", "tracker": "jira", "summary": "Bug title", "issue_type": "Bug|Story|Task|Epic", "description": "details", "priority": "High", "assignee": "username", "labels": ["label1"], "components": ["component1"]}}

19. **Jira Issue Edit:**
   {{"action": "edit_issue", "tracker": "jira", "bug_id": "PROJ-123", "summary": "New title", "description": "New desc", "priority": "Medium", "assignee": "user", "labels": ["new-label"]}}

20. **Delete Issue:**
   {{"action": "delete_issue", "tracker": "jira", "bug_id": "PROJ-123"}}

21. **Assign/Unassign Issue:**
   {{"action": "assign_issue", "tracker": "jira", "bug_id": "PROJ-123", "assignee": "username"}}

22. **Comments Management:**
   - Get: {{"action": "get_comments", "tracker": "jira", "bug_id": "PROJ-123"}}
   - Edit: {{"action": "edit_comment", "tracker": "jira", "bug_id": "PROJ-123", "comment_id": "10001", "new_body": "Updated text"}}
   - Delete: {{"action": "delete_comment", "tracker": "jira", "bug_id": "PROJ-123", "comment_id": "10001"}}

23. **Workflow Transitions:**
   {{"action": "get_transitions", "tracker": "jira", "bug_id": "PROJ-123"}}

24. **Labels on Issues:**
   - Add: {{"action": "add_labels", "tracker": "jira", "bug_id": "PROJ-123", "labels": ["bug", "urgent"]}}
   - Remove: {{"action": "remove_labels", "tracker": "jira", "bug_id": "PROJ-123", "labels": ["old-label"]}}

25. **Watchers:**
   - Add: {{"action": "add_watchers", "tracker": "jira", "bug_id": "PROJ-123", "usernames": ["user1", "user2"]}}
   - Remove: {{"action": "remove_watchers", "tracker": "jira", "bug_id": "PROJ-123", "usernames": ["user1"]}}
   - Get: {{"action": "get_watchers", "tracker": "jira", "bug_id": "PROJ-123"}}

26. **Issue Links:**
   - Link: {{"action": "link_issues", "tracker": "jira", "bug_id": "PROJ-123", "target_issue": "PROJ-456", "link_type": "Blocks|Relates|Cloners"}}
   - Get Links: {{"action": "get_issue_links", "tracker": "jira", "bug_id": "PROJ-123"}}
   - Link Types: {{"action": "get_link_types", "tracker": "jira"}}

27. **Attachments:**
   - Add: {{"action": "add_attachment", "tracker": "jira", "bug_id": "PROJ-123", "file_path": "/path/to/file.txt"}}
   - Get: {{"action": "get_attachments", "tracker": "jira", "bug_id": "PROJ-123"}}
   - Delete: {{"action": "delete_attachment", "tracker": "jira", "attachment_id": "10001"}}

28. **Components:**
   - List: {{"action": "get_components", "tracker": "jira", "project_key": "PROJ"}}
   - Create: {{"action": "create_component", "tracker": "jira", "name": "Backend", "description": "Backend services"}}
   - Add to Issue: {{"action": "add_components", "tracker": "jira", "bug_id": "PROJ-123", "components": ["Backend"]}}
   - Remove: {{"action": "remove_components", "tracker": "jira", "bug_id": "PROJ-123", "components": ["Frontend"]}}

29. **Versions/Releases:**
   - List: {{"action": "get_versions", "tracker": "jira", "project_key": "PROJ"}}
   - Create: {{"action": "create_version", "tracker": "jira", "name": "v2.0", "description": "Q1 Release", "release_date": "2025-03-31"}}
   - Release: {{"action": "release_version", "tracker": "jira", "version_id": "10001"}}
   - Set Fix Version: {{"action": "set_fix_version", "tracker": "jira", "bug_id": "PROJ-123", "versions": ["v2.0"]}}
   - Set Affects: {{"action": "set_affects_version", "tracker": "jira", "bug_id": "PROJ-123", "versions": ["v1.9"]}}

30. **Sprints & Agile:**
   - Boards: {{"action": "get_boards", "tracker": "jira"}}
   - Sprints: {{"action": "get_sprints", "tracker": "jira", "board_id": 1, "state": "active|future|closed"}}
   - Add to Sprint: {{"action": "add_to_sprint", "tracker": "jira", "sprint_id": 10, "issue_keys": ["PROJ-123", "PROJ-124"]}}
   - Sprint Issues: {{"action": "get_sprint_issues", "tracker": "jira", "sprint_id": 10}}

31. **Users:**
   - Search: {{"action": "search_users", "tracker": "jira", "query": "john", "max_results": 10}}
   - Assignable: {{"action": "get_assignable_users", "tracker": "jira", "project_key": "PROJ"}}

32. **Projects:**
   - List All: {{"action": "get_projects", "tracker": "jira"}}
   - Get Details: {{"action": "get_project", "tracker": "jira", "project_key": "PROJ"}}

33. **Advanced Search (JQL):**
   {{"action": "jql_search", "tracker": "jira", "jql": "project = PROJ AND status = Open AND assignee = currentUser()", "max_results": 50}}

34. **Meta Information:**
   - Issue Types: {{"action": "get_issue_types", "tracker": "jira", "project_key": "PROJ"}}
   - Priorities: {{"action": "get_priorities", "tracker": "jira"}}
   - Statuses: {{"action": "get_statuses", "tracker": "jira"}}

35. **Work Logs:**
   - Add: {{"action": "add_worklog", "tracker": "jira", "bug_id": "PROJ-123", "time_spent": "2h 30m", "comment": "Debugging"}}
   - Get: {{"action": "get_worklogs", "tracker": "jira", "bug_id": "PROJ-123"}}

36. **Subtasks:**
   - Create: {{"action": "create_subtask", "tracker": "jira", "parent_key": "PROJ-123", "summary": "Subtask title", "description": "Details", "assignee": "user"}}
   - Get: {{"action": "get_subtasks", "tracker": "jira", "bug_id": "PROJ-123"}}

Examples of CORRECT responses:
- Action: {{"action": "list_pull_requests", "tracker": "github", "state": "open"}}
- Action: {{"action": "create_issue", "tracker": "github", "title": "Login bug", "labels": ["bug"]}}
- Action: {{"action": "merge_pull_request", "tracker": "github", "pr_number": 45, "merge_method": "squash"}}
- Action: {{"action": "create_issue", "tracker": "jira", "summary": "Login bug", "issue_type": "Bug", "priority": "High"}}
- Action: {{"action": "jql_search", "tracker": "jira", "jql": "assignee = currentUser() AND status != Done"}}
- Chat: "Hello! I can help you manage bugs, PRs, labels, milestones, and more across trackers."

Examples of INCORRECT responses:
- ❌ "I'll create that issue: {{"action": "create_issue"}}"
- ❌ "Let me merge that PR for you..."
- ❌ "I don't have a function to do that" (check if action exists!)

"""

            # Build messages with conversation history
            messages = self.conversation_history[session_id].copy()
            messages.append({"role": "user", "content": message})
            
            response = client.messages.create(
                model=Config.CLAUDE_MODEL,
                max_tokens=1000,
                system=system_prompt,
                messages=messages
            )
            
            # Parse Claude's response
            llm_text = response.content[0].text.strip()
            
            # Check if response is JSON (action) or plain text (conversational)
            try:
                # Try to extract JSON from response
                if "```json" in llm_text:
                    llm_text = llm_text.split("```json")[1].split("```")[0].strip()
                elif "```" in llm_text:
                    llm_text = llm_text.split("```")[1].split("```")[0].strip()
                
                # Look for JSON object in the response (robust extraction)
                json_obj = None
                if '{' in llm_text and '}' in llm_text:
                    # Find the first { and last } to extract potential JSON
                    start_idx = llm_text.find('{')
                    end_idx = llm_text.rfind('}') + 1
                    potential_json = llm_text[start_idx:end_idx].strip()
                    
                    try:
                        json_obj = json.loads(potential_json)
                    except json.JSONDecodeError:
                        json_obj = None
                
                # Check if we found valid JSON with an action
                if json_obj and 'action' in json_obj:
                    # Execute the action
                    result = self._execute_action(json_obj, session_id, message)
                    return result
                else:
                    # It's a conversational response
                    self._store_conversation(session_id, message, llm_text)
                    return {"success": True, "message": llm_text}
                    
            except json.JSONDecodeError:
                # Not JSON, treat as conversational response
                self._store_conversation(session_id, message, llm_text)
                return {"success": True, "message": llm_text}
            except Exception as e:
                # If Claude returns plain text or error, treat as conversational
                error_msg = f"I encountered an issue: {str(e)}. How else can I help you?"
                self._store_conversation(session_id, message, error_msg)
                return {"success": False, "message": error_msg}
        
        except Exception as e:
            # If Claude fails, respond with error message
            print(f"⚠️  Error in chat: {e}")
            return {
                "success": False,
                "message": f"❌ I encountered an error processing your request: {str(e)}"
            }
    
    def _execute_action(self, action_data: Dict[str, Any], session_id: str, user_message: str) -> Dict[str, Any]:
        """Execute action based on Claude's decision.
        
        Args:
            action_data: Dictionary containing action and parameters
            session_id: Session identifier
            user_message: Original user message
            
        Returns:
            Response dictionary
        """
        action = action_data.get("action")
        
        if action == "fetch_bugs":
            tracker = action_data.get("tracker", self.tracker_type)
            max_results = action_data.get("max_results", 10)
            issue_type = action_data.get("issue_type")
            
            result = self.route("fetch_bugs", max_results=max_results, tracker=tracker, issue_type=issue_type)
            
            if result["success"]:
                bugs = result["data"]
                tracker_used = result.get('tracker_used', tracker).upper()
                
                # Determine label and emoji
                if issue_type:
                    if issue_type.lower() in ['story', 'user story']:
                        label, emoji = "user stories", "📖"
                    elif issue_type.lower() == 'task':
                        label, emoji = "tasks", "✅"
                    elif issue_type.lower() == 'epic':
                        label, emoji = "epics", "🎯"
                    else:
                        label, emoji = "bugs", "🐛"
                else:
                    label, emoji = "issues", "📋"
                
                response_msg = f"✅ Found {result['count']} {label} from **{tracker_used}**:\n\n"
                for bug in bugs:
                    response_msg += f"{emoji} **{bug['id']}**: {bug['title']}\n"
                    response_msg += f"   Status: {bug.get('status') or bug.get('state', 'Unknown')}\n\n"
                
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": result["data"]}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Unknown error')}"}
        
        elif action == "list_ids":
            tracker = action_data.get("tracker")
            issue_type = action_data.get("issue_type")
            
            bug_ids = self._extract_ids_from_history(session_id, tracker, issue_type)
            
            if bug_ids:
                if issue_type:
                    if issue_type.lower() in ['story', 'user story']:
                        label = "user story"
                    elif issue_type.lower() == 'task':
                        label = "task"
                    elif issue_type.lower() == 'epic':
                        label = "epic"
                    else:
                        label = "bug"
                else:
                    label = "issue"
                
                tracker_label = tracker.upper() if tracker else "recent conversation"
                response_msg = f"📋 **{label.title()} IDs from {tracker_label}:**\n\n"
                response_msg += "\n".join([f"- {bug_id}" for bug_id in bug_ids])
                response_msg += f"\n\n**Total:** {len(bug_ids)} {label}{'s' if len(bug_ids) != 1 else ''}"
                
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {
                    "success": False,
                    "message": "❌ I don't see any bugs in our recent conversation. Would you like me to fetch some bugs first?"
                }
        
        elif action == "get_bug_details":
            bug_id = action_data.get("bug_id")
            tracker = action_data.get("tracker", self.tracker_type)
            
            if not bug_id:
                return {"success": False, "message": "❌ Please specify a bug ID"}
            
            result = self.route("get_bug_details", bug_id=str(bug_id), tracker=tracker)
            
            if result["success"]:
                bug = result["data"]
                response_msg = f"🐛 **Bug Details: {bug['id']}**\n\n"
                response_msg += f"**Title:** {bug['title']}\n"
                response_msg += f"**Status:** {bug.get('status') or bug.get('state', 'Unknown')}\n"
                if bug.get('priority'):
                    response_msg += f"**Priority:** {bug['priority']}\n"
                if bug.get('assignee'):
                    response_msg += f"**Assignee:** {bug['assignee']}\n"
                response_msg += f"\n**Description:**\n{bug.get('description', 'No description')}"
                
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": bug}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Bug not found')}"}
        
        elif action == "add_comment":
            bug_id = action_data.get("bug_id")
            comment = action_data.get("comment")
            tracker = action_data.get("tracker", self.tracker_type)
            
            if not bug_id or not comment:
                return {"success": False, "message": "❌ Please specify bug ID and comment text"}
            
            result = self.route("add_comment", bug_id=str(bug_id), comment=comment, tracker=tracker)
            
            if result["success"]:
                response_msg = f"✅ Comment added to bug {bug_id}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to add comment')}"}
        
        elif action == "update_status":
            bug_id = action_data.get("bug_id")
            status = action_data.get("status", "closed")
            tracker = action_data.get("tracker", self.tracker_type)
            
            if not bug_id:
                return {"success": False, "message": "❌ Please specify a bug ID"}
            
            # Map status to tracker-specific values
            if status == "closed":
                new_status = "Done" if tracker in ["tfs", "azuredevops"] else "closed"
            else:
                new_status = "To Do" if tracker in ["tfs", "azuredevops"] else "open"
            
            action_name = "update_state" if tracker in ["tfs", "azuredevops", "github"] else "update_status"
            param_name = "new_state" if tracker in ["tfs", "azuredevops", "github"] else "new_status"
            result = self.route(action_name, bug_id=str(bug_id), tracker=tracker, **{param_name: new_status})
            
            if result["success"]:
                response_msg = f"✅ Updated bug {bug_id} to {new_status}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to update')}"}
        
        elif action == "analyze_bug":
            bug_id = action_data.get("bug_id")
            tracker = action_data.get("tracker", self.tracker_type)
            
            if not bug_id:
                return {"success": False, "message": "❌ Please specify a bug ID to analyze"}
            
            # First get bug details
            bug_result = self.route("get_bug_details", bug_id=str(bug_id), tracker=tracker)
            if not bug_result["success"]:
                return {"success": False, "message": f"❌ Error: Could not fetch bug {bug_id}"}
            
            bug = bug_result["data"]
            bug_description = f"Title: {bug['title']}\n\nDescription: {bug.get('description', 'No description')}"
            
            # Analyze code
            analysis_agent = self.agents.get("code_analysis")
            if not analysis_agent:
                return {"success": False, "message": "❌ Code analysis agent not available"}
            
            response_msg = f"🔍 **Analyzing bug {bug_id}...**\n\nThis may take a moment while I scan the codebase.\n\n"
            
            analysis_result = analysis_agent.execute(
                "analyze_bug",
                bug_id=str(bug_id),
                bug_description=bug_description
            )
            
            if analysis_result["success"]:
                data = analysis_result["data"]
                response_msg += f"**Analysis Complete**\n"
                response_msg += f"Files analyzed: {data['total_files_analyzed']}\n\n"
                
                findings = data.get('findings', [])
                if findings:
                    response_msg += f"**Findings ({len(findings)}):**\n\n"
                    for idx, finding in enumerate(findings, 1):
                        response_msg += f"---\n\n"
                        response_msg += f"### Finding {idx}: {finding.get('file', 'Unknown')}\n\n"
                        response_msg += f"**Lines:** {finding.get('lines', 'N/A')}\n\n"
                        response_msg += f"**Severity:** {finding.get('severity', 'Unknown')}\n\n"
                        response_msg += f"**Issue:** {finding.get('issue', 'N/A')}\n\n"
                        response_msg += f"**Resolution:**\n{finding.get('resolution', 'N/A')}\n\n"
                        if finding.get('code_fix'):
                            response_msg += f"**Code Fix:**\n```\n{finding.get('code_fix')}\n```\n\n"
                else:
                    response_msg += "No specific issues found in analyzed files."
                
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": data}
            else:
                return {"success": False, "message": f"❌ Error: {analysis_result.get('error', 'Analysis failed')}"}
        
        elif action == "list_branches":
            repo_url = action_data.get("repo_url")
            
            # Use GitHub agent to list branches
            github_agent = self.agents.get("github")
            if not github_agent:
                return {"success": False, "message": "❌ GitHub agent not available"}
            
            response_msg = f"🌿 **Fetching branches from repository...**\n\n"
            if repo_url:
                response_msg += f"Repository: {repo_url}\n\n"
            else:
                response_msg += f"Repository: Using configured GitHub repo\n\n"
            
            result = github_agent.execute("list_branches", repo_url=repo_url)
            
            if result["success"]:
                data = result.get("data", {})
                branches = data.get("branches", [])
                
                response_msg += f"✅ **Found {len(branches)} branches:**\n\n"
                for branch in branches:
                    response_msg += f"🔹 {branch}\n"
                
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": data}
            else:
                error_msg = f"❌ **Failed to list branches**\n\n{result.get('error', 'Unknown error')}"
                self._store_conversation(session_id, user_message, error_msg)
                return {"success": False, "message": error_msg}
        
        elif action == "clone_repo":
            repo_url = action_data.get("repo_url")
            target_dir = action_data.get("target_dir", "./data/repos")
            branch = action_data.get("branch")
            shallow = action_data.get("shallow", False)
            
            # Use GitHub agent to clone the repo
            github_agent = self.agents.get("github")
            if not github_agent:
                return {"success": False, "message": "❌ GitHub agent not available"}
            
            response_msg = f"📥 **Cloning repository...**\n\n"
            if repo_url:
                response_msg += f"Repository: {repo_url}\n"
            else:
                response_msg += f"Repository: Using configured GitHub repo\n"
            response_msg += f"Target directory: {target_dir}\n"
            if branch:
                response_msg += f"Branch: {branch}\n"
            response_msg += "\n"
            
            # Pass all parameters including branch and shallow
            result = github_agent.execute(
                "clone_repo", 
                repo_url=repo_url, 
                target_dir=target_dir,
                branch=branch,
                shallow=shallow
            )
            
            if result["success"]:
                data = result.get("data", {})
                response_msg += f"✅ **{result['message']}**\n\n"
                response_msg += f"Repository name: **{data.get('repo_name', 'N/A')}**\n"
                response_msg += f"Location: `{data.get('path', 'N/A')}`\n"
                response_msg += f"Action: {data.get('action', 'N/A')}\n"
                
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": data}
            else:
                error_msg = f"❌ **Failed to clone repository**\n\n{result.get('error', 'Unknown error')}"
                self._store_conversation(session_id, user_message, error_msg)
                return {"success": False, "message": error_msg}
        
        elif action == "check_repo_status":
            repo_name = action_data.get("repo_name")
            target_dir = action_data.get("target_dir", "./data/repos")
            
            # Use GitHub agent to check repo status
            github_agent = self.agents.get("github")
            if not github_agent:
                return {"success": False, "message": "❌ GitHub agent not available"}
            
            result = github_agent.execute(
                "check_repo_status",
                repo_name=repo_name,
                target_dir=target_dir
            )
            
            if result["success"]:
                data = result.get("data", {})
                response_msg = f"📊 **Repository Status**\n\n"
                response_msg += f"Repository: **{data.get('repo_name', 'N/A')}**\n"
                response_msg += f"Location: `{data.get('path', 'N/A')}`\n"
                response_msg += f"Current Branch: **{data.get('current_branch', 'N/A')}**\n"
                response_msg += f"Last Commit: {data.get('last_commit', 'N/A')}\n"
                
                if data.get('has_uncommitted_changes'):
                    response_msg += f"\n⚠️ Has uncommitted changes\n"
                else:
                    response_msg += f"\n✓ Working tree clean\n"
                
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": data}
            else:
                error_msg = f"❌ **Failed to get repository status**\n\n{result.get('error', 'Unknown error')}"
                self._store_conversation(session_id, user_message, error_msg)
                return {"success": False, "message": error_msg}
        
        elif action == "list_cloned_repos":
            target_dir = action_data.get("target_dir", "./data/repos")
            
            # Use GitHub agent to list all cloned repos
            github_agent = self.agents.get("github")
            if not github_agent:
                return {"success": False, "message": "❌ GitHub agent not available"}
            
            result = github_agent.execute(
                "list_cloned_repos",
                target_dir=target_dir
            )
            
            if result["success"]:
                data = result.get("data", {})
                repos = data.get("repositories", [])
                
                if repos:
                    response_msg = f"📚 **Cloned Repositories ({len(repos)})**\n\n"
                    for repo in repos:
                        response_msg += f"📁 **{repo.get('name', 'N/A')}**\n"
                        response_msg += f"   Branch: {repo.get('current_branch', 'N/A')}\n"
                        response_msg += f"   Last Commit: {repo.get('last_commit', 'N/A')}\n"
                        response_msg += f"   Path: `{repo.get('path', 'N/A')}`\n\n"
                else:
                    response_msg = f"📭 No cloned repositories found in `{target_dir}`\n"
                
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": data}
            else:
                error_msg = f"❌ **Failed to list repositories**\n\n{result.get('error', 'Unknown error')}"
                self._store_conversation(session_id, user_message, error_msg)
                return {"success": False, "message": error_msg}
        
        # ==== JIRA-SPECIFIC ACTIONS ====
        
        elif action == "create_issue":
            tracker = action_data.get("tracker", self.tracker_type)
            
            # For GitHub vs Jira, different field names
            if tracker == "github":
                title = action_data.get("title")
                body = action_data.get("body")
                labels = action_data.get("labels", [])
                assignees = action_data.get("assignees", [])
                result = self.route("create_issue", tracker=tracker, title=title, body=body, labels=labels, assignees=assignees)
            else:  # Jira
                summary = action_data.get("summary")
                description = action_data.get("description")
                issue_type = action_data.get("issue_type", "Bug")
                priority = action_data.get("priority")
                assignee = action_data.get("assignee")
                labels = action_data.get("labels", [])
                components = action_data.get("components", [])
                result = self.route("create_issue", tracker=tracker, summary=summary, description=description, 
                                   issue_type=issue_type, priority=priority, assignee=assignee, 
                                   labels=labels, components=components)
            
            if result["success"]:
                data = result.get("data", {})
                issue_id = data.get("id") or data.get("number")
                response_msg = f"✅ **Issue Created: {issue_id}**\n\n"
                response_msg += f"**Title:** {data.get('title', data.get('summary', 'N/A'))}\n"
                if data.get('status') or data.get('state'):
                    response_msg += f"**Status:** {data.get('status') or data.get('state')}\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": data}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to create issue')}"}
        
        elif action == "edit_issue":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id") or action_data.get("issue_number")
            
            if not bug_id:
                return {"success": False, "message": "❌ Please specify an issue ID"}
            
            # Pass through all edit parameters
            params = {k: v for k, v in action_data.items() if k not in ["action", "tracker", "bug_id", "issue_number"]}
            result = self.route("edit_issue", tracker=tracker, bug_id=str(bug_id), **params)
            
            if result["success"]:
                response_msg = f"✅ Issue {bug_id} updated successfully"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to update issue')}"}
        
        elif action == "delete_issue":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            
            if not bug_id:
                return {"success": False, "message": "❌ Please specify an issue ID"}
            
            result = self.route("delete_issue", tracker=tracker, bug_id=str(bug_id))
            
            if result["success"]:
                response_msg = f"✅ Issue {bug_id} deleted"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to delete issue')}"}
        
        elif action == "assign_issue":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            assignee = action_data.get("assignee")
            
            if not bug_id:
                return {"success": False, "message": "❌ Please specify an issue ID"}
            
            result = self.route("assign_issue", tracker=tracker, bug_id=str(bug_id), assignee=assignee)
            
            if result["success"]:
                action_msg = f"assigned to {assignee}" if assignee else "unassigned"
                response_msg = f"✅ Issue {bug_id} {action_msg}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to assign issue')}"}
        
        elif action == "get_comments":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            
            if not bug_id:
                return {"success": False, "message": "❌ Please specify an issue ID"}
            
            result = self.route("get_comments", tracker=tracker, bug_id=str(bug_id))
            
            if result["success"]:
                comments = result.get("data", [])
                response_msg = f"💬 **Comments on {bug_id}** ({len(comments)} total):\n\n"
                for c in comments[:10]:
                    response_msg += f"**{c.get('author', 'Unknown')}** ({c.get('created', 'N/A')[:10]}):\n"
                    response_msg += f"{c.get('body', '')[:200]}...\n\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": comments}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get comments')}"}
        
        elif action == "edit_comment":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            comment_id = action_data.get("comment_id")
            new_body = action_data.get("new_body")
            
            if not bug_id or not comment_id or not new_body:
                return {"success": False, "message": "❌ Please specify issue ID, comment ID, and new text"}
            
            result = self.route("edit_comment", tracker=tracker, bug_id=str(bug_id), comment_id=str(comment_id), new_body=new_body)
            
            if result["success"]:
                response_msg = f"✅ Comment updated on {bug_id}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to edit comment')}"}
        
        elif action == "delete_comment":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            comment_id = action_data.get("comment_id")
            
            if not bug_id or not comment_id:
                return {"success": False, "message": "❌ Please specify issue ID and comment ID"}
            
            result = self.route("delete_comment", tracker=tracker, bug_id=str(bug_id), comment_id=str(comment_id))
            
            if result["success"]:
                response_msg = f"✅ Comment deleted from {bug_id}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to delete comment')}"}
        
        elif action == "get_transitions":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            
            if not bug_id:
                return {"success": False, "message": "❌ Please specify an issue ID"}
            
            result = self.route("get_transitions", tracker=tracker, bug_id=str(bug_id))
            
            if result["success"]:
                transitions = result.get("data", [])
                response_msg = f"🔄 **Available Transitions for {bug_id}:**\n\n"
                for t in transitions:
                    response_msg += f"- {t.get('name', 'Unknown')}\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": transitions}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get transitions')}"}
        
        elif action == "add_labels":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            labels = action_data.get("labels", [])
            
            if not bug_id or not labels:
                return {"success": False, "message": "❌ Please specify issue ID and labels"}
            
            result = self.route("add_labels", tracker=tracker, bug_id=str(bug_id), labels=labels)
            
            if result["success"]:
                response_msg = f"🏷️ Added labels to {bug_id}: {', '.join(labels)}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to add labels')}"}
        
        elif action == "remove_labels":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id") or action_data.get("issue_number")
            labels = action_data.get("labels", [])
            
            if not bug_id or not labels:
                return {"success": False, "message": "❌ Please specify issue ID and labels"}
            
            result = self.route("remove_labels", tracker=tracker, bug_id=str(bug_id), labels=labels)
            
            if result["success"]:
                response_msg = f"🏷️ Removed labels from {bug_id}: {', '.join(labels)}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to remove labels')}"}
        
        elif action == "add_watchers":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            usernames = action_data.get("usernames", [])
            
            if not bug_id or not usernames:
                return {"success": False, "message": "❌ Please specify issue ID and usernames"}
            
            result = self.route("add_watchers", tracker=tracker, bug_id=str(bug_id), usernames=usernames)
            
            if result["success"]:
                response_msg = f"👁️ Added watchers to {bug_id}: {', '.join(usernames)}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to add watchers')}"}
        
        elif action == "remove_watchers":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            usernames = action_data.get("usernames", [])
            
            if not bug_id or not usernames:
                return {"success": False, "message": "❌ Please specify issue ID and usernames"}
            
            result = self.route("remove_watchers", tracker=tracker, bug_id=str(bug_id), usernames=usernames)
            
            if result["success"]:
                response_msg = f"👁️ Removed watchers from {bug_id}: {', '.join(usernames)}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to remove watchers')}"}
        
        elif action == "get_watchers":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            
            if not bug_id:
                return {"success": False, "message": "❌ Please specify an issue ID"}
            
            result = self.route("get_watchers", tracker=tracker, bug_id=str(bug_id))
            
            if result["success"]:
                watchers = result.get("data", [])
                response_msg = f"👁️ **Watchers on {bug_id}:** {', '.join(watchers) if watchers else 'None'}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": watchers}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get watchers')}"}
        
        elif action == "link_issues":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            target_issue = action_data.get("target_issue")
            link_type = action_data.get("link_type", "Relates")
            
            if not bug_id or not target_issue:
                return {"success": False, "message": "❌ Please specify source and target issue IDs"}
            
            result = self.route("link_issues", tracker=tracker, bug_id=str(bug_id), target_issue=str(target_issue), link_type=link_type)
            
            if result["success"]:
                response_msg = f"🔗 Linked {bug_id} → {target_issue} ({link_type})"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to link issues')}"}
        
        elif action == "get_issue_links":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            
            if not bug_id:
                return {"success": False, "message": "❌ Please specify an issue ID"}
            
            result = self.route("get_issue_links", tracker=tracker, bug_id=str(bug_id))
            
            if result["success"]:
                links = result.get("data", [])
                response_msg = f"🔗 **Issue Links for {bug_id}:**\n\n"
                for link in links:
                    response_msg += f"- {link.get('type', 'Unknown')}: {link.get('issue', 'N/A')} ({link.get('direction', '')})\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": links}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get issue links')}"}
        
        elif action == "get_link_types":
            tracker = action_data.get("tracker", self.tracker_type)
            result = self.route("get_link_types", tracker=tracker)
            
            if result["success"]:
                link_types = result.get("data", [])
                response_msg = f"🔗 **Available Link Types:**\n\n"
                for lt in link_types:
                    response_msg += f"- **{lt.get('name', 'Unknown')}**: {lt.get('inward', '')} / {lt.get('outward', '')}\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": link_types}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get link types')}"}
        
        elif action == "add_attachment":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            file_path = action_data.get("file_path")
            
            if not bug_id or not file_path:
                return {"success": False, "message": "❌ Please specify issue ID and file path"}
            
            result = self.route("add_attachment", tracker=tracker, bug_id=str(bug_id), file_path=file_path)
            
            if result["success"]:
                response_msg = f"📎 Attachment added to {bug_id}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to add attachment')}"}
        
        elif action == "get_attachments":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            
            if not bug_id:
                return {"success": False, "message": "❌ Please specify an issue ID"}
            
            result = self.route("get_attachments", tracker=tracker, bug_id=str(bug_id))
            
            if result["success"]:
                attachments = result.get("data", [])
                response_msg = f"📎 **Attachments on {bug_id}:**\n\n"
                for a in attachments:
                    response_msg += f"- {a.get('filename', 'Unknown')} ({a.get('size', 0)} bytes)\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": attachments}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get attachments')}"}
        
        elif action == "delete_attachment":
            tracker = action_data.get("tracker", self.tracker_type)
            attachment_id = action_data.get("attachment_id")
            
            if not attachment_id:
                return {"success": False, "message": "❌ Please specify attachment ID"}
            
            result = self.route("delete_attachment", tracker=tracker, attachment_id=str(attachment_id))
            
            if result["success"]:
                response_msg = f"📎 Attachment {attachment_id} deleted"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to delete attachment')}"}
        
        elif action == "get_components":
            tracker = action_data.get("tracker", self.tracker_type)
            project_key = action_data.get("project_key")
            
            result = self.route("get_components", tracker=tracker, project_key=project_key)
            
            if result["success"]:
                components = result.get("data", [])
                response_msg = f"🧩 **Project Components:**\n\n"
                for c in components:
                    response_msg += f"- **{c.get('name', 'Unknown')}**: {c.get('description', 'No description')}\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": components}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get components')}"}
        
        elif action == "create_component":
            tracker = action_data.get("tracker", self.tracker_type)
            name = action_data.get("name")
            description = action_data.get("description")
            
            if not name:
                return {"success": False, "message": "❌ Please specify component name"}
            
            result = self.route("create_component", tracker=tracker, name=name, description=description)
            
            if result["success"]:
                response_msg = f"🧩 Component '{name}' created"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to create component')}"}
        
        elif action == "add_components":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            components = action_data.get("components", [])
            
            if not bug_id or not components:
                return {"success": False, "message": "❌ Please specify issue ID and components"}
            
            result = self.route("add_components", tracker=tracker, bug_id=str(bug_id), components=components)
            
            if result["success"]:
                response_msg = f"🧩 Added components to {bug_id}: {', '.join(components)}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to add components')}"}
        
        elif action == "remove_components":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            components = action_data.get("components", [])
            
            if not bug_id or not components:
                return {"success": False, "message": "❌ Please specify issue ID and components"}
            
            result = self.route("remove_components", tracker=tracker, bug_id=str(bug_id), components=components)
            
            if result["success"]:
                response_msg = f"🧩 Removed components from {bug_id}: {', '.join(components)}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to remove components')}"}
        
        elif action == "get_versions":
            tracker = action_data.get("tracker", self.tracker_type)
            project_key = action_data.get("project_key")
            
            result = self.route("get_versions", tracker=tracker, project_key=project_key)
            
            if result["success"]:
                versions = result.get("data", [])
                response_msg = f"📦 **Project Versions:**\n\n"
                for v in versions:
                    status = "✅ Released" if v.get('released') else "📋 Unreleased"
                    response_msg += f"- **{v.get('name', 'Unknown')}** {status}\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": versions}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get versions')}"}
        
        elif action == "create_version":
            tracker = action_data.get("tracker", self.tracker_type)
            name = action_data.get("name")
            description = action_data.get("description")
            release_date = action_data.get("release_date")
            
            if not name:
                return {"success": False, "message": "❌ Please specify version name"}
            
            result = self.route("create_version", tracker=tracker, name=name, description=description, release_date=release_date)
            
            if result["success"]:
                response_msg = f"📦 Version '{name}' created"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to create version')}"}
        
        elif action == "release_version":
            tracker = action_data.get("tracker", self.tracker_type)
            version_id = action_data.get("version_id")
            
            if not version_id:
                return {"success": False, "message": "❌ Please specify version ID"}
            
            result = self.route("release_version", tracker=tracker, version_id=str(version_id))
            
            if result["success"]:
                response_msg = f"📦 Version {version_id} released"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to release version')}"}
        
        elif action == "set_fix_version":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            versions = action_data.get("versions", [])
            
            if not bug_id or not versions:
                return {"success": False, "message": "❌ Please specify issue ID and versions"}
            
            result = self.route("set_fix_version", tracker=tracker, bug_id=str(bug_id), versions=versions)
            
            if result["success"]:
                response_msg = f"📦 Set fix version for {bug_id}: {', '.join(versions)}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to set fix version')}"}
        
        elif action == "set_affects_version":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            versions = action_data.get("versions", [])
            
            if not bug_id or not versions:
                return {"success": False, "message": "❌ Please specify issue ID and versions"}
            
            result = self.route("set_affects_version", tracker=tracker, bug_id=str(bug_id), versions=versions)
            
            if result["success"]:
                response_msg = f"📦 Set affects version for {bug_id}: {', '.join(versions)}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to set affects version')}"}
        
        elif action == "get_boards":
            tracker = action_data.get("tracker", self.tracker_type)
            result = self.route("get_boards", tracker=tracker)
            
            if result["success"]:
                boards = result.get("data", [])
                response_msg = f"📊 **Agile Boards:**\n\n"
                for b in boards:
                    response_msg += f"- **{b.get('name', 'Unknown')}** (ID: {b.get('id')}, Type: {b.get('type', 'N/A')})\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": boards}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get boards')}"}
        
        elif action == "get_sprints":
            tracker = action_data.get("tracker", self.tracker_type)
            board_id = action_data.get("board_id")
            state = action_data.get("state")
            
            if not board_id:
                return {"success": False, "message": "❌ Please specify board ID"}
            
            result = self.route("get_sprints", tracker=tracker, board_id=int(board_id), state=state)
            
            if result["success"]:
                sprints = result.get("data", [])
                response_msg = f"🏃 **Sprints:**\n\n"
                for s in sprints:
                    response_msg += f"- **{s.get('name', 'Unknown')}** (ID: {s.get('id')}, State: {s.get('state', 'N/A')})\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": sprints}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get sprints')}"}
        
        elif action == "add_to_sprint":
            tracker = action_data.get("tracker", self.tracker_type)
            sprint_id = action_data.get("sprint_id")
            issue_keys = action_data.get("issue_keys", [])
            
            if not sprint_id or not issue_keys:
                return {"success": False, "message": "❌ Please specify sprint ID and issue keys"}
            
            result = self.route("add_to_sprint", tracker=tracker, sprint_id=int(sprint_id), issue_keys=issue_keys)
            
            if result["success"]:
                response_msg = f"🏃 Added {len(issue_keys)} issue(s) to sprint {sprint_id}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to add to sprint')}"}
        
        elif action == "get_sprint_issues":
            tracker = action_data.get("tracker", self.tracker_type)
            sprint_id = action_data.get("sprint_id")
            
            if not sprint_id:
                return {"success": False, "message": "❌ Please specify sprint ID"}
            
            result = self.route("get_sprint_issues", tracker=tracker, sprint_id=int(sprint_id))
            
            if result["success"]:
                issues = result.get("data", [])
                response_msg = f"🏃 **Sprint {sprint_id} Issues ({len(issues)}):**\n\n"
                for issue in issues:
                    response_msg += f"📋 **{issue.get('id')}**: {issue.get('title', 'N/A')}\n"
                    response_msg += f"   Status: {issue.get('status', 'Unknown')}\n\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": issues}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get sprint issues')}"}
        
        elif action == "search_users":
            tracker = action_data.get("tracker", self.tracker_type)
            query = action_data.get("query")
            max_results = action_data.get("max_results", 10)
            
            if not query:
                return {"success": False, "message": "❌ Please specify search query"}
            
            result = self.route("search_users", tracker=tracker, query=query, max_results=max_results)
            
            if result["success"]:
                users = result.get("data", [])
                response_msg = f"👥 **Users matching '{query}':**\n\n"
                for u in users:
                    response_msg += f"- **{u.get('displayName', 'Unknown')}** ({u.get('emailAddress', 'N/A')})\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": users}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to search users')}"}
        
        elif action == "get_assignable_users":
            tracker = action_data.get("tracker", self.tracker_type)
            project_key = action_data.get("project_key")
            bug_id = action_data.get("bug_id")
            
            result = self.route("get_assignable_users", tracker=tracker, project_key=project_key, bug_id=bug_id)
            
            if result["success"]:
                users = result.get("data", [])
                response_msg = f"👥 **Assignable Users:**\n\n"
                for u in users:
                    response_msg += f"- **{u.get('displayName', 'Unknown')}** ({u.get('name', u.get('accountId', 'N/A'))})\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": users}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get assignable users')}"}
        
        elif action == "get_projects":
            tracker = action_data.get("tracker", self.tracker_type)
            result = self.route("get_projects", tracker=tracker)
            
            if result["success"]:
                projects = result.get("data", [])
                response_msg = f"📁 **Projects ({len(projects)}):**\n\n"
                for p in projects:
                    response_msg += f"- **{p.get('key', 'N/A')}**: {p.get('name', 'Unknown')}\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": projects}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get projects')}"}
        
        elif action == "get_project":
            tracker = action_data.get("tracker", self.tracker_type)
            project_key = action_data.get("project_key")
            
            result = self.route("get_project", tracker=tracker, project_key=project_key)
            
            if result["success"]:
                project = result.get("data", {})
                response_msg = f"📁 **Project: {project.get('name', 'Unknown')}**\n\n"
                response_msg += f"**Key:** {project.get('key', 'N/A')}\n"
                response_msg += f"**Lead:** {project.get('lead', 'N/A')}\n"
                response_msg += f"**Description:** {project.get('description', 'No description')}\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": project}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get project')}"}
        
        elif action == "jql_search":
            tracker = action_data.get("tracker", self.tracker_type)
            jql = action_data.get("jql")
            max_results = action_data.get("max_results", 50)
            
            if not jql:
                return {"success": False, "message": "❌ Please specify JQL query"}
            
            result = self.route("jql_search", tracker=tracker, jql=jql, max_results=max_results)
            
            if result["success"]:
                issues = result.get("data", [])
                response_msg = f"🔍 **JQL Results ({len(issues)} issues):**\n\n"
                for issue in issues[:15]:
                    response_msg += f"📋 **{issue.get('id')}**: {issue.get('title', 'N/A')}\n"
                    response_msg += f"   Status: {issue.get('status', 'Unknown')}\n\n"
                if len(issues) > 15:
                    response_msg += f"... and {len(issues) - 15} more\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": issues}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'JQL search failed')}"}
        
        elif action == "get_issue_types":
            tracker = action_data.get("tracker", self.tracker_type)
            project_key = action_data.get("project_key")
            
            result = self.route("get_issue_types", tracker=tracker, project_key=project_key)
            
            if result["success"]:
                issue_types = result.get("data", [])
                response_msg = f"📝 **Issue Types:**\n\n"
                for it in issue_types:
                    subtask_label = " (Subtask)" if it.get('subtask') else ""
                    response_msg += f"- **{it.get('name', 'Unknown')}**{subtask_label}\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": issue_types}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get issue types')}"}
        
        elif action == "get_priorities":
            tracker = action_data.get("tracker", self.tracker_type)
            result = self.route("get_priorities", tracker=tracker)
            
            if result["success"]:
                priorities = result.get("data", [])
                response_msg = f"⚡ **Priorities:**\n\n"
                for p in priorities:
                    response_msg += f"- **{p.get('name', 'Unknown')}**: {p.get('description', 'N/A')}\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": priorities}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get priorities')}"}
        
        elif action == "get_statuses":
            tracker = action_data.get("tracker", self.tracker_type)
            project_key = action_data.get("project_key")
            
            result = self.route("get_statuses", tracker=tracker, project_key=project_key)
            
            if result["success"]:
                statuses = result.get("data", [])
                response_msg = f"📊 **Statuses:**\n\n"
                for s in statuses:
                    response_msg += f"- **{s.get('name', 'Unknown')}** ({s.get('category', 'N/A')})\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": statuses}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get statuses')}"}
        
        elif action == "add_worklog":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            time_spent = action_data.get("time_spent")
            comment = action_data.get("comment")
            
            if not bug_id or not time_spent:
                return {"success": False, "message": "❌ Please specify issue ID and time spent"}
            
            result = self.route("add_worklog", tracker=tracker, bug_id=str(bug_id), time_spent=time_spent, comment=comment)
            
            if result["success"]:
                response_msg = f"⏱️ Logged {time_spent} on {bug_id}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to add worklog')}"}
        
        elif action == "get_worklogs":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            
            if not bug_id:
                return {"success": False, "message": "❌ Please specify an issue ID"}
            
            result = self.route("get_worklogs", tracker=tracker, bug_id=str(bug_id))
            
            if result["success"]:
                worklogs = result.get("data", [])
                response_msg = f"⏱️ **Work Logs for {bug_id}:**\n\n"
                total_seconds = 0
                for w in worklogs:
                    response_msg += f"- **{w.get('author', 'Unknown')}**: {w.get('timeSpent', 'N/A')} - {w.get('comment', 'No comment')[:50]}\n"
                    total_seconds += w.get('timeSpentSeconds', 0)
                hours = total_seconds // 3600
                response_msg += f"\n**Total:** {hours}h {(total_seconds % 3600) // 60}m"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": worklogs}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get worklogs')}"}
        
        elif action == "create_subtask":
            tracker = action_data.get("tracker", self.tracker_type)
            parent_key = action_data.get("parent_key")
            summary = action_data.get("summary")
            description = action_data.get("description")
            assignee = action_data.get("assignee")
            
            if not parent_key or not summary:
                return {"success": False, "message": "❌ Please specify parent issue and subtask summary"}
            
            result = self.route("create_subtask", tracker=tracker, parent_key=parent_key, summary=summary, description=description, assignee=assignee)
            
            if result["success"]:
                data = result.get("data", {})
                response_msg = f"✅ Subtask {data.get('id')} created under {parent_key}"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": data}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to create subtask')}"}
        
        elif action == "get_subtasks":
            tracker = action_data.get("tracker", self.tracker_type)
            bug_id = action_data.get("bug_id")
            
            if not bug_id:
                return {"success": False, "message": "❌ Please specify parent issue ID"}
            
            result = self.route("get_subtasks", tracker=tracker, bug_id=str(bug_id))
            
            if result["success"]:
                subtasks = result.get("data", [])
                response_msg = f"📋 **Subtasks of {bug_id} ({len(subtasks)}):**\n\n"
                for st in subtasks:
                    response_msg += f"- **{st.get('id')}**: {st.get('title', 'N/A')} ({st.get('status', 'Unknown')})\n"
                self._store_conversation(session_id, user_message, response_msg)
                return {"success": True, "message": response_msg, "data": subtasks}
            else:
                return {"success": False, "message": f"❌ Error: {result.get('error', 'Failed to get subtasks')}"}
        
        else:
            return {"success": False, "message": f"❌ Unknown action: {action}"}
    
    def _store_conversation(self, session_id: str, user_message: str, assistant_message: str):
        """Store user and assistant messages in conversation history."""
        from datetime import datetime
        
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
            # Generate dynamic title based on user query
            title = self._generate_session_title(user_message)
            self.session_metadata[session_id] = {
                "title": title,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        else:
            # Update timestamp
            self.session_metadata.setdefault(session_id, {
                "title": "Chat Session",
                "created_at": datetime.now().isoformat()
            })
            self.session_metadata[session_id]["updated_at"] = datetime.now().isoformat()
        
        self.conversation_history[session_id].append({"role": "user", "content": user_message})
        self.conversation_history[session_id].append({"role": "assistant", "content": assistant_message})
        
        # Keep only last 10 exchanges (20 messages) to avoid token limits
        if len(self.conversation_history[session_id]) > 20:
            self.conversation_history[session_id] = self.conversation_history[session_id][-20:]
        
        # Persist to disk
        self._save_conversation_history()
    
    def _generate_session_title(self, user_message: str) -> str:
        """Generate a descriptive session title based on user query."""
        import re
        
        # Normalize message
        msg = user_message.lower().strip()
        
        # Pattern-based title generation
        if any(word in msg for word in ['fetch', 'show', 'get', 'list', 'display']) and any(word in msg for word in ['bug', 'issue', 'ticket']):
            tracker = None
            if 'jira' in msg:
                tracker = 'Jira'
            elif 'github' in msg:
                tracker = 'GitHub'
            elif 'tfs' in msg:
                tracker = 'TFS'
            
            issue_type = None
            if 'story' in msg or 'stories' in msg:
                issue_type = 'Stories'
            elif 'epic' in msg:
                issue_type = 'Epics'
            elif 'task' in msg:
                issue_type = 'Tasks'
            else:
                issue_type = 'Issues'
            
            return f"{tracker + ' ' if tracker else ''}{issue_type}"
        
        elif any(word in msg for word in ['branch', 'branches']):
            if 'list' in msg or 'show' in msg:
                return "List Branches"
            elif 'clone' in msg:
                # Extract branch name if present
                match = re.search(r'\b(\d+\.\d+\.x|main|master|develop|\w+[-_]\w+)\b', msg)
                if match:
                    return f"Clone {match.group(1)}"
                return "Clone Repository"
            return "Repository Branches"
        
        elif 'clone' in msg or 'pull' in msg:
            # Extract repo or branch name
            match = re.search(r'(spring-\w+|\w+/\w+|[\w-]+)', msg)
            if match:
                return f"Clone {match.group(1)}"
            return "Clone Repository"
        
        elif 'status' in msg and 'repo' in msg:
            return "Repository Status"
        
        elif 'cloned' in msg and ('list' in msg or 'show' in msg or 'what' in msg):
            return "List Cloned Repos"
        
        elif any(word in msg for word in ['comment', 'add comment']):
            # Extract bug ID if present
            match = re.search(r'([A-Z]+-\d+|#\d+|\d+)', msg)
            if match:
                return f"Comment on {match.group(1)}"
            return "Add Comment"
        
        elif any(word in msg for word in ['close', 'open', 'update']) and any(word in msg for word in ['bug', 'issue']):
            match = re.search(r'([A-Z]+-\d+|#\d+)', msg)
            action = 'Close' if 'close' in msg else 'Open' if 'open' in msg else 'Update'
            if match:
                return f"{action} {match.group(1)}"
            return f"{action} Issue"
        
        elif 'analyze' in msg or 'analysis' in msg:
            match = re.search(r'([A-Z]+-\d+|#\d+)', msg)
            if match:
                return f"Analyze {match.group(1)}"
            return "Bug Analysis"
        
        elif any(word in msg for word in ['help', 'what can you', 'capabilities']):
            return "Help & Capabilities"
        
        elif any(word in msg for word in ['hello', 'hi', 'hey', 'greet']):
            return "General Chat"
        
        # Default: use first 40 chars with smart truncation
        if len(user_message) <= 40:
            return user_message
        else:
            # Truncate at word boundary
            truncated = user_message[:40]
            last_space = truncated.rfind(' ')
            if last_space > 20:  # Only truncate at space if it's not too early
                truncated = truncated[:last_space]
            return truncated + "..."
    
    def _extract_ids_from_history(self, session_id: str, tracker: Optional[str] = None, issue_type: Optional[str] = None) -> List[str]:
        """Extract bug IDs from conversation history.
        
        Args:
            session_id: Session identifier
            tracker: Optional tracker to filter by
            issue_type: Optional issue type to filter by
            
        Returns:
            List of bug IDs found in recent conversation
        """
        import re
        
        if session_id not in self.conversation_history:
            return []
        
        bug_ids = []
        
        # Search through assistant messages for bug IDs
        for msg in reversed(self.conversation_history[session_id]):
            if msg["role"] == "assistant":
                content = msg["content"]
                
                # Look for patterns like "ABC-123", "#123", "**36026**"
                # Jira pattern: ABC-123
                jira_pattern = r'\b([A-Z]+-\d+)\b'
                # GitHub pattern: #123 or **123**
                github_pattern = r'(?:\*\*|#)(\d+)(?:\*\*|:)'
                
                # Extract IDs based on tracker
                if tracker:
                    if tracker.lower() == "jira":
                        matches = re.findall(jira_pattern, content)
                        bug_ids.extend(matches)
                    elif tracker.lower() == "github":
                        matches = re.findall(github_pattern, content)
                        bug_ids.extend(matches)
                else:
                    # Extract all patterns
                    jira_matches = re.findall(jira_pattern, content)
                    github_matches = re.findall(github_pattern, content)
                    bug_ids.extend(jira_matches)
                    bug_ids.extend(github_matches)
                
                # Stop if we found IDs (only look at most recent bug list)
                if bug_ids:
                    break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_ids = []
        for bug_id in bug_ids:
            if bug_id not in seen:
                seen.add(bug_id)
                unique_ids.append(bug_id)
        
        return unique_ids
    
    def clear_history(self, session_id: str = "default"):
        """Clear conversation history for a session."""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
            # Persist to disk
            self._save_conversation_history()
    
    def delete_session(self, session_id: str):
        """Delete a chat session completely (history and metadata)."""
        deleted = False
        
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
            deleted = True
        
        if session_id in self.session_metadata:
            del self.session_metadata[session_id]
            deleted = True
        
        if deleted:
            # Persist to disk
            self._save_conversation_history()
            return True
        
        return False
    
    def get_all_sessions(self):
        """Get metadata for all chat sessions."""
        sessions = []
        for session_id, metadata in self.session_metadata.items():
            message_count = len(self.conversation_history.get(session_id, []))
            sessions.append({
                "id": session_id,
                "title": metadata.get("title", "Chat Session"),
                "created_at": metadata.get("created_at", ""),
                "updated_at": metadata.get("updated_at", ""),
                "message_count": message_count
            })
        
        # Sort by updated_at descending
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions
    
    def _get_help_message(self) -> str:
        """Get help message."""
        available_trackers = [k.upper() for k in ["jira", "tfs", "github"] if k in self.agents]
        
        if not available_trackers:
            return "❌ No bug trackers are configured. Please set up credentials for Jira, TFS, or GitHub in your .env file."
        
        response = f"🤖 **Sustenance** - Intelligent Multi-Tracker Assistant\n\n"
        response += f"**Available Trackers:** {', '.join(available_trackers)}\n"
        
        if self.tracker_type:
            response += f"**Default Tracker:** {self.tracker_type.upper()}\n\n"
        else:
            response += "**Tracker Selection:** Dynamic (I decide based on your query)\n\n"
        
        response += "## 📋 Issue Management\n"
        response += "• **Fetch Issues**: \"show me 10 bugs\" | \"pull user stories from jira\" | \"get github issues\"\n"
        response += "• **Create Issues**: \"create issue 'Bug in login' with label 'bug'\"\n"
        response += "• **Edit Issues**: \"edit issue #123 title to 'Fixed: Login bug'\"\n"
        response += "• **Search Issues**: \"search issues by author 'johndoe' with label 'bug'\"\n"
        response += "• **Bug Details**: \"details about ABC-123\" | \"what's issue #456?\"\n"
        response += "• **Add Comments**: \"add comment 'fixed in v2.0' to bug ABC-123\"\n"
        response += "• **Update Status**: \"close bug ABC-123\" | \"reopen issue #456\"\n"
        response += "• **Labels**: \"add label 'urgent' to #123\" | \"remove label 'wontfix' from #123\" | \"list all labels\"\n"
        response += "• **Assign**: \"assign user 'johndoe' to #123\"\n\n"
        
        response += "## 🔄 Pull Requests\n"
        response += "• **List PRs**: \"list open pull requests\" | \"show all PRs\"\n"
        response += "• **PR Details**: \"details about PR #45\"\n"
        response += "• **Create PR**: \"create PR from 'feature-branch' to 'main'\"\n"
        response += "• **Merge PR**: \"merge PR #45 with squash\" | \"merge PR #45\"\n"
        response += "• **Review PR**: \"approve PR #45\" | \"request changes on PR #45\"\n"
        response += "• **View Diff**: \"show diff for PR #45\"\n"
        response += "• **Changed Files**: \"what files changed in PR #45\"\n\n"
        
        response += "## 🏷️ Labels & Milestones\n"
        response += "• **Labels**: \"create label 'needs-review' with color 'yellow'\" | \"list all labels\" | \"delete label 'wontfix'\"\n"
        response += "• **Milestones**: \"create milestone 'v2.0'\" | \"list milestones\" | \"assign issue #123 to milestone 1\"\n\n"
        
        response += "## 🔧 Repository Management\n"
        response += "• **Branches**: \"show all branches\" | \"create branch 'feature-x' from 'develop'\" | \"delete branch 'old-feature'\"\n"
        response += "• **Clone**: \"clone 6.2.x branch\" | \"clone main branch\"\n"
        response += "• **Status**: \"what branch is cloned?\" | \"check repo status\"\n"
        response += "• **List Repos**: \"what repos do I have?\" | \"list all cloned repos\"\n"
        response += "• **Compare**: \"compare main and develop branches\"\n"
        response += "• **Info**: \"get repo info\" | \"show contributors\" | \"list top contributors\"\n\n"
        
        response += "## 📁 Files & Code\n"
        response += "• **Get Files**: \"get content of README.md\" | \"show README from main branch\"\n"
        response += "• **Search Code**: \"search for 'authentication' in src\" | \"search code for 'handleLogin'\"\n"
        response += "• **Commits**: \"show last 10 commits\" | \"get commit history for develop\"\n\n"
        
        response += "## 🏷️ Releases & Tags\n"
        response += "• **Releases**: \"list all releases\" | \"create release v2.0 'Major Update'\" | \"get release v1.5\"\n"
        response += "• **Tags**: \"list all tags\" | \"create tag v2.0.1\"\n\n"
        
        response += "## 👥 Collaborators\n"
        response += "• **List**: \"list all collaborators\" | \"show collaborators\"\n"
        response += "• **Add**: \"add 'johndoe' as collaborator\" | \"invite 'janedoe' with push access\"\n"
        response += "• **Remove**: \"remove collaborator 'johndoe'\"\n\n"
        
        response += "## 🔍 Code Analysis\n"
        response += "• **Analyze Bug**: \"analyze bug ABC-123\" | \"analyze github issue #456\"\n\n"
        
        response += "## 💬 Session Management\n"
        response += "• **New Chat**: Click '➕ New Chat' button to start fresh conversation\n"
        response += "• **Session History**: All chats saved automatically in sidebar\n"
        response += "• **Delete Session**: Hover over session and click 🗑️ to delete\n"
        response += "• **Dynamic Titles**: Sessions auto-named based on your queries\n"
        response += "• **Persistent Storage**: Chat history saved even after server restart\n\n"
        
        response += "💡 **Tips:**\n"
        response += "• Use natural language - I understand context from conversation\n"
        response += "• All GitHub capabilities available: issues, PRs, labels, milestones, branches, releases, collaborators\n"
        response += "• Specify tracker name (jira/github/tfs) or I'll use smart defaults\n"
        response += "• Large repos use 15-minute timeout for cloning\n"
        response += "• Switch between sessions anytime by clicking in sidebar\n\n"
        
        response += "Just ask me in natural language - I'm here to help! 🚀\n"
        response += "📖 **Full documentation**: docs/GITHUB_CAPABILITIES.md"
        return response
    
    def _fallback_parse(self, message: str) -> Dict[str, Any]:
        """Fallback keyword-based parsing if Claude fails."""
        message_lower = message.lower()
        
        # Parse intent and extract parameters
        if any(keyword in message_lower for keyword in ["fetch", "get", "show", "list", "retrieve"]) and \
           any(keyword in message_lower for keyword in ["bug", "issue", "ticket"]):
            # Extract max_results if specified
            import re
            max_match = re.search(r'(\d+)', message)
            max_results = int(max_match.group(1)) if max_match else 10
            
            result = self.route("fetch_bugs", max_results=max_results)
            if result["success"]:
                bugs = result["data"]
                response = f"✅ Found {result['count']} bugs:\n\n"
                for bug in bugs:
                    response += f"🐛 **{bug['id']}**: {bug['title']}\n"
                    response += f"   Status: {bug.get('status') or bug.get('state', 'Unknown')}\n\n"
                return {"success": True, "message": response, "data": result["data"]}
            else:
                return {"success": False, "message": f"❌ Error: {result['error']}"}
            # Extract max_results if specified
            import re
            max_match = re.search(r'(\d+)', message)
            max_results = int(max_match.group(1)) if max_match else 10
            
            result = self.route("fetch_bugs", max_results=max_results)
            if result["success"]:
                bugs = result["data"]
                response = f"✅ Found {result['count']} bugs:\n\n"
                for bug in bugs:
                    response += f"🐛 **{bug['id']}**: {bug['title']}\n"
                    response += f"   Status: {bug.get('status') or bug.get('state', 'Unknown')}\n\n"
                return {"success": True, "message": response, "data": result["data"]}
            else:
                return {"success": False, "message": f"❌ Error: {result['error']}"}
        
        elif "detail" in message_lower or "info" in message_lower or "about" in message_lower:
            # Extract bug ID
            import re
            id_match = re.search(r'#?([A-Z]+-\d+|\d+|[A-Z]+\d+)', message, re.IGNORECASE)
            if id_match:
                bug_id = id_match.group(1).replace('#', '')
                result = self.route("get_bug_details", bug_id=bug_id)
                if result["success"]:
                    bug = result["data"]
                    response = f"🐛 **Bug Details: {bug['id']}**\n\n"
                    response += f"**Title:** {bug['title']}\n"
                    response += f"**Status:** {bug.get('status') or bug.get('state', 'Unknown')}\n"
                    if bug.get('priority'):
                        response += f"**Priority:** {bug['priority']}\n"
                    if bug.get('assignee'):
                        response += f"**Assignee:** {bug['assignee']}\n"
                    response += f"\n**Description:**\n{bug.get('description', 'No description')}"
                    return {"success": True, "message": response, "data": bug}
                else:
                    return {"success": False, "message": f"❌ Error: {result['error']}"}
            else:
                return {"success": False, "message": "❌ Please specify a bug ID (e.g., 'details about #123')"}
        
        elif "comment" in message_lower or "add note" in message_lower:
            # Extract bug ID and comment
            import re
            parts = message.split(" on ", 1)
            if len(parts) == 2:
                comment_text = parts[0].split("comment", 1)[-1].strip().strip('"\'')
                bug_id_match = re.search(r'#?([A-Z]+-\d+|\d+|[A-Z]+\d+)', parts[1], re.IGNORECASE)
                if bug_id_match:
                    bug_id = bug_id_match.group(1).replace('#', '')
                    result = self.route("add_comment", bug_id=bug_id, comment=comment_text)
                    if result["success"]:
                        return {"success": True, "message": f"✅ Comment added to {bug_id}"}
                    else:
                        return {"success": False, "message": f"❌ Error: {result['error']}"}
            return {"success": False, "message": "❌ Format: 'add comment \"your comment\" on #BUG-123'"}
        
        elif "update" in message_lower or "change" in message_lower or "close" in message_lower:
            # Extract bug ID and new status
            import re
            id_match = re.search(r'#?([A-Z]+-\d+|\d+|[A-Z]+\d+)', message, re.IGNORECASE)
            if id_match:
                bug_id = id_match.group(1).replace('#', '')
                # Determine status
                if "close" in message_lower or "done" in message_lower or "resolved" in message_lower:
                    new_status = "Done" if self.tracker_type in ["tfs", "azuredevops"] else "closed"
                elif "open" in message_lower or "reopen" in message_lower:
                    new_status = "To Do" if self.tracker_type in ["tfs", "azuredevops"] else "open"
                else:
                    return {"success": False, "message": "❌ Specify status: 'close #123' or 'open #123'"}
                
                action = "update_state" if self.tracker_type in ["tfs", "azuredevops", "github"] else "update_status"
                param = "new_state" if self.tracker_type in ["tfs", "azuredevops", "github"] else "new_status"
                result = self.route(action, bug_id=bug_id, **{param: new_status})
                if result["success"]:
                    return {"success": True, "message": f"✅ Updated {bug_id} to {new_status}"}
                else:
                    return {"success": False, "message": f"❌ Error: {result['error']}"}
            return {"success": False, "message": "❌ Please specify a bug ID (e.g., 'close #123')"}
        
        elif "help" in message_lower or "what can" in message_lower or "capabilities" in message_lower:
            return {"success": True, "message": self._get_help_message()}
        
        else:
            return {
                "success": False, 
                "message": "🤔 I didn't quite understand that. Try asking about bugs, or type 'help' to see what I can do."
            }
    
    def route(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Route action to appropriate agent using Claude LLM for intelligent routing.
        
        Args:
            action: Action to perform
            **kwargs: Action parameters (including optional 'tracker' parameter)
            
        Returns:
            Response dictionary with success status and data/error
        """
        # Check if it's a code analysis action
        if action in ["analyze_bug", "scan_repository", "analyze_with_context"]:
            agent = self.agents.get("code_analysis")
            if not agent:
                return {
                    "success": False,
                    "error": "Code analysis agent not available"
                }
            return agent.execute(action, **kwargs)
        
        # Get tracker from kwargs or use Claude to determine best tracker
        tracker = kwargs.pop("tracker", None)
        
        if not tracker:
            # Use Claude LLM to intelligently select the best tracker
            tracker = self._route_to_best_tracker(action, kwargs)
        
        # Validate tracker is available
        if tracker not in self.agents:
            available = [k for k in ["jira", "tfs", "github"] if k in self.agents]
            # Auto-fallback to default or first available
            if self.tracker_type and self.tracker_type in self.agents:
                tracker = self.tracker_type
                print(f"⚠️  Requested tracker not available, using default: {tracker.upper()}")
            elif available:
                tracker = available[0]
                print(f"⚠️  Requested tracker not available, using first available: {tracker.upper()}")
            else:
                return {
                    "success": False,
                    "error": f"No bug tracker agents are available"
                }
        
        # Get the agent for the specified tracker
        agent = self.agents.get(tracker)
        
        if not agent:
            available = [k for k in ["jira", "tfs", "github"] if k in self.agents]
            return {
                "success": False,
                "error": f"Tracker '{tracker}' not initialized properly. Available trackers: {', '.join(available)}"
            }
        
        # Check if agent supports the action
        if action not in agent.get_capabilities():
            return {
                "success": False,
                "error": f"Agent {agent.name} does not support action: {action}",
                "supported_actions": agent.get_capabilities()
            }
        
        # Execute the action
        return agent.execute(action, **kwargs)
    
    def _route_to_best_tracker(self, action: str, params: Dict[str, Any]) -> str:
        """Use Claude LLM to intelligently route to the best tracker."""
        try:
            from anthropic import Anthropic
            import json
            http_client = httpx.Client(verify=False, timeout=60.0)
            client = Anthropic(api_key=Config.ANTHROPIC_API_KEY, http_client=http_client)
            
            available_trackers = [k for k in ["jira", "tfs", "github"] if k in self.agents]
            
            if len(available_trackers) == 1:
                return available_trackers[0]
            
            if not available_trackers:
                return None
            
            # Get default tracker description for prompt
            default_desc = f"Default tracker: {self.tracker_type}" if self.tracker_type else "No default tracker set"
            
            routing_prompt = f"""You are a routing agent for a bug tracking system.

Available trackers: {', '.join(available_trackers)}
{default_desc}

Action requested: {action}
Parameters: {json.dumps(params)}

Analyze the request and determine which tracker is most appropriate:
1. If bug_id contains specific patterns (e.g., ABC-123 for Jira, #123 for GitHub, plain numbers for TFS)
2. Consider the default tracker preference
3. Consider context clues in the parameters

Respond with ONLY the tracker name (one of: {', '.join(available_trackers)}) and nothing else."""

            response = client.messages.create(
                model=Config.CLAUDE_MODEL,
                max_tokens=50,
                messages=[{"role": "user", "content": routing_prompt}]
            )
            
            suggested_tracker = response.content[0].text.strip().lower()
            
            # Validate the suggestion
            if suggested_tracker in available_trackers:
                print(f"🤖 Claude LLM routed to: {suggested_tracker.upper()}")
                return suggested_tracker
            else:
                print(f"⚠️  Claude suggested invalid tracker: {suggested_tracker}, using fallback")
                return self.tracker_type if self.tracker_type else available_trackers[0]
                
        except Exception as e:
            print(f"⚠️  Routing LLM failed: {e}, using fallback tracker")
            available_trackers = [k for k in ["jira", "tfs", "github"] if k in self.agents]
            return self.tracker_type if self.tracker_type else (available_trackers[0] if available_trackers else None)
    
    def get_available_actions(self) -> List[str]:
        """Get list of all available actions for current agent."""
        agent = self.agents.get(self.tracker_type)
        return agent.get_capabilities() if agent else []
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the active agent."""
        # If no specific tracker, return info about all available trackers
        if not self.tracker_type:
            available = [k for k in ["jira", "tfs", "github"] if k in self.agents]
            return {
                "name": "SuperAgent (Dynamic Routing)",
                "tracker": "dynamic",
                "available_trackers": available,
                "capabilities": ["fetch_bugs", "get_bug_details", "add_comment", "update_status", "analyze_bug"]
            }
        
        agent = self.agents.get(self.tracker_type)
        if agent:
            return {
                "name": agent.name,
                "tracker": self.tracker_type,
                "capabilities": agent.get_capabilities()
            }
        return {
            "error": f"No agent available for: {self.tracker_type}"
        }
