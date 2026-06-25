"""Python repo indexer — walks a repo and parses all Python files."""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from synthesis.packages.codegraph.python_ast_parser import parse_python_file
from synthesis.packages.codegraph.graph_store import CodeGraph
from synthesis.packages.sandbox.runner import canonicalize_workspace_path


@dataclass
class GraphQuotas:
    max_files: int = 2000
    max_nodes: int = 100000
    max_parse_time_per_file_ms: int = 500
    max_total_index_time_sec: int = 120


def index_python_repo(
    repo_root: str,
    quotas: Optional[GraphQuotas] = None,
    ledger=None,
    trace_id: str = "",
) -> CodeGraph:
    """Walk a repo root and parse all .py files into a CodeGraph."""
    if quotas is None:
        quotas = GraphQuotas()

    graph = CodeGraph()
    # Resolve repo_root to real path to handle systems with symlinked roots (like macOS /var -> /private/var)
    repo_root = os.path.realpath(repo_root)
    root_path = Path(repo_root)

    if not root_path.exists():
        graph.errors.append(f"Repo root not found: {repo_root}")
        return graph

    # Collect all .py files (canonical paths)
    py_files = []
    for dirpath, dirnames, filenames in os.walk(str(root_path)):
        # Skip hidden dirs and common exclusions
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in
                       ("__pycache__", "node_modules", ".git", "venv", ".venv", "build", "dist", ".pytest_cache")]
        for f in filenames:
            if f.endswith(".py"):
                abs_path = os.path.join(dirpath, f)
                rel_path = os.path.relpath(abs_path, repo_root)
                py_files.append(rel_path)

    # Enforce max_files quota
    if len(py_files) > quotas.max_files:
        graph.errors.append(f"File count {len(py_files)} exceeds max {quotas.max_files}")
        py_files = py_files[:quotas.max_files]

    for rel_path in py_files:
        parsed = parse_python_file(repo_root, rel_path)
        graph.add_parsed_file(parsed)
        if len(graph.nodes) >= quotas.max_nodes:
            graph.errors.append(f"Node count exceeded max {quotas.max_nodes}")
            break

    return graph
