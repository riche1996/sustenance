# GitHub Agent Capabilities Documentation

## Overview
The GitHub Agent provides comprehensive integration with GitHub repositories, issues, pull requests, and repository management features.

## 📋 Issue Management

### Fetch Issues
**Action**: `fetch_bugs`
- **Description**: Retrieve GitHub issues with filtering options
- **Parameters**:
  - `state`: 'open', 'closed', or 'all' (default: 'open')
  - `labels`: Filter by labels (array)
  - `max_results`: Maximum number of issues (default: 10)
- **Example**: "show me 10 open GitHub issues"

### Get Issue Details
**Action**: `get_bug_details`
- **Description**: Get detailed information about a specific issue
- **Parameters**:
  - `bug_id`: Issue number
- **Example**: "details about issue #123"

### Create Issue
**Action**: `create_issue`
- **Description**: Create a new GitHub issue
- **Parameters**:
  - `title`: Issue title (required)
  - `body`: Issue description
  - `labels`: Array of label names
  - `assignees`: Array of usernames
  - `milestone`: Milestone number
- **Example**: "create issue 'Bug in login' with label 'bug'"

### Edit Issue
**Action**: `edit_issue`
- **Description**: Update an existing issue
- **Parameters**:
  - `issue_number`: Issue to edit
  - `title`: New title (optional)
  - `body`: New description (optional)
  - `state`: 'open' or 'closed' (optional)
  - `labels`: New labels (optional)
- **Example**: "edit issue #123 title to 'Fixed: Bug in login'"

### Add Comment
**Action**: `add_comment`
- **Description**: Add a comment to an issue
- **Parameters**:
  - `bug_id`: Issue number
  - `comment`: Comment text
- **Example**: "add comment 'Working on this' to #123"

### Update State
**Action**: `update_state`
- **Description**: Update issue state (open/closed)
- **Parameters**:
  - `bug_id`: Issue number
  - `new_state`: 'open' or 'closed'
- **Example**: "close issue #123"

### Add Labels
**Action**: `add_labels`
- **Description**: Add labels to an issue
- **Parameters**:
  - `bug_id`: Issue number
  - `labels`: Array of label names
- **Example**: "add labels 'bug' and 'urgent' to #123"

### Remove Labels
**Action**: `remove_labels`
- **Description**: Remove labels from an issue
- **Parameters**:
  - `issue_number`: Issue number
  - `labels`: Array of label names to remove
- **Example**: "remove label 'wontfix' from #123"

### Assign Users
**Action**: `assign_users`
- **Description**: Assign users to an issue
- **Parameters**:
  - `bug_id`: Issue number
  - `assignees`: Array of usernames
- **Example**: "assign user 'johndoe' to #123"

### Search Issues
**Action**: `search_issues`
- **Description**: Advanced issue search with filters
- **Parameters**:
  - `query`: Search query
  - `author`: Filter by author
  - `assignee`: Filter by assignee
  - `labels`: Filter by labels
  - `state`: 'open', 'closed', or 'all'
  - `sort`: Sort by 'created', 'updated', 'comments'
  - `order`: 'asc' or 'desc'
- **Example**: "search issues by author 'johndoe' with label 'bug'"

## 🔖 Labels Management

### List Labels
**Action**: `list_labels`
- **Description**: Get all repository labels
- **Parameters**: None
- **Example**: "list all labels"

### Create Label
**Action**: `create_label`
- **Description**: Create a new label
- **Parameters**:
  - `name`: Label name (required)
  - `color`: Hex color code without '#' (required)
  - `description`: Label description (optional)
- **Example**: "create label 'needs-review' with color 'yellow'"

### Edit Label
**Action**: `edit_label`
- **Description**: Update an existing label
- **Parameters**:
  - `name`: Current label name
  - `new_name`: New label name (optional)
  - `color`: New color (optional)
  - `description`: New description (optional)
- **Example**: "change label 'bug' color to red"

### Delete Label
**Action**: `delete_label`
- **Description**: Delete a label from repository
- **Parameters**:
  - `name`: Label name
- **Example**: "delete label 'wontfix'"

## 🎯 Milestones Management

### List Milestones
**Action**: `list_milestones`
- **Description**: Get all repository milestones
- **Parameters**:
  - `state`: 'open', 'closed', or 'all' (default: 'open')
- **Example**: "list all milestones"

### Create Milestone
**Action**: `create_milestone`
- **Description**: Create a new milestone
- **Parameters**:
  - `title`: Milestone title (required)
  - `description`: Milestone description (optional)
  - `due_date`: Due date in ISO format (optional)
  - `state`: 'open' or 'closed' (default: 'open')
- **Example**: "create milestone 'v2.0 Release'"

### Update Milestone
**Action**: `update_milestone`
- **Description**: Update milestone details
- **Parameters**:
  - `number`: Milestone number
  - `title`: New title (optional)
  - `description`: New description (optional)
  - `due_date`: New due date (optional)
  - `state`: 'open' or 'closed' (optional)
- **Example**: "close milestone 1"

### Assign to Milestone
**Action**: `assign_milestone`
- **Description**: Assign an issue to a milestone
- **Parameters**:
  - `issue_number`: Issue number
  - `milestone_number`: Milestone number
- **Example**: "assign issue #123 to milestone 1"

## 🔄 Pull Requests

### List Pull Requests
**Action**: `list_pull_requests`
- **Description**: Get repository pull requests
- **Parameters**:
  - `state`: 'open', 'closed', 'all' (default: 'open')
  - `sort`: 'created', 'updated', 'popularity' (default: 'created')
  - `direction`: 'asc' or 'desc' (default: 'desc')
- **Example**: "list all open pull requests"

### Get Pull Request Details
**Action**: `get_pull_request`
- **Description**: Get detailed PR information
- **Parameters**:
  - `pr_number`: Pull request number
- **Example**: "details about PR #45"

### Create Pull Request
**Action**: `create_pull_request`
- **Description**: Create a new pull request
- **Parameters**:
  - `title`: PR title (required)
  - `body`: PR description
  - `head`: Branch to merge from (required)
  - `base`: Branch to merge into (default: 'main')
  - `draft`: Create as draft (optional)
- **Example**: "create PR from 'feature-branch' to 'main'"

### Merge Pull Request
**Action**: `merge_pull_request`
- **Description**: Merge a pull request
- **Parameters**:
  - `pr_number`: Pull request number
  - `merge_method`: 'merge', 'squash', or 'rebase' (default: 'merge')
  - `commit_message`: Custom merge commit message (optional)
- **Example**: "merge PR #45 with squash"

### Add PR Review
**Action**: `add_review`
- **Description**: Add a review to a pull request
- **Parameters**:
  - `pr_number`: Pull request number
  - `event`: 'APPROVE', 'REQUEST_CHANGES', or 'COMMENT'
  - `body`: Review comment
- **Example**: "approve PR #45"

### Get PR Diff
**Action**: `get_pr_diff`
- **Description**: Get the code diff for a pull request
- **Parameters**:
  - `pr_number`: Pull request number
- **Example**: "show diff for PR #45"

### Get PR Files
**Action**: `get_pr_files`
- **Description**: Get list of files changed in a PR
- **Parameters**:
  - `pr_number`: Pull request number
- **Example**: "what files changed in PR #45"

## 📦 Repository Management

### List Branches
**Action**: `list_branches`
- **Description**: List all repository branches
- **Parameters**:
  - `repo_url`: Repository URL (uses configured repo if not provided)
- **Example**: "list all branches"

### Clone Repository
**Action**: `clone_repo`
- **Description**: Clone a repository locally
- **Parameters**:
  - `repo_url`: Repository URL (uses configured repo if not provided)
  - `target_dir`: Target directory (default: './data/repos')
  - `branch`: Specific branch to clone (optional)
  - `shallow`: Shallow clone (default: false)
- **Example**: "clone 6.2.x branch"

### Check Repository Status
**Action**: `check_repo_status`
- **Description**: Check status of cloned repository
- **Parameters**:
  - `repo_name`: Repository name
  - `target_dir`: Directory containing repos (default: './data/repos')
- **Example**: "check repo status"

### List Cloned Repos
**Action**: `list_cloned_repos`
- **Description**: List all locally cloned repositories
- **Parameters**:
  - `target_dir`: Directory containing repos (default: './data/repos')
- **Example**: "list all cloned repos"

### Get Repository Info
**Action**: `get_repo_info`
- **Description**: Get repository information
- **Parameters**:
  - `owner`: Repository owner (uses configured if not provided)
  - `repo`: Repository name (uses configured if not provided)
- **Example**: "get repo info"
- **Returns**: Name, description, stars, forks, language, size, etc.

### List Contributors
**Action**: `list_contributors`
- **Description**: Get repository contributors
- **Parameters**:
  - `max_results`: Maximum number of contributors (default: 30)
- **Example**: "list top contributors"

### Get Commit History
**Action**: `get_commit_history`
- **Description**: Get recent commits
- **Parameters**:
  - `branch`: Branch name (default: default branch)
  - `max_results`: Maximum number of commits (default: 10)
  - `author`: Filter by author (optional)
- **Example**: "show last 10 commits"

### Get File Content
**Action**: `get_file_content`
- **Description**: Read file content from repository
- **Parameters**:
  - `path`: File path in repository
  - `branch`: Branch name (optional, uses default)
- **Example**: "get content of README.md"

### Search Code
**Action**: `search_code`
- **Description**: Search code in repository
- **Parameters**:
  - `query`: Search query
  - `path`: Limit to specific path (optional)
  - `language`: Filter by language (optional)
- **Example**: "search for 'authentication' in src"

### Create Branch
**Action**: `create_branch`
- **Description**: Create a new branch
- **Parameters**:
  - `branch_name`: New branch name
  - `from_branch`: Source branch (default: default branch)
- **Example**: "create branch 'feature-login' from 'develop'"

### Delete Branch
**Action**: `delete_branch`
- **Description**: Delete a remote branch
- **Parameters**:
  - `branch_name`: Branch to delete
- **Example**: "delete branch 'old-feature'"

### Compare Branches
**Action**: `compare_branches`
- **Description**: Compare two branches
- **Parameters**:
  - `base`: Base branch
  - `head`: Head branch
- **Example**: "compare 'main' with 'develop'"

## 👥 Collaborators

### List Collaborators
**Action**: `list_collaborators`
- **Description**: Get repository collaborators
- **Parameters**: None
- **Example**: "list all collaborators"

### Add Collaborator
**Action**: `add_collaborator`
- **Description**: Invite user as collaborator
- **Parameters**:
  - `username`: GitHub username
  - `permission`: 'pull', 'push', 'admin', 'maintain', 'triage' (default: 'push')
- **Example**: "add 'johndoe' as collaborator"

### Remove Collaborator
**Action**: `remove_collaborator`
- **Description**: Remove collaborator access
- **Parameters**:
  - `username`: GitHub username
- **Example**: "remove collaborator 'johndoe'"

## 🏷️ Releases & Tags

### List Releases
**Action**: `list_releases`
- **Description**: Get all repository releases
- **Parameters**:
  - `max_results`: Maximum number of releases (default: 10)
- **Example**: "list all releases"

### Get Release
**Action**: `get_release`
- **Description**: Get specific release details
- **Parameters**:
  - `tag`: Release tag name
- **Example**: "get release v2.0"

### Create Release
**Action**: `create_release`
- **Description**: Create a new release
- **Parameters**:
  - `tag`: Tag name (required)
  - `name`: Release name (required)
  - `body`: Release notes
  - `draft`: Is draft (default: false)
  - `prerelease`: Is prerelease (default: false)
  - `target`: Target commitish (default: default branch)
- **Example**: "create release v2.0 'Version 2.0'"

### List Tags
**Action**: `list_tags`
- **Description**: Get all repository tags
- **Parameters**:
  - `max_results`: Maximum number of tags (default: 30)
- **Example**: "list all tags"

### Create Tag
**Action**: `create_tag`
- **Description**: Create a new tag
- **Parameters**:
  - `tag`: Tag name (required)
  - `sha`: Commit SHA (required)
  - `message`: Tag message
- **Example**: "create tag v2.0.1 on latest commit"

## 🔔 Notifications

### Get Notifications
**Action**: `get_notifications`
- **Description**: Get user notifications
- **Parameters**:
  - `all`: Include read notifications (default: false)
  - `participating`: Only participating notifications (default: false)
  - `max_results`: Maximum number (default: 20)
- **Example**: "show my notifications"

### Mark Notification as Read
**Action**: `mark_notification_read`
- **Description**: Mark notification as read
- **Parameters**:
  - `notification_id`: Notification ID
- **Example**: "mark notification as read"

## 🔗 Webhooks

### List Webhooks
**Action**: `list_webhooks`
- **Description**: Get repository webhooks
- **Parameters**: None
- **Example**: "list all webhooks"

### Create Webhook
**Action**: `create_webhook`
- **Description**: Create a new webhook
- **Parameters**:
  - `url`: Webhook URL (required)
  - `events`: Array of events (default: ['push'])
  - `active`: Webhook is active (default: true)
  - `secret`: Webhook secret (optional)
- **Example**: "create webhook for push events"

### Delete Webhook
**Action**: `delete_webhook`
- **Description**: Delete a webhook
- **Parameters**:
  - `webhook_id`: Webhook ID
- **Example**: "delete webhook 12345"

## Usage Tips

1. **Natural Language**: All actions support natural language queries
2. **Default Repository**: Most actions use configured GitHub repo if not specified
3. **Batch Operations**: Some actions support bulk operations (e.g., multiple labels)
4. **Error Handling**: All actions return structured error messages
5. **Rate Limiting**: GitHub API rate limits apply (5000 requests/hour for authenticated)

## Configuration

Set these environment variables in `.env`:
```
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=repository_owner
GITHUB_REPO=repository_name
```

## Examples

```python
# Fetch open issues
"show me 10 open issues"

# Create issue with labels
"create issue 'Login broken' with labels 'bug' and 'urgent'"

# List and merge PR
"list open PRs"
"merge PR #45 with squash"

# Clone and check status
"clone 6.2.x branch"
"check repo status"

# Search and analyze
"search for 'authentication' in code"
"show commit history for develop branch"

# Manage releases
"list all releases"
"create release v2.0 'Major Update'"
```

## Version
**Last Updated**: December 19, 2025
**API Version**: GitHub REST API v3
**Documentation**: https://docs.github.com/rest
