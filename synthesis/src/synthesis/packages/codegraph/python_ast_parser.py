"""Python AST parser (Graphify-lite) — parses Python files into a graph."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

PARSER_VERSION = "python-ast-v1"


@dataclass
class GraphNode:
    """A node in the code graph representing a symbol."""
    symbol_id: str
    name: str
    kind: str  # function, class, method, module, variable
    file_path: str
    line_number: int
    docstring: Optional[str] = None
    taint: str = "tool_observed"

    def to_dict(self) -> dict:
        return {
            "symbol_id": self.symbol_id,
            "name": self.name,
            "kind": self.kind,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "docstring": self.docstring,
            "taint": self.taint,
        }


@dataclass
class GraphEdge:
    """A directed edge between two nodes."""
    source_id: str
    target_id: str
    edge_type: str  # calls, imports, inherits, contains
    line_number: int
    best_effort: bool = False

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type,
            "line_number": self.line_number,
            "best_effort": self.best_effort,
        }


@dataclass
class ParsedFile:
    """Result of parsing a single Python file."""
    file_path: str
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    call_edges_best_effort: bool = True


# ── Python AST Visitor ────────────────────────────────────────────────────────

class _GraphifyVisitor(ast.NodeVisitor):
    """AST visitor that extracts functions, classes, methods, and calls."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.nodes: list[GraphNode] = []
        self.edges: list[GraphEdge] = []
        self._current_class: Optional[str] = None
        self._module_name = Path(file_path).stem

    def _symbol_id(self, name: str, kind: str) -> str:
        return f"{kind}:{self.file_path}.{name}"

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        class_id = self._symbol_id(node.name, "class")
        module_id = self._symbol_id(self._module_name, "module")
        self.nodes.append(GraphNode(
            symbol_id=class_id, name=node.name, kind="class",
            file_path=self.file_path, line_number=node.lineno,
            docstring=ast.get_docstring(node),
        ))
        self.edges.append(GraphEdge(module_id, class_id, "contains", node.lineno))

        prev_class = self._current_class
        self._current_class = class_id
        self.generic_visit(node)
        self._current_class = prev_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self._current_class:
            kind = "method"
            func_id = self._symbol_id(f"{Path(self.file_path).stem}.{node.name}", "method")
            self.edges.append(GraphEdge(self._current_class, func_id, "contains", node.lineno))
        else:
            kind = "function"
            func_id = self._symbol_id(node.name, "function")

        self.nodes.append(GraphNode(
            symbol_id=func_id, name=node.name, kind=kind,
            file_path=self.file_path, line_number=node.lineno,
            docstring=ast.get_docstring(node),
        ))

        # Find calls within the function body
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                target_name = self._resolve_call_target(child)
                if target_name:
                    target_id = self._symbol_id(target_name, "function")
                    self.edges.append(GraphEdge(
                        func_id, target_id, "calls", child.lineno,
                        best_effort=True,
                    ))

    def _resolve_call_target(self, node: ast.Call) -> Optional[str]:
        """Best-effort call target resolution."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def parse_python_file(
    repo_root: str,
    file_path: str,
    taint: str = "tool_observed",
) -> ParsedFile:
    """Parse a single Python file into a ParsedFile graph."""
    from synthesis.packages.sandbox.runner import canonicalize_workspace_path

    full_path = canonicalize_workspace_path(repo_root, file_path)
    path = Path(full_path)

    if not path.exists():
        return ParsedFile(file_path=file_path, errors=[f"File not found: {full_path}"])
    if not path.suffix == ".py":
        return ParsedFile(file_path=file_path, errors=[f"Not a Python file: {file_path}"])

    try:
        source = path.read_text()
        tree = ast.parse(source)
    except SyntaxError as e:
        return ParsedFile(file_path=file_path, errors=[f"Syntax error: {e}"])
    except Exception as e:
        return ParsedFile(file_path=file_path, errors=[f"Parse error: {e}"])

    visitor = _GraphifyVisitor(file_path)
    visitor.visit(tree)

    for node in visitor.nodes:
        node.taint = taint

    return ParsedFile(
        file_path=file_path,
        nodes=visitor.nodes,
        edges=visitor.edges,
        call_edges_best_effort=True,
    )
