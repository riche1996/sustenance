# Quick Start Guide: Bug Tracker Connectors

## Setup in 3 Steps

### 1. Choose Your Bug Tracker

Edit `.env` and set `BUG_TRACKER` to one of: `jira`, `tfs`, or `github`

### 2. Configure Credentials

#### For Jira:
```env
BUG_TRACKER=jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_api_token
JIRA_PROJECT_KEY=PROJ
```

#### For TFS/Azure DevOps:
```env
BUG_TRACKER=tfs
TFS_URL=https://dev.azure.com
TFS_ORGANIZATION=your_org
TFS_PROJECT=your_project
TFS_PAT=your_personal_access_token
```

#### For GitHub:
```env
BUG_TRACKER=github
GITHUB_OWNER=your_username_or_org
GITHUB_REPO=your_repository
GITHUB_TOKEN=your_github_token
```

### 3. Test Connection

```bash
$env:PYTHONPATH = "C:\Users\richard.mochahari\my_space\POCs\sustenance\sustenance\src"
.\.venv\Scripts\python.exe scripts/test_bug_trackers.py
```

## Usage Examples

### Using Specific Connector

```python
# Jira
from jira_mcp import JiraMCPServer
jira = JiraMCPServer()
bugs = jira.get_bugs(max_results=10)

# TFS
from tfs_mcp import TfsMCPServer
tfs = TfsMCPServer()
bugs = tfs.get_bugs(max_results=10)

# GitHub
from github_mcp import GitHubMCPServer
github = GitHubMCPServer()
bugs = github.get_bugs(max_results=10)
```

### Using Unified Interface (Recommended)

```python
from bug_tracker_factory import UnifiedBugTracker

# Works with any configured tracker
tracker = UnifiedBugTracker()
bugs = tracker.get_bugs(max_results=10)

for bug in bugs:
    bug_id = tracker.get_bug_identifier(bug)
    summary = tracker.get_bug_summary(bug)
    print(f"{bug_id}: {summary}")
```

## Getting API Tokens

### Jira API Token
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy and save the token

### Azure DevOps PAT
1. Go to Azure DevOps → User Settings (top right)
2. Select "Personal access tokens"
3. Click "New Token"
4. Select "Work Items (Read & Write)" scope
5. Copy the token immediately

### GitHub Token
1. Go to GitHub → Settings → Developer settings
2. Select "Personal access tokens" → "Tokens (classic)"
3. Click "Generate new token"
4. Select "repo" scope
5. Copy the token

## Common Commands

```bash
# Set Python path
$env:PYTHONPATH = "C:\Users\richard.mochahari\my_space\POCs\sustenance\sustenance\src"

# Test connectors
.\.venv\Scripts\python.exe scripts/test_bug_trackers.py

# Run analysis
.\.venv\Scripts\python.exe src/main.py --max-bugs 5

# Run demo
.\.venv\Scripts\python.exe scripts/demo.py
```

## Switching Trackers

Just change `BUG_TRACKER` in `.env`:

```env
# Switch from Jira to GitHub
BUG_TRACKER=github  # was: jira
```

No code changes needed! The `UnifiedBugTracker` handles everything.

## Troubleshooting

**"ConnectionError: Failed to connect"**
- Check URL format (no trailing slash for Jira)
- Verify credentials are correct
- Test API token/PAT is not expired

**"No bugs found"**
- Check project key/name is correct
- Verify bugs exist in the tracker
- Check filters (status, state, labels)

**"Missing required environment variables"**
- Run setup check: `python scripts/setup_check.py`
- Verify `.env` file exists and has correct variables

## Files Created

- `src/jira_mcp.py` - Jira connector
- `src/tfs_mcp.py` - TFS/Azure DevOps connector
- `src/github_mcp.py` - GitHub connector
- `src/bug_tracker_factory.py` - Unified interface
- `scripts/test_bug_trackers.py` - Test script
- `docs/BUG_TRACKER_CONNECTORS.md` - Full documentation

## Next Steps

1. Configure your preferred bug tracker
2. Test the connection
3. Run the analysis workflow
4. Check generated reports

For more details, see [BUG_TRACKER_CONNECTORS.md](BUG_TRACKER_CONNECTORS.md)
