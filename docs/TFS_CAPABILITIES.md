# TFS/Azure DevOps Capabilities

This document describes all TFS (Team Foundation Server) and Azure DevOps capabilities available in the Sustenance application.

## Overview

The TFS integration provides **36 capabilities** for interacting with TFS/Azure DevOps work items, comments, attachments, iterations, areas, teams, queries, and more.

## Configuration

TFS connection is configured via environment variables in `.env`:

```env
TFS_URL=https://your-tfs-server.com/collection
TFS_PROJECT=YourProject
TFS_PAT=your-personal-access-token
```

## Capabilities Reference

### Work Item Management (8 capabilities)

| Capability | Description | Parameters |
|------------|-------------|------------|
| `fetch_bugs` | Fetch bugs from TFS project | `project`, `state`, `max_results` |
| `get_bug_details` | Get detailed information about a specific work item | `bug_id` (required) |
| `create_work_item` | Create a new work item | `title` (required), `work_item_type`, `description`, `assigned_to`, `area_path`, `iteration_path`, `tags`, `priority`, `project` |
| `edit_work_item` | Update an existing work item | `bug_id` (required), `title`, `description`, `assigned_to`, `state`, `area_path`, `iteration_path`, `tags`, `priority` |
| `delete_work_item` | Delete a work item | `bug_id` (required), `permanent` (false=recycle bin) |
| `assign_work_item` | Assign a work item to a user | `bug_id` (required), `assignee` (required) |
| `update_state` | Change the state of a work item | `bug_id` (required), `new_state` (required) |
| `search_work_items` | Search for work items | `search_text`, `work_item_types`, `states`, `assigned_to`, `project`, `max_results` |

### Comments (4 capabilities)

| Capability | Description | Parameters |
|------------|-------------|------------|
| `add_comment` | Add a comment to a work item | `bug_id` (required), `comment` (required) |
| `get_comments` | Get all comments on a work item | `bug_id` (required) |
| `edit_comment` | Update an existing comment | `bug_id` (required), `comment_id` (required), `text` (required) |
| `delete_comment` | Delete a comment | `bug_id` (required), `comment_id` (required) |

### Tags (2 capabilities)

| Capability | Description | Parameters |
|------------|-------------|------------|
| `add_tags` | Add tags to a work item | `bug_id` (required), `tags` (required, list) |
| `remove_tags` | Remove tags from a work item | `bug_id` (required), `tags` (required, list) |

### Attachments (3 capabilities)

| Capability | Description | Parameters |
|------------|-------------|------------|
| `get_attachments` | Get all attachments on a work item | `bug_id` (required) |
| `add_attachment` | Add an attachment to a work item | `bug_id` (required), `file_path` (required) |
| `delete_attachment` | Remove an attachment | `bug_id` (required), `attachment_url` (required) |

### Work Item Links (3 capabilities)

| Capability | Description | Parameters |
|------------|-------------|------------|
| `get_work_item_links` | Get all links for a work item | `bug_id` (required) |
| `link_work_items` | Create a link between two work items | `source_id` (required), `target_id` (required), `link_type` |
| `get_link_types` | Get available link types | None |

**Common Link Types:**
- `System.LinkTypes.Related` - Related work items
- `System.LinkTypes.Hierarchy-Forward` - Parent/Child (child)
- `System.LinkTypes.Hierarchy-Reverse` - Parent/Child (parent)
- `System.LinkTypes.Dependency-Forward` - Successor
- `System.LinkTypes.Dependency-Reverse` - Predecessor

### Iterations/Sprints (3 capabilities)

| Capability | Description | Parameters |
|------------|-------------|------------|
| `get_iterations` | Get project iterations/sprints | `project`, `depth` |
| `set_iteration` | Set iteration path for a work item | `bug_id` (required), `iteration_path` (required) |
| `get_sprint_work_items` | Get work items in a sprint | `iteration_path`, `project`, `max_results` |

### Areas (2 capabilities)

| Capability | Description | Parameters |
|------------|-------------|------------|
| `get_areas` | Get project area paths | `project`, `depth` |
| `set_area` | Set area path for a work item | `bug_id` (required), `area_path` (required) |

### Teams (2 capabilities)

| Capability | Description | Parameters |
|------------|-------------|------------|
| `get_teams` | Get teams in the project | `project` |
| `get_team_members` | Get members of a team | `team_id` (required), `project` |

### Queries (3 capabilities)

| Capability | Description | Parameters |
|------------|-------------|------------|
| `get_queries` | Get saved queries | `project`, `folder` |
| `run_query` | Execute a saved query | `query_id` (required), `project` |
| `run_wiql` | Execute a WIQL query | `wiql` (required), `project`, `max_results` |

**WIQL Example:**
```sql
SELECT [System.Id], [System.Title], [System.State]
FROM WorkItems
WHERE [System.WorkItemType] = 'Bug'
AND [System.State] = 'Active'
ORDER BY [System.CreatedDate] DESC
```

### Projects (2 capabilities)

| Capability | Description | Parameters |
|------------|-------------|------------|
| `get_projects` | Get all projects in the collection | None |
| `get_project` | Get details of a specific project | `project` |

### Work Item Types & States (2 capabilities)

| Capability | Description | Parameters |
|------------|-------------|------------|
| `get_work_item_types` | Get available work item types | `project` |
| `get_work_item_states` | Get states for a work item type | `work_item_type`, `project` |

**Common Work Item Types:**
- Bug
- Task
- User Story
- Epic
- Feature
- Test Case

### History (2 capabilities)

| Capability | Description | Parameters |
|------------|-------------|------------|
| `get_work_item_history` | Get revision history of a work item | `bug_id` (required) |
| `get_work_item_updates` | Get detailed field updates | `bug_id` (required) |

## Usage Examples

### Creating a Bug

```
Create a bug titled "Login page crashes on IE11" assigned to john@company.com with priority 2
```

### Searching Work Items

```
Search for all active bugs assigned to me in the current sprint
```

### Managing Iterations

```
Get all iterations for the project and move bug 12345 to Sprint 5
```

### Running WIQL Queries

```
Run WIQL: SELECT * FROM WorkItems WHERE [System.WorkItemType] = 'Task' AND [System.State] = 'In Progress'
```

### Linking Work Items

```
Link bug 123 to user story 456 as a child
```

## Response Format

All capabilities return a standardized response:

```json
{
  "success": true,
  "data": { ... },
  "count": 10,
  "message": "Operation completed successfully"
}
```

Error responses:

```json
{
  "success": false,
  "error": "Error description"
}
```

## Work Item Data Structure

Work items are returned with the following fields:

| Field | Description |
|-------|-------------|
| `id` | Work item ID |
| `title` | Title/summary |
| `description` | Full description (HTML) |
| `type` | Work item type (Bug, Task, etc.) |
| `state` | Current state |
| `priority` | Priority level |
| `severity` | Severity level |
| `assigned_to` | Assignee |
| `created_by` | Creator |
| `created` | Creation date |
| `updated` | Last modified date |
| `tags` | List of tags |
| `area_path` | Area path |
| `iteration_path` | Iteration/sprint path |

## API Version

This integration uses TFS/Azure DevOps REST API version **5.0**, compatible with:
- TFS 2018 and later
- Azure DevOps Server 2019 and later
- Azure DevOps Services (cloud)

## Comparison with Other Trackers

| Feature | TFS | Jira | GitHub |
|---------|-----|------|--------|
| Work Items/Issues | ✅ 36 capabilities | ✅ 50 capabilities | ✅ 47 capabilities |
| Comments | ✅ | ✅ | ✅ |
| Attachments | ✅ | ✅ | ✅ |
| Labels/Tags | ✅ | ✅ | ✅ |
| Sprints/Iterations | ✅ | ✅ | ✅ (Milestones) |
| Custom Queries | ✅ WIQL | ✅ JQL | ✅ Search API |
| Work Item Links | ✅ | ✅ | ✅ |
| Teams | ✅ | ✅ | ✅ |

## Troubleshooting

### Connection Issues

1. **401 Unauthorized**: Check PAT token is valid and not expired
2. **404 Not Found**: Verify project name (case-sensitive)
3. **400 Bad Request**: Check WIQL syntax or field names

### Common Field Issues

- `[System.Priority]` may not exist in all projects
- `[System.Severity]` is typically only on Bug type
- Field names are case-sensitive in WIQL

### Project Name Case Sensitivity

TFS project names are **case-sensitive**. Use exact casing:
- ✅ `Aiforce-EN`
- ❌ `AIForce-EN`
- ❌ `aiforce-en`
