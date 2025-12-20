# Jira Agent Capabilities Documentation

## Overview

The Jira Agent provides comprehensive integration with Atlassian Jira for issue tracking, project management, and agile workflows. This document details all **50 capabilities** available through the Sustenance Jira integration.

**Implementation Date:** December 2025  
**Total Capabilities:** 50 actions  
**Previous Capabilities:** 5 actions  
**New Capabilities Added:** 45 actions (900% increase)

---

## 📋 Issue Management (12 actions)

### Fetch Issues
**Action**: `fetch_bugs`
- **Description**: Retrieve issues from Jira with filtering
- **Parameters**:
  - `status`: List of statuses (e.g., ['Open', 'In Progress'])
  - `max_results`: Maximum number of results (default: 10)
  - `issue_type`: Type filter (Bug, Story, Task, Epic)
- **Example**: "show me open bugs from Jira"

### Get Issue Details
**Action**: `get_bug_details`
- **Description**: Get detailed information about a specific issue
- **Parameters**:
  - `bug_id`: Jira issue key (e.g., 'PROJ-123')
- **Example**: "get details for PROJ-123"

### Create Issue
**Action**: `create_issue`
- **Description**: Create a new Jira issue
- **Parameters**:
  - `summary`: Issue title (required)
  - `issue_type`: Bug, Story, Task, Epic, Sub-task (default: Bug)
  - `description`: Issue description
  - `priority`: Highest, High, Medium, Low, Lowest
  - `assignee`: Username to assign
  - `labels`: List of labels
  - `components`: List of component names
- **Example**: "create a bug 'Login fails on mobile' with priority High"

### Edit Issue
**Action**: `edit_issue`
- **Description**: Update an existing issue's fields
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `summary`: New title
  - `description`: New description
  - `priority`: New priority
  - `assignee`: New assignee
  - `labels`: New labels (replaces existing)
  - `components`: New components
- **Example**: "update PROJ-123 priority to Highest"

### Delete Issue
**Action**: `delete_issue`
- **Description**: Delete an issue permanently
- **Parameters**:
  - `bug_id`: Issue key (required)
- **Example**: "delete issue PROJ-123"
- **Warning**: This action is irreversible

### Assign Issue
**Action**: `assign_issue`
- **Description**: Assign or unassign a user to/from an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `assignee`: Username (None to unassign)
- **Example**: "assign PROJ-123 to johndoe"

### Add Comment
**Action**: `add_comment`
- **Description**: Add a comment to an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `comment`: Comment text (required)
- **Example**: "add comment 'Working on this' to PROJ-123"

### Edit Comment
**Action**: `edit_comment`
- **Description**: Update an existing comment
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `comment_id`: Comment ID (required)
  - `new_body`: New comment text (required)
- **Example**: "edit comment 10001 on PROJ-123 to 'Updated analysis'"

### Delete Comment
**Action**: `delete_comment`
- **Description**: Delete a comment
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `comment_id`: Comment ID (required)
- **Example**: "delete comment 10001 from PROJ-123"

### Get Comments
**Action**: `get_comments`
- **Description**: Get all comments for an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
- **Example**: "show comments on PROJ-123"

### Update Status
**Action**: `update_status`
- **Description**: Change issue status via workflow transition
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `new_status`: Transition name (e.g., 'In Progress', 'Done')
- **Example**: "move PROJ-123 to In Progress"

### Get Transitions
**Action**: `get_transitions`
- **Description**: Get available workflow transitions for an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
- **Example**: "what transitions are available for PROJ-123?"

---

## 🏷️ Labels Management (2 actions)

### Add Labels
**Action**: `add_labels`
- **Description**: Add labels to an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `labels`: List of label names (required)
- **Example**: "add labels 'urgent' and 'backend' to PROJ-123"

### Remove Labels
**Action**: `remove_labels`
- **Description**: Remove labels from an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `labels`: List of label names (required)
- **Example**: "remove label 'wontfix' from PROJ-123"

---

## 👁️ Watchers Management (3 actions)

### Add Watchers
**Action**: `add_watchers`
- **Description**: Add users as watchers to an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `usernames`: List of usernames (required)
- **Example**: "add johndoe and janedoe as watchers to PROJ-123"

### Remove Watchers
**Action**: `remove_watchers`
- **Description**: Remove watchers from an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `usernames`: List of usernames (required)
- **Example**: "remove johndoe from watching PROJ-123"

### Get Watchers
**Action**: `get_watchers`
- **Description**: Get list of watchers for an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
- **Example**: "who is watching PROJ-123?"

---

## 🔗 Issue Links (3 actions)

### Link Issues
**Action**: `link_issues`
- **Description**: Create a link between two issues
- **Parameters**:
  - `bug_id`: Source issue key (required)
  - `target_issue`: Target issue key (required)
  - `link_type`: Link type (Relates, Blocks, Cloners, Duplicate, etc.)
- **Example**: "link PROJ-123 blocks PROJ-456"

### Get Issue Links
**Action**: `get_issue_links`
- **Description**: Get all links for an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
- **Example**: "show links for PROJ-123"

### Get Link Types
**Action**: `get_link_types`
- **Description**: Get all available issue link types
- **Parameters**: None
- **Example**: "what link types are available?"

---

## 📎 Attachments (3 actions)

### Add Attachment
**Action**: `add_attachment`
- **Description**: Upload a file attachment to an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `file_path`: Local file path (required)
- **Example**: "attach /path/to/file.txt to PROJ-123"

### Get Attachments
**Action**: `get_attachments`
- **Description**: List all attachments on an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
- **Example**: "show attachments on PROJ-123"

### Delete Attachment
**Action**: `delete_attachment`
- **Description**: Delete an attachment
- **Parameters**:
  - `attachment_id`: Attachment ID (required)
- **Example**: "delete attachment 10001"

---

## 🧩 Components (4 actions)

### Get Components
**Action**: `get_components`
- **Description**: List all components in a project
- **Parameters**:
  - `project_key`: Project key (optional, uses default)
- **Example**: "list components in PROJ"

### Create Component
**Action**: `create_component`
- **Description**: Create a new component in a project
- **Parameters**:
  - `name`: Component name (required)
  - `description`: Component description
  - `lead_username`: Component lead
- **Example**: "create component 'Backend Services'"

### Add Components to Issue
**Action**: `add_components`
- **Description**: Add components to an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `components`: List of component names (required)
- **Example**: "add component 'Backend' to PROJ-123"

### Remove Components from Issue
**Action**: `remove_components`
- **Description**: Remove components from an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `components`: List of component names (required)
- **Example**: "remove component 'Frontend' from PROJ-123"

---

## 📦 Versions / Releases (5 actions)

### Get Versions
**Action**: `get_versions`
- **Description**: List all versions in a project
- **Parameters**:
  - `project_key`: Project key (optional)
- **Example**: "show versions in PROJ"

### Create Version
**Action**: `create_version`
- **Description**: Create a new version/release
- **Parameters**:
  - `name`: Version name (required)
  - `description`: Version description
  - `release_date`: Target release date (YYYY-MM-DD)
- **Example**: "create version v2.0 with release date 2025-03-31"

### Release Version
**Action**: `release_version`
- **Description**: Mark a version as released
- **Parameters**:
  - `version_id`: Version ID (required)
- **Example**: "release version 10001"

### Set Fix Version
**Action**: `set_fix_version`
- **Description**: Set fix version(s) for an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `versions`: List of version names (required)
- **Example**: "set fix version v2.0 for PROJ-123"

### Set Affects Version
**Action**: `set_affects_version`
- **Description**: Set affects version(s) for an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `versions`: List of version names (required)
- **Example**: "set affects version v1.9 for PROJ-123"

---

## 🏃 Sprints & Agile (4 actions)

### Get Boards
**Action**: `get_boards`
- **Description**: List all agile boards
- **Parameters**: None
- **Example**: "show all boards"

### Get Sprints
**Action**: `get_sprints`
- **Description**: List sprints for a board
- **Parameters**:
  - `board_id`: Board ID (required)
  - `state`: Filter by state (active, future, closed)
- **Example**: "show active sprints on board 1"

### Add to Sprint
**Action**: `add_to_sprint`
- **Description**: Add issues to a sprint
- **Parameters**:
  - `sprint_id`: Sprint ID (required)
  - `issue_keys`: List of issue keys (required)
- **Example**: "add PROJ-123 and PROJ-124 to sprint 10"

### Get Sprint Issues
**Action**: `get_sprint_issues`
- **Description**: Get all issues in a sprint
- **Parameters**:
  - `sprint_id`: Sprint ID (required)
- **Example**: "show issues in sprint 10"

---

## 👥 Users (2 actions)

### Search Users
**Action**: `search_users`
- **Description**: Search for users by name or email
- **Parameters**:
  - `query`: Search query (required)
  - `max_results`: Maximum results (default: 10)
- **Example**: "search for user john"

### Get Assignable Users
**Action**: `get_assignable_users`
- **Description**: Get users who can be assigned to issues
- **Parameters**:
  - `project_key`: Project key (optional)
  - `bug_id`: Issue key (optional, for issue-specific)
- **Example**: "who can be assigned to issues in PROJ?"

---

## 📁 Projects (2 actions)

### Get Projects
**Action**: `get_projects`
- **Description**: List all accessible projects
- **Parameters**: None
- **Example**: "show all projects"

### Get Project Details
**Action**: `get_project`
- **Description**: Get detailed project information
- **Parameters**:
  - `project_key`: Project key (optional, uses default)
- **Example**: "get details for project PROJ"

---

## 🔍 Search (2 actions)

### Search Issues
**Action**: `search_bugs`
- **Description**: Basic issue search
- **Parameters**:
  - `jql`: JQL query string
  - `max_results`: Maximum results (default: 50)
- **Example**: "search for bugs assigned to me"

### JQL Search
**Action**: `jql_search`
- **Description**: Advanced search using JQL (Jira Query Language)
- **Parameters**:
  - `jql`: JQL query string (required)
  - `max_results`: Maximum results (default: 50)
- **Example**: "jql search: project = PROJ AND status = Open AND assignee = currentUser()"

#### Common JQL Queries:
```jql
# Open issues assigned to me
assignee = currentUser() AND status != Done

# High priority bugs
project = PROJ AND type = Bug AND priority in (High, Highest)

# Issues updated in last 7 days
updated >= -7d

# Unassigned issues in current sprint
assignee is EMPTY AND Sprint = "Sprint 10"

# Issues with specific label
labels = "critical" AND status != Closed
```

---

## 📝 Meta Information (3 actions)

### Get Issue Types
**Action**: `get_issue_types`
- **Description**: Get available issue types for a project
- **Parameters**:
  - `project_key`: Project key (optional)
- **Example**: "what issue types are available?"

### Get Priorities
**Action**: `get_priorities`
- **Description**: Get all available priorities
- **Parameters**: None
- **Example**: "show priority levels"

### Get Statuses
**Action**: `get_statuses`
- **Description**: Get all available statuses
- **Parameters**:
  - `project_key`: Project key (optional)
- **Example**: "what statuses are available?"

---

## ⏱️ Work Logs (2 actions)

### Add Work Log
**Action**: `add_worklog`
- **Description**: Log time spent on an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
  - `time_spent`: Time spent (required, e.g., '2h', '30m', '1d')
  - `comment`: Work log comment
- **Example**: "log 2h 30m on PROJ-123 for debugging"

### Get Work Logs
**Action**: `get_worklogs`
- **Description**: Get all work logs for an issue
- **Parameters**:
  - `bug_id`: Issue key (required)
- **Example**: "show work logs for PROJ-123"

---

## 📋 Subtasks (2 actions)

### Create Subtask
**Action**: `create_subtask`
- **Description**: Create a subtask under a parent issue
- **Parameters**:
  - `parent_key`: Parent issue key (required)
  - `summary`: Subtask title (required)
  - `description`: Subtask description
  - `assignee`: Assignee username
- **Example**: "create subtask 'Write unit tests' under PROJ-123"

### Get Subtasks
**Action**: `get_subtasks`
- **Description**: Get all subtasks of an issue
- **Parameters**:
  - `bug_id`: Parent issue key (required)
- **Example**: "show subtasks of PROJ-123"

---

## Configuration

### Required Environment Variables

```env
# Jira Configuration
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_api_token
JIRA_PROJECT_KEY=PROJ  # Default project
```

### Getting a Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a descriptive label
4. Copy the token and add it to your `.env` file

---

## Usage Examples

### Natural Language Commands

```
# Issue Management
"show me open bugs"
"create a bug 'Login fails on mobile' with priority High"
"assign PROJ-123 to johndoe"
"move PROJ-123 to In Progress"

# Comments & Collaboration
"add comment 'Working on this' to PROJ-123"
"add johndoe and janedoe as watchers to PROJ-123"

# Agile Workflow
"show active sprints on board 1"
"add PROJ-123 to sprint 10"

# Search & Query
"search for high priority bugs assigned to me"
"jql search: project = PROJ AND status = Open"

# Time Tracking
"log 2h on PROJ-123 for debugging"
"show work logs for PROJ-123"

# Versions & Releases
"create version v2.0 with release date 2025-03-31"
"set fix version v2.0 for PROJ-123"
```

### Programmatic Usage

```python
from agents import SuperAgent

agent = SuperAgent()

# Fetch bugs
result = agent.route("fetch_bugs", tracker="jira", max_results=10)

# Create issue
result = agent.route("create_issue", 
    tracker="jira",
    summary="Login fails on mobile",
    issue_type="Bug",
    priority="High",
    assignee="johndoe"
)

# JQL search
result = agent.route("jql_search",
    tracker="jira",
    jql="project = PROJ AND status = Open AND assignee = currentUser()"
)

# Add work log
result = agent.route("add_worklog",
    tracker="jira",
    bug_id="PROJ-123",
    time_spent="2h 30m",
    comment="Fixed authentication issue"
)
```

---

## Capability Summary

| Category | Actions | Description |
|----------|---------|-------------|
| Issue Management | 12 | Create, edit, delete, assign, comment, transition |
| Labels | 2 | Add/remove labels |
| Watchers | 3 | Add/remove/get watchers |
| Issue Links | 3 | Link issues, get links, get link types |
| Attachments | 3 | Add/get/delete attachments |
| Components | 4 | List, create, add/remove from issues |
| Versions | 5 | List, create, release, set fix/affects |
| Sprints & Agile | 4 | Boards, sprints, add issues |
| Users | 2 | Search, get assignable |
| Projects | 2 | List projects, get details |
| Search | 2 | Basic search, JQL search |
| Meta | 3 | Issue types, priorities, statuses |
| Work Logs | 2 | Add/get work logs |
| Subtasks | 2 | Create/get subtasks |
| **Total** | **50** | |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 2025 | Initial release with 5 capabilities |
| 2.0 | Dec 2025 | Expanded to 50 capabilities (900% increase) |

---

## See Also

- [GitHub Capabilities](./GITHUB_CAPABILITIES.md) - GitHub integration documentation
- [Architecture](./ARCHITECTURE.md) - System architecture overview
- [Quick Reference](./QUICK_REFERENCE.md) - Command quick reference
