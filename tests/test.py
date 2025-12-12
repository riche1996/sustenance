
#!/usr/bin/env python3
"""
Index & search a Python codebase using Whoosh.
"""

import argparse
import os
import time
from pathlib import Path
from typing import Iterable, Tuple

from whoosh import index
from whoosh.fields import Schema, TEXT, ID, STORED
from whoosh.analysis import RegexTokenizer, LowercaseFilter, StopFilter
from whoosh.qparser import MultifieldParser, OrGroup, QueryParser
from whoosh.highlight import ContextFragmenter, UppercaseFormatter

# Optional pretty printing
try:
    from rich.console import Console
    console = Console()
    RICH = True
except Exception:
    RICH = False


# ---------------------------
# Analyzers & schema
# ---------------------------

def content_analyzer():
    """Tokenizer suitable for source code & text (keeps underscores)."""
    return RegexTokenizer(r"[A-Za-z_][A-Za-z0-9_]*") | LowercaseFilter() | StopFilter()

def identifier_analyzer():
    """Tokenizer for identifiers only (no stopwords)."""
    return RegexTokenizer(r"[A-Za-z_][A-Za-z0-9_]*") | LowercaseFilter()

SCHEMA = Schema(
    path=ID(stored=True, unique=True),
    mtime=STORED,                      # store last modified timestamp
    content=TEXT(analyzer=content_analyzer(), stored=False),
    identifiers=TEXT(analyzer=identifier_analyzer(), stored=False),
)


# ---------------------------
# Helpers
# ---------------------------

SKIP_DIRS = {"venv", ".venv", ".git", "node_modules", "dist", "build", "__pycache__"}

def iter_python_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p

def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_bytes().decode("latin-1", errors="ignore")

def extract_identifiers(text: str) -> str:
    # Simple regex extraction of identifiers (AST-based extraction shown later)
    import re
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text)
    return " ".join(tokens)


# ---------------------------
# Indexing
# ---------------------------

def create_or_open_index(index_dir: Path):
    if not index_dir.exists():
        index_dir.mkdir(parents=True)
    if index.exists_in(index_dir):
        return index.open_dir(index_dir)
    else:
        return index.create_in(index_dir, SCHEMA)

def index_repo(root: Path, index_dir: Path, incremental=True) -> Tuple[int, int]:
    ix = create_or_open_index(index_dir)
    writer = ix.writer(limitmb=256)

    added, updated = 0, 0

    for file_path in iter_python_files(root):
        text = read_file(file_path)
        idents = extract_identifiers(text)
        mtime = int(file_path.stat().st_mtime)

        if incremental:
            # Check existing doc mtime
            with ix.searcher() as s:
                q = QueryParser("path", ix.schema).parse(str(file_path))
                r = s.search(q, limit=1)
                if r:
                    stored_mtime = r[0]["mtime"]
                    if stored_mtime == mtime:
                        continue  # unchanged, skip
                    else:
                        updated += 1

        writer.update_document(
            path=str(file_path),
            mtime=mtime,
            content=text,
            identifiers=idents,
        )
        if not incremental:
            added += 1

    writer.commit()
    return added, updated


# ---------------------------
# Searching
# ---------------------------

def search_index(index_dir: Path, query_str: str, field: str, limit: int = 25, show_snippets: bool = True):
    ix = index.open_dir(index_dir)

    # Allow querying across both fields; but set default field for QueryParser
    parser = MultifieldParser(["content", "identifiers"], schema=ix.schema, group=OrGroup.factory(0.9))
    if field in ("content", "identifiers"):
        # Bias the default field by parsing with a single-field parser
        parser = QueryParser(field, schema=ix.schema)

    q = parser.parse(query_str)

    with ix.searcher() as s:
        results = s.search(q, limit=limit)
        results.fragmenter = ContextFragmenter(surround=60)  # line-ish fragments
        results.formatter = UppercaseFormatter()

        total = len(results)
        hdr = f"Total hits: {total}"
        if RICH: console.rule(hdr)
        else: print(hdr)

        for hit in results:
            path = hit["path"]
            if RICH:
                console.print(f"[bold]{path}[/bold]")
            else:
                print(path)

            if show_snippets:
                # generate best fragments from 'content'
                frags = hit.highlights("content", top=3)
                if frags:
                    if RICH:
                        console.print(frags)
                    else:
                        print(frags)
            if RICH: console.print()  # spacing


# ---------------------------
# CLI
# ---------------------------

def main():
    ap = argparse.ArgumentParser(description="Whoosh-based index & search for Python code")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_index = sub.add_parser("index", help="Index a codebase")
    ap_index.add_argument("--root", required=True, help="Path to repo root")
    ap_index.add_argument("--index", required=True, help="Index directory")
    ap_index.add_argument("--no-incremental", action="store_true", help="Force reindex all files")

    ap_search = sub.add_parser("search", help="Search the index")
    ap_search.add_argument("--index", required=True, help="Index directory")
    ap_search.add_argument("--query", required=True, help="Query string")
    ap_search.add_argument("--field", default="content", choices=("content", "identifiers"), help="Default field for parser")
    ap_search.add_argument("--limit", type=int, default=50, help="Max results")
    ap_search.add_argument("--no-snippets", action="store_true", help="Disable contextual highlights")

    args = ap.parse_args()

    if args.cmd == "index":
        root = Path(args.root).resolve()
        index_dir = Path(args.index).resolve()
        t0 = time.time()
        added, updated = index_repo(root, index_dir, incremental=not args.no_incremental)
        dt = time.time() - t0
        msg = f"Index complete in {dt:.2f}s | added={added} updated={updated}"
        if RICH: console.print(f"[green]{msg}[/green]")
        else: print(msg)

    elif args.cmd == "search":
        index_dir = Path(args.index).resolve()
        search_index(index_dir, args.query, field=args.field, limit=args.limit, show_snippets=not args.no_snippets)


if __name__ == "__main__":
    main()
