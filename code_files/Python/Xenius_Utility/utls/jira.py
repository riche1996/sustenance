
from typing import List

import requests
from requests.auth import HTTPBasicAuth
from jira import JIRA

from utility.logging import logging_utils as log_utils

from .base import BugItem, DataConnector, ProjectFile, Sprints, StoryItem, TestCase


class JiraConnector(DataConnector):
    """
    Jira data connector class.
    """

    def __init__(self, url: str, username: str, password: str, project, *args, **kwargs):
        """
        Constructor for the JiraDataConnector class.

        Args:
            url: The URL of the Jira instance.
            username: The username to authenticate with.
            password: The password to authenticate with.
        """
        _unused_args = [args, kwargs]  # review needed
        super().__init__()
        self.url = url+"/rest/api/3/search/jql"
        self.username = username
        self.password = password
        self.project = project

    def test_connection(self) -> bool:
        """
        Checks validity of configuration/connection.
        """
        try:
            self.client = JIRA(self.url, basic_auth=(self.username, self.password), max_retries=1)
            return True
        except:  # pylint: disable=bare-except
            return False

    def get_code_files(self, directory: str = "/") -> List[ProjectFile]:
        """
        Fetches code files from the data source.

        Returns:
            A list of code file objects.
        """

    def get_bugs(
        self,
        bug_ids: List[int | str] = None,
        area_path: List[str] = None,
        iteration_path: List[str] = None,
    ) -> List[BugItem]:
        """
        Fetches Bugs from the data source.

        Returns:
            A list of Bugs objects.
        """

        _unused_args = [iteration_path]  # review needed
        options = {"server": self.url, "verify": False}
        if not self.client:
            self.client = "{self.url}/rest/api/3/search/jql"

            # self.client = JIRA(options, basic_auth=(self.username, self.password))
        if area_path:
            jql_query = (
                        f"project = {self.project} AND issuetype = Bug AND status in"
                        f'({", ".join(f"{path}" for path in area_path)})'
                    )
        else:
            jql_query = f'project = {self.project} AND issuetype = Bug ORDER BY created DESC'

        # REST API request
        response = requests.post(
            self.url,
            auth=HTTPBasicAuth(self.username, self.password),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json={
                "jql": jql_query,
                "maxResults": 100,
                "fields": ["*all"]   # ✅ Request all fields explicitly
            }
        )
        if response.status_code == 200:
            data = response.json()
            issues = data.get("issues", [])
        bugs = []
        for issue in issues:
            fields = issue.get("fields", {})
            bug = BugItem(id= issue.get("key"),
                        type= "Bug",
                        title= fields.get("summary", ""),
                        description=fields.get("description", ""),
                        created_by=fields.get("creator", {}).get("displayName", ""),
                        created_date= fields.get("created", ""),
                        change_date= fields.get("updated", ""),
                        release= fields.get("fixVersions", [{}])[0].get("name", "") if fields.get("fixVersions") else "",
                        assigned_to= fields.get("assignee", {}).get("displayName", "") if fields.get("assignee") else "",
                        state= fields.get("status", {}).get("name", ""),
                        priority= fields.get("priority", {}).get("name", ""),
                        severity= fields.get("customfield_10009") or "2_Medium",
                        resolution= fields.get("resolution", {}).get("name", "") if fields.get("resolution") else "",
                        resolved_by= fields.get("resolution", {}).get("name", "") if fields.get("resolution") else "",
                        meta= fields,)
            bugs.append(bug)
        return bugs

    def get_testcases(
        self,
        testcase_ids: List[int | str] = None,
        area_path: List[str] = None,
        iteration_path: List[str] = None,
    ) -> List[TestCase]:
        """
        Fetches Testcases from the data source.

        Returns:
            A list of Testcases objects.
        """
        _unused_args = [iteration_path]  # review needed
        # options = {"server": self.url, "verify": False}
        # if not self.client:
        #     self.client = JIRA(options, basic_auth=(self.username, self.password))
        if area_path:
            jql = (
                f"project = {self.project} AND issuetype = Test AND status in"
                f'({", ".join(f"{path}" for path in area_path)})'
            )
            # issues = self.client.search_issues(jql)
        else:
            jql = f'project = {self.project} AND issuetype = "Test Case"'
            # issues = self.client.search_issues(jql)
        # REST API request
        response = requests.post(
            self.url,
            auth=HTTPBasicAuth(self.username, self.password),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json={
                "jql": jql,
                "maxResults": 100,
                "fields": ["*all"]   # ✅ Request all fields explicitly
            }
        )
        if response.status_code == 200:
            data = response.json()
            issues = data.get("issues", [])
     
        testcases = []
        for issue in issues:
            fields = issue.get("fields", {})
            testcase = TestCase(
                id=issue.get("key"),
                type="Testcase",
                title=fields.get("summary", ""),
                description=fields.get("description", ""),
                created_by=fields.get("creator", {}).get("displayName", ""),
                created_date=fields.get("created", ""),
                change_date=fields.get("updated", ""),
                release=(fields.get("fixVersions", [{}])[0].get("name", "")
                        if fields.get("fixVersions") else ""),
                steps=fields.get("customfield_10010", ""),
                environment=fields.get("customfield_10011", ""),
                test_type=fields.get("customfield_10012", ""),
                priority=(fields.get("priority", {}).get("name", "")
                        if fields.get("priority") else ""),
                automated=fields.get("customfield_10013", ""),
                meta=fields
            )
            testcases.append(testcase)

        return testcases

    def push_testcases(self, testcases: List[TestCase]) -> List[int | str]:
        """
        Push Testcases to the data source.

        Returns:
            A list of Testcases Ids.
        """
        if not self.client:
            self.client = JIRA(self.url, basic_auth=(self.username, self.password))

        issue_ids = []
        for testcase in testcases:
            issue_dict = {
                "project": {"key": "TEST"},
                "summary": testcase.title,
                "description": testcase.description,
                "issuetype": {"name": "Test"},
                "priority": {"name": testcase.priority},
                "customfield_10010": testcase.steps,
                "customfield_10011": testcase.environment,
                "customfield_10012": testcase.test_type,
                "customfield_10013": testcase.automated,
            }
            issue = self.client.create_issue(fields=issue_dict)
            issue_ids.append(issue.id)

        return issue_ids

    def get_userstory(
        self,
        userstory_ids: List[int | str] = None,
        area_path: List[str] = None,
        iteration_path: List[str] = None,
    ) -> List[StoryItem]:
        """
        Fetches Stories from the data source.

        Returns:
            A list of Story objects.
        """

        _unused_args = [userstory_ids, iteration_path]  # review needed
        options = {"server": self.url, "verify": False}
        # if not self.client:

        #     self.client = JIRA(options, basic_auth=(self.username, self.password))
        if area_path:
            jql = (
                f"project = {self.project} AND issuetype = Story AND status in"
                f'({", ".join(f"{path}" for path in area_path)})'
            )
            # issues = self.client.search_issues(jql)
        else:
            jql = f"project = {self.project} AND issuetype = Story"
            # issues = self.client.search_issues(f"project = {self.project} AND issuetype = Story")
        
        
        max_results = 50
        total_limit = 250
        total_issues = []
        next_page_token = None

        while True:
            payload = {
                "jql": jql,
                "maxResults": 100,
                "fields": ["*all"]
            }

            # Add token for subsequent pages
            if next_page_token:
                payload["nextPageToken"] = next_page_token

            response = requests.post(
                self.url,
                auth=HTTPBasicAuth(self.username, self.password),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                json=payload
                )
            data = response.json()
            issues = data.get("issues", [])
            total_issues.extend(issues)

            # Stop if limit reached
            if len(total_issues) >= total_limit:
                total_issues = total_issues[:total_limit]
                break

            # Get next page token
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                # No more pages
                break

            
        stories = []
        for issue in total_issues:
            fields = issue.get("fields", {})
            story = StoryItem(
                id=issue.get("key", ""),
                type="Story",
                title=fields.get("summary", ""),
                description=extract_adf_text(fields.get("description", "")),
                created_by=fields.get("creator", {}).get("displayName", ""),
                created_date=fields.get("created", ""),
                change_date=fields.get("updated", ""),
                components=[c.get("name") for c in fields.get("components", [])],
                labels=fields.get("labels", []),
                priority=fields.get("priority", {}).get("name", ""),
                status=fields.get("status", {}).get("name", ""),
                environment=fields.get("customfield_10011", ""),
                test_type=fields.get("customfield_10012", ""),
                automated=fields.get("customfield_10013", ""),
                assignee = (fields.get("assignee") or {}).get("displayName", ""),
                release=fields.get("fixVersions", [{}])[0].get("name", "") if fields.get("fixVersions") else "",
                steps=fields.get("customfield_10010", ""),
                meta=fields,
            )
            stories.append(story)
        return stories

    def get_sprints(self) -> List[Sprints]:
        """
        Fetches sprints from the Jira API and returns a dictionary containing
        the unique status category names and an empty list for sprints.

        This method performs an HTTP GET request to the Jira API to fetch issues
        and extract the status category names. It returns a dictionary with the
        unique status names under the 'area' key and an empty list for sprints.

        Returns:
            dict: A dictionary containing:
                - "area": A list of unique status category names.
                - "sprints": An empty list (placeholder for future sprint data).

        Raises:
            requests.exceptions.RequestException: If the request to Jira API fails.
            ValueError: If the response cannot be parsed as JSON.
            Exception: Any other unforeseen exceptions during execution.

        """
        jira_url = self.url
        api_endpoint = "/rest/api/2/search"
        fields = "status"
        headers = {
            "Content-Type": "application/json",
        }
        params = {
            "fields": fields,
            "maxResults": 100,  # Adjust the number of results per page as needed
        }
        auth = (self.username, self.password)
        response = requests.get(
            f"{jira_url}{api_endpoint}", headers=headers, params=params, auth=auth, timeout=10
        )
        try:
            if response.status_code == 200:
                data = response.json()
                unique_status_category_names = set()
                for issue in data["issues"]:
                    status_category_name = issue["fields"]["status"]["name"]
                    unique_status_category_names.add(status_category_name)
                unique_status_category_names = list(unique_status_category_names)

                status = {"area": unique_status_category_names, "sprints": []}
                return status

            logger = log_utils.get_logger()
            logger.error(
                "Error fetching issues. Status code: %s", response.status_code, exc_info=True
            )

        except requests.exceptions.RequestException as e:
            logger = log_utils.get_logger()
            logger.error("Error fetching issues. Exception: %s", e, exc_info=True)
        except ValueError as e:
            logger = log_utils.get_logger()
            logger.error("Error parsing JSON response. Exception: %s", e, exc_info=True)
        except Exception as e:
            logger = log_utils.get_logger()
            logger.error(str(e), exc_info=True)
        return None

def extract_adf_text(adf):
    if not adf:
        return ""
    if isinstance(adf, str):
        return adf


    output = []


    def walker(node):
        if isinstance(node, dict):
            if node.get("text"):
                output.append(node["text"])
            for child in node.get("content", []):
                walker(child)
        elif isinstance(node, list):
            for item in node:
                walker(item)


    walker(adf)
    return "\n".join(output)