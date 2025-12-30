# System Architecture Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│           Sustenance - Multi-Tracker Issue Management           │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │       SuperAgent        │
                    │   (src/agents/agents)   │
                    │  - Natural language UI  │
                    │  - Intent recognition   │
                    │  - Multi-tracker routing│
                    └─────┬──────┬──────┬──────┘
                          │      │      │
           ┌─────────────┘     │      └─────────────┐
           │                   │                   │
     ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
     │  JiraAgent  │      │GitHubAgent │      │  TFSAgent  │
     │ (50 actions)│      │(47 actions)│      │ (10 actions)│
     └─────┬──────┘      └─────┬──────┘      └─────┬──────┘
           │                   │                   │
     ┌─────▼─────┐      ┌─────▼─────┐      ┌─────▼─────┐
     │ JiraMCP    │      │ GitHubMCP  │      │  TfsMCP   │
     │ Server     │      │ Server    │      │  Server   │
     └─────┬──────┘      └─────┬──────┘      └─────┬──────┘
           │                   │                   │
           ▼                   ▼                   ▼
     ┌───────────┐      ┌───────────┐      ┌───────────┐
     │Jira Cloud │      │ GitHub API│      │Azure DevOps│
     └───────────┘      └───────────┘      └───────────┘
```

## Legacy Orchestrator Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Bug Triage & Analysis System                 │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Main Orchestrator (main.py)                   │
│  - Workflow coordination                                         │
│  - Progress tracking                                             │
│  - Error handling                                                │
│  - Log history management                                        │
└───┬─────────────┬───────────────────────┬───────────────────────┘
    │             │                       │
┌───▼────┐  ┌─────▼──────┐      ┌────────▼────────┐
│  Jira  │  │   Code     │      │  Log History    │
│  MCP   │  │  Analyzer  │      │  Manager        │
│        │  │            │      │                 │
└───┬────┘  └─────┬──────┘      └────────┬────────┘
    │             │                      │
    │             │              ┌───────┴───────┐
    │             │              │               │
┌───▼────┐  ┌─────▼──────┐  ┌───▼────────┐ ┌───▼──────────┐
│  Jira  │  │  Claude    │  │ Embedding  │ │  OpenSearch  │
│  Cloud │  │  API       │  │ Service    │ │  Client      │
│        │  │ (Anthropic)│  │            │ │              │
└────────┘  └────────────┘  └────┬───────┘ └───┬──────────┘
                                 │             │
                                 │    384-dim  │
                                 │    vectors  │
                                 └──────┬──────┘
                                        │
                              ┌─────────▼─────────┐
                              │   OpenSearch DB   │
                              │  - Bug analyses   │
                              │  - Embeddings     │
                              │  - History logs   │
                              └───────────────────┘
```
                                        │
         ┌──────────────────────────────┴─────────┐
         │                                        │
┌────────▼────────────┐              ┌────────────▼──────────┐
│  Report Generator   │              │  Log Query Tool       │
│  (report_generator) │              │  (query_log_history)  │
│  - JSON reports     │              │  - Semantic search    │
│  - Markdown reports │              │  - History lookup     │
└────────┬────────────┘              │  - Analytics          │
         │                           └───────────────────────┘
         ▼
┌─────────────────┐
│  Reports/       │
│  Output Files   │
└─────────────────┘
```

## Data Flow

```
1. START
   │
   ▼
2. Initialize Components
   │
   ├─► Load Configuration (.env)
   ├─► Connect to Jira
   ├─► Initialize Claude Client
   └─► Initialize Log History (NEW)
       ├─► Connect to OpenSearch
       ├─► Load Embedding Model
       └─► Create/Verify Index
   │
   ▼
3. Scan Repository
   │
   ├─► Search for *.py, *.java, etc.
   ├─► Read file contents
   └─► Create CodeFile objects
   │
   ▼
4. Fetch Bugs from Jira
   │
   ├─► Build JQL Query (status, project, etc.)
   ├─► Execute API request
   └─► Parse to JiraIssue objects
   │
   ▼
5. For Each Bug:
   │
   ├─► Prepare Bug Context
   │   ├─ Summary
   │   ├─ Description
   │   └─ Metadata
   │
   ├─► Group Code Files by Type
   │   ├─ .py files
   │   ├─ .java files
   │   └─ etc.
   │
   ├─► Analyze in Batches
   │   │
   │   ├─► Send to Claude API
   │   │   ├─ Bug description
   │   │   ├─ Code files
   │   │   └─ Analysis prompt
   │   │
   │   ├─► Receive Analysis
   │   │   ├─ File paths
   │   │   ├─ Line numbers
   │   │   ├─ Issues
   │   │   ├─ Severity
   │   │   └─ Resolutions
   │   │
   │   └─► Parse Response
   │       └─ Create Finding objects
   │
   ├─► Store Analysis Results
   │
   └─► Log to History (NEW)
       │
       ├─► Generate Embedding
       │   ├─ Combine bug summary
       │   ├─ Bug description
       │   └─ Analysis results
       │   → 384-dim vector
       │
       └─► Index to OpenSearch
           ├─ Bug metadata
           ├─ Analysis findings
           ├─ Embedding vector
           └─ Timestamp
   │
   ▼
6. Generate Reports
   │
   ├─► Calculate Summary Stats
   ├─► Create JSON Report
   ├─► Create Markdown Report
   └─► Save to reports/
   │
   ▼
7. END

Optional: Query Log History
   │
   ├─► Semantic Search (by meaning)
   ├─► Get Bug History (by ID)
   ├─► Find Duplicates (similarity)
   └─► View Statistics
```

## Component Interaction Sequence

```
User
 │
 │ run()
 ▼
BugTriageOrchestrator
 │
 ├─────────────────┐
 │                 │
 │ get_bugs()      │ scan_repository()
 ▼                 ▼
JiraMCPServer    CodeAnalysisAgent
 │                 │
 │ HTTP Request    │ Read Files
 ▼                 ▼
Jira Cloud       Local Repo
 │                 │
 │ JiraIssue[]     │ CodeFile[]
 └────────┬────────┘
          │
          │ For each bug
          ▼
    CodeAnalysisAgent
          │
          │ analyze_bug()
          ▼
    Anthropic Claude API
          │
          │ Analysis Results
          ▼
    ReportGenerator
          │
          │ generate_report()
          ▼
    Reports Directory
```

## Module Dependencies

```
src/main.py
  ├─► src/config.py
  ├─► src/trackers/jira_client.py
  │     ├─► jira (library)
  │     ├─► pydantic
  │     └─► src/config.py
  │
  ├─► src/services/code_analyzer.py
  │     ├─► anthropic (library)
  │     ├─► pathlib
  │     └─► src/config.py
  │
  ├─► src/services/report_generator.py
  │     ├─► json
  │     ├─► datetime
  │     └─► src/config.py
  │
  └─► src/services/log_history_manager.py
        ├─► src/services/opensearch_client.py
        ├─► src/services/embedding_service.py
        └─► src/trackers/jira_client.py

src/agents/agents.py
  ├─► src/config.py
  ├─► src/trackers/factory.py
  ├─► src/trackers/jira_client.py
  ├─► src/trackers/github_client.py
  ├─► src/trackers/tfs_client.py
  └─► src/services/code_analyzer.py

src/config.py
  ├─► os
  ├─► dotenv
  └─► pathlib
```

## File System Structure

```
sustenance/
│
├── src/                              [Source Code]
│   ├── __init__.py
│   ├── config.py                     [Configuration]
│   ├── main.py                       [Orchestrator]
│   │
│   ├── agents/                       [Agent System]
│   │   ├── __init__.py
│   │   └── agents.py                 [SuperAgent, JiraAgent, etc.]
│   │
│   ├── trackers/                     [Bug Tracker Integrations]
│   │   ├── __init__.py
│   │   ├── factory.py                [BugTrackerFactory]
│   │   ├── jira_client.py            [Jira Integration - 50 actions]
│   │   ├── github_client.py          [GitHub Integration - 47 actions]
│   │   └── tfs_client.py             [TFS/Azure DevOps Integration]
│   │
│   └── services/                     [Core Services]
│       ├── __init__.py
│       ├── code_analyzer.py          [AI Code Analysis]
│       ├── embedding_service.py      [Vector Embeddings]
│       ├── opensearch_client.py      [OpenSearch Integration]
│       ├── log_history_manager.py    [Analysis History]
│       └── report_generator.py       [Report Generation]
│
├── web/                              [Web Application]
│   ├── __init__.py
│   ├── app.py                        [Flask Web Interface]
│   └── templates/
│       └── chat.html                 [Chat UI]
│
├── cli/                              [Command Line Interface]
│   ├── __init__.py
│   └── cli.py                        [CLI Application]
│
├── tests/                            [Test Suite]
│   ├── __init__.py
│   ├── test_components.py            [Component Tests]
│   ├── test_bug_trackers.py          [Tracker Tests]
│   └── test_*.py                     [Other Tests]
│
├── scripts/                          [Utility Scripts]
│   ├── demo.py                       [Demo Script]
│   ├── examples.py                   [Usage Examples]
│   └── setup_check.py                [Setup Verification]
│
├── docs/                             [Documentation]
│   ├── architecture/                 [System Architecture]
│   │   └── ARCHITECTURE.md           [This File]
│   ├── capabilities/                 [Feature Documentation]
│   │   ├── JIRA_CAPABILITIES.md      [50 Jira Actions]
│   │   └── GITHUB_CAPABILITIES.md    [47 GitHub Actions]
│   └── guides/                       [User Guides]
│       ├── QUICK_REFERENCE.md
│       └── QUICK_START_TRACKERS.md
│
├── data/                             [Runtime Data]
│   ├── sessions/                     [Chat Sessions]
│   ├── reports/                      [Generated Reports]
│   └── repos/                        [Cloned Repositories]
│
├── Configuration Files
│   ├── .env                          [Credentials - Private]
│   ├── .env.example                  [Template]
│   ├── requirements.txt              [Dependencies]
│   └── .gitignore                    [Git Ignore]
│
└── README.md                         [User Guide]
```

## Key Design Patterns

### 1. Model Context Protocol (MCP)
```
JiraMCPServer acts as an MCP server providing:
- Tools for fetching bugs
- Tools for updating issues
- Structured data models (JiraIssue)
```

### 2. Agent-Based Architecture
```
CodeAnalysisAgent operates as an autonomous agent:
- Scans environment (repository)
- Makes decisions (batch grouping)
- Executes actions (API calls)
- Processes results (parsing)
```

### 3. Orchestration Pattern
```
BugTriageOrchestrator coordinates:
- Component initialization
- Workflow sequencing
- Error handling
- Progress reporting
```

### 4. Data Transformation Pipeline
```
Raw Data → Structured Models → AI Processing → Parsed Results → Reports

JiraIssue (Pydantic) ─┐
                      ├─► Analysis ─► Findings ─► JSON/Markdown
CodeFile (Class)  ────┘
```

## Configuration Flow

```
.env file
   │
   │ Load via dotenv
   ▼
Environment Variables
   │
   │ Read in config.py
   ▼
Config Class (Static)
   │
   │ Used by all components
   ├─► JiraMCPServer
   ├─► CodeAnalysisAgent
   ├─► ReportGenerator
   └─► BugTriageOrchestrator
```

## Error Handling Strategy

```
BugTriageOrchestrator (Top Level)
   │
   ├─► Try/Catch for each component
   │
   ├─► JiraMCPServer
   │   ├─► Connection errors → Exit with message
   │   └─► API errors → Log and continue
   │
   ├─► CodeAnalysisAgent
   │   ├─► File read errors → Log and skip file
   │   └─► API errors → Return error finding
   │
   └─► ReportGenerator
       └─► File write errors → Raise exception
```

## Scalability Considerations

### Horizontal Scaling
```
Multiple Instances
   │
   ├─► Instance 1: Projects A-M
   └─► Instance 2: Projects N-Z

Or

   ├─► Instance 1: Critical bugs
   └─► Instance 2: Normal bugs
```

### Batch Processing
```
Large Bug List
   │
   ├─► Batch 1 (10 bugs) ──► Process ──► Report 1
   ├─► Batch 2 (10 bugs) ──► Process ──► Report 2
   └─► Batch 3 (10 bugs) ──► Process ──► Report 3
```

### Parallel Analysis
```
Bug List
   │
   ├─► Bug 1 ──► Thread 1 ──┐
   ├─► Bug 2 ──► Thread 2 ──┤
   └─► Bug 3 ──► Thread 3 ──┤
                             ├─► Combine Results
                             │
                             ▼
                          Report
```

## API Rate Limit Management

```
Rate Limiter
   │
   ├─► Jira API
   │   └─► Max 300 req/min
   │       └─► Add delays between batches
   │
   └─► Claude API
       └─► Tier-based limits
           └─► Batch files to reduce requests
```

## Future Enhancements

### Potential Extensions
```
1. Database Integration
   ├─► Store analysis history
   └─► Track bug patterns

2. Web Interface
   ├─► Dashboard for results
   └─► Real-time monitoring

3. CI/CD Integration
   ├─► Automated PR analysis
   └─► Pre-commit bug detection

4. Multi-Repository Support
   ├─► Analyze multiple repos
   └─► Cross-repo bug tracking

5. Enhanced AI Features
   ├─► Auto-fix generation
   ├─► Patch file creation
   └─► PR generation
```

---

**Document Version**: 2.0
**Last Updated**: December 20, 2025
