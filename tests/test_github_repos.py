"""Quick test to find GitHub repositories."""
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

print(f"Testing GitHub token for user: {Config.GITHUB_OWNER}")
print("\nFetching repositories...")

# List user's repositories
url = f"https://api.github.com/users/{Config.GITHUB_OWNER}/repos"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    repos = response.json()
    print(f"\n✓ Found {len(repos)} repositories:\n")
    for repo in repos[:10]:
        print(f"  - {repo['name']} ({'private' if repo['private'] else 'public'})")
        print(f"    {repo['html_url']}")
    
    if repos:
        print(f"\n\nUpdate your .env file with one of these repos:")
        print(f"GITHUB_REPO={repos[0]['name']}")
else:
    print(f"✗ Failed: {response.status_code} - {response.text}")

# Try to get authenticated user info
print("\n" + "="*60)
print("Authenticated user info:")
url = "https://api.github.com/user"
response = requests.get(url, headers=headers)
if response.status_code == 200:
    user = response.json()
    print(f"Username: {user['login']}")
    print(f"Name: {user.get('name', 'N/A')}")
    print(f"Public repos: {user['public_repos']}")
else:
    print(f"✗ Failed: {response.status_code}")
