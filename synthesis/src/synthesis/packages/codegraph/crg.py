"""CRG (Change-Required-Graph) — propagates changes to identify required tests."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from synthesis.packages.codegraph.graph_store import CodeGraph, GraphNode


@dataclass
class CRGReport:
    """CRG propagation report for a changed symbol."""
    trace_id: str
    changed_symbol_id: str
    symbol_name: str
    required_tests: list[str] = field(default_factory=list)
    affected_symbols: list[str] = field(default_factory=list)
    confidence: float = 0.0
    errors: list[str] = field(default_factory=list)
    call_edges_best_effort: bool = True

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "changed_symbol_id": self.changed_symbol_id,
            "symbol_name": self.symbol_name,
            "required_tests": self.required_tests,
            "affected_symbols": self.affected_symbols,
            "confidence": self.confidence,
            "errors": self.errors,
            "call_edges_best_effort": self.call_edges_best_effort,
        }


def _infer_test_file(file_path: str) -> Optional[str]:
    """Heuristic: given src/X/foo.py, look for tests/test_X.py or tests/X/test_foo.py."""
    parts = file_path.replace("\\", "/").split("/")

    # Look for tests/test_<filename>.py at the tests root
    filename = parts[-1]
    basename = filename.replace(".py", "")
    candidates = [
        f"tests/test_{basename}.py",
    ]

    # Also try: tests/<rest>/test_<filename>.py
    if len(parts) > 1 and parts[0] == "src":
        subpath = "/".join(parts[1:-1])
        candidates.append(f"tests/{subpath}/test_{basename}.py" if subpath else f"tests/test_{basename}.py")

    return candidates[0] if candidates else None


def _propagate_callers(graph: CodeGraph, symbol_id: str, visited: set[str] | None = None) -> set[str]:
    """Recursively find all callers of a symbol."""
    if visited is None:
        visited = set()
    if symbol_id in visited:
        return visited
    visited.add(symbol_id)
    for edge in graph.edges:
        if edge.target_id == symbol_id and edge.edge_type == "calls":
            _propagate_callers(graph, edge.source_id, visited)
    return visited


def propagate_change(
    graph: CodeGraph,
    changed_symbol_contains: str,
    trace_id: str = "",
    ledger=None,
) -> CRGReport:
    """Propagate a change from a symbol to identify required tests.

    Args:
        graph: The CodeGraph to analyze.
        changed_symbol_contains: Substring match for symbol name (e.g., "normalize_token").
        trace_id: Trace identifier.
        ledger: Optional ledger for event emission.

    Returns:
        CRGReport with required_tests and affected_symbols.
    """
    # Reject empty or whitespace-only input early
    if not changed_symbol_contains or not changed_symbol_contains.strip():
        return CRGReport(
            trace_id=trace_id,
            changed_symbol_id="",
            symbol_name=changed_symbol_contains,
            errors=["Empty or whitespace-only changed_symbol_contains"],
            confidence=0.0,
        )

    # Find matching symbols
    matches: list[GraphNode] = []
    for node in graph.nodes.values():
        if changed_symbol_contains in node.name:
            matches.append(node)

    if not matches:
        return CRGReport(
            trace_id=trace_id,
            changed_symbol_id="",
            symbol_name=changed_symbol_contains,
            errors=[f"No symbol matching '{changed_symbol_contains}' found"],
            confidence=0.0,
        )

    # Use the first match
    node = matches[0]
    affected = _propagate_callers(graph, node.symbol_id)

    # Collect affected symbols
    affected_symbols = [
        n.symbol_id for n in graph.nodes.values()
        if n.symbol_id in affected and n.symbol_id != node.symbol_id
    ]

    # Infer test files
    required_tests: list[str] = []
    test_file = _infer_test_file(node.file_path)
    if test_file:
        required_tests.append(test_file)

    # Also look for test files among affected
    for sym_id in affected_symbols:
        for n in graph.nodes.values():
            if n.symbol_id == sym_id:
                tf = _infer_test_file(n.file_path)
                if tf and tf not in required_tests:
                    required_tests.append(tf)

    # Confidence calculation based on graph completeness
    if required_tests and not graph.errors:
        confidence = 0.85
    elif required_tests:
        confidence = 0.65
    else:
        confidence = 0.1

    return CRGReport(
        trace_id=trace_id,
        changed_symbol_id=node.symbol_id,
        symbol_name=node.name,
        required_tests=required_tests,
        affected_symbols=affected_symbols,
        confidence=confidence,
        call_edges_best_effort=True,
    )
