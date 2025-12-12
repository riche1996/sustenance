# Quick Reference Guide

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env
# Edit .env with your Jira and Anthropic credentials

# 3. Verify setup
python setup_check.py

# 4. Run analysis
python main.py
```

## 📝 Common Commands

### Run Default Workflow
```bash
python main.py
```

### Run Examples
```bash
python examples.py
```

### Test Components
```bash
python test_components.py
```

### Check Setup
```bash
python setup_check.py
```

## 🔧 Configuration (.env)

```env
# Required
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_api_token
JIRA_PROJECT_KEY=PROJ
ANTHROPIC_API_KEY=your_anthropic_key

# Optional
REPO_PATH=./code_files
REPORT_OUTPUT_PATH=./reports
CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

## 💻 Python API Examples

### Basic Usage
```python
from main import BugTriageOrchestrator

orchestrator = BugTriageOrchestrator()
orchestrator.run(max_bugs=5)
```

### Custom Filters
```python
orchestrator.run(
    status_filter=['Open', 'In Progress'],
    max_bugs=10,
    file_extensions=['.py', '.java']
)
```

### Single Bug Analysis
```python
orchestrator.analyze_single_bug('PROJ-123')
```

### Fetch Bugs Only
```python
from jira_mcp import JiraMCPServer

jira = JiraMCPServer()
bugs = jira.get_bugs(
    project_key='PROJ',
    status=['Open'],
    max_results=10
)

for bug in bugs:
    print(f"{bug.key}: {bug.summary}")
```

### Analyze Code Only
```python
from code_analyzer import CodeAnalysisAgent

analyzer = CodeAnalysisAgent()
code_files = analyzer.scan_repository(extensions=['.py'])

result = analyzer.analyze_bug(
    bug_description="Null pointer exception in login",
    bug_key="PROJ-123",
    code_files=code_files
)
```

### Generate Report Only
```python
from report_generator import ReportGenerator

generator = ReportGenerator()
report_files = generator.generate_consolidated_report(
    analysis_results=[...],
    format='both'
)
```

## 🎯 Jira MCP API

### Initialize
```python
from jira_mcp import JiraMCPServer
jira = JiraMCPServer()
```

### Get Bugs
```python
bugs = jira.get_bugs(
    project_key='PROJ',           # Optional, uses config default
    status=['Open', 'To Do'],     # Optional, filter by status
    max_results=50                # Optional, default 50
)
```

### Get Single Issue
```python
bug = jira.get_issue('PROJ-123')
print(bug.summary)
print(bug.description)
print(bug.status)
```

### Add Comment
```python
jira.add_comment('PROJ-123', 'Analysis complete. See report.')
```

### Update Status
```python
jira.update_issue_status('PROJ-123', 'In Progress')
```

## 🤖 Code Analyzer API

### Initialize
```python
from code_analyzer import CodeAnalysisAgent
analyzer = CodeAnalysisAgent()
```

### Scan Repository
```python
code_files = analyzer.scan_repository(
    extensions=['.py', '.java', '.js']  # Optional
)
```

### Analyze Bug
```python
result = analyzer.analyze_bug(
    bug_description="Bug description here",
    bug_key="PROJ-123",
    code_files=code_files,
    max_files_per_analysis=10  # Optional
)
```

### Access Results
```python
print(f"Status: {result['status']}")
print(f"Files analyzed: {result['total_files_analyzed']}")

for finding in result['findings']:
    print(f"File: {finding['file']}")
    print(f"Lines: {finding['lines']}")
    print(f"Issue: {finding['issue']}")
    print(f"Severity: {finding['severity']}")
    print(f"Resolution: {finding['resolution']}")
```

## 📊 Report Generator API

### Initialize
```python
from report_generator import ReportGenerator
generator = ReportGenerator()
```

### Consolidated Report
```python
report_files = generator.generate_consolidated_report(
    analysis_results=results_list,
    format='both'  # 'json', 'markdown', or 'both'
)

print(report_files['json'])      # Path to JSON report
print(report_files['markdown'])  # Path to Markdown report
```

### Individual Report
```python
report_path = generator.generate_individual_report(
    bug_key='PROJ-123',
    analysis_result=result
)
```

## 🔍 Filtering Options

### Status Filters
```python
status_filter=[
    'Open',
    'In Progress',
    'To Do',
    'Reopened',
    'Backlog'
]
```

### File Extensions
```python
file_extensions=[
    '.py',      # Python
    '.java',    # Java
    '.js',      # JavaScript
    '.ts',      # TypeScript
    '.go',      # Go
    '.rs',      # Rust
    '.cpp',     # C++
    '.c',       # C
    '.h',       # Headers
]
```

## 📋 JQL Query Examples

The system builds JQL automatically, but you can customize in `jira_mcp.py`:

```python
# Basic
'project = "PROJ" AND type = Bug'

# With status
'project = "PROJ" AND type = Bug AND status IN ("Open", "In Progress")'

# With priority
'project = "PROJ" AND type = Bug AND priority IN ("High", "Highest")'

# With date
'project = "PROJ" AND type = Bug AND created >= -7d'

# Combined
'project = "PROJ" AND type = Bug AND status = "Open" AND priority = "High" ORDER BY created DESC'
```

## 🐛 Troubleshooting

### Jira Connection Issues
```python
# Test connection
from jira_mcp import JiraMCPServer
try:
    jira = JiraMCPServer()
    print("✓ Connected")
except Exception as e:
    print(f"✗ Failed: {e}")
```

### Claude API Issues
```python
# Test API
from anthropic import Anthropic
from config import Config

client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
response = client.messages.create(
    model=Config.CLAUDE_MODEL,
    max_tokens=50,
    messages=[{"role": "user", "content": "Test"}]
)
print(response.content[0].text)
```

### No Code Files Found
```python
# Check repository path
from config import Config
print(f"Looking in: {Config.REPO_PATH}")
print(f"Exists: {Config.REPO_PATH.exists()}")

# List files
for f in Config.REPO_PATH.rglob('*.py'):
    print(f)
```

## 📈 Performance Tips

### Reduce API Calls
```python
# Use fewer bugs
orchestrator.run(max_bugs=5)

# Use specific file types
orchestrator.run(file_extensions=['.py'])

# Reduce batch size
analyzer.analyze_bug(..., max_files_per_analysis=5)
```

### Parallel Processing (Advanced)
```python
from concurrent.futures import ThreadPoolExecutor

def analyze_one(bug):
    # Analysis code here
    pass

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(analyze_one, bugs))
```

## 📁 File Locations

```
Configuration:     .env
Dependencies:      requirements.txt
Main script:       main.py
Examples:          examples.py
Tests:             test_components.py, setup_check.py

Documentation:     README.md, PROJECT_OVERVIEW.md, ARCHITECTURE.md
Quick Reference:   QUICK_REFERENCE.md (this file)

Code to analyze:   code_files/
Generated reports: reports/
```

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| JIRA_URL | Yes | - | Jira instance URL |
| JIRA_EMAIL | Yes | - | Your Jira email |
| JIRA_API_TOKEN | Yes | - | Jira API token |
| JIRA_PROJECT_KEY | Yes | - | Project key (e.g., PROJ) |
| ANTHROPIC_API_KEY | Yes | - | Claude API key |
| CLAUDE_MODEL | No | claude-3-5-sonnet-20241022 | Claude model |
| REPO_PATH | No | ./code_files | Repository path |
| REPORT_OUTPUT_PATH | No | ./reports | Report output path |

## 📞 API Reference Quick Links

- **Jira REST API**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- **Claude API**: https://docs.anthropic.com/
- **Jira Python Library**: https://jira.readthedocs.io/
- **Anthropic Python SDK**: https://github.com/anthropics/anthropic-sdk-python

## 🎓 Learning Path

1. **Beginner**: Run `setup_check.py` and `examples.py`
2. **Intermediate**: Customize `main.py` with your filters
3. **Advanced**: Modify `code_analyzer.py` analysis logic
4. **Expert**: Extend with custom MCP tools

## 💡 Common Patterns

### Pattern 1: Daily Bug Review
```python
# Run every morning to review new bugs
orchestrator.run(
    status_filter=['Open'],
    max_bugs=20
)
```

### Pattern 2: Sprint Planning
```python
# Analyze sprint backlog
orchestrator.run(
    status_filter=['To Do', 'Backlog'],
    max_bugs=50
)
```

### Pattern 3: Critical Bug Triage
```python
# Focus on high-priority bugs
bugs = jira.get_bugs(status=['Open'], max_results=100)
critical = [b for b in bugs if b.priority in ['Highest', 'High']]
# Analyze critical bugs...
```

### Pattern 4: Component-Specific Analysis
```python
# Analyze bugs for specific component
bugs = jira.get_bugs()
auth_bugs = [b for b in bugs if 'Authentication' in b.components]
# Analyze auth bugs...
```

## 🎨 Customization Examples

### Custom Analysis Prompt
Edit `code_analyzer.py`, method `_analyze_batch`:
```python
prompt = f"""Your custom prompt here...
Bug: {bug_description}
Code: {files_content}
"""
```

### Custom Report Format
Edit `report_generator.py`, method `_generate_markdown_report`:
```python
# Add custom sections
lines.append("## Custom Section\n")
lines.append(f"Custom data: {custom_data}\n")
```

### Custom Jira Query
Edit `jira_mcp.py`, method `get_bugs`:
```python
# Add custom JQL
jql_parts.append('labels = "urgent"')
jql_parts.append('component = "Backend"')
```

## ⚡ Keyboard Shortcuts (None - CLI tool)

Use with VS Code or other IDE shortcuts for:
- Running scripts: Ctrl+Shift+P → "Run Python File"
- Terminal: Ctrl+` to open terminal
- Search: Ctrl+F in files

---

**Quick Reference Version**: 1.0
**Last Updated**: December 12, 2025
