import requests

# =======================
# Configuration
# =======================
BASE_URL= "https://api.github.com"
GITHUB_OWNER="spring-projects"
GITHUB_REPO="spring-framework"
GITHUB_TOKEN="your-github-token-here"  # Set via environment variable

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


def get_github_issues(state="open", labels=None, max_results=10):
    """
    Fetch GitHub issues for the configured repository (excluding PRs).
    """
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

            url = f"{BASE_URL}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues"
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)

            # Handle rate limit
            if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                return {
                    "success": False,
                    "action": "get_issues",
                    "data": [],
                    "message": "",
                    "error": "GitHub API rate limit exceeded"
                }

            response.raise_for_status()
            issues_data = response.json()

            if not issues_data:
                break

            for issue in issues_data:
                # Skip pull requests
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
            "action": "get_issues",
            "data": all_issues,
            "message": f"Retrieved {len(all_issues)} issues",
            "error": ""
        }

    except Exception as e:
        return {
            "success": False,
            "action": "get_issues",
            "data": [],
            "message": "",
            "error": str(e)
        }


# =======================
# Execute
# =======================
if __name__ == "__main__":
    result = get_github_issues(max_results=5)

    if result["success"]:
        print(f"✓ {result['message']}\n")
        for issue in result["data"]:
            print(f"#{issue['number']}: {issue['title']}")
    else:
        print(f"✗ Error: {result['error']}")
