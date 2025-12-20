# Bug Triage & Analysis System - Project Overview

## 🎯 Project Summary

A Python-based agentic workflow system that automates bug triaging by:
1. Integrating with Jira via custom MCP (Model Context Protocol) server
2. Pulling bugs from Jira with flexible filtering
3. Analyzing repository code using Claude AI SDK
4. Generating detailed reports with file names, line numbers, issues, and resolutions

## 📁 Project Structure

```
sustenance/
│
├── 📄 main.py                      # Main orchestration workflow
├── 📄 jira_mcp.py                  # Jira MCP server implementation
├── 📄 code_analyzer.py             # Claude AI-powered code analysis
├── 📄 report_generator.py          # Report generation (JSON & Markdown)
├── 📄 config.py                    # Configuration management
├── 📄 examples.py                  # Usage examples and scenarios
├── 📄 setup_check.py               # Setup verification script
│
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env.example                 # Environment template
├── 📄 .env                         # Your credentials (create this)
├── 📄 .gitignore                   # Git ignore rules
├── 📄 README.md                    # Complete documentation
├── 📄 PROJECT_OVERVIEW.md          # This file
│
├── 📁 code_files/                  # Your code repository to analyze
│   ├── Python/
│   │   └── Xenius_Utility/
│   └── Java/
│       └── RegexGeneration/
│
├── 📁 reports/                     # Generated analysis reports
│   └── README.md
│
└── 📁 mcp_server/                  # Existing MCP server files
    ├── server.py
    └── tools/
```

## 🔧 Core Components

### 1. Jira MCP Server (`jira_mcp.py`)

**Purpose**: Acts as a Model Context Protocol server for Jira integration

**Key Features**:
- Connects to Jira using API token authentication
- Fetches bugs with JQL query support
- Filters by project, status, priority
- Retrieves issue metadata (assignee, reporter, labels, components)
- Can add comments and update issue status

**Main Classes**:
- `JiraIssue`: Pydantic model for issue data
- `JiraMCPServer`: MCP server implementation

**Key Methods**:
```python
get_bugs(project_key, status, max_results)  # Fetch multiple bugs
get_issue(issue_key)                        # Fetch single bug
add_comment(issue_key, comment)             # Add comment to issue
update_issue_status(issue_key, transition)  # Update bug status
```

### 2. Code Analysis Agent (`code_analyzer.py`)

**Purpose**: Uses Claude AI to analyze code and identify bug locations

**Key Features**:
- Scans repository for code files by extension
- Groups files by type for efficient analysis
- Sends code + bug description to Claude
- Parses AI responses into structured findings
- Identifies specific line numbers and issues

**Main Classes**:
- `CodeFile`: Represents a code file
- `CodeAnalysisAgent`: AI-powered analysis engine

**Key Methods**:
```python
scan_repository(extensions)                 # Scan for code files
analyze_bug(bug_description, code_files)    # Analyze bug with AI
_analyze_batch(bug_description, batch)      # Analyze file batch
_parse_analysis(analysis_text)              # Parse AI response
```

### 3. Report Generator (`report_generator.py`)

**Purpose**: Creates comprehensive analysis reports

**Key Features**:
- Generates JSON and Markdown formats
- Creates consolidated reports for multiple bugs
- Generates individual bug reports
- Includes summary statistics and severity breakdown
- Timestamps all reports

**Main Class**:
- `ReportGenerator`: Report creation and formatting

**Key Methods**:
```python
generate_consolidated_report(results, format)  # Multi-bug report
generate_individual_report(bug_key, result)    # Single bug report
_generate_summary(results)                     # Statistics summary
```

### 4. Main Orchestrator (`main.py`)

**Purpose**: Coordinates the entire workflow

**Key Features**:
- Validates configuration
- Manages workflow steps
- Handles error scenarios
- Provides progress updates
- Supports batch and single-bug processing

**Main Class**:
- `BugTriageOrchestrator`: Workflow coordinator

**Key Methods**:
```python
run(project_key, status_filter, max_bugs)  # Full workflow
analyze_single_bug(issue_key)              # Single bug analysis
```

### 5. Configuration (`config.py`)

**Purpose**: Centralized configuration management

**Key Features**:
- Loads environment variables from .env
- Validates required credentials
- Creates necessary directories
- Provides configuration defaults

**Main Class**:
- `Config`: Static configuration class

## 🔄 Workflow Process

### Full Workflow (`orchestrator.run()`)

```
1. Initialize Components
   ├── Validate configuration
   ├── Connect to Jira
   └── Initialize Claude client

2. Scan Repository
   ├── Search for code files by extension
   └── Load file contents

3. Fetch Bugs from Jira
   ├── Build JQL query with filters
   ├── Retrieve bug data
   └── Parse issue metadata

4. Analyze Each Bug
   ├── For each bug:
   │   ├── Prepare bug description
   │   ├── Group code files by type
   │   ├── Send to Claude AI in batches
   │   ├── Parse analysis results
   │   └── Collect findings
   
5. Generate Reports
   ├── Consolidate all results
   ├── Generate summary statistics
   ├── Create JSON report
   └── Create Markdown report

6. Output Results
   ├── Print summary
   └── Save report files
```

## 🚀 Quick Start Guide

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy template
cp .env.example .env

# Edit with your credentials
# - Jira URL, email, API token
# - Anthropic API key
# - Repository path
```

### Step 3: Verify Setup
```bash
python setup_check.py
```

### Step 4: Run Analysis
```bash
# Option 1: Run default workflow
python main.py

# Option 2: Run examples
python examples.py
```

## 📊 Report Output Example

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
  "detailed_results": [
    {
      "bug_key": "PROJ-123",
      "bug_summary": "Null pointer exception in user service",
      "status": "analyzed",
      "findings": [
        {
          "file": "src/services/user_service.py",
          "lines": "45-47",
          "issue": "Null check missing before accessing user object",
          "severity": "High",
          "resolution": "Add null check before user.email access",
          "code_fix": "if user is not None and user.email: ..."
        }
      ]
    }
  ]
}
```

### Markdown Report Sections
- Executive summary with statistics
- Severity breakdown
- Detailed findings per bug:
  - Bug metadata (key, summary, status, priority)
  - Description
  - Issues found with:
    - File paths
    - Line numbers
    - Severity levels
    - Problem descriptions
    - Resolution suggestions
    - Code fixes

## 🎨 Usage Examples

### Example 1: Analyze Open Bugs
```python
from main import BugTriageOrchestrator

orchestrator = BugTriageOrchestrator()
orchestrator.run(
    status_filter=['Open', 'To Do'],
    max_bugs=10,
    file_extensions=['.py', '.java']
)
```

### Example 2: Single Bug Analysis
```python
orchestrator.analyze_single_bug('PROJ-123')
```

### Example 3: Python Files Only
```python
orchestrator.run(
    max_bugs=5,
    file_extensions=['.py']
)
```

### Example 4: Update Jira After Analysis
```python
bugs = orchestrator.jira_mcp.get_bugs(status=['Open'], max_results=3)
code_files = orchestrator.code_analyzer.scan_repository()

for bug in bugs:
    result = orchestrator.code_analyzer.analyze_bug(
        bug_description=bug.description,
        bug_key=bug.key,
        code_files=code_files
    )
    
    # Add analysis as comment
    if result['findings']:
        orchestrator.jira_mcp.add_comment(
            bug.key,
            f"AI found {len(result['findings'])} potential issues"
        )
```

## 🔑 Key Features

### Agentic Workflow
- Autonomous bug processing
- Iterative analysis through bug list
- Self-contained analysis pipeline

### Jira Integration (MCP)
- Custom MCP server implementation
- JQL query support
- Bidirectional communication (read & write)
- Status tracking and updates

### AI-Powered Analysis
- Claude 3.5 Sonnet integration
- Context-aware code analysis
- Batch processing for efficiency
- Structured output parsing

### Comprehensive Reports
- Multiple output formats (JSON, Markdown)
- Detailed findings with line numbers
- Severity classification
- Code fix suggestions
- Summary statistics

## 🛠️ Customization Options

### Filters
- **Status**: Filter bugs by Jira status
- **Priority**: Focus on high-priority bugs
- **Labels**: Filter by labels/tags
- **Date**: Filter by creation/update date

### Analysis
- **File Extensions**: Choose which code types to analyze
- **Batch Size**: Control files per AI request
- **Max Bugs**: Limit number of bugs to process

### Output
- **Format**: JSON, Markdown, or both
- **Individual Reports**: Per-bug detailed reports
- **Custom Templates**: Modify report structure

## 🔐 Security Notes

- Store credentials in `.env` (never commit)
- `.env` is gitignored by default
- Use API tokens, not passwords
- Jira token should have minimal required permissions
- Monitor Claude API usage and costs

## 📈 Performance Considerations

### API Rate Limits
- Jira: Typically 100-300 requests per minute
- Claude: Based on tier (see Anthropic docs)

### Optimization Tips
- Start with small bug counts
- Use specific file extensions
- Reduce `max_files_per_analysis` if hitting token limits
- Cache repository scans for multiple runs
- Use status filters to reduce bug count

## 🐛 Troubleshooting

### Common Issues

**1. Jira Connection Failed**
- Verify Jira URL format (include https://)
- Check API token validity
- Ensure email is correct
- Verify network/firewall access

**2. No Code Files Found**
- Check REPO_PATH in .env
- Verify path exists and contains code
- Check file extension filters

**3. Claude API Errors**
- Verify API key is valid
- Check account has credits
- Reduce batch size if hitting token limits
- Check model name is correct

**4. Import Errors**
- Run `pip install -r requirements.txt`
- Check Python version (3.8+)
- Verify virtual environment is activated

## 📚 Dependencies

- **anthropic** (>=0.34.0): Claude AI SDK
- **jira** (>=3.8.0): Jira API client
- **python-dotenv** (>=1.0.0): Environment management
- **pydantic** (>=2.5.0): Data validation
- **requests** (>=2.31.0): HTTP library

## 🎯 Use Cases

1. **Automated Bug Triage**: Automatically analyze new bugs
2. **Code Review**: Find potential issues in code
3. **Legacy Code Analysis**: Understand old codebases
4. **Bug Prioritization**: Identify critical issues
5. **Developer Assistance**: Suggest fixes to developers
6. **Documentation**: Generate bug analysis documentation

## 🚦 Next Steps

After setup, you can:
1. Run `setup_check.py` to verify everything works
2. Test with a small number of bugs first
3. Review generated reports
4. Customize filters and extensions for your needs
5. Integrate into CI/CD pipeline
6. Add custom analysis rules
7. Extend with additional MCP tools

## 📖 Additional Resources

- Jira API: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- Claude API: https://docs.anthropic.com/
- MCP Specification: https://modelcontextprotocol.io/

---

**Created**: December 12, 2025
**Version**: 1.0
**Author**: Sustenance Bug Triage System
