import os
import json
from typing import List

from src.trackers.jira_fetch import fetch_jira_issues


def main() -> None:
    base_url = os.environ.get("JIRA_BASE_URL", "")
    email = os.environ.get("JIRA_EMAIL", "")
    api_token = os.environ.get("JIRA_API_TOKEN", "")
    jql = os.environ.get("JIRA_JQL", "project = TEST ORDER BY created DESC")
    max_results = int(os.environ.get("JIRA_MAX_RESULTS", "20"))
    fields_env = os.environ.get("JIRA_FIELDS", "summary,status,assignee,labels,issuetype,priority,created,updated,resolutiondate")
    fields: List[str] = [f.strip() for f in fields_env.split(",") if f.strip()]

    if not base_url or not email or not api_token:
        print("Missing required env vars: JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN")
        return

    result = fetch_jira_issues(
        base_url=base_url,
        email=email,
        api_token=api_token,
        jql=jql,
        max_results=max_results,
        fields=fields,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
