# Code Indexing & RAG-Based Analysis

## Overview

The Code Indexing system enables Sustenance to handle **large repositories with millions of lines of code** through a RAG (Retrieval-Augmented Generation) approach. Instead of scanning all files for every bug analysis, the system:

1. **Indexes code once** - Parses files into semantic chunks (functions, classes, methods)
2. **Generates embeddings** - Creates 384-dimension vectors for semantic search
3. **Retrieves relevant code** - Uses vector similarity to find related code snippets
4. **Analyzes efficiently** - Sends only relevant code to Claude for analysis

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CODE INDEXING PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │   Source    │───▶│   Code      │───▶│  Embedding  │                 │
│  │   Code      │    │   Chunker   │    │  Service    │                 │
│  │   Files     │    │ (AST/Regex) │    │ (MiniLM)    │                 │
│  └─────────────┘    └─────────────┘    └─────────────┘                 │
│         │                  │                  │                        │
│         ▼                  ▼                  ▼                        │
│  ┌─────────────────────────────────────────────────────┐               │
│  │                    OpenSearch                       │               │
│  │  ┌─────────────────┐  ┌─────────────────────────┐  │               │
│  │  │   code_index    │  │   code_file_hashes      │  │               │
│  │  │ (chunks+vectors)│  │  (incremental tracking) │  │               │
│  │  └─────────────────┘  └─────────────────────────┘  │               │
│  └─────────────────────────────────────────────────────┘               │
│                              │                                         │
└──────────────────────────────│─────────────────────────────────────────┘
                               │
┌──────────────────────────────│─────────────────────────────────────────┐
│                        RAG ANALYSIS FLOW                               │
├──────────────────────────────│─────────────────────────────────────────┤
│                              ▼                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │
│  │    Bug      │───▶│   Code      │───▶│   Claude    │                │
│  │  Report     │    │   Search    │    │   Analysis  │                │
│  │            │    │  (k-NN)     │    │            │                │
│  └─────────────┘    └─────────────┘    └─────────────┘                │
│         │                  │                  │                        │
│         ▼                  ▼                  ▼                        │
│  Extract symbols    Find relevant code   Precise bug fix              │
│  from bug text      via vector search    recommendations              │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Services

### 1. CodeChunker (`code_chunker.py`)

Parses source code into semantic chunks for indexing.

**Features:**
- **AST Parsing** for Python (accurate function/class extraction)
- **Regex Parsing** for Java, JavaScript, TypeScript, C/C++
- **Line-based fallback** for other languages
- Extracts metadata: functions called, imports, docstrings, signatures

**Supported Languages:**
| Language | Method | Chunk Types |
|----------|--------|-------------|
| Python | AST | classes, functions, methods, module |
| Java | Regex | classes, methods, interfaces |
| JavaScript/TypeScript | Regex | classes, functions, methods |
| C/C++ | Regex | classes, functions |
| Others | Line-based | code blocks |

**Example Output:**
```python
CodeChunk(
    chunk_type='function',
    name='authenticate_user',
    file_path='src/auth/login.py',
    start_line=45,
    end_line=78,
    content='''def authenticate_user(username, password):
    """Authenticate a user with username and password.
    
    Args:
        username: The user's username
        password: The user's password
        
    Returns:
        User object if authentication succeeds
        
    Raises:
        AuthenticationError: If credentials are invalid
    """
    user = User.get(username=username)
    if not user:
        raise AuthenticationError("User not found")
    
    hashed = hash_password(password, user.salt)
    if hashed != user.password_hash:
        raise AuthenticationError("Invalid password")
    
    token = generate_token(user.id)
    return user''',
    language='python',
    signature='def authenticate_user(username: str, password: str) -> User:',
    docstring='Authenticate a user with username and password.',
    imports=['hashlib', 'jwt'],
    function_calls=['hash_password', 'generate_token', 'User.get'],
    embedding=None  # Generated by CodeIndexService
)
```

### 2. CodeIndexService (`code_index_service.py`)

Indexes code chunks in OpenSearch with embeddings.

**Features:**
- **Incremental indexing** - Only indexes changed files (tracks via SHA-256 hash)
- **Bulk operations** - Efficient batch indexing for large repos
- **Vector search** - k-NN search on 384-dimension embeddings
- **Multi-search** - Semantic + symbol + exact match

**OpenSearch Indices:**
- `code_index` - Code chunks with embeddings
- `code_file_hashes` - File hashes for incremental updates

**Key Methods:**
```python
# Index a repository
service.index_repository(
    repo_path="./data/repos/spring-boot",
    repo_full_name="spring-projects/spring-boot",
    extensions=[".java", ".py"],
    incremental=True
)

# Search code semantically
results = service.search_code(
    query="authentication handler",
    repo_full_name="spring-projects/spring-boot",
    language="java",
    limit=10
)

# Search by symbol name
results = service.search_by_symbol(
    symbol_name="UserService",
    repo_full_name="spring-projects/spring-boot"
)
```

### 3. CodeSearchService (`code_search_service.py`)

RAG-based code search combining multiple retrieval strategies.

**Search Strategies:**
1. **Semantic Search** - Vector similarity on query embedding
2. **Symbol Search** - Exact match on function/class names
3. **Pattern Search** - Keywords from bug description
4. **Historical Context** - Similar issues from issue_history index

**Key Methods:**
```python
# Find code relevant to a bug
results = service.find_code_for_bug(
    bug_title="Login fails with invalid credentials",
    bug_description="Users report...",
    repo_full_name="spring-projects/spring-boot"
)

# Prepare full context for Claude
context = service.prepare_analysis_context(
    bug_title="Login fails with invalid credentials",
    bug_description="Users are unable to login to the application. When they enter valid credentials, the system returns an authentication error. Stack trace shows NullPointerException in UserService.authenticate() method at line 45.",
    repo_full_name="spring-projects/spring-boot",
    historical_context=historical_issues,
    max_chunks=15
)
```

### 4. CodeAnalysisAgent (Updated)

Enhanced with RAG capabilities for large repositories.

**Two Modes:**
1. **Traditional Mode** - Scans all files (good for small repos)
2. **RAG Mode** - Uses indexed code for semantic search (required for large repos)

**Smart Mode Selection:**
```python
# Automatically chooses the right mode
result = agent.smart_analyze_bug(
    bug_description="Users are unable to login to the application. When they enter valid credentials, the system returns an authentication error. Stack trace shows NullPointerException in UserService.authenticate() method at line 45.",
    bug_key="GH-123",
    repo_full_name="spring-projects/spring-boot"
)
# Uses RAG if repo is indexed, otherwise falls back to scanning
```

## Usage

### Via Chat Interface

```
# Index a repository
> index spring-boot repo at ./data/repos/spring-boot

# Check index status
> show code index stats

# Search code
> search code for authentication handler in spring-boot

# Analyze bug with RAG
> analyze bug #123 with rag for spring-projects/spring-boot

# Clear code index
> clear code index for spring-projects/spring-boot
```

### Via JSON Actions

```json
// Index repository
{"action": "index_repository", "repo_path": "./data/repos/spring-boot", "repo_full_name": "spring-projects/spring-boot"}

// Search code
{"action": "search_code", "query": "authentication", "repo_full_name": "spring-projects/spring-boot"}

// RAG analysis
{"action": "analyze_bug_rag", "bug_id": "123", "repo_full_name": "spring-projects/spring-boot", "tracker": "github"}

// Get stats
{"action": "get_code_stats", "repo_full_name": "spring-projects/spring-boot"}
```

### Via Python API

```python
from src.services import CodeIndexService, CodeSearchService
from src.services.code_analyzer import CodeAnalysisAgent

# Index a repository
index_service = CodeIndexService()
result = index_service.index_repository(
    repo_path="./data/repos/spring-boot",
    repo_full_name="spring-projects/spring-boot"
)
print(f"Indexed {result['files_indexed']} files, {result['chunks_indexed']} chunks")

# Search code
search_service = CodeSearchService()
results = search_service.find_code_for_bug(
    bug_title="NullPointerException in UserService",
    bug_description="Application crashes when user logs in with valid credentials. The error occurs in UserService.authenticate() method when checking the password hash. Stack trace points to line 45 where user.getPasswordHash() returns null for new users who haven't set a password yet.",
    repo_full_name="spring-projects/spring-boot"
)

# RAG-based analysis
analyzer = CodeAnalysisAgent(use_rag=True)
analysis = analyzer.analyze_bug_with_rag(
    bug_description="Application crashes when user logs in with valid credentials. The error occurs in UserService.authenticate() method when checking the password hash. Stack trace points to line 45 where user.getPasswordHash() returns null for new users who haven't set a password yet.",
    bug_key="GH-456",
    repo_full_name="spring-projects/spring-boot"
)
```

## Performance

### Indexing Benchmarks

| Repository Size | Files | Chunks | Index Time | Index Size |
|-----------------|-------|--------|------------|------------|
| Small (<100 files) | 50 | 200 | ~30s | ~5MB |
| Medium (1K files) | 1,000 | 8,000 | ~5min | ~100MB |
| Large (10K files) | 10,000 | 80,000 | ~30min | ~800MB |
| Very Large (100K files) | 100,000 | 500,000+ | ~3hr | ~5GB |

### Search Performance

| Query Type | Latency | Notes |
|------------|---------|-------|
| Semantic (k-NN) | 50-200ms | Depends on index size |
| Symbol search | 10-50ms | Exact match, fast |
| Combined RAG | 200-500ms | Multiple searches |

### Memory Requirements

- **Embedding Model**: ~500MB (MiniLM-L6-v2)
- **Per 1000 chunks**: ~10MB in memory during indexing
- **OpenSearch**: ~100MB base + data

## Configuration

### Environment Variables

```bash
# OpenSearch
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200

# Embedding Model
EMBEDDING_MODEL_PATH=C:\AIForce\offline_model\embedding_model

# Indexing
MAX_CHUNK_SIZE=5000  # characters
MIN_CHUNK_SIZE=50
```

### Index Settings

The `code_index` uses these OpenSearch settings:
- **k-NN enabled**: For vector similarity search
- **Vector dimension**: 384 (MiniLM-L6-v2)
- **Space type**: cosinesimil (cosine similarity)
- **Engine**: nmslib (fast approximate nearest neighbor)

## Best Practices

### When to Use RAG vs Traditional

| Scenario | Recommended Approach |
|----------|---------------------|
| Small project (<1000 files) | Traditional scan |
| Large project (>10K files) | RAG (index first) |
| Frequent analysis of same repo | RAG (index once, query many) |
| One-time analysis | Traditional scan |
| Million-line codebase | RAG (required) |

### Optimizing Indexing

1. **Use incremental indexing** - Only re-indexes changed files
2. **Index by extension** - Only index relevant file types
3. **Schedule off-peak** - Index during low-usage periods
4. **Monitor OpenSearch** - Watch disk space and memory

### Optimizing Search

1. **Be specific in queries** - Include function names, error messages
2. **Filter by language** - If you know the target language
3. **Use historical context** - Connect with issue_history for patterns
4. **Limit results** - Start with 10-15 chunks, increase if needed

## Troubleshooting

### Common Issues

**1. "CodeIndexService not available"**
```
Cause: OpenSearch not running or not reachable
Fix: Start OpenSearch: docker-compose up opensearch
```

**2. "No relevant code found"**
```
Cause: Repository not indexed
Fix: Index the repository first with index_repository action
```

**3. "Embedding model not found"**
```
Cause: Model path not configured
Fix: Set EMBEDDING_MODEL_PATH environment variable
```

**4. Slow indexing**
```
Cause: Large repository with many files
Fix: 
- Use incremental=True (default)
- Index specific extensions only
- Increase OpenSearch heap size
```

### Debug Commands

```python
# Check if repo is indexed
stats = index_service.get_index_stats("spring-projects/spring-boot")
print(f"Chunks: {stats['total_chunks']}, Files: {stats['unique_files']}")

# Verify search works
results = index_service.search_code("test query", limit=5)
print(f"Found {len(results)} results")

# Check OpenSearch connection
from src.services import OpenSearchClient
client = OpenSearchClient()
print(f"Connected: {client.test_connection()}")
```

## API Reference

### CodeChunker

| Method | Description | Parameters |
|--------|-------------|------------|
| `chunk_file(file_path, language)` | Chunk a single file | path, language (optional) |
| `chunk_repository(repo_path, extensions)` | Chunk entire repo | path, extensions list |

### CodeIndexService

| Method | Description | Parameters |
|--------|-------------|------------|
| `index_file(file_path, repo_full_name)` | Index single file | path, repo name |
| `index_repository(repo_path, repo_full_name)` | Index entire repo | path, repo name, extensions |
| `search_code(query, repo_full_name)` | Semantic search | query, repo, language, limit |
| `search_by_symbol(symbol_name)` | Symbol search | name, repo |
| `get_index_stats(repo_full_name)` | Get statistics | repo (optional) |
| `clear_repository(repo_full_name)` | Clear indexed code | repo name |

### CodeSearchService

| Method | Description | Parameters |
|--------|-------------|------------|
| `search_relevant_code(query, repo)` | Combined search | query, repo, max_chunks |
| `find_code_for_bug(title, desc, repo)` | Bug-specific search | bug info, repo |
| `prepare_analysis_context(...)` | Full RAG context | bug, repo, historical |
| `get_code_context(chunks)` | Format for prompt | chunk list |

### CodeAnalysisAgent

| Method | Description | Parameters |
|--------|-------------|------------|
| `scan_repository(extensions)` | Traditional scan | extensions list |
| `analyze_bug(desc, key, files)` | Traditional analysis | bug info, files |
| `analyze_bug_with_rag(desc, key, repo)` | RAG analysis | bug info, repo |
| `smart_analyze_bug(...)` | Auto-select mode | bug info, repo |
| `index_repository(path, name)` | Index for RAG | path, repo name |
| `get_index_stats(repo)` | Check index | repo (optional) |
