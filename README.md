# Bug Triage & Analysis System

An intelligent agentic workflow system for automated bug triaging that integrates with Jira and uses Claude AI for code analysis.

## Features

- **Jira Integration**: Pull bugs directly from Jira using Model Context Protocol (MCP)
- **AI-Powered Analysis**: Leverage Claude SDK to analyze repository code and identify bug locations
- **Automated Reports**: Generate comprehensive reports with file names, line numbers, issues, and resolutions
- **Flexible Configuration**: Easy setup with environment variables
- **Multiple Output Formats**: JSON and Markdown report formats

## Architecture

### Components

1. **Jira MCP Server** (`jira_mcp.py`)
   - Connects to Jira API
   - Retrieves bugs with filtering options
   - Provides structured bug data

2. **Code Analysis Agent** (`code_analyzer.py`)
   - Scans repository for code files
   - Uses Claude AI to analyze code
   - Maps bugs to specific code locations
   - Identifies issues and suggests fixes

3. **Report Generator** (`report_generator.py`)
   - Creates consolidated reports
   - Generates JSON and Markdown formats
   - Provides severity breakdowns and summaries

4. **Orchestrator** (`main.py`)
   - Coordinates the entire workflow
   - Manages the bug triaging process
   - Handles batch processing and single bug analysis

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Jira Configuration
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=PROJ

# Claude API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key

# Repository Path
REPO_PATH=./code_files

# Report Configuration
REPORT_OUTPUT_PATH=./reports
```

### 3. Get API Credentials

#### Jira API Token
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create a new API token
3. Copy the token to your `.env` file

#### Anthropic API Key
1. Sign up at https://console.anthropic.com/
2. Generate an API key
3. Copy the key to your `.env` file

## Usage

### Run Full Workflow

Analyze multiple bugs from Jira:

```python
from main import BugTriageOrchestrator

orchestrator = BugTriageOrchestrator()

# Analyze bugs with specific status
orchestrator.run(
    status_filter=['Open', 'In Progress', 'To Do'],
    max_bugs=10,
    file_extensions=['.py', '.java', '.js']
)
```

### Analyze Single Bug

Analyze a specific bug by its key:

```python
orchestrator = BugTriageOrchestrator()
orchestrator.analyze_single_bug('PROJ-123')
```

### Command Line

Run the default workflow:

```bash
python main.py
```

Customize in `main.py`:

```python
def main():
    orchestrator = BugTriageOrchestrator()
    
    # Option 1: Full workflow
    orchestrator.run(
        status_filter=['Open'],
        max_bugs=5,
        file_extensions=['.py']
    )
    
    # Option 2: Single bug
    # orchestrator.analyze_single_bug('PROJ-123')
```

## Report Output

Reports are saved in the `reports/` directory with timestamps.

### JSON Report Structure

```json
{
  "generated_at": "2025-12-12T10:30:00",
  "total_bugs_analyzed": 5,
  "summary": {
    "bugs_with_findings": 3,
    "total_files_analyzed": 25,
    "total_issues_found": 8,
    "severity_breakdown": {
      "Critical": 2,
      "High": 3,
      "Medium": 3
    }
  },
  "detailed_results": [...]
}
```

### Markdown Report

Includes:
- Summary statistics
- Severity breakdown
- Detailed findings for each bug
- File paths and line numbers
- Issue descriptions
- Suggested resolutions
- Code fixes

## Workflow

1. **Repository Scan**: Scans configured repository for code files
2. **Bug Retrieval**: Fetches bugs from Jira based on filters
3. **AI Analysis**: For each bug:
   - Sends bug description + code files to Claude
   - Identifies relevant files and line numbers
   - Determines root causes
   - Suggests fixes
4. **Report Generation**: Creates consolidated reports in JSON and Markdown

## Configuration Options

### File Extensions

Specify which file types to analyze:

```python
file_extensions=['.py', '.java', '.js', '.ts', '.go']
```

### Status Filters

Filter bugs by Jira status:

```python
status_filter=['Open', 'In Progress', 'To Do', 'Reopened']
```

### Max Bugs

Limit the number of bugs to analyze:

```python
max_bugs=10
```

## Project Structure

```
sustenance/
├── main.py                 # Main orchestrator
├── jira_mcp.py            # Jira MCP server
├── code_analyzer.py       # Claude-powered code analysis
├── report_generator.py    # Report generation
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── .env                  # Your credentials (gitignored)
├── code_files/           # Your code repository
├── reports/              # Generated reports
└── README.md             # This file
```

## Advanced Usage

### Custom Analysis Parameters

```python
orchestrator = BugTriageOrchestrator()

# Customize analysis
analysis_result = orchestrator.code_analyzer.analyze_bug(
    bug_description="Bug description",
    bug_key="PROJ-123",
    code_files=code_files,
    max_files_per_analysis=5  # Analyze fewer files per batch
)
```

### Add Comments to Jira

```python
jira_mcp = JiraMCPServer()
jira_mcp.add_comment(
    'PROJ-123',
    'Analysis complete. See attached report.'
)
```

### Update Issue Status

```python
jira_mcp.update_issue_status('PROJ-123', 'In Progress')
```

## Best Practices

1. **Start Small**: Begin with a small number of bugs to test the workflow
2. **Review Reports**: Always review AI-generated suggestions before applying fixes
3. **Iterative Analysis**: Analyze bugs in batches for better performance
4. **Filter Wisely**: Use status filters to focus on actionable bugs
5. **Monitor API Usage**: Claude API has rate limits and token costs

## Troubleshooting

### Connection Errors
- Verify Jira URL and credentials
- Check network connectivity
- Ensure API token has proper permissions

### No Code Files Found
- Verify `REPO_PATH` in `.env`
- Check file extensions configuration
- Ensure code files exist in the specified path

### API Rate Limits
- Reduce `max_bugs` parameter
- Reduce `max_files_per_analysis` parameter
- Add delays between requests if needed

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
