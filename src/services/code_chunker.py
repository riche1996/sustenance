"""Code Chunker Service - Splits code files into semantic chunks for indexing.

Supports AST-based chunking for Python, Java, JavaScript/TypeScript, and 
line-based chunking for other languages.
"""
import ast
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ChunkType(Enum):
    """Types of code chunks."""
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    IMPORT = "import"
    CONSTANT = "constant"
    BLOCK = "block"  # For non-AST languages


@dataclass
class CodeChunk:
    """Represents a chunk of code for indexing."""
    chunk_id: str
    file_path: str
    relative_path: str
    chunk_type: ChunkType
    name: str  # Function/class name or "block_N"
    content: str
    start_line: int
    end_line: int
    language: str
    parent_name: Optional[str] = None  # For methods, the class name
    signature: Optional[str] = None  # Function signature
    docstring: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)  # Functions called
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for indexing."""
        return {
            "chunk_id": self.chunk_id,
            "file_path": self.file_path,
            "relative_path": self.relative_path,
            "chunk_type": self.chunk_type.value,
            "name": self.name,
            "content": self.content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "language": self.language,
            "parent_name": self.parent_name,
            "signature": self.signature,
            "docstring": self.docstring,
            "imports": self.imports,
            "calls": self.calls,
            "metadata": self.metadata
        }


class CodeChunker:
    """Service for chunking code files into semantic units."""
    
    # Language extensions mapping
    LANGUAGE_MAP = {
        '.py': 'python',
        '.java': 'java',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.go': 'go',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.rb': 'ruby',
        '.php': 'php',
        '.scala': 'scala',
        '.kt': 'kotlin',
        '.swift': 'swift',
        '.vue': 'vue',
        '.sql': 'sql',
        '.sh': 'bash',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
        '.xml': 'xml',
        '.md': 'markdown',
    }
    
    # Languages with AST support
    AST_LANGUAGES = {'python'}  # Can be extended with tree-sitter
    
    def __init__(self, 
                 max_chunk_lines: int = 100,
                 min_chunk_lines: int = 5,
                 overlap_lines: int = 3):
        """
        Initialize the code chunker.
        
        Args:
            max_chunk_lines: Maximum lines per chunk for non-AST chunking
            min_chunk_lines: Minimum lines for a chunk
            overlap_lines: Lines to overlap between chunks for context
        """
        self.max_chunk_lines = max_chunk_lines
        self.min_chunk_lines = min_chunk_lines
        self.overlap_lines = overlap_lines
    
    def get_language(self, file_path: str) -> str:
        """Detect language from file extension."""
        ext = Path(file_path).suffix.lower()
        return self.LANGUAGE_MAP.get(ext, 'unknown')
    
    def chunk_file(self, file_path: str, content: str, 
                   repo_root: str = None) -> List[CodeChunk]:
        """
        Chunk a code file into semantic units.
        
        Args:
            file_path: Absolute path to the file
            content: File content
            repo_root: Repository root for relative paths
            
        Returns:
            List of CodeChunk objects
        """
        language = self.get_language(file_path)
        
        # Calculate relative path
        if repo_root:
            try:
                relative_path = str(Path(file_path).relative_to(repo_root))
            except ValueError:
                relative_path = file_path
        else:
            relative_path = file_path
        
        # Use AST chunking for supported languages
        if language == 'python':
            return self._chunk_python(file_path, content, relative_path)
        elif language in ('java', 'javascript', 'typescript'):
            return self._chunk_curly_brace_language(file_path, content, relative_path, language)
        else:
            return self._chunk_by_lines(file_path, content, relative_path, language)
    
    def _generate_chunk_id(self, file_path: str, name: str, start_line: int) -> str:
        """Generate a unique chunk ID."""
        import hashlib
        content = f"{file_path}:{name}:{start_line}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _chunk_python(self, file_path: str, content: str, 
                      relative_path: str) -> List[CodeChunk]:
        """Chunk Python files using AST."""
        chunks = []
        lines = content.split('\n')
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning(f"Could not parse Python file {file_path}: {e}")
            return self._chunk_by_lines(file_path, content, relative_path, 'python')
        
        # Extract imports at file level
        file_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    file_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    file_imports.append(f"{module}.{alias.name}")
        
        # Process top-level definitions
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                chunks.extend(self._process_python_class(
                    node, file_path, relative_path, lines, file_imports
                ))
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                chunk = self._process_python_function(
                    node, file_path, relative_path, lines, file_imports
                )
                if chunk:
                    chunks.append(chunk)
        
        # If no chunks found, create a file-level chunk
        if not chunks and content.strip():
            chunk_id = self._generate_chunk_id(file_path, "file", 1)
            chunks.append(CodeChunk(
                chunk_id=chunk_id,
                file_path=file_path,
                relative_path=relative_path,
                chunk_type=ChunkType.FILE,
                name=Path(file_path).name,
                content=content[:10000],  # Limit size
                start_line=1,
                end_line=len(lines),
                language='python',
                imports=file_imports
            ))
        
        return chunks
    
    def _process_python_class(self, node: ast.ClassDef, file_path: str,
                               relative_path: str, lines: List[str],
                               file_imports: List[str]) -> List[CodeChunk]:
        """Process a Python class definition."""
        chunks = []
        
        # Get class source
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        class_content = '\n'.join(lines[start_line-1:end_line])
        
        # Extract docstring
        docstring = ast.get_docstring(node)
        
        # Extract base classes
        bases = [self._get_name(base) for base in node.bases]
        
        # Create class chunk
        chunk_id = self._generate_chunk_id(file_path, node.name, start_line)
        class_chunk = CodeChunk(
            chunk_id=chunk_id,
            file_path=file_path,
            relative_path=relative_path,
            chunk_type=ChunkType.CLASS,
            name=node.name,
            content=class_content,
            start_line=start_line,
            end_line=end_line,
            language='python',
            docstring=docstring,
            imports=file_imports,
            metadata={'bases': bases}
        )
        chunks.append(class_chunk)
        
        # Process methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_chunk = self._process_python_function(
                    item, file_path, relative_path, lines, file_imports,
                    parent_name=node.name
                )
                if method_chunk:
                    chunks.append(method_chunk)
        
        return chunks
    
    def _process_python_function(self, node, file_path: str,
                                  relative_path: str, lines: List[str],
                                  file_imports: List[str],
                                  parent_name: str = None) -> Optional[CodeChunk]:
        """Process a Python function/method definition."""
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        
        # Skip very small functions
        if end_line - start_line < self.min_chunk_lines - 1:
            return None
        
        func_content = '\n'.join(lines[start_line-1:end_line])
        
        # Extract docstring
        docstring = ast.get_docstring(node)
        
        # Build signature
        args = []
        for arg in node.args.args:
            arg_name = arg.arg
            if arg.annotation:
                arg_name += f": {self._get_name(arg.annotation)}"
            args.append(arg_name)
        
        signature = f"def {node.name}({', '.join(args)})"
        if node.returns:
            signature += f" -> {self._get_name(node.returns)}"
        
        # Extract function calls
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_name = self._get_name(child.func)
                if call_name:
                    calls.append(call_name)
        
        chunk_id = self._generate_chunk_id(file_path, node.name, start_line)
        chunk_type = ChunkType.METHOD if parent_name else ChunkType.FUNCTION
        
        return CodeChunk(
            chunk_id=chunk_id,
            file_path=file_path,
            relative_path=relative_path,
            chunk_type=chunk_type,
            name=node.name,
            content=func_content,
            start_line=start_line,
            end_line=end_line,
            language='python',
            parent_name=parent_name,
            signature=signature,
            docstring=docstring,
            imports=file_imports,
            calls=list(set(calls))  # Unique calls
        )
    
    def _get_name(self, node) -> str:
        """Extract name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[{self._get_name(node.slice)}]"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return ""
    
    def _chunk_curly_brace_language(self, file_path: str, content: str,
                                     relative_path: str, language: str) -> List[CodeChunk]:
        """Chunk Java/JavaScript/TypeScript using regex-based detection."""
        chunks = []
        lines = content.split('\n')
        
        # Patterns for function/class detection
        patterns = {
            'java': {
                'class': r'(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:abstract\s+)?class\s+(\w+)',
                'function': r'(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[^{]+)?\s*\{',
            },
            'javascript': {
                'class': r'class\s+(\w+)',
                'function': r'(?:async\s+)?(?:function\s+(\w+)|(\w+)\s*[=:]\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))',
            },
            'typescript': {
                'class': r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)',
                'function': r'(?:export\s+)?(?:async\s+)?(?:function\s+(\w+)|(\w+)\s*[=:]\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))',
            }
        }
        
        lang_patterns = patterns.get(language, patterns['javascript'])
        
        # Find all classes and functions
        definitions = []
        
        for i, line in enumerate(lines):
            # Check for class
            class_match = re.search(lang_patterns['class'], line)
            if class_match:
                name = class_match.group(1)
                definitions.append({
                    'type': ChunkType.CLASS,
                    'name': name,
                    'line': i + 1
                })
            
            # Check for function
            func_match = re.search(lang_patterns['function'], line)
            if func_match:
                name = func_match.group(1) or func_match.group(2) if func_match.lastindex >= 2 else func_match.group(1)
                if name:
                    definitions.append({
                        'type': ChunkType.FUNCTION,
                        'name': name,
                        'line': i + 1
                    })
        
        # Create chunks from definitions
        for i, defn in enumerate(definitions):
            start_line = defn['line']
            
            # Find end line (next definition or end of file)
            if i + 1 < len(definitions):
                end_line = definitions[i + 1]['line'] - 1
            else:
                end_line = len(lines)
            
            # Find matching brace
            brace_end = self._find_matching_brace(lines, start_line - 1)
            if brace_end:
                end_line = min(end_line, brace_end + 1)
            
            chunk_content = '\n'.join(lines[start_line-1:end_line])
            
            if len(chunk_content.strip()) > 0:
                chunk_id = self._generate_chunk_id(file_path, defn['name'], start_line)
                chunks.append(CodeChunk(
                    chunk_id=chunk_id,
                    file_path=file_path,
                    relative_path=relative_path,
                    chunk_type=defn['type'],
                    name=defn['name'],
                    content=chunk_content,
                    start_line=start_line,
                    end_line=end_line,
                    language=language
                ))
        
        # If no chunks found, use line-based chunking
        if not chunks:
            return self._chunk_by_lines(file_path, content, relative_path, language)
        
        return chunks
    
    def _find_matching_brace(self, lines: List[str], start_idx: int) -> Optional[int]:
        """Find the line index of matching closing brace."""
        brace_count = 0
        started = False
        
        for i in range(start_idx, min(start_idx + 500, len(lines))):  # Limit search
            line = lines[i]
            for char in line:
                if char == '{':
                    brace_count += 1
                    started = True
                elif char == '}':
                    brace_count -= 1
                    if started and brace_count == 0:
                        return i
        
        return None
    
    def _chunk_by_lines(self, file_path: str, content: str,
                        relative_path: str, language: str) -> List[CodeChunk]:
        """Chunk file by line count with overlap."""
        chunks = []
        lines = content.split('\n')
        total_lines = len(lines)
        
        if total_lines == 0:
            return chunks
        
        # If file is small enough, return as single chunk
        if total_lines <= self.max_chunk_lines:
            chunk_id = self._generate_chunk_id(file_path, "block_1", 1)
            chunks.append(CodeChunk(
                chunk_id=chunk_id,
                file_path=file_path,
                relative_path=relative_path,
                chunk_type=ChunkType.BLOCK,
                name=f"block_1",
                content=content,
                start_line=1,
                end_line=total_lines,
                language=language
            ))
            return chunks
        
        # Chunk with overlap
        chunk_num = 1
        start = 0
        
        while start < total_lines:
            end = min(start + self.max_chunk_lines, total_lines)
            chunk_content = '\n'.join(lines[start:end])
            
            chunk_id = self._generate_chunk_id(file_path, f"block_{chunk_num}", start + 1)
            chunks.append(CodeChunk(
                chunk_id=chunk_id,
                file_path=file_path,
                relative_path=relative_path,
                chunk_type=ChunkType.BLOCK,
                name=f"block_{chunk_num}",
                content=chunk_content,
                start_line=start + 1,
                end_line=end,
                language=language
            ))
            
            # Move start with overlap
            start = end - self.overlap_lines
            chunk_num += 1
            
            # Prevent infinite loop
            if start >= total_lines - self.overlap_lines:
                break
        
        return chunks
    
    def chunk_repository(self, repo_path: str, 
                         extensions: List[str] = None,
                         exclude_patterns: List[str] = None,
                         max_file_size: int = 1_000_000) -> List[CodeChunk]:
        """
        Chunk all files in a repository.
        
        Args:
            repo_path: Path to repository root
            extensions: File extensions to include (None = all supported)
            exclude_patterns: Patterns to exclude (e.g., ['node_modules', '.git'])
            max_file_size: Maximum file size in bytes to process
            
        Returns:
            List of all code chunks
        """
        if extensions is None:
            extensions = list(self.LANGUAGE_MAP.keys())
        
        if exclude_patterns is None:
            exclude_patterns = [
                'node_modules', '.git', '__pycache__', '.venv', 'venv',
                'dist', 'build', '.idea', '.vscode', 'target', 'bin', 'obj',
                '.next', '.nuxt', 'coverage', '.pytest_cache', '.mypy_cache'
            ]
        
        repo_path = Path(repo_path)
        all_chunks = []
        files_processed = 0
        files_skipped = 0
        
        logger.info(f"Chunking repository: {repo_path}")
        
        for ext in extensions:
            for file_path in repo_path.rglob(f'*{ext}'):
                # Check exclusions
                if any(excl in str(file_path) for excl in exclude_patterns):
                    files_skipped += 1
                    continue
                
                # Check file size
                if file_path.stat().st_size > max_file_size:
                    logger.warning(f"Skipping large file: {file_path}")
                    files_skipped += 1
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    chunks = self.chunk_file(str(file_path), content, str(repo_path))
                    all_chunks.extend(chunks)
                    files_processed += 1
                    
                    if files_processed % 100 == 0:
                        logger.info(f"  Processed {files_processed} files, {len(all_chunks)} chunks...")
                        
                except Exception as e:
                    logger.warning(f"Error processing {file_path}: {e}")
                    files_skipped += 1
        
        logger.info(f"✓ Chunking complete: {files_processed} files, {len(all_chunks)} chunks, {files_skipped} skipped")
        return all_chunks


# Convenience function
def chunk_code_file(file_path: str, content: str, repo_root: str = None) -> List[Dict[str, Any]]:
    """Convenience function to chunk a single file."""
    chunker = CodeChunker()
    chunks = chunker.chunk_file(file_path, content, repo_root)
    return [chunk.to_dict() for chunk in chunks]
