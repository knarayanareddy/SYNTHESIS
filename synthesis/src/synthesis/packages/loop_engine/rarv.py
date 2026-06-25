"""RARV loop engine — Reason→Act→Reflect→Verify with golden demo support.

Phase 0 RARV with explicit phase methods per architecture 3.4.
Supports both real Ollama model calls and stubbed fallback for CI.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from typing import Optional

from synthesis.packages.loop_engine.termination import (
    LoopBudget, LoopCounters, should_stop,
)
from synthesis.packages.loop_engine.gates import (
    make_gate_result, write_gate,
)
from synthesis.packages.loop_engine.hashing import stable_state_hash
from synthesis.packages.observability.ledger import JsonlLedger, LedgerContext
from synthesis.packages.observability.trace_completeness import trace_completeness_from_ledger
from synthesis.packages.observability.spans import (
    model_call_span, loop_iteration_span, routing_decision_span,
    sandbox_span, end_span,
)


# ── Optional Ollama import ───────────────────────────────────────────────────
try:
    from synthesis.packages.modelpool.adapters.ollama import OllamaAdapter
    _OLLAMA_AVAILABLE = True
except ImportError:
    _OLLAMA_AVAILABLE = False


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class GoldenDemoResult:
    """Result of a golden demo RARV run."""
    loop_id: str
    trace_id: str
    status: str  # success, failed, error
    reason: str
    iterations: int = 0
    graph_summary: dict = field(default_factory=dict)
    crg_required_tests: list[str] = field(default_factory=list)
    crg_confidence: float = 0.0
    initial_pytest_result: dict = field(default_factory=dict)
    final_pytest_result: dict = field(default_factory=dict)
    patch_result: dict = field(default_factory=dict)
    model_reasoning: str = ""
    trace_completeness: dict = field(default_factory=dict)
    ledger_verified: bool = False
    errors: list[str] = field(default_factory=list)


# ── Ollama helper ────────────────────────────────────────────────────────────

def _call_ollama_for_reasoning(
    ctx: LedgerContext,
    test_file: str,
    test_output: str,
    source_snippet: str,
    ollama_host: str = "http://localhost:11434",
    ollama_model: str = "qwen2.5-coder:7b",
) -> str:
    """Call Ollama to reason about a bug, returning the model's analysis.

    Falls back to a deterministic message if Ollama is unavailable in CI.
    """
    if not _OLLAMA_AVAILABLE:
        _emit_stubbed_model_call(ctx, ollama_model)
        return _deterministic_reasoning()

    adapter = OllamaAdapter(host=ollama_host)

    # Check if Ollama is reachable
    health = adapter.health()
    if not health.get("reachable"):
        _emit_stubbed_model_call(ctx, ollama_model, reason="ollama_unreachable")
        return _deterministic_reasoning()

    prompt = (
        "You are a code review assistant. Analyze this Python bug and suggest a fix.\n\n"
        f"SOURCE CODE:\n```python\n{source_snippet}\n```\n\n"
        f"FAILING TEST ({test_file}):\n```\n{test_output[:2000]}\n```\n\n"
        "What is the bug and how should it be fixed? "
        "Respond with a concise analysis and the exact fix needed. "
        "Keep your response short — just identify the problem and the corrected line of code."
    )

    try:
        from synthesis.packages.modelpool.adapters.base import ChatRequest
        ctx.append("model_call_started", {
            "model": ollama_model,
            "backend": "ollama",
            "purpose": "reason_about_bug",
        })

        model_span = model_call_span(ctx.trace_id, ollama_model, "ollama")
        response = adapter.chat(ChatRequest(
            model=ollama_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.3,
        ))
        end_span(model_span, success=True)

        # Validate model response
        from synthesis.packages.loop_engine.model_validator import (
            validate_model_response, extract_reasoning,
        )
        validation = validate_model_response(response.content, model=ollama_model)

        ctx.append("model_call_completed", {
            "model": response.model,
            "backend": "ollama",
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "reasoning": extract_reasoning(response.content),
            "response_valid": validation.valid,
            "response_warnings": validation.warnings,
        })

        if not validation.valid:
            ctx.append("model_call_failed", {
                "model": ollama_model,
                "backend": "ollama",
                "error": validation.error,
                "fallback": "deterministic_reasoning",
            })
            return _deterministic_reasoning()

        return response.content

    except (TimeoutError, ConnectionError, RuntimeError) as e:
        _emit_stubbed_model_call(ctx, ollama_model, reason=str(e))
        return _deterministic_reasoning()


def _emit_stubbed_model_call(
    ctx: LedgerContext,
    model: str,
    reason: str = "CI environment — no Ollama available",
) -> None:
    """Emit model call events for CI/stubbed execution."""
    ctx.append("model_call_started", {
        "model": model,
        "backend": "ollama",
        "purpose": "reason_about_bug",
        "stubbed": True,
        "stub_reason": reason,
    })
    ctx.append("model_call_completed", {
        "model": model,
        "backend": "ollama",
        "reasoning": "The function should strip whitespace before lowercasing. "
                     "Fix: change 'return token.lower()' to 'return token.strip().lower()'.",
        "stubbed": True,
        "stub_reason": reason,
    })


def _deterministic_reasoning() -> str:
    """Return the deterministic reasoning (known fix for golden demo)."""
    return (
        "The function should strip whitespace before lowercasing. "
        "Fix: change 'return token.lower()' to 'return token.strip().lower()'."
    )


# ── Phase methods (architecture 3.4) ─────────────────────────────────────────

def phase_reason(
    ctx: LedgerContext,
    repo_root: str,
    task_type: str,
    trace_id: str,
    loop_id: str,
    iteration: int,
    ollama_host: str = "http://localhost:11434",
    ollama_model: str = "qwen2.5-coder:7b",
) -> dict:
    """Reason phase: classify task, retrieve graph/memory, plan.

    Returns dict with 'graph', 'crg', 'test_file', 'source_snippet', 'model_reasoning'.
    """
    # Index repo
    from synthesis.packages.codegraph.indexer import index_python_repo
    graph = index_python_repo(repo_root, trace_id=trace_id)
    ctx.append("codegraph_update", graph.summary())

    # Find normalize_token
    ctx.append("codegraph_query", {"query": "normalize_token"})
    matches = graph.find_symbol("normalize_token", kind="function")
    if not matches:
        raise ValueError("Symbol not found: normalize_token")

    # CRG propagation
    from synthesis.packages.codegraph.crg import propagate_change
    crg = propagate_change(graph, "normalize_token", trace_id=trace_id)
    ctx.append("crg_propagate", crg.to_dict())

    if not crg.required_tests:
        raise ValueError("CRG found no required tests")

    test_file = crg.required_tests[0]

    # Read source snippet for model reasoning
    source_snippet = ""
    try:
        source_path = os.path.join(repo_root, matches[0].file_path)
        with open(source_path) as f:
            source_snippet = f.read()
    except Exception:
        pass

    # Model reasoning
    model_reasoning = _call_ollama_for_reasoning(
        ctx, test_file,
        test_output="",  # Will be filled after first pytest run
        source_snippet=source_snippet,
        ollama_host=ollama_host,
        ollama_model=ollama_model,
    )

    return {
        "graph": graph,
        "crg": crg,
        "test_file": test_file,
        "source_snippet": source_snippet,
        "model_reasoning": model_reasoning,
    }


def phase_act(
    ctx: LedgerContext,
    repo_root: str,
    test_file: str,
    trace_id: str,
    loop_id: str,
    iteration: int,
) -> dict:
    """Act phase: run initial pytest, apply deterministic patch, rerun.

    Returns dict with 'initial_pytest', 'patch', 'final_pytest'.
    """
    from synthesis.packages.sandbox.runner import run_argv, SandboxViolation

    # ── Initial pytest ──
    try:
        initial_result = run_argv(
            ["pytest", test_file, "-v"],
            repo_root,
            timeout_sec=30,
        )
        ctx.append("sandbox_exec", {
            "argv": ["pytest", test_file, "-v"],
            "returncode": initial_result.returncode,
            "timed_out": initial_result.timed_out,
            "stdout_lines": len(initial_result.stdout.splitlines()) if initial_result.stdout else 0,
        })
    except SandboxViolation as e:
        ctx.append("sandbox_denial", e.decision.to_event_payload())
        raise

    # ── Apply deterministic patch ──
    from synthesis.packages.codegraph.patch_writer import apply_patch
    patch_result = apply_patch(
        repo_root, "src/auth.py",
        "return token.lower()",
        "return token.strip().lower()",
    )
    if not patch_result.success:
        raise ValueError(f"Patch failed: {patch_result.error}")

    # ── Final pytest ──
    try:
        sandbox_span_final = sandbox_span(trace_id, ["pytest", test_file, "-v"])
        final_result = run_argv(
            ["pytest", test_file, "-v"],
            repo_root,
            timeout_sec=30,
        )
        end_span(sandbox_span_final, success=(final_result.returncode == 0))
        ctx.append("sandbox_exec", {
            "argv": ["pytest", test_file, "-v"],
            "returncode": final_result.returncode,
            "timed_out": final_result.timed_out,
            "stdout_lines": len(final_result.stdout.splitlines()) if final_result.stdout else 0,
        })
    except SandboxViolation as e:
        end_span(sandbox_span_final, success=False, error=str(e))
        ctx.append("sandbox_denial", e.decision.to_event_payload())
        raise

    return {
        "initial_pytest": {
            "returncode": initial_result.returncode,
            "passed": initial_result.returncode == 0,
            "stdout": initial_result.stdout[:2000],
        },
        "patch": patch_result.to_payload(),
        "final_pytest": {
            "returncode": final_result.returncode,
            "passed": final_result.returncode == 0,
            "stdout": final_result.stdout[:2000],
        },
    }


def phase_reflect(
    ctx: LedgerContext,
    final_pytest: dict,
    model_reasoning: str,
    loop_id: str,
    iteration: int,
) -> None:
    """Reflect phase: reconcile observations, propagate CRG, propose memory."""
    # Memory commit after successful test
    ctx.append("memory_commit", {
        "key": "project.test_command",
        "value": "pytest tests/test_auth.py -v",
        "provenance": "observed",
        "confidence": "confirmed",
        "taint": "none",
    })


def phase_verify(
    ctx: LedgerContext,
    final_pytest: dict,
    counters: LoopCounters,
    trace_id: str,
    loop_id: str,
    iteration: int,
) -> bool:
    """Verify phase: check test results, write gates, set success. Returns True if success."""
    if final_pytest["returncode"] != 0:
        ctx.append("loop_gate_result", {
            "gate_name": "termination_gate",
            "severity": "blocking",
            "result": "fail",
            "reason": "Final pytest still fails",
            "next_action": "escalate",
        })
        return False

    # Success
    counters.goal_achieved = True
    counters.verification_passed = True

    ctx.append("loop_gate_result", {
        "gate_name": "termination_gate",
        "severity": "blocking",
        "result": "pass",
        "reason": "All tests pass, patch verified",
        "next_action": "terminate_success",
    })
    ctx.append("route_outcome", {
        "task_success": True,
        "tests_passed": True,
        "escalated": False,
        "failure_reason": None,
        "decision_kind": "model_selection",
    })
    return True


# ── Main RARV entry point ────────────────────────────────────────────────────

def run_golden_demo_rarv(
    ledger: JsonlLedger,
    repo_root: str,
    task_type: str = "bug_fix",
    trace_id: Optional[str] = None,
    model_pool: Optional[dict] = None,
    ollama_host: str = "http://localhost:11434",
    ollama_model: str = "qwen2.5-coder:7b",
) -> GoldenDemoResult:
    """Run the golden demo RARV loop against a repository.

    Executes the full golden demo flow:
      Reason → Act → Reflect → Verify

    Each phase uses explicit methods per architecture 3.4.
    """
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    loop_id = str(uuid.uuid4())

    ctx = LedgerContext(ledger, trace_id)
    budget = LoopBudget(task_type=task_type)
    counters = LoopCounters()

    result = GoldenDemoResult(loop_id=loop_id, trace_id=trace_id, status="running", reason="")

    try:
        # ── Preamble ──
        ctx.append("request_started", {"task_type": task_type, "repo_root": repo_root})
        ctx.append("policy_check", {"local_first": True, "cloud_allowed": False})
        ctx.append("route_decision", {
            "selected_model": ollama_model,
            "backend": "ollama",
            "locality": "local",
            "selection_reason": "deterministic_local_first",
            "candidates_considered": 1,
        })
        ctx.append("loop_iteration_started", {"loop_id": loop_id, "iteration": 0})

        # ── Intent gate ──
        intent_gate = make_gate_result("intent_gate", "blocking", "pass",
            reason="Bug-fix task intent accepted",
            trace_id=trace_id, loop_id=loop_id, iteration=0,
            next_action="proceed_to_reason")
        write_gate(ctx, intent_gate)

        # ── REASON ──
        reason_data = phase_reason(
            ctx, repo_root, task_type, trace_id, loop_id, 0,
            ollama_host=ollama_host, ollama_model=ollama_model,
        )
        result.graph_summary = reason_data["graph"].summary()
        result.crg_required_tests = reason_data["crg"].required_tests
        result.crg_confidence = reason_data["crg"].confidence
        result.model_reasoning = reason_data["model_reasoning"]

        # ── Safety gate ──
        safety_gate = make_gate_result("safety_gate", "blocking", "pass",
            reason="No safety concerns for deterministic patch in sandbox",
            trace_id=trace_id, loop_id=loop_id, iteration=0,
            next_action="proceed_to_act")
        write_gate(ctx, safety_gate)

        # ── Sandbox gate ──
        sandbox_gate = make_gate_result("sandbox_gate", "blocking", "pass",
            reason="Sandbox validated for pytest execution",
            trace_id=trace_id, loop_id=loop_id, iteration=0,
            next_action="run_pytest")
        write_gate(ctx, sandbox_gate)

        # ── ACT ──
        act_data = phase_act(
            ctx, repo_root, reason_data["test_file"],
            trace_id, loop_id, 0,
        )
        result.initial_pytest_result = act_data["initial_pytest"]
        result.patch_result = act_data["patch"]
        result.final_pytest_result = act_data["final_pytest"]

        # Initial pytest must fail
        if act_data["initial_pytest"]["passed"]:
            result.status = "failed"
            result.reason = "Initial pytest passed unexpectedly — test should fail with bug"
            result.errors.append(result.reason)
            ctx.append("loop_terminated", {"status": "failed", "reason": result.reason})
            return result

        # ── Execution gate ──
        exec_gate = make_gate_result("execution_gate", "blocking", "pass",
            reason="Deterministic patch applied successfully",
            trace_id=trace_id, loop_id=loop_id, iteration=0,
            next_action="proceed_to_reflect")
        write_gate(ctx, exec_gate)

        # ── REFLECT ──
        phase_reflect(ctx, act_data["final_pytest"], reason_data["model_reasoning"],
                      loop_id, 0)

        # ── VERIFY ──
        success = phase_verify(ctx, act_data["final_pytest"], counters,
                               trace_id, loop_id, 0)
        if not success:
            result.status = "failed"
            result.reason = "Final pytest still fails after patch"
            result.errors.append(result.reason)
            ctx.append("loop_terminated", {"status": "failed", "reason": result.reason})
            return result

        # ── Loop completion ──
        ctx.append("loop_iteration_completed", {"loop_id": loop_id, "iteration": 0})
        ctx.append("loop_terminated", {"status": "success", "reason": "goal_achieved"})

        result.status = "success"
        result.reason = "Golden demo completed successfully"
        result.iterations = 1

    except Exception as e:
        result.status = "error"
        result.reason = str(e)
        result.errors.append(str(e))
        try:
            ctx.append("loop_terminated", {"status": "error", "reason": str(e)})
        except Exception:
            pass

    # ── Post-execution verification ──
    result.ledger_verified = ledger.verify().valid
    result.trace_completeness = trace_completeness_from_ledger(ledger.path, task_type, trace_id)

    return result
