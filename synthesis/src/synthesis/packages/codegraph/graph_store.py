"""In-memory code graph store."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict
from synthesis.packages.codegraph.python_ast_parser import (
    GraphNode, GraphEdge, ParsedFile,
)


@dataclass
class CodeGraph:
    """In-memory store for parsed code graph nodes and edges."""
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)
    files: dict[str, ParsedFile] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def add_parsed_file(self, parsed: ParsedFile) -> None:
        """Add a parsed file's nodes and edges to the graph."""
        self.files[parsed.file_path] = parsed
        if parsed.errors:
            self.errors.extend(parsed.errors)
        for node in parsed.nodes:
            self.nodes[node.symbol_id] = node
        self.edges.extend(parsed.edges)

    def find_symbol(self, name: str, kind: str = "function") -> list[GraphNode]:
        """Find all symbols matching a name and kind."""
        results = []
        for node in self.nodes.values():
            if node.name == name and node.kind == kind:
                results.append(node)
        return results

    def get_callers(self, symbol_id: str) -> list[str]:
        """Return all symbols that call the given symbol."""
        callers = []
        for edge in self.edges:
            if edge.target_id == symbol_id and edge.edge_type == "calls":
                callers.append(edge.source_id)
        return callers

    def get_callees(self, symbol_id: str) -> list[str]:
        """Return all symbols called by the given symbol."""
        callees = []
        for edge in self.edges:
            if edge.source_id == symbol_id and edge.edge_type == "calls":
                callees.append(edge.target_id)
        return callees

    def summary(self) -> dict:
        """Return a summary of the graph."""
        node_counts: dict[str, int] = defaultdict(int)
        for n in self.nodes.values():
            node_counts[n.kind] += 1
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "total_files": len(self.files),
            "node_kinds": dict(node_counts),
            "errors": len(self.errors),
        }
