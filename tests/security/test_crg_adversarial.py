"""Adversarial CRG symbol injection tests — verify CRG handles malicious input safely."""

import os
import sys
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from synthesis.packages.codegraph.graph_store import CodeGraph
from synthesis.packages.codegraph.python_ast_parser import GraphNode, parse_python_file
from synthesis.packages.codegraph.crg import propagate_change


class TestCRGAdversarial:
    """Tests that CRG handles adversarial input safely."""

    def _make_graph_with_symbol(self, symbol_name: str, file_path: str = "src/malicious.py") -> CodeGraph:
        graph = CodeGraph()
        node = GraphNode(
            symbol_id=f"function:{file_path}.{symbol_name}",
            name=symbol_name,
            kind="function",
            file_path=file_path,
            line_number=1,
        )
        graph.nodes[node.symbol_id] = node
        graph.files[file_path] = type('obj', (object,), {'errors': []})()
        return graph

    def test_crg_with_import_injection(self):
        graph = self._make_graph_with_symbol("__import__")
        report = propagate_change(graph, "__import__")
        assert report.changed_symbol_id
        assert report.symbol_name == "__import__"

    def test_crg_with_eval_injection(self):
        graph = self._make_graph_with_symbol("eval")
        report = propagate_change(graph, "eval")
        assert report.symbol_name == "eval"

    def test_crg_with_exec_injection(self):
        graph = self._make_graph_with_symbol("exec")
        report = propagate_change(graph, "exec")
        assert report.symbol_name == "exec"

    def test_crg_with_subclasses_injection(self):
        graph = self._make_graph_with_symbol("__subclasses__")
        report = propagate_change(graph, "__subclasses__")
        assert report.symbol_name == "__subclasses__"

    def test_crg_with_system_injection(self):
        graph = self._make_graph_with_symbol("system")
        report = propagate_change(graph, "system")
        assert report.symbol_name == "system"

    def test_crg_with_sql_injection_like(self):
        graph = self._make_graph_with_symbol("normalize_token'; DROP TABLE --")
        report = propagate_change(graph, "normalize_token")
        assert report.symbol_name == "normalize_token'; DROP TABLE --"

    def test_crg_with_very_long_input(self):
        graph = self._make_graph_with_symbol("normalize_token")
        long_input = "normalize_token" + "A" * 100000
        report = propagate_change(graph, long_input)
        assert report.confidence >= 0.0

    def test_crg_with_empty_input(self):
        graph = self._make_graph_with_symbol("normalize_token")
        report = propagate_change(graph, "")
        assert report.confidence == 0.0

    def test_crg_with_only_special_chars(self):
        graph = self._make_graph_with_symbol("!@#$%^&*()")
        report = propagate_change(graph, "!@#$%^&*()")
        assert report.symbol_name == "!@#$%^&*()"

    def test_crg_with_no_matching_symbols(self):
        graph = self._make_graph_with_symbol("foo")
        report = propagate_change(graph, "nonexistent_symbol_xyz")
        assert report.confidence == 0.0
        assert report.errors
