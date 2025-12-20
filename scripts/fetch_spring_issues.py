"""Fetch recent issues from Spring Framework repository."""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import Config
import requests

headers = {
    'Authorization': f'token {Config.GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

owner = "spring-projects"
repo = "spring-framework"

print(f"Fetching recent issues from {owner}/{repo}\n")
print("="*70)

# Fetch all open issues (not just bugs)
url = f"https://api.github.com/repos/{owner}/{repo}/issues"
params = {
    'state': 'open',
    'per_page': 10,
    'sort': 'created',
    'direction': 'desc'
}

response = requests.get(url, headers=headers, params=params)
response.raise_for_status()

issues = response.json()

print(f"\n✓ Found {len(issues)} recent open issues:\n")

for i, issue in enumerate(issues, 1):
    # Skip pull requests
    if 'pull_request' in issue:
        continue
    
    labels = [label['name'] for label in issue.get('labels', [])]
    
    print(f"{i}. Issue #{issue['number']}: {issue['title']}")
    print(f"   State: {issue['state']}")
    print(f"   Labels: {', '.join(labels) if labels else 'None'}")
    print(f"   Created: {issue['created_at']}")
    print(f"   Author: {issue['user']['login']}")
    print(f"   URL: {issue['html_url']}")
    print()

# Now fetch issues with specific labels (type: bug, in: regression, etc.)
print("\n" + "="*70)
print("Searching for bug-related issues...\n")

params = {
    'state': 'open',
    'labels': 'type: bug',
    'per_page': 5,
    'sort': 'created',
    'direction': 'desc'
}

response = requests.get(url, headers=headers, params=params)
if response.status_code == 200:
    bugs = response.json()
    print(f"✓ Found {len(bugs)} issues with 'type: bug' label:\n")
    
    for i, bug in enumerate(bugs, 1):
        labels = [label['name'] for label in bug.get('labels', [])]
        print(f"{i}. Issue #{bug['number']}: {bug['title']}")
        print(f"   Labels: {', '.join(labels)}")
        print(f"   Created: {bug['created_at']}")
        print(f"   URL: {bug['html_url']}")
        print()
else:
    print(f"No issues found with 'type: bug' label")

# Try other common bug labels
print("\n" + "="*70)
print("Checking available labels...\n")

url = f"https://api.github.com/repos/{owner}/{repo}/labels"
response = requests.get(url, headers=headers, params={'per_page': 100})
if response.status_code == 200:
    labels = response.json()
    bug_labels = [l['name'] for l in labels if 'bug' in l['name'].lower() or 'defect' in l['name'].lower() or 'regression' in l['name'].lower()]
    print(f"Bug-related labels in repository:")
    for label in bug_labels[:10]:
        print(f"  - {label}")
