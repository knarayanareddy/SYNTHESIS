# SYNTHESIS — Canonical Architecture Document v1.0
# Extracted from Rounds 1–13
# Status: FROZEN — no changes without explicit human approval
# Last updated: 2026-06-25

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 1 — ARCHITECTURAL IDENTITY & NON-NEGOTIABLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. **LOCAL-FIRST ARCHITECTURAL IDENTITY**  
   Rule: SYNTHESIS must function fully with zero API keys configured, using local inference as the default execution path.  
   Violation: Any feature requiring Anthropic, OpenAI, Google, OpenRouter, LiteLLM cloud, or any other cloud API for core functionality violates the architecture.  
   Status: ✅ IMPLEMENTED for discovery/router defaults; 📋 DECIDED for full feature parity.

2. **ALL FOUR LOCAL BACKENDS ARE FIRST-CLASS**  
   Rule: Ollama, LM Studio, Jan, and MLX are first-class local backends by defined standard: discovery, health, lifecycle, capability index, routing eligibility, tracing, error normalization, cancellation/non-cancellable reason, conformance tests, and local/remote classification.  
   Violation: Treating Ollama as the only real backend or misclassifying Jan remote models as local violates the architecture.  
   Status: ✅ IMPLEMENTED for endpoint discovery representation; 📋 DECIDED for full conformance parity.

3. **BYOK CLOUD IS STRICTLY OPT-IN**  
   Rule: Cloud backends may be used only when BYOK credentials exist, cloud is enabled, the user explicitly approves the specific task/cloud call, and cost ceiling allows it.  
   Violation: Selecting a cloud or remote model by default, silently, or as normal fallback violates the architecture.  
   Status: ✅ IMPLEMENTED for router rejection of remote candidates; 📋 DECIDED for full BYOK provider implementation.

4. **DETERMINISTIC LOCAL-FIRST ROUTING IS THE PERMANENT SAFE FALLBACK**  
   Rule: Learned routing may augment SYNTHESIS only after offline validation, but deterministic local-first routing must remain permanently available.  
   Violation: Replacing deterministic routing with a learned router that cannot fall back safely violates the architecture.  
   Status: ✅ IMPLEMENTED.

5. **LOOPS MUST BE BOUNDED**  
   Rule: Every loop must enforce explicit task-specific max iterations, model-call caps, tool-call caps, world-simulation caps, error caps, repeated-state stops, same-failed-gate stops, wall-clock limits, and safety stops.  
   Violation: Any autonomous loop without hard termination limits violates the architecture.  
   Status: ✅ IMPLEMENTED for minimal RARV skeleton.

6. **OBSERVABILITY IS STRUCTURAL**  
   Rule: Every autonomous decision must be ledgered through the hash-chained JSONL ledger and later correlated with OpenTelemetry spans.  
   Violation: Any model call, routing decision, loop gate, memory operation, sandbox action, approval transition, or safety event that executes without trace/ledger visibility violates the architecture.  
   Status: ✅ IMPLEMENTED for ledger/event registry; 📋 DECIDED for full OpenTelemetry span wrappers.

7. **REDACTION BEFORE PERSISTENCE**  
   Rule: Ledger events must be redacted before disk persistence and must fail if secret values remain after redaction.  
   Violation: Persisting raw API keys, passwords, authorization values, or tokens violates the architecture.  
   Status: ✅ IMPLEMENTED.

8. **SANDBOX BEFORE AUTONOMY**  
   Rule: Tool and shell execution must be argv-only, sandbox-validated, workspace-confined, and path-canonicalized before execution.  
   Violation: Running shell strings, using `shell=True`, allowing path escape, or following symlink escapes violates the architecture.  
   Status: ✅ IMPLEMENTED for argv runner and tests; 📋 DECIDED for full process resource limits.

9. **BLOCKING GATES CANNOT BE SKIPPED**  
   Rule: A blocking gate cannot return `skip_with_reason` unless explicit policy allows blocking-gate skips.  
   Violation: Skipping `safety_gate`, `sandbox_gate`, `execution_gate`, or other blocking gates without explicit policy violates the loop design.  
   Status: ✅ IMPLEMENTED.

10. **WORLD MODEL IS ADVISORY ONLY**  
    Rule: The world model may predict, warn, recommend sandboxing, and produce divergence signals, but may never approve correctness, bypass tests, bypass verifier, bypass safety, approve destructive actions, or commit memory alone.  
    Violation: Treating world-model prediction as proof of correctness or authorization violates the architecture.  
    Status: ✅ IMPLEMENTED as constants; 📋 DECIDED for full world-model execution.

11. **RUNTIME SELF-EVOLUTION IS DISABLED IN PHASE 0**  
    Rule: Prompt, workflow, router-policy, safety-policy, cloud-policy, sandbox-policy, max-cap, and audit-policy mutation must be blocked at runtime.  
    Violation: Any runtime self-modification of safety, routing, prompt, workflow, caps, audit, or cloud behavior violates Phase 0.  
    Status: 📋 DECIDED; constants exist, enforcement function tests pending.

12. **CODEBASE INTELLIGENCE IS INTEGRATED INTO THE LOOP**  
    Rule: Python Graphify-lite and CRG must provide structural scope for golden-demo bug-fix verification.  
    Violation: Performing generic text-only code review/testing when graph and CRG data are available violates the accepted MVP path.  
    Status: ✅ IMPLEMENTED for Python AST graph and CRG golden-demo mapping.

13. **GOLDEN DEMO IS THE PRIMARY PHASE 0 SUCCESS PATH**  
    Rule: Phase 0 success is measured by the local Python auth bug-fix golden demo using local routing, graph/CRG scope, sandboxed tests, deterministic patching, ledger trace, and trace completeness.  
    Violation: Expanding JS/TS, full Langfuse, learned routing, full conductor, or model patching before the golden path passes violates Phase 0 scope.  
    Status: 📋 DECIDED; partially implemented.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 2 — PACKAGE & FILE STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```text
synthesis/
├── README.md                                      ✅ — Phase 0 overview and quick-start.
├── pyproject.toml                                 ✅ — Python project metadata and dependencies.
├── Makefile                                       ✅ — install/lint/typecheck/test/security/conformance/release-gate commands.
├── .env.example                                   ✅ — local-first environment defaults.
├── docker/
│   ├── docker-compose.phase0.yml                  ✅ — Phase 0 local Docker Compose stack.
│   ├── Dockerfile.api                             ✅ — API container stub.
│   ├── Dockerfile.worker                          ✅ — worker container stub.
│   └── Dockerfile.dashboard                       ✅ — dashboard container stub.
├── .github/
│   ├── workflows/ci.yml                           ✅ — CI workflow; CI smoke does not require Ollama.
│   └── pull_request_template.md                   ✅ — Phase 0 PR checklist.
├── schemas/
│   ├── synthesis_state.schema.json                ✅ — canonical state schema.
│   ├── ledger_event.schema.json                   ✅ — hash-chained ledger event schema.
│   ├── routing_decision.schema.json               ✅ — route decision schema.
│   ├── route_outcome.schema.json                  ✅ — route outcome schema.
│   ├── memory_commit.schema.json                  ✅ — memory commit/quarantine/rollback schema.
│   ├── crg_report.schema.json                     ✅ — CRG report schema.
│   ├── approval.schema.json                       ✅ — task-scoped approval schema.
│   ├── gate_result.schema.json                    ✅ — loop gate result schema.
│   ├── world_transition.schema.json               ✅ — world-model transition schema.
│   ├── model_capability.schema.json               ✅ — model capability schema.
│   ├── sandbox_event.schema.json                  ✅ — sandbox allow/deny event schema.
│   ├── memory_retrieval.schema.json               ✅ — memory retrieval schema.
│   ├── procedural_memory_diff.schema.json         📋 — procedural memory diff schema placeholder.
│   ├── ledger_checkpoint.schema.json              📋 — ledger checkpoint schema placeholder.
│   ├── dashboard_data.schema.json                 📋 — dashboard data contract placeholder.
│   ├── escalation_summary.schema.json             📋 — escalation summary schema placeholder.
│   ├── graph_quota_config.schema.json             ✅ — graph quota config schema.
│   ├── stale_graph_event.schema.json              ✅ — stale graph fallback event schema.
│   ├── benchmark_result_manifest.schema.json      ✅ — benchmark result manifest schema.
│   └── event_type_registry.schema.json            📋 — event-type registry schema placeholder.
├── apps/
│   ├── api/main.py                                ✅ — FastAPI `/v1/models`, `/synthesis/model-pool`, `/synthesis/backend-health`.
│   ├── worker/main.py                             ✅ — worker stub.
│   ├── cli/main.py                                ✅ — Typer CLI: doctor, release-gate, run, dashboard, ledger, benchmark.
│   └── dashboard_static/
│       ├── index.html                             ✅ — static dashboard stub.
│       └── dashboard.js                           ✅ — static dashboard stub script.
├── packages/
│   ├── policy/constants.py                        ✅ — circuit breakers, mutation blocklist, command allow/deny lists.
│   ├── policy/immutable.py                        ✅ — immutable policy key enforcement.
│   ├── modelpool/timeouts.py                      ✅ — backend timeout constants.
│   ├── modelpool/types.py                         ✅ — backend status/maturity dataclasses.
│   ├── modelpool/discovery.py                     ✅ — Ollama/LM Studio/Jan/MLX probing.
│   ├── modelpool/adapters/base.py                 ✅ — `ModelBackendAdapter`, `ChatRequest`, `ChatResponse`, `StreamChunk`.
│   ├── modelpool/adapters/ollama.py               ✅ — Ollama Phase 0 adapter.
│   ├── router/deterministic.py                    ✅ — local-first deterministic router.
│   ├── router/scoring.py                          ✅ — route score loading/calculation.
│   ├── router/outcomes.py                         ✅ — route outcome writer.
│   ├── router/sanitize.py                         ✅ — backend model-name sanitizer.
│   ├── router/config/routing_weights_v1.json      ✅ — routing score weights.
│   ├── loop_engine/termination.py                 ✅ — `LoopBudget`, `LoopCounters`, `should_stop()`.
│   ├── loop_engine/gates.py                       ✅ — `GateResult`, `BLOCKING_GATES`, `make_gate_result()`, `write_gate()`.
│   ├── loop_engine/hashing.py                     ✅ — deterministic loop state hashing.
│   ├── loop_engine/rarv.py                        ✅ — minimal RARV skeleton.
│   ├── sandbox/runner.py                          ✅ — argv-only sandbox runner and path validation.
│   ├── world_model/constants.py                   ✅ — advisory-only prohibitions and thresholds.
│   ├── codegraph/python_ast_parser.py             ✅ — Python AST parser.
│   ├── codegraph/graph_store.py                   ✅ — in-memory code graph.
│   ├── codegraph/indexer.py                       ✅ — Python repo indexer with canonical path validation.
│   ├── codegraph/crg.py                           ✅ — CRG change propagation.
│   ├── memory/hashing.py                          ✅ — deterministic memory commit hash helper.
│   ├── observability/event_registry.py            ✅ — allowed event types and non-sampled event set.
│   ├── observability/redaction.py                 ✅ — redaction-before-persistence.
│   ├── observability/ledger.py                    ✅ — hash-chained JSONL ledger.
│   ├── observability/context.py                   ✅ — `LedgerContext`.
│   ├── observability/trace_completeness.py        ✅ — trace completeness scoring and ledger reader.
│   ├── approvals/policy.py                        ✅ — `Approval`, `approval_allows()`.
│   └── approvals/events.py                        ✅ — approval transition ledger helper.
├── tests/                                        ✅ — unit/security/conformance/integration fixture structure.
└── docs/
    ├── release_gates.md                           ✅ — Phase 0 release gates.
    └── golden_demo.md                             ✅ — golden demo specification.
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 3 — COMPONENT SPECIFICATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 3.1 Local Backend Discovery & Model Pool
Status: ✅ IMPLEMENTED for discovery; 📋 DECIDED for full conformance.

Purpose: Discover local inference backends, classify backend health/lifecycle/maturity/locality, expose ModelPool state to router/API, and avoid cloud by default.

Key Types / Classes / Functions:
- `ModelBackendAdapter` — protocol for backend adapters.
- `ChatRequest` — model, messages, max_tokens, temperature, stream.
- `ChatResponse` — model, content, token counts, raw response.
- `StreamChunk` — streaming delta, finish_reason, raw.
- `OllamaAdapter` — Phase 0 Ollama adapter.
- `OllamaAdapter.discover()` — probes `GET http://localhost:11434/api/tags`.
- `OllamaAdapter.health()` — returns backend health fields.
- `OllamaAdapter.list_models()` — returns discovered capabilities.
- `OllamaAdapter.capability_index()` — returns model capability list.
- `OllamaAdapter.chat()` — calls `POST /api/chat`.
- `OllamaAdapter.embeddings()` — calls `POST /api/embeddings`.
- `OllamaAdapter.cancel()` — returns non-cancellable reason.
- `discover_model_pool(ledger=None)` — probes Ollama, LM Studio, Jan, MLX.
- `BACKEND_TIMEOUTS_SEC` — backend health/discovery timeout constants.
- `BackendProbe` — backend discovery result dataclass.

Behavior Rules:
1. Ollama is full adapter maturity in Phase 0.
2. LM Studio, Jan, and MLX are partial/discovery adapters in Phase 0.
3. No backend may auto-pull or auto-download models.
4. Jan locality is `unknown` unless proven local.
5. MLX is `unsupported_platform` unless macOS arm64/aarch64.
6. `/v1/models` must not expose Jan models as local unless Jan model locality is local.
7. Discovery must not fail when local servers are absent.
8. Adapter maturity must be surfaced in `/synthesis/model-pool`.

Interfaces:
- Input: backend endpoints and optional `LedgerContext`.
- Output: `{"backends": [...], "cloud_enabled": false, "local_first": true, "degraded_notes": [...]}`.

Known Constraints:
- Backend timeout default is 1.5 seconds for Ollama, LM Studio, Jan, MLX.
- Ollama `context_window_safe` default is 8192 in current capability mapping.
- Ollama streaming is explicit `NotImplementedError`; `streaming_supported=false`.

⚠️ UNDERSPECIFIED AREAS:
- Live Ollama chat conformance is decided but not implemented.
- Backend version capture is decided but not implemented.
- Latency/tokens-per-second instrumentation is decided but not implemented.

---

### 3.2 Intelligent Router
Status: ✅ IMPLEMENTED.

Purpose: Select the best local selectable model using deterministic local-first routing and ledger route decisions/outcomes.

Key Types / Classes / Functions:
- `TaskSpec` — task_type, agent_role, required_capability, trace_id.
- `RoutingResult` — route decision object with selected model/backend and rejection details.
- `select_model(model_pool, task, ledger=None)` — deterministic local-first selector.
- `load_routing_weights()` — loads `routing_weights_v1.json`.
- `score_model()` — computes route score components.
- `weighted_score()` — applies configured routing weights.
- `sanitize_model_name()` — sanitizes backend-provided model names.

Behavior Rules:
1. Non-local candidates are rejected by default.
2. Partial/discovery-only adapters are rejected for chat in Phase 0.
3. Non-serving models are rejected.
4. Missing chat or embedding capability rejects the candidate for the corresponding task.
5. If no candidate remains, router returns no-model-available and ledgers `route_decision` and `route_outcome` when `LedgerContext` is supplied.
6. Cloud gate result is `not_allowed` unless explicitly approved; cloud routing is not implemented in Phase 0.
7. Routing weights are versioned as `router-score-v1`.

Interfaces:
- Input: ModelPool dict, `TaskSpec`, optional `LedgerContext`.
- Output: `RoutingResult`.

Known Constraints:
- `SELECTABLE_MATURITY = {"full"}`.
- `SELECTABLE_LIFECYCLE = {"serving", "warm"}`.
- Latency/history/verifier/divergence scores are placeholder `0.5` until observed metrics exist.

⚠️ UNDERSPECIFIED AREAS:
- Historical performance decay is decided conceptually but not implemented.
- MasRouter feature logging is decided but not implemented.
- Learned router deployment is deferred.

---

### 3.3 Ledger (Hash-Chained JSONL)
Status: ✅ IMPLEMENTED.

Purpose: Persist redacted, schema-validated, hash-chained JSONL events for auditability, replay, debugging, and future learning.

Key Types / Classes / Functions:
- `JsonlLedger` — append/verify hash-chained JSONL ledger.
- `JsonlLedger.append(event_type, trace_id, payload)` — validates event type, redacts, hashes, schema-validates, appends.
- `JsonlLedger.verify()` — checks JSON validity and hash chain.
- `LedgerVerificationResult` — verification result object.
- `canonical_json()` — deterministic JSON serialization.
- `event_hash()` — SHA-256 event hash.
- `LedgerContext` — request-scoped helper around `JsonlLedger`.

Behavior Rules:
1. Event type must be registered before append.
2. Redaction must occur before persistence.
3. Ledger append must fail if secret values remain after redaction.
4. `hash_prev` links to previous event hash.
5. `hash_self` is computed over canonical event JSON with blank `hash_self`.
6. Verification fails at first invalid JSON, `hash_prev` mismatch, or `hash_self` mismatch.

Interfaces:
- Input: event_type, trace_id, payload.
- Output: persisted event dict.

Known Constraints:
- `schema_version` is `"1.0"`.
- `redaction_applied` must be `true`.
- Ledger writes are append-only through `JsonlLedger.append()`.

⚠️ UNDERSPECIFIED AREAS:
- Ledger checkpoint writing/recovery is decided but not implemented.
- OpenTelemetry span correlation is decided but not implemented.

---

### 3.4 Loop Engine (RARV)
Status: ✅ IMPLEMENTED as minimal skeleton; 📋 DECIDED for full phase methods.

Purpose: Execute bounded Reason→Act→Reflect→Verify workflows with local routing, gate ledgering, route outcomes, and deterministic termination.

Key Types / Classes / Functions:
- `run_minimal_rarv(ctx, model_pool, task_type="bug_fix")` — minimal bounded loop skeleton.
- `MinimalLoopResult` — loop_id, status, reason, iterations, selected_model.

Behavior Rules:
1. Minimal RARV starts with `request_started` and `policy_check`.
2. Minimal RARV writes `loop_iteration_started`.
3. Minimal RARV writes `intent_gate`.
4. Minimal RARV calls deterministic router for `agent_role="worker"`.
5. Minimal RARV writes `execution_gate`.
6. Minimal RARV writes `route_outcome`.
7. Minimal RARV writes `loop_iteration_completed` and `loop_terminated`.
8. Minimal RARV performs no code editing, no tool execution, and no model call.

Interfaces:
- Input: `LedgerContext`, ModelPool dict, task_type.
- Output: `MinimalLoopResult`.

Known Constraints:
- Minimal loop is a baseline and must not become the permanent full RARV architecture.
- Full RARV must later expose explicit `reason`, `act`, `reflect`, `verify` methods.

⚠️ UNDERSPECIFIED AREAS:
- Explicit phase methods are decided but not implemented.
- Safety gate, sandbox gate, and CRG integration are decided for golden demo but not in minimal loop.

---

### 3.5 Termination System
Status: ✅ IMPLEMENTED.

Purpose: Ensure no loop can run unbounded.

Key Types / Classes / Functions:
- `LoopBudget` — task_type and cap configuration.
- `LoopCounters` — runtime counters.
- `should_stop(budget, counters)` — stop condition evaluator.
- `MAX_ITERATIONS_BY_TASK` — task-specific iteration caps.

Behavior Rules:
1. Success stops when `goal_achieved` and `verification_passed` are true.
2. `safety_stop` stops immediately.
3. `iteration >= max_iterations` stops.
4. Model/tool/world simulation/error/repeated-state/same-failed-gate/wall-clock caps stop the loop.

Interfaces:
- Input: `LoopBudget`, `LoopCounters`.
- Output: `(bool, reason_string)`.

Known Constraints:
- Task-specific max iterations are fixed in `MAX_ITERATIONS_BY_TASK`.

⚠️ UNDERSPECIFIED AREAS:
- Cap mutation prevention is decided at policy level; full integration with runtime config is pending.

---

### 3.6 Gate System
Status: ✅ IMPLEMENTED.

Purpose: Represent, enforce, and ledger loop quality gates.

Key Types / Classes / Functions:
- `GateResult` — gate result dataclass.
- `make_gate_result()` — creates validated gate result.
- `write_gate(ctx, gate)` — ledgers gate result.
- `BLOCKING_GATES` — blocking gate set.

Behavior Rules:
1. Blocking gate skip is forbidden unless `policy_allows_blocking_skip=True`.
2. Gate results are ledgered as `loop_gate_result`.

Interfaces:
- Input: trace_id, loop_id, iteration, gate_name, severity, result, reason, next_action, evidence.
- Output: `GateResult` and ledger event.

Known Constraints:
- Gate severity is one of `blocking`, `warning`, `informational`.
- Gate result is one of `pass`, `fail`, `escalate`, `skip_with_reason`.

⚠️ UNDERSPECIFIED AREAS:
- Complete full-loop gate order is decided but not implemented in full RARV.

---

### 3.7 State Hashing
Status: ✅ IMPLEMENTED.

Purpose: Detect repeated loop states without using nondeterministic fields.

Key Types / Classes / Functions:
- `stable_state_hash(state)` — deterministic hash of selected state fields.
- `HASH_INCLUDED_FIELDS` — deterministic field set.

Behavior Rules:
1. Hash includes task_type, success_criteria, changed_file_digests, failed_gates, last_error_class, crg_digest, world_divergence_bucket.
2. Hash excludes timestamps, span IDs, token counts, latency, and model wording.

Interfaces:
- Input: state dict.
- Output: SHA-256 hex digest.

Known Constraints:
- `repeated_state_hash_count >= 2` stops the loop.

⚠️ UNDERSPECIFIED AREAS:
- Property-based hashing tests are partially decided; direct deterministic test exists.

---

### 3.8 Sandbox
Status: ✅ IMPLEMENTED.

Purpose: Safely execute approved local commands with argv-only semantics and workspace path confinement.

Key Types / Classes / Functions:
- `SandboxDecision` — allow/deny decision object.
- `SandboxDecision.to_event_payload()` — serializes sandbox event.
- `SandboxResult` — execution result.
- `SandboxViolation` — exception carrying denial decision.
- `canonicalize_workspace_path(workspace, candidate)` — path confinement.
- `validate_argv(argv, workspace, cwd=None)` — command validation.
- `run_argv(argv, workspace, cwd=None, timeout_sec=60)` — safe execution.
- `parse_shell_string_forbidden(command)` — always raises.

Behavior Rules:
1. Shell strings are forbidden.
2. `shell=False` is mandatory.
3. Commands must be allowlisted.
4. Denylisted commands are rejected.
5. Shell metacharacters are denied in argv.
6. Path-like args are canonicalized under workspace.
7. Path escape is rejected.
8. Symlink escape is rejected.
9. Environment is scrubbed to `PATH`.

Interfaces:
- Input: argv list, workspace, optional cwd, timeout.
- Output: `SandboxResult` or `SandboxViolation`.

Known Constraints:
- Network namespace enforcement is not implemented.
- Process resource limits beyond timeout are deferred.

⚠️ UNDERSPECIFIED AREAS:
- Repo-defined test command approval integration is decided but not implemented.

---

### 3.9 Approval System
Status: ✅ IMPLEMENTED.

Purpose: Represent narrow, task-scoped, expiring, one-use approvals and ledger approval transitions.

Key Types / Classes / Functions:
- `Approval` — approval dataclass.
- `approval_allows(approval, task_id, requested_action, now=None)` — approval validator.
- `ledger_approval(ctx, event_type, approval)` — ledgers approval transitions.

Behavior Rules:
1. Approval status must be `approved`.
2. `task_id` must exactly match.
3. `requested_action` must exactly match.
4. `uses < max_uses`.
5. Approval must not be expired.
6. Approval must not include immutable policy mutation attempt.
7. Default `max_uses` is 1.

Interfaces:
- Input: `Approval`, task_id, requested_action, optional now.
- Output: boolean allow/deny; ledger events for transitions.

Known Constraints:
- Approval lifecycle events are `approval_requested`, `approval_approved`, `approval_denied`, `approval_revoked`, `approval_expired`.

⚠️ UNDERSPECIFIED AREAS:
- Approval API endpoints are decided but not implemented.

---

### 3.10 Trace Completeness Scoring
Status: ✅ IMPLEMENTED.

Purpose: Compute whether required event types for a task trace are present.

Key Types / Classes / Functions:
- `REQUIRED_EVENTS_BY_TASK` — required event sets.
- `trace_completeness(task_type, event_types)` — computes score from list/set.
- `trace_completeness_from_ledger(path, task_type, trace_id=None)` — computes score from ledger file.

Behavior Rules:
1. Bug-fix trace completeness requires request, policy, route, codegraph, CRG, loop, gate, route outcome, and termination events.
2. Score is present-required count divided by total required count.
3. Missing required events must be reported.

Interfaces:
- Input: task_type and event types or ledger path.
- Output: dict with task_type, required, present, missing, score.

Known Constraints:
- Golden demo trace completeness must reach 1.0.

⚠️ UNDERSPECIFIED AREAS:
- Dashboard rendering of completeness is decided but not implemented.

---

### 3.11 Route Outcome Writer
Status: ✅ IMPLEMENTED.

Purpose: Persist post-routing outcome labels for replay, evaluation, and future learned routing.

Key Types / Classes / Functions:
- `write_route_outcome(ctx, decision, task_success, verifier_score=None, tests_passed=None, escalated=False, failure_reason=None)`.

Behavior Rules:
1. Route outcome is emitted as `route_outcome`.
2. Outcome includes task_success, verifier_score, tests_passed, safety_triggered, escalated, failure_reason.
3. No-model-available writes a confirmed failed route outcome.

Interfaces:
- Input: `LedgerContext`, `RoutingResult`, outcome fields.
- Output: ledger event.

Known Constraints:
- `decision_kind` is `model_selection`.

⚠️ UNDERSPECIFIED AREAS:
- Role-selection outcomes are schema-supported but runtime conductor not implemented.

---

### 3.12 Model Name Sanitizer
Status: ✅ IMPLEMENTED.

Purpose: Treat backend-provided model names as untrusted strings before UI/log display.

Key Types / Classes / Functions:
- `sanitize_model_name(name, max_len=160)`.

Behavior Rules:
1. Control characters are replaced with `�`.
2. `<` becomes `‹`.
3. `>` becomes `›`.
4. Output is truncated to max_len.

Interfaces:
- Input: string-like model name.
- Output: sanitized string.

Known Constraints:
- Intended for UI/log output.

⚠️ UNDERSPECIFIED AREAS:
- Full UI integration is pending.

---

### 3.13 Observability Backend
Status: ✅ IMPLEMENTED for JSONL ledger; ❌ DEFERRED for Langfuse default.

Purpose: Provide local-first event persistence, audit, trace completeness, and future replay substrate.

Key Types / Classes / Functions:
- `JsonlLedger`.
- `LedgerContext`.
- `ALLOWED_EVENT_TYPES`.
- `NON_SAMPLED_EVENT_TYPES`.
- `trace_completeness_from_ledger()`.

Behavior Rules:
1. JSONL ledger is Phase 0 default.
2. Langfuse local Docker is Phase 1 optional/default after Phase 0.
3. Stdout/JSONL must work without Langfuse.
4. Redaction happens before persistence.

Interfaces:
- Input: events from components.
- Output: hash-chained ledger file and trace completeness reports.

Known Constraints:
- OpenTelemetry span helpers are decided but not implemented.

⚠️ UNDERSPECIFIED AREAS:
- OpenTelemetry span names were decided but helper implementation is pending.
- Langfuse integration is deferred.

---

### 3.14 World Model
Status: 📋 DECIDED; constants implemented; execution deferred.

Purpose: Provide local advisory Terminal/SWE transition prediction and reconciliation for future divergence-aware loop control.

Key Types / Classes / Functions:
- `WORLD_MODEL_MAY_NOT`.
- `PER_DOMAIN_THRESHOLDS`.
- `WorldTransition` schema.
- Future: Terminal extractor, SWE extractor, predictor, reconciler.

Behavior Rules:
1. World model is advisory only.
2. Disallowed actions must be blocked before simulation.
3. Prediction may not bypass tests, verifier, safety, or memory approval.
4. Terminal and SWE are the only Phase 0 world-model domains.

Interfaces:
- Input: extracted Terminal/SWE state and planned action.
- Output: prediction, verdict, confidence, actual observation, divergence score.

Known Constraints:
- MVP calibration requires 50 Terminal transitions and 50 SWE transitions, with at least 20 negative/failure transitions total.

⚠️ UNDERSPECIFIED AREAS:
- Terminal extractor not implemented.
- SWE extractor not implemented.
- Disallowed-before-simulation function not implemented.
- Calibration fixtures are directories only.
- Predictor/reconciler prompt templates not implemented.

---

### 3.15 Codebase Intelligence Layer
Status: ✅ IMPLEMENTED for Python Graphify-lite and CRG; 📋 DECIDED for codebase-memory-mcp/Harmony; ❌ DEFERRED for Understand Anything full adapters.

Purpose: Parse local Python code into a graph, identify changed symbols, and scope required tests/review via CRG.

Key Types / Classes / Functions:
- `GraphNode`.
- `GraphEdge`.
- `ParsedFile`.
- `parse_python_file(repo_root, file_path, taint="tool_observed")`.
- `CodeGraph`.
- `CodeGraph.add_parsed_file()`.
- `CodeGraph.find_symbol()`.
- `index_python_repo(repo_root, quotas=None, ledger=None, trace_id="")`.
- `GraphQuotas`.
- `CRGReport`.
- `propagate_change(graph, changed_symbol_contains, trace_id="", ledger=None)`.

Behavior Rules:
1. Python AST is the Phase 0 parser.
2. Calls are best-effort.
3. Parser version is `python-ast-v1`.
4. Graph traversal must use canonical path validation.
5. Golden demo must find `function:src.auth.normalize_token`.
6. Golden demo CRG must map `normalize_token` to `tests/test_auth.py`.
7. `call_edges_best_effort=true` must be preserved.

Interfaces:
- Input: repo root and Python files.
- Output: `CodeGraph`, `CRGReport`, ledger events.

Known Constraints:
- Default graph quotas: max_files=2000, max_nodes=100000, max_parse_time_per_file_ms=500, max_total_index_time_sec=120.

⚠️ UNDERSPECIFIED AREAS:
- Parser failure fallback test is accepted but not implemented.
- Stale graph fallback test is accepted but not implemented.
- codebase-memory-mcp persistence is decided but not implemented.
- Harmony MCP conflict bundles are decided but not implemented.
- Understand Anything full ingestion is deferred beyond Phase 0.

---

### 3.16 Memory System (MEMTIER tiers)
Status: 📋 DECIDED; limited hashing implemented.

Purpose: Maintain hot/warm/cold/audit memory with provenance, taint, quarantine, rollback, and eventual codebase memory.

Key Types / Classes / Functions:
- `memory_commit.schema.json`.
- `memory_retrieval.schema.json`.
- `canonical_memory_json()`.
- `memory_commit_hash()`.

Behavior Rules:
1. Hot memory lives in current task state.
2. Warm memory is session memory in SQLite.
3. Cold semantic memory stores durable code/project facts.
4. Cold procedural memory stores prompts/workflows/router rules.
5. Audit memory is hash-chained ledger and never evicted.
6. Tainted/speculative facts must be quarantined before influencing routing/planning.
7. Memory commits must be rollbackable via inverse operation.

Interfaces:
- Input: memory proposals, provenance, confidence, taint.
- Output: committed/quarantined/rollbackable memory records.

Known Constraints:
- Vector search is optional if no local embedding model is available.
- Runtime procedural memory changes are blocked.

⚠️ UNDERSPECIFIED AREAS:
- SQLite MEMTIER store not implemented.
- Taint propagation engine not implemented.
- Quarantine enforcement not implemented.
- Rollback index update not implemented.

---

### 3.17 Agent Coordination (TRINITY / Conductor)
Status: 📋 DECIDED; not implemented.

Purpose: Assign Thinker, Worker, Verifier, and Memory/Graph Clerk roles for bounded local multi-agent execution.

Key Types / Classes / Functions:
- Future `Conductor`.
- Future role-selection event.
- `ROLE_FORBIDDEN` concept decided; role constants were discussed but not implemented in final code.

Behavior Rules:
1. Thinker cannot execute shell or write files.
2. Worker cannot approve own patch.
3. Verifier cannot modify files or bypass tests.
4. Memory/Graph Clerk cannot change policy or unreviewed procedural memory.
5. Conductor cannot bypass SafetyGovernor.
6. Learned Conductor is offline-only until benchmarked and approved.

Interfaces:
- Input: SynthesisState snapshot, ModelPool, task type, loop state.
- Output: role assignments and role-selection ledger events.

Known Constraints:
- Full conductor must not precede golden demo graph/test path.

⚠️ UNDERSPECIFIED AREAS:
- Runtime Conductor implementation missing.
- Role-selection event writer missing.
- Verifier independence enforcement missing.

---

### 3.18 Self-Evolution Layer
Status: ❌ DEFERRED for runtime; 📋 DECIDED for offline workbench.

Purpose: Optimize prompts, routing thresholds, workflow variants, and planning templates only through offline replay with human approval and rollback.

Key Types / Classes / Functions:
- `RUNTIME_MUTATION_BLOCKLIST`.
- Future offline DSPy/LATS/EvoAgentX/EvoConfig workbench.

Behavior Rules:
1. Runtime self-evolution is disabled.
2. Prompt/workflow/router/safety/cloud/sandbox/max-cap/audit policy mutation is blocked at runtime.
3. Offline mutations require benchmark improvement, safety non-regression, cost/resource non-regression, human approval, and rollback artifact.

Interfaces:
- Input: replayed traces and benchmark results.
- Output: reviewed versioned procedural updates.

Known Constraints:
- Deterministic fallback must remain after learned policy deployment.

⚠️ UNDERSPECIFIED AREAS:
- Runtime mutation block function test missing.
- Offline workbench package is not implemented.

---

### 3.19 BYOK & Cloud Backend Integration
Status: 📋 DECIDED; runtime cloud selection rejected in Phase 0.

Purpose: Allow user-approved cloud calls only when local models cannot satisfy a requirement and BYOK policy permits the specific task.

Behavior Rules:
1. Cloud is disabled by default.
2. BYOK credentials are optional.
3. Cloud calls require explicit task-scoped approval.
4. Cloud cost must be tracked per token.
5. Cloud is not local fallback and must not be selected silently.

Interfaces:
- Input: cloud policy, BYOK credentials, approval object, cost ceiling.
- Output: approved or denied cloud candidate.

Known Constraints:
- Phase 0 router rejects remote candidates by default.

⚠️ UNDERSPECIFIED AREAS:
- BYOK encrypted keystore not implemented.
- Cloud provider adapters not implemented.
- Cloud cost ledger instrumentation not implemented.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 4 — EVENT & SCHEMA REGISTRY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### LedgerEvent Schema
Emitted by: `JsonlLedger.append()`  
Emitted when: Any registered event is persisted.  
Required fields: `schema_version`, `event_id`, `trace_id`, `timestamp`, `event_type`, `payload`, `redaction_applied`, `hash_prev`, `hash_self`.  
Optional fields: None.  
Status: ✅ IMPLEMENTED

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "LedgerEvent",
  "type": "object",
  "required": [
    "schema_version",
    "event_id",
    "trace_id",
    "timestamp",
    "event_type",
    "payload",
    "redaction_applied",
    "hash_prev",
    "hash_self"
  ],
  "properties": {
    "schema_version": { "const": "1.0" },
    "event_id": { "type": "string" },
    "trace_id": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "event_type": { "type": "string" },
    "payload": { "type": "object" },
    "redaction_applied": { "type": "boolean", "const": true },
    "hash_prev": { "type": ["string", "null"] },
    "hash_self": { "type": "string" }
  }
}
```

### Registered Event Types

Implemented or accepted events:

```text
request_started
request_completed
policy_check
config_snapshot
approval_requested
approval_approved
approval_denied
approval_revoked
approval_expired
model_discovery
backend_health
model_call_started
model_call_completed
model_call_failed
route_decision
route_outcome
role_selection
loop_iteration_started
loop_iteration_completed
loop_gate_result
loop_terminated
tool_call_started
tool_call_completed
tool_call_failed
sandbox_exec
sandbox_denial
path_escape_blocked
destructive_command_blocked
network_request_blocked
world_predict
world_reconcile
codegraph_update
codegraph_query
crg_propagate
stale_graph_fallback
memory_retrieve
memory_commit
memory_rollback
memory_quarantined
runtime_self_evolution_blocked
cost_event
ledger_checkpoint
ledger_corruption_detected
```

### Non-Sampled Event Types

```text
approval_requested
approval_approved
approval_denied
approval_revoked
approval_expired
model_call_completed
model_call_failed
tool_call_started
tool_call_completed
tool_call_failed
sandbox_exec
sandbox_denial
path_escape_blocked
destructive_command_blocked
network_request_blocked
memory_commit
memory_rollback
memory_quarantined
runtime_self_evolution_blocked
cost_event
ledger_checkpoint
ledger_corruption_detected
```

### Schemas Present

```text
synthesis_state.schema.json                ✅
ledger_event.schema.json                   ✅
routing_decision.schema.json               ✅
route_outcome.schema.json                  ✅
memory_commit.schema.json                  ✅
crg_report.schema.json                     ✅
approval.schema.json                       ✅
gate_result.schema.json                    ✅
world_transition.schema.json               ✅
model_capability.schema.json               ✅
sandbox_event.schema.json                  ✅
memory_retrieval.schema.json               ✅
procedural_memory_diff.schema.json         📋 placeholder
ledger_checkpoint.schema.json              📋 placeholder
dashboard_data.schema.json                 📋 placeholder
escalation_summary.schema.json             📋 placeholder
graph_quota_config.schema.json             ✅
stale_graph_event.schema.json              ✅
benchmark_result_manifest.schema.json      ✅
event_type_registry.schema.json            📋 placeholder
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 5 — ROUTING LOGIC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ROUTING PRIORITY ORDER:
  Step 1: Iterate models from ModelPool backends.
  Step 2: Record every candidate in `candidates_considered`.
  Step 3: Reject non-local candidates.
  Step 4: Reject partial/discovery-only adapters for chat.
  Step 5: Reject non-serving models.
  Step 6: Reject missing capability.
  Step 7: Score remaining local candidates using `router-score-v1`.
  Step 8: Select highest weighted score.
  Step 9: Emit `route_decision` if `LedgerContext` is supplied.
  Step 10: If no candidate remains, emit `route_decision` and `route_outcome` with failure_reason `no_model_available` if `LedgerContext` is supplied.

REJECTION RULES:
  Reject if: `model.locality != "local"` → reason: `non_local_candidate_rejected_by_default`
  Reject if: `model.adapter_maturity not in {"full"}` → reason: `adapter_maturity_not_selectable_for_chat`
  Reject if: `model.lifecycle_state not in {"serving", "warm"}` → reason: `model_not_serving`
  Reject if: `required_capability == "chat"` and `supports_chat == false` → reason: `chat_not_supported`
  Reject if: `required_capability == "embedding"` and `supports_embeddings == false` → reason: `embedding_not_supported`

FALLBACK CHAIN:
  1. Apple Silicon with compatible serving MLX: MLX → Ollama → LM Studio → Jan
  2. Otherwise: Ollama → LM Studio → Jan
  If all exhausted: return no-model-available with `cloud_gate_result="not_allowed"` in Phase 0.

MAX_ITERATIONS_BY_TASK:
```python
MAX_ITERATIONS_BY_TASK = {
    "question": 2,
    "terminal": 3,
    "code_review": 3,
    "test_generation": 4,
    "bug_fix": 5,
    "refactor": 5,
}
```

COST GATE LOGIC:
  Step 1: Cloud is disabled by default.
  Step 2: Remote candidates are rejected by `non_local_candidate_rejected_by_default`.
  Step 3: BYOK cloud requires user approval, BYOK key, cloud_allowed, cost ceiling, and no adequate local candidate.
  Step 4: Phase 0 does not select cloud.

HISTORICAL PERFORMANCE LEARNING:
  - Historical success, verifier score, and world divergence are score components.
  - Current implementation uses placeholder values.
  - Learned routing and MasRouter are deferred until replay data and benchmark validation exist.

ROUTING WEIGHTS:
```json
{
  "version": "router-score-v1",
  "weights": {
    "capability_match": 0.25,
    "context_fit": 0.15,
    "role_match": 0.15,
    "lifecycle_health": 0.10,
    "latency_score": 0.10,
    "historical_success_decayed": 0.10,
    "verifier_score_decayed": 0.05,
    "low_world_divergence": 0.05,
    "safety_compatibility": 0.05
  }
}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 6 — LOOP DESIGN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RARV PHASE SEQUENCE:
  Reason: classify task, retrieve graph/memory, define success criteria, plan, and later invoke world.predict for allowed risky actions.
  Act: execute approved sandbox actions, run tests, apply deterministic or future model patches.
  Reflect: reconcile observations, propagate CRG, propose memory commits, compute state hash.
  Verify: run gates, verify tests/results, write route outcome, terminate/retry/escalate.

QUALITY GATES:
  1. `intent_gate` — blocking; fails/escalates if task intent cannot be accepted.
  2. `execution_gate` — blocking; escalates if no selectable local model or execution cannot proceed.
  3. `safety_gate` — blocking; must precede tool execution. 📋
  4. `sandbox_gate` — blocking; must wrap sandboxed pytest/tool execution. 📋
  5. `termination_gate` — blocking; validates stop condition. 📋
  6. `cloud_approval_gate` — blocking; required before cloud use. 📋
  7. `simulation_gate` — warning/blocking depending action risk; future world model. 📋
  8. `crg_confidence_gate` — warning/blocking depending CRG confidence. 📋
  9. `style_gate` — informational. 📋
  10. `memory_update_gate` — informational. 📋

BLOCKING_GATES SET:
```python
BLOCKING_GATES = {
    "intent_gate",
    "safety_gate",
    "sandbox_gate",
    "execution_gate",
    "termination_gate",
    "cloud_approval_gate",
}
```

TERMINATION CONDITIONS:
  1. `success`: `goal_achieved and verification_passed`.
  2. `safety_stop`: `safety_stop == True`.
  3. `max_iterations`: `iteration >= resolved_max_iterations()`.
  4. `model_call_cap`: `model_calls >= max_model_calls`.
  5. `tool_call_cap`: `tool_calls >= max_tool_calls`.
  6. `world_sim_call_cap`: `world_sim_calls >= max_world_sim_calls`.
  7. `error_cap`: `error_count >= max_errors`.
  8. `repeated_state_hash`: `repeated_state_hash_count >= 2`.
  9. `same_failed_gate`: `same_failed_gate_count >= 2`.
  10. `wall_clock_limit`: elapsed monotonic time >= `wall_clock_limit_sec`.
  11. `continue`: no stop condition matched.

LOOP BUDGET FIELDS:
  - `task_type: str`
  - `max_iterations: int | None`
  - `max_model_calls: int = 30`
  - `max_tool_calls: int = 40`
  - `max_world_sim_calls: int = 8`
  - `max_errors: int = 2`
  - `wall_clock_limit_sec: int = 900`

LOOP COUNTERS FIELDS:
  - `iteration: int = 0`
  - `model_calls: int = 0`
  - `tool_calls: int = 0`
  - `world_sim_calls: int = 0`
  - `error_count: int = 0`
  - `repeated_state_hash_count: int = 0`
  - `same_failed_gate_count: int = 0`
  - `safety_stop: bool = False`
  - `started_monotonic: float`
  - `goal_achieved: bool = False`
  - `verification_passed: bool = False`

STOP FUNCTION LOGIC:
```python
if counters.goal_achieved and counters.verification_passed:
    return True, "success"
if counters.safety_stop:
    return True, "safety_stop"
if counters.iteration >= budget.resolved_max_iterations():
    return True, "max_iterations"
if counters.model_calls >= budget.max_model_calls:
    return True, "model_call_cap"
if counters.tool_calls >= budget.max_tool_calls:
    return True, "tool_call_cap"
if counters.world_sim_calls >= budget.max_world_sim_calls:
    return True, "world_sim_call_cap"
if counters.error_count >= budget.max_errors:
    return True, "error_cap"
if counters.repeated_state_hash_count >= 2:
    return True, "repeated_state_hash"
if counters.same_failed_gate_count >= 2:
    return True, "same_failed_gate"
if monotonic() - counters.started_monotonic >= budget.wall_clock_limit_sec:
    return True, "wall_clock_limit"
return False, "continue"
```

SAFETY RULES:
  - Blocking gates cannot be skipped without explicit policy.
  - `safety_stop` is non-overridable.
  - Real tool execution must be sandboxed.
  - Cloud routing is rejected in Phase 0.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 7 — SECURITY & SANDBOX RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SANDBOX RULES:
1. Commands must be argv arrays; shell strings are forbidden.
2. `shell=False` must be used for process execution.
3. Empty argv is denied.
4. Command name must be in `COMMAND_ALLOWLIST`.
5. Command name in `COMMAND_DENYLIST` is denied.
6. Shell metacharacters `;`, `|`, `&`, `` ` ``, `$`, `>`, `<` are denied in argv.
7. Workspace root is resolved with `Path.resolve(strict=True)`.
8. CWD must canonicalize under workspace.
9. Path-like args must canonicalize under workspace.
10. Paths escaping workspace are denied.
11. Symlink escapes are denied through canonical path resolution.
12. Environment is scrubbed to `PATH`.
13. Network defaults to off; network namespace enforcement is not implemented.
14. Timeout is enforced by `subprocess.run(timeout=timeout_sec)`.

INJECTION PREVENTION:
- Backend model names are untrusted; sanitize with `sanitize_model_name()`.
- Jan locality is unknown unless proven local; unknown locality is not selectable.
- Partial/discovery adapters are not selectable for chat.
- Repo-defined commands are tainted by default and must run only through sandbox/approval policy when integrated.
- Repo Markdown instructions must remain tainted when memory integration lands.
- Runtime self-evolution mutation types are blocked by policy constants.

LEDGER INTEGRITY:
- Every event must use registered event type.
- Redaction occurs before persistence.
- Secret values remaining after redaction cause append failure.
- Events are canonicalized before hash.
- `hash_prev` must match previous event hash.
- `hash_self` must match event hash.
- Verification stops at first bad event.

APPROVAL SYSTEM RULES:
- Approval status must be `approved`.
- `task_id` must exactly match.
- `requested_action` must exactly match.
- `uses < max_uses`.
- `max_uses` defaults to 1.
- Expired approvals are invalid.
- Approvals with immutable policy mutation attempts are invalid.
- Approval transitions are ledgerable.

IMMUTABLE POLICY RULES:
- Runtime mutation of `local_first` is blocked.
- Runtime mutation of `cloud_requires_explicit_approval` is blocked.
- Runtime mutation of `network_default` is blocked.
- Runtime mutation of `max_iterations_by_task` is blocked.
- Runtime mutation of `safety_circuit_breakers` is blocked.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 8 — TEST COVERAGE MAP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Test Name | File | What It Verifies | Status |
|---|---|---|---|
| test_scaffold_exists | tests/unit/test_scaffold.py | schema scaffold exists | ✅ passing |
| test_ledger_append_verify_and_redact | tests/unit/test_ledger.py | ledger append, redaction, verification | ✅ passing |
| test_ledger_detects_corruption | tests/unit/test_ledger.py | ledger corruption detection | ✅ passing |
| test_known_event_type | tests/unit/test_event_registry.py | known event accepted | ✅ passing |
| test_unknown_event_type_rejected | tests/unit/test_event_registry.py | unknown event rejected | ✅ passing |
| test_memory_hash_deterministic_key_order | tests/unit/test_memory_hashing.py | memory hash deterministic across key order | ✅ passing |
| test_discovery_unavailable_does_not_fail | tests/unit/test_modelpool_discovery.py | all-backend discovery tolerates absent servers | ✅ passing |
| test_approval_exact_task_match_and_max_uses | tests/unit/test_approval_policy.py | approval exact task and max use | ✅ passing |
| test_approval_expiry_and_immutable_attempt_block | tests/unit/test_approval_policy.py | expiry and immutable-attempt denial | ✅ passing |
| test_immutable_policy_mutation_blocked | tests/unit/test_immutable_policy.py | immutable key mutation blocked | ✅ passing |
| test_mutable_policy_change_allowed | tests/unit/test_immutable_policy.py | non-immutable mutation allowed | ✅ passing |
| test_selects_full_local_before_partial_or_unknown | tests/unit/test_router_deterministic.py | full local model selected over partial/unknown | ✅ passing |
| test_no_model_available_ledgered | tests/unit/test_router_deterministic.py | no-model route decision/outcome ledgered | ✅ passing |
| test_model_pool_endpoint_reports_maturity | tests/unit/test_api_modelpool.py | API model-pool maturity and ledger file | ⏭️ skipped if FastAPI unavailable |
| test_approval_event_ledgered_and_reuse_blocked | tests/unit/test_approval_events.py | approval event ledgered and reuse blocked | ✅ passing |
| test_should_stop_max_iterations | tests/unit/test_loop_engine.py | max iteration stop | ✅ passing |
| test_should_stop_model_call_cap | tests/unit/test_loop_engine.py | model-call cap stop | ✅ passing |
| test_should_stop_safety | tests/unit/test_loop_engine.py | safety stop | ✅ passing |
| test_blocking_gate_cannot_skip | tests/unit/test_loop_engine.py | blocking gate skip rejected | ✅ passing |
| test_minimal_rarv_success_trace | tests/unit/test_loop_engine.py | minimal loop succeeds and ledgers gate/outcome | ✅ passing |
| test_trace_completeness_bug_fix_full | tests/unit/test_trace_completeness.py | full bug_fix event set scores 1.0 | ✅ passing |
| test_trace_completeness_missing | tests/unit/test_trace_completeness.py | missing events reduce completeness | ✅ passing |
| test_cloud_candidate_never_selected_without_approval | tests/unit/test_router_cloud_and_sanitize.py | cloud candidate rejected | ✅ passing |
| test_model_name_sanitization | tests/unit/test_router_cloud_and_sanitize.py | model name sanitization | ✅ passing |
| test_parse_golden_demo_finds_normalize_token | tests/unit/test_codegraph.py | graph finds `function:src.auth.normalize_token` | ✅ passing |
| test_crg_maps_normalize_token_to_required_test | tests/unit/test_codegraph.py | CRG maps function to `tests/test_auth.py` | ✅ passing |
| test_codegraph_and_crg_ledger_events_and_completeness | tests/unit/test_codegraph.py | graph/CRG ledger events and completeness 1.0 | ✅ passing |
| test_state_hash_ignores_nondeterministic_fields | tests/unit/test_loop_hashing.py | stable hash ignores timestamp/span_id | ✅ passing |
| test_repeated_state_hash_stop | tests/unit/test_loop_hashing.py | repeated-state stop | ✅ passing |
| test_same_failed_gate_stop | tests/unit/test_loop_hashing.py | same-failed-gate stop | ✅ passing |
| test_shell_strings_forbidden | tests/security/test_sandbox_runner.py | shell strings forbidden | ✅ passing |
| test_path_escape_blocked | tests/security/test_sandbox_runner.py | path escape blocked | ✅ passing |
| test_symlink_escape_blocked | tests/security/test_sandbox_runner.py | symlink escape blocked | ✅ passing |
| test_shell_metacharacters_denied | tests/security/test_sandbox_runner.py | shell metacharacters denied | ✅ passing |
| test_allowed_argv_runs | tests/security/test_sandbox_runner.py | allowed argv command executes | ✅ passing |
| test_sandbox_decision_serializes_to_schema | tests/security/test_sandbox_event_schema.py | sandbox event validates against schema | ✅ passing |
| test_sandbox_fuzz_smoke_metacharacters | tests/security/test_sandbox_fuzz_smoke.py | metacharacter fuzz smoke denied | ✅ passing |
| test_codegraph_path_escape_blocked | tests/security/test_codegraph_paths.py | graph path escape blocked | ✅ passing |

CRITICAL PATHS WITH NO TEST COVERAGE:
- Live Ollama chat conformance.
- Live Ollama embeddings conformance.
- OpenTelemetry span wrappers.
- Ledger checkpoint/recovery beyond verification.
- Approval API endpoints.
- Full TRINITY role-selection event.
- Runtime self-evolution block event.
- SQLite MEMTIER memory store.
- Taint propagation full chain.
- Parser failure fallback.
- Graph quota enforcement.
- Stale graph fallback event.
- Hostile filename graph traversal.
- Disallowed-before-simulation world-model pre-check.
- Terminal/SWE world extractors.
- Sandboxed pytest golden execution.
- Deterministic golden patch application.
- Confirmed memory commit after pytest pass.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 9 — GOLDEN DEMO SPECIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GOLDEN DEMO INPUT:
- Repository path: `tests/fixtures/golden_demo_repo`
- File: `tests/fixtures/golden_demo_repo/src/auth.py`
- Buggy function:
```python
def normalize_token(token: str) -> str:
    # Bug: should strip surrounding whitespace before validation.
    return token.lower()
```
- Test file: `tests/fixtures/golden_demo_repo/tests/test_auth.py`
- Failing test:
```python
from src.auth import normalize_token

def test_token_normalization_strips_whitespace():
    assert normalize_token("  ABC  ") == "abc"
```
- Expected deterministic patch:
```python
return token.strip().lower()
```

GOLDEN DEMO EXPECTED EXECUTION PATH:
  Step 1: ModelPool discovers local backends and exposes local-first ModelPool.
  Step 2: Deterministic router selects a full local selectable model or records no-model-available.
  Step 3: RARV loop starts and ledgers `request_started`, `policy_check`, and `loop_iteration_started`.
  Step 4: Codegraph indexes `tests/fixtures/golden_demo_repo` with Python AST parser.
  Step 5: Codegraph finds `function:src.auth.normalize_token`.
  Step 6: CRG propagates change for `normalize_token`.
  Step 7: CRG identifies `tests/test_auth.py` as required test.
  Step 8: Loop writes `safety_gate`.
  Step 9: Loop writes `sandbox_gate`.
  Step 10: Sandbox runs `pytest tests/test_auth.py` as argv array.
  Step 11: Initial pytest failure is observed and ledgered.
  Step 12: Deterministic patch changes `return token.lower()` to `return token.strip().lower()`.
  Step 13: Sandbox reruns `pytest tests/test_auth.py`.
  Step 14: Passing pytest is observed and ledgered.
  Step 15: Verifier/execution gate approves deterministic fix.
  Step 16: Route outcome is written with task_success true.
  Step 17: Confirmed memory commit records `project.test_command = pytest tests/test_auth.py` with provenance `test_observed` and confidence `confirmed`.
  Step 18: Ledger verifies.
  Step 19: Trace completeness equals 1.0.

GOLDEN DEMO PASS CONDITIONS:
- Cloud calls count is 0.
- Cost USD is 0.00.
- Selected backend is local or no-model path is explicitly reported before demo execution.
- `function:src.auth.normalize_token` is found.
- CRG `required_tests` includes `tests/test_auth.py`.
- CRG confidence is greater than 0.60.
- Sandbox executes pytest via argv array.
- Initial pytest failure is captured.
- Deterministic patch is applied exactly.
- Final pytest pass is captured.
- `route_outcome` reports task_success true.
- Ledger verifies successfully.
- Trace completeness is 1.0.
- No shell strings are executed.
- No path escapes occur.

GOLDEN DEMO FAIL CONDITIONS:
- Any cloud call occurs.
- Any shell string is executed.
- Any command executes outside workspace.
- Any blocking gate is skipped without explicit policy.
- Ledger verification fails.
- Trace completeness is less than 1.0.
- CRG does not identify `tests/test_auth.py`.
- Final pytest does not pass.
- Patch is model-generated before deterministic golden path is accepted.

GOLDEN DEMO BLOCKERS:
- Sandboxed pytest execution is not integrated into loop.
- Deterministic patch application is not implemented.
- `safety_gate` and `sandbox_gate` are not integrated into minimal loop.
- Initial/final pytest observation ledgering is not implemented.
- Confirmed memory commit is not implemented.
- Full golden demo runner is not implemented.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 10 — RELEASE GATES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### H1 — Divergence-Aware Loop Control
Blocks: Claims that world-model prediction/reconciliation improves loop control.  
Pass condition: ≥15% fewer failed tool actions and ≥10% bounded completion improvement.  
Status: 📋 NOT YET EVALUATED.

### H2 — CRG-Scoped Verification
Blocks: Claims that Graphify-lite + CRG improves review/test targeting.  
Pass condition: ≥20% reduction in irrelevant review/test actions and ≥10% increase in caught regressions.  
Status: 📋 NOT YET EVALUATED; golden-demo CRG path partially implemented.

### H3 — Trace-Replay Coordination Learning
Blocks: Learned routing/conductor deployment.  
Pass condition: ≥10% routing oracle agreement improvement and ≥8% latency reduction at equal verifier score.  
Status: 📋 NOT YET EVALUATED.

### H4 — Taint/Sandbox Safety
Blocks: Phase 0 release.  
Pass condition: ≥90% unsafe action block rate on adversarial task suite and ≤5% absolute benign completion loss.  
Status: 🔴 BLOCKING; safety primitives implemented, full H4 suite not implemented.

### Phase 0 Golden Demo Gate
Blocks: Phase 0 completion.  
Pass condition: golden demo pass conditions in Section 9 all true.  
Status: 🔴 BLOCKING.

### Phase 0 Release Gate
Blocks: Phase 0 release.  
Pass condition: `synthesis release-gate phase0` passes all listed checks: doctor, Ollama conformance, all-backend discovery, local-first router, sandbox denial, path traversal, symlink defense, command parser fuzz smoke, approval expiry/reuse, taint propagation, memory rollback/index update, runtime self-evolution block, world disallowed-before-simulation, CRG confidence/stale graph, repeated-state loop detection, ledger verification/recovery, fake-secret redaction, dashboard golden trace, trace completeness 1.0, H4 suite.  
Status: 🔴 BLOCKING.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 11 — EXPLICITLY DEFERRED WORK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Component / Feature | Deferred Until | Scope When It Lands |
|---|---|---|
| Full LM Studio chat parity | After golden demo | Full adapter conformance and chat behavior. |
| Full Jan chat parity | After golden demo | Full adapter conformance, local/remote classification, chat behavior. |
| Full MLX chat parity | After golden demo | Apple Silicon full adapter conformance and chat behavior. |
| Langfuse default backend | Phase 1 | Local Docker Compose Langfuse + PostgreSQL integration. |
| OpenTelemetry span helpers | After ledgered golden path starts | Span wrappers correlated with ledger events. |
| Learned RouteLLM/LLMRouter/MasRouter | After deterministic baseline traces and benchmarks | Offline training; deployment only after safety and performance gates. |
| Full TRINITY conductor | After golden demo graph/test path | Thinker/Worker/Verifier/Memory-Graph Clerk assignments and role-selection events. |
| Runtime learned Conductor | After trace replay benchmark improvement | Offline-trained policy with deterministic fallback. |
| World model Terminal/SWE predictor | After sandboxed pytest and deterministic golden patch path | Advisory predict/reconcile with transition ledgering. |
| Web/OS/Android/Search world simulation | Beyond Phase 0 | Additional validated world-model domains. |
| Runtime self-evolution | Not allowed in Phase 0 | Offline-only replay workbench with rollback/human approval. |
| DSPy prompt optimization | Offline workbench phase | Optimize verifier/routing/world/memory prompts, not safety policy. |
| LATS planning search | Offline workbench phase | Planning strategy templates for complex tasks. |
| EvoAgentX workflow mutation | Offline workbench phase | Workflow graph variants with benchmark/safety gates. |
| EvoConfig tuning | Offline workbench phase | Backend preference, context compression, routing thresholds. |
| JS/TS Graphify | After Python golden demo | tree-sitter JS/TS support. |
| Understand Anything full ingestion | After Phase 0 | Additional adapters beyond Python/Markdown/OpenAPI/JSON Schema. |
| codebase-memory-mcp persistence | After golden demo memory foundation | Durable project facts and codebase memory. |
| Harmony MCP conflict bundles | After multi-agent write paths exist | File-level locks, conflict bundles, verifier merge approval. |
| Process resource limits beyond timeout | Phase 1/platform-specific hardening | CPU/RAM/process/network limits where supported. |
| Cloud BYOK provider adapters | After local-first core passes | Optional Anthropic/OpenAI/Google/OpenRouter/LiteLLM providers. |
| Encrypted BYOK keystore | After cloud mode begins | Local encrypted key storage and rotation. |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 12 — EXPLICITLY REJECTED DECISIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Rejected Approach | Reason for Rejection |
|---|---|
| Any cloud-required feature | Violates local-first identity. |
| Cloud selected by default | Violates BYOK opt-in and local-first routing. |
| Full JS/TS support before Phase 0 release | Violates MVP scope. |
| Full LM Studio/Jan/MLX chat parity before golden demo | Jeopardizes Phase 0 golden path. |
| Runtime self-evolution in Phase 0 | Violates safety and rollback constraints. |
| Arbitrary shell execution before sandbox tests pass | Violates safety release gate. |
| Shell-string execution support | Violates argv-only sandbox rule. |
| Patch writing before repeated-state and same-failed-gate tests pass | Violates loop safety requirements. |
| Model-generated patches before deterministic golden path passes | Premature autonomy and safety risk. |
| Full conductor before golden demo graph path | Premature complexity. |
| Learned routing before golden demo | Premature complexity and lacks replay data. |
| Selecting partial adapters for chat before smoke conformance | Overclaims adapter maturity. |
| Advertising native tool calling without conformance proof | Misrepresents backend capability. |
| Requiring Ollama in CI | CI must remain portable; local release gate validates real Ollama. |
| Expanding dashboard polish before trace correctness | Trace correctness is prerequisite. |
| Expanding benchmark breadth at expense of golden demo quality | Golden demo is primary Phase 0 success path. |
| Documentation claiming complete Python call-graph precision | Python AST call graph is best-effort. |
| Generalizing beyond Python AST before Phase 0 golden demo | Violates Phase 0 scope. |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 13 — UNRESOLVED CONFLICTS & OPEN QUESTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### UQ-1 — OpenTelemetry Span Helper Implementation
Type: ⚠️ UNDERSPECIFIED  
Description: OpenTelemetry-first tracing and span names were decided, but helper implementation and exact integration with `LedgerContext` are not implemented.  
Options on the table: ledger-first wrapper that also emits OTel spans; separate OTel decorator wrapping components.  
Blocking: Full observability dashboard and OpenTelemetry backend integration.  
Recommended resolution path: Implement span wrappers around existing ledgered component calls after golden path ledgering is stable.

### UQ-2 — World Model Execution
Type: ⚠️ UNDERSPECIFIED  
Description: World model advisory role, schemas, thresholds, and prohibitions are decided, but Terminal/SWE extractors, disallowed-before-simulation pre-check, prompts, and calibration fixtures are missing.  
Options on the table: implement Terminal/SWE extractors first, then prompted local prediction/reconcile.  
Blocking: H1 divergence-aware loop-control evaluation.  
Recommended resolution path: Build disallowed-before-simulation pre-check and extractors before predictor prompts.

### UQ-3 — MEMTIER Store and Taint Propagation
Type: ⚠️ UNDERSPECIFIED  
Description: MEMTIER tiers, quarantine, rollback, provenance, and taint rules are decided, but SQLite store and full taint propagation engine are not implemented.  
Options on the table: implement confirmed test-command memory after sandboxed pytest passes.  
Blocking: Memory contribution to golden demo and memory safety gates.  
Recommended resolution path: Add minimal confirmed memory commit after deterministic golden demo passes tests.

### UQ-4 — Full TRINITY Conductor
Type: ⚠️ UNDERSPECIFIED  
Description: TRINITY roles and restrictions are decided, but runtime Conductor and role-selection ledger event are not implemented.  
Options on the table: add simple deterministic role-selection stub after Graphify/CRG integration.  
Blocking: Multi-agent coordination claims and H3 coordination-learning substrate.  
Recommended resolution path: Implement role-selection event before final golden demo trace.

### UQ-5 — BYOK Keystore and Cloud Providers
Type: ⚠️ UNDERSPECIFIED  
Description: BYOK policy is decided, but provider adapters, encrypted keystore, key rotation, and per-provider cost calculation are not implemented.  
Options on the table: defer until after local-first Phase 0.  
Blocking: Optional cloud mode only.  
Recommended resolution path: Keep blocked until Phase 0 local golden demo passes.

### UQ-6 — Graph Robustness Tests
Type: ⚠️ UNDERSPECIFIED  
Description: Parser failure fallback, quota enforcement, stale graph fallback, and hostile filename traversal tests were accepted but not implemented.  
Options on the table: add before sandboxed pytest golden execution or immediately after.  
Blocking: Robustness of codegraph in adversarial repos.  
Recommended resolution path: Add tests before broadening graph use beyond golden repo.

No unresolved contradictions identified. All critical architectural conflicts were resolved by later decisions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 14 — HARDWARE & DEPLOYMENT REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MINIMUM HARDWARE:
  MacBook Pro M2 or equivalent, 16GB RAM, Ollama with one 7B/8B code-capable model.

RECOMMENDED HARDWARE:
  32GB RAM, Qwen2.5-Coder 14B or similar local code model, local embedding model such as `nomic-embed-text`.

OPTIMAL HARDWARE:
  64GB RAM, MLX or Ollama 32B planner, separate verifier model, local embeddings.

DOCKER COMPOSE SPEC:
```yaml
services:
  synthesis-api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    ports:
      - "8787:8787"
    volumes:
      - ../workspace:/workspace
      - ../data:/data
    environment:
      SYNTHESIS_CLOUD_ALLOWED: "false"
      SYNTHESIS_NETWORK_DEFAULT: "off"
      SYNTHESIS_WORKSPACE: "/workspace"
      SYNTHESIS_LEDGER_PATH: "/data/ledger.jsonl"

  synthesis-worker:
    build:
      context: ..
      dockerfile: docker/Dockerfile.worker
    volumes:
      - ../workspace:/workspace
      - ../data:/data
    environment:
      SYNTHESIS_SANDBOX_CWD: "/workspace"
      SYNTHESIS_MAX_WALL_CLOCK_SEC: "900"

  synthesis-dashboard:
    build:
      context: ..
      dockerfile: docker/Dockerfile.dashboard
    ports:
      - "8788:8788"
    volumes:
      - ../data:/data
```

RUNTIME SELF-EVOLUTION:
  Runtime self-evolution is disabled in Phase 0. Prompt mutation, workflow mutation, router policy mutation, safety policy mutation, cloud policy mutation, sandbox policy mutation, max cap mutation, and audit policy mutation are blocked. Offline self-evolution is allowed only after replay benchmarks, safety non-regression, cost/resource non-regression, human approval, and rollback artifact.

DEPLOYMENT DEFAULTS:
  - `SYNTHESIS_CLOUD_ALLOWED=false`
  - `SYNTHESIS_NETWORK_DEFAULT=off`
  - `SYNTHESIS_WORKSPACE=/workspace`
  - `SYNTHESIS_LEDGER_PATH=/data/ledger.jsonl`

CLI COMMANDS:
  - `synthesis doctor`
  - `synthesis release-gate phase0`
  - `synthesis run --task bugfix --repo ./workspace/demo`
  - `synthesis dashboard --ledger ./data/ledger.jsonl`
  - `synthesis ledger verify ./data/ledger.jsonl`
  - `synthesis ledger replay --target langfuse --redact`
  - `synthesis benchmark run --suite h4`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## SECTION 15 — DOCUMENT HEALTH REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### Extraction Completeness

| Section | Status | Notes |
|---|---|---|
| 1. Architectural Identity | ✅ | Non-negotiables are clear and consistent. |
| 2. Package & File Structure | ✅ | Implemented and decided files are enumerated; some placeholders remain marked. |
| 3. Component Specifications | ⚠️ | World model, MEMTIER, Conductor, BYOK are decided but underspecified/not implemented. |
| 4. Event & Schema Registry | ⚠️ | Event names are clear; several payload schemas remain placeholders or prose-defined. |
| 5. Routing Logic | ✅ | Deterministic local-first routing is implemented; learned routing deferred. |
| 6. Loop Design | ⚠️ | Minimal loop implemented; full explicit RARV phase methods pending. |
| 7. Security & Sandbox Rules | ✅ | Sandbox core, redaction, approvals, immutable policy rules are clear. |
| 8. Test Coverage Map | ✅ | Passing, skipped, and missing critical tests are listed. |
| 9. Golden Demo Specification | ⚠️ | Spec is binary and clear; sandboxed pytest/deterministic patch not implemented. |
| 10. Release Gates | ⚠️ | Gates are defined; H1–H4 not evaluated, H4 and golden demo blocking. |
| 11. Deferred Work | ✅ | Explicitly deferred work is captured. |
| 12. Rejected Decisions | ✅ | Rejected approaches and reasons are captured. |
| 13. Unresolved Conflicts | ✅ | No unresolved contradictions; underspecified areas listed. |
| 14. Hardware & Deployment | ✅ | Minimum/recommended/optimal hardware and Docker Compose are captured. |

### Overall Document Readiness

READY FOR PHASE 2: CONDITIONAL

Required before Phase 2 implementation begins:

1. Implement sandboxed pytest execution for CRG `required_tests`.
2. Implement deterministic golden patch application.
3. Integrate `safety_gate` and `sandbox_gate` into the golden loop.
4. Ledger sandbox execution events during golden demo.
5. Achieve golden demo trace completeness 1.0 from actual ledger file.
6. Implement parser failure fallback, graph quota enforcement, and stale graph fallback tests.
7. Decide whether Phase 2 includes world model extractors or defers them until after deterministic golden demo completion.
8. Decide whether Phase 2 includes minimal MEMTIER confirmed memory commit or defers memory until after golden demo.

### Confidence Assessment

Confidence level: HIGH

Reason: Architectural identity, local-first routing, ledger, sandbox, minimal loop, codegraph, CRG, and Phase 0 scope were repeatedly preserved and partially implemented with passing tests. Remaining gaps are clearly marked as underspecified or deferred rather than reconstructed.

---
SYNTHESIS Canonical Architecture Document v1.0 — Extraction Complete.
Produced from Rounds 1–13. Ready for Phase 2 implementation review.
---
