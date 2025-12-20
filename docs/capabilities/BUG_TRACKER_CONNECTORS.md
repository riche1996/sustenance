# Bug Tracker Connectors

This document describes the bug tracking system connectors available in the sustenance project.

## Overview

The system supports three bug tracking platforms:
- **Jira** (Atlassian Jira Cloud/Server)
- **TFS/Azure DevOps** (Microsoft Azure DevOps Services)
- **GitHub** (GitHub Issues)

All connectors follow a unified interface pattern, making it easy to switch between different bug tracking systems.

## Supported Bug Trackers

### 1. Jira Connector

**File**: `src/jira_mcp.py`

**Features**:
- Fetch bugs using JQL queries
- Filter by project, status, priority
- Add comments to issues
- Update issue status/transitions
- Support for custom fields, labels, and components

**Configuration** (`.env`):
```env
BUG_TRACKER=jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_api_token
JIRA_PROJECT_KEY=PROJ
```

**Usage Example**:
```python
from jira_mcp import JiraMCPServer

jira = JiraMCPServer()
bugs = jira.get_bugs(status=['Open', 'In Progress'], max_results=10)

for bug in bugs:
    print(f"{bug.key}: {bug.summary}")
    print(f"Status: {bug.status}, Priority: {bug.priority}")
```

### 2. TFS/Azure DevOps Connector

**File**: `src/tfs_mcp.py`

**Features**:
- Fetch bugs using WIQL queries
- Filter by project, state, area path, iteration
- Support for priority and severity
- Add comments to work items
- Update work item state
- Full Azure DevOps REST API v7.1 support

**Configuration** (`.env`):
```env
BUG_TRACKER=tfs
TFS_URL=https://dev.azure.com
TFS_ORGANIZATION=your_organization
TFS_PROJECT=your_project
TFS_PAT=your_personal_access_token
```

**Usage Example**:
```python
from tfs_mcp import TfsMCPServer

tfs = TfsMCPServer()
bugs = tfs.get_bugs(state=['New', 'Active'], max_results=10)

for bug in bugs:
    print(f"#{bug.id}: {bug.title}")
    print(f"State: {bug.state}, Priority: {bug.priority}")
```

### 3. GitHub Connector

**File**: `src/github_mcp.py`

**Features**:
- Fetch issues with 'bug' label
- Filter by state, labels, milestones
- Add comments to issues
- Update issue state (open/closed)
- Add/remove labels
- Assign/unassign users

**Configuration** (`.env`):
```env
BUG_TRACKER=github
GITHUB_OWNER=your_username_or_org
GITHUB_REPO=your_repository
GITHUB_TOKEN=your_personal_access_token
```

**Usage Example**:
```python
from github_mcp import GitHubMCPServer

github = GitHubMCPServer()
bugs = github.get_bugs(state='open', max_results=10)

for bug in bugs:
    print(f"#{bug.number}: {bug.title}")
    print(f"State: {bug.state}, Labels: {', '.join(bug.labels)}")
```

## Unified Bug Tracker Interface

**File**: `src/bug_tracker_factory.py`

The `UnifiedBugTracker` class provides a common interface that works with all bug tracking systems:

```python
from bug_tracker_factory import UnifiedBugTracker

# Automatically uses the configured tracker (from BUG_TRACKER env var)
tracker = UnifiedBugTracker()

# Get bugs (works with any tracker)
bugs = tracker.get_bugs(max_results=10)

# Get specific issue
bug = tracker.get_issue("PROJ-123")  # Jira
bug = tracker.get_issue(12345)       # TFS/GitHub

# Add comment (works with any tracker)
tracker.add_comment(issue_id, "Analysis complete")

# Update status/state
tracker.update_status(issue_id, "In Progress")

# Format bug for display
description = tracker.format_bug_description(bug)
print(description)
```

### Benefits of Unified Interface

1. **Switch trackers easily** - Change `BUG_TRACKER` in `.env` without modifying code
2. **Consistent API** - Same methods work across all trackers
3. **Easy integration** - Plug into existing analysis workflow
4. **Future-proof** - Add new trackers without breaking existing code

## Authentication

### Jira
- **API Token**: Generate from Atlassian Account Settings → Security → API Tokens
- **Email**: Your Atlassian account email

### TFS/Azure DevOps
- **Personal Access Token (PAT)**: 
  1. Go to Azure DevOps → User Settings → Personal Access Tokens
  2. Create new token with "Work Items (Read & Write)" scope
  3. Copy the token immediately (shown only once)

### GitHub
- **Personal Access Token**:
  1. Go to GitHub → Settings → Developer settings → Personal access tokens
  2. Generate new token (classic) with `repo` scope
  3. Copy the token

## Testing

Test your bug tracker configuration:

```bash
# Set PYTHONPATH and run test
$env:PYTHONPATH = "C:\Users\richard.mochahari\my_space\POCs\sustenance\sustenance\src"
.\.venv\Scripts\python.exe scripts/test_bug_trackers.py
```

The test script will:
- Validate connection to configured tracker
- Fetch sample bugs
- Test unified interface
- Display formatted output

## Data Models

### Jira Issue
```python
class JiraIssue:
    key: str
    summary: str
    description: Optional[str]
    issue_type: str
    status: str
    priority: Optional[str]
    assignee: Optional[str]
    reporter: Optional[str]
    created: str
    updated: str
    labels: List[str]
    components: List[str]
```

### TFS Work Item
```python
class TfsWorkItem:
    id: int
    title: str
    description: Optional[str]
    work_item_type: str
    state: str
    priority: Optional[int]
    severity: Optional[str]
    assigned_to: Optional[str]
    created_by: Optional[str]
    created_date: str
    changed_date: str
    tags: List[str]
    area_path: Optional[str]
    iteration_path: Optional[str]
```

### GitHub Issue
```python
class GitHubIssue:
    number: int
    title: str
    body: Optional[str]
    state: str
    labels: List[str]
    assignee: Optional[str]
    assignees: List[str]
    created_by: Optional[str]
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    milestone: Optional[str]
    html_url: str
```

## Integration with Analysis Workflow

The bug tracker connectors integrate seamlessly with the existing analysis workflow:

```python
from bug_tracker_factory import UnifiedBugTracker
from code_analyzer import CodeAnalysisAgent
from report_generator import ReportGenerator

# Initialize tracker (automatically uses configured system)
tracker = UnifiedBugTracker()

# Fetch bugs
bugs = tracker.get_bugs(max_results=10)

# Analyze each bug
analyzer = CodeAnalysisAgent()
for bug in bugs:
    bug_id = tracker.get_bug_identifier(bug)
    bug_description = tracker.format_bug_description(bug)
    
    # Analyze with Claude AI
    findings = analyzer.analyze_bug(bug_description, code_files)
    
    # Add analysis as comment
    comment = f"Analysis complete: {len(findings)} findings"
    tracker.add_comment(bug_id, comment)
```

## Error Handling

All connectors implement proper error handling:

```python
try:
    tracker = UnifiedBugTracker()
    bugs = tracker.get_bugs()
except ConnectionError as e:
    print(f"Failed to connect: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Troubleshooting

### Jira Connection Issues
- Verify URL format: `https://your-domain.atlassian.net` (no trailing slash)
- Check API token is not expired
- Ensure email matches Atlassian account

### TFS/Azure DevOps Issues
- Verify organization and project names are correct
- Check PAT has proper permissions (Work Items Read/Write)
- Ensure PAT is not expired

### GitHub Issues
- Verify owner/repo names are correct
- Check token has `repo` scope
- Public repos still require authentication

## API Rate Limits

Be aware of API rate limits:
- **Jira Cloud**: ~100 requests per minute per user
- **Azure DevOps**: 200 requests per minute per user/PAT
- **GitHub**: 5,000 requests per hour (authenticated)

## Future Enhancements

Planned improvements:
- GitLab connector
- Bugzilla connector
- Linear connector
- Custom field mapping
- Webhook support
- Bulk operations
- Advanced filtering

## Contributing

To add a new bug tracker:

1. Create `src/<tracker>_mcp.py` following the existing pattern
2. Define issue model using Pydantic
3. Implement core methods: `get_bugs()`, `get_issue()`, `add_comment()`, `update_status()`
4. Update `bug_tracker_factory.py` to support new tracker
5. Add configuration to `config.py`
6. Update `.env` with new settings
7. Add tests to `test_bug_trackers.py`
8. Document in this README
