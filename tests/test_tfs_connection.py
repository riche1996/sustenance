"""Quick test for TFS connection debugging."""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import Config
import requests
from requests.auth import HTTPBasicAuth
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("TFS Configuration:")
print(f"URL: {Config.TFS_URL}")
print(f"Organization: {Config.TFS_ORGANIZATION}")
print(f"Project: {Config.TFS_PROJECT}")
print(f"PAT: {'*' * 10}{Config.TFS_PAT[-4:]}")

# Test basic connection
base_url = Config.TFS_URL.rstrip('/')
auth = HTTPBasicAuth('', Config.TFS_PAT)
headers = {'Content-Type': 'application/json'}

print(f"\nTesting connection...")
test_url = f"{base_url}/{Config.TFS_ORGANIZATION}/{Config.TFS_PROJECT}/_apis/projects/{Config.TFS_PROJECT}?api-version=5.0"
print(f"URL: {test_url}")

try:
    response = requests.get(test_url, auth=auth, headers=headers, verify=False, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    response.raise_for_status()
    print("✓ Connection successful!")
except Exception as e:
    print(f"✗ Connection failed: {e}")
