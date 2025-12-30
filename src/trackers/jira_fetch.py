from typing import Any, Dict, List, Optional, Tuple
import requests


def fetch_jira_issues(
    base_url: str,
    email: str,
    api_token: str,
    jql: str,
    max_results: int = 50,
    fields: Optional[List[str]] = None,
    verify: bool = True,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Fetch issues from Jira using the REST API via JQL.

    Args:
        base_url: Jira base URL, e.g., "https://your-domain.atlassian.net".
        email: Jira account email (for Basic auth) for Cloud.
        api_token: Jira API token (for Basic auth).
        jql: JQL query string to filter issues.
        max_results: Maximum number of issues to retrieve (will paginate as needed).
        fields: Optional list of fields to include (e.g., ["summary", "status", "assignee", "labels"]).
        verify: Whether to verify SSL certificates.
        timeout: Request timeout in seconds.

    Returns:
        A dict with keys: success, data (list of issues), total, message, error.
    """
    endpoint = base_url.rstrip("/") + "/rest/api/3/search"

    auth = (email, api_token)
    collected: List[Dict[str, Any]] = []
    start_at = 0
    per_page = 100  # Jira allows up to 100 per request

    params_base: Dict[str, Any] = {"jql": jql}
    if fields:
        params_base["fields"] = ",".join(fields)

    try:
        total: Optional[int] = None
        while len(collected) < max_results:
            remaining = max_results - len(collected)
            params = dict(params_base)
            params.update({
                "startAt": start_at,
                "maxResults": min(per_page, remaining),
            })

            resp = requests.get(
                endpoint,
                params=params,
                auth=auth,
                verify=verify,
                timeout=timeout,
            )

            if resp.status_code == 429:
                return {
                    "success": False,
                    "data": [],
                    "total": 0,
                    "message": "Rate limit exceeded",
                    "error": "HTTP 429 Too Many Requests",
                }

            if resp.status_code != 200:
                return {
                    "success": False,
                    "data": [],
                    "total": 0,
                    "message": "Failed to fetch Jira issues",
                    "error": f"HTTP {resp.status_code}: {resp.text}",
                }

            payload = resp.json()
            issues = payload.get("issues", [])
            if total is None:
                total = payload.get("total", len(issues))

            for issue in issues:
                fields_obj = issue.get("fields", {})

                def _get(path: Tuple[str, ...]) -> Optional[Any]:
                    cur = fields_obj
                    for key in path:
                        if cur is None:
                            return None
                        cur = cur.get(key)
                    return cur

                collected.append({
                    "key": issue.get("key"),
                    "id": issue.get("id"),
                    "summary": fields_obj.get("summary"),
                    "status": _get(("status", "name")),
                    "assignee": _get(("assignee", "displayName")),
                    "assignee_account_id": _get(("assignee", "accountId")),
                    "reporter": _get(("reporter", "displayName")),
                    "priority": _get(("priority", "name")),
                    "issue_type": _get(("issuetype", "name")),
                    "labels": fields_obj.get("labels", []),
                    "created": fields_obj.get("created"),
                    "updated": fields_obj.get("updated"),
                    "resolutiondate": fields_obj.get("resolutiondate"),
                    "url": base_url.rstrip("/") + "/browse/" + str(issue.get("key")),
                })

            if not issues:
                break

            start_at += len(issues)

        return {
            "success": True,
            "data": collected,
            "total": total or len(collected),
            "message": f"Retrieved {len(collected)} issues",
            "error": "",
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "data": [],
            "total": 0,
            "message": "Network or request error",
            "error": str(e),
        }
