
import os
import re

BASE_DIR = "./your_project"

def list_files(directory=BASE_DIR):
    results = []
    for root, _, files in os.walk(directory):
        for f in files:
            results.append(os.path.join(root, f))
    return results


def search(keyword, directory=BASE_DIR):
    matches = []

    for root, _, files in os.walk(directory):
        for fname in files:
            path = os.path.join(root, fname)
            try:
                with open(path, "r", errors="ignore") as f:
                    content = f.read()
                if keyword.lower() in content.lower():
                    matches.append({"file": path, "match_type": "text"})
            except Exception:
                pass
    
    return matches


def read_file(path):
    full_path = os.path.join(BASE_DIR, path.replace(BASE_DIR, ""))
    if not os.path.exists(full_path):
        raise FileNotFoundError("File not found")

    with open(full_path, "r") as f:
        return f.read()


def apply_patch(path, original, updated):
    full_path = os.path.join(BASE_DIR, path.replace(BASE_DIR, ""))

    with open(full_path, "r") as f:
        content = f.read()

    if original not in content:
        raise Exception("Original content not found")

    new_content = content.replace(original, updated)

    with open(full_path, "w") as f:
        f.write(new_content)
        
def register_filesystem_tools(server):

    @server.tool("list_files")
    def _list_files():
        return list_files()

    @server.tool("search")
    def _search(keyword: str):
        return search(keyword)

    @server.tool("read_file")
    def _read_file(path: str):
        return {"path": path, "content": read_file(path)}

    @server.tool("apply_patch")
    def _apply_patch(path: str, original: str, updated: str):
        return apply_patch(path, original, updated)
