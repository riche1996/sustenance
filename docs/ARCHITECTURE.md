# System Architecture Diagram

## High-Level Architecture

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
│        │  │            │      │  (NEW)          │
└───┬────┘  └─────┬──────┘      └────────┬────────┘
    │             │                      │
    │             │              ┌───────┴───────┐
    │             │              │               │
┌───▼────┐  ┌─────▼──────┐  ┌───▼────────┐ ┌───▼──────────┐
│  Jira  │  │  Claude    │  │ Embedding  │ │  OpenSearch  │
│  Cloud │  │  API       │  │ Service    │ │  Client      │
│        │  │ (Anthropic)│  │  (NEW)     │ │  (NEW)       │
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
main.py
  ├─► config.py
  ├─► jira_mcp.py
  │     ├─► jira (library)
  │     ├─► pydantic
  │     └─► config.py
  │
  ├─► code_analyzer.py
  │     ├─► anthropic (library)
  │     ├─► pathlib
  │     └─► config.py
  │
  └─► report_generator.py
        ├─► json
        ├─► datetime
        └─► config.py

config.py
  ├─► os
  ├─► dotenv
  └─► pathlib
```

## File System Structure

```
sustenance/
│
├── Core System Files
│   ├── main.py                    [Orchestrator]
│   ├── jira_mcp.py               [Jira Integration]
│   ├── code_analyzer.py          [AI Analysis]
│   ├── report_generator.py       [Reporting]
│   └── config.py                 [Configuration]
│
├── Helper & Utility Files
│   ├── examples.py               [Usage Examples]
│   ├── setup_check.py            [Setup Verification]
│   └── test_components.py        [Component Tests]
│
├── Configuration Files
│   ├── .env                      [Credentials - Private]
│   ├── .env.example             [Template]
│   ├── requirements.txt         [Dependencies]
│   └── .gitignore              [Git Ignore]
│
├── Documentation
│   ├── README.md                [User Guide]
│   ├── PROJECT_OVERVIEW.md      [System Overview]
│   └── ARCHITECTURE.md          [This File]
│
├── Data Directories
│   ├── code_files/              [Code to Analyze]
│   ├── reports/                 [Generated Reports]
│   └── mcp_server/              [Existing MCP]
│
└── Output
    └── reports/
        ├── bug_analysis_report_*.json
        ├── bug_analysis_report_*.md
        └── {JIRA-KEY}_*.md
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

**Document Version**: 1.0
**Last Updated**: December 12, 2025
