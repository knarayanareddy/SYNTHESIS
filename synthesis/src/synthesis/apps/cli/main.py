"""Synthesis CLI — Typer command-line interface."""

from __future__ import annotations

import os, sys, json, time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(
    name="synthesis",
    help="Local-first AI agent orchestration system",
)
console = Console()


BACKEND_HELP = {
    "ollama": {
        "install_macos": "brew install ollama",
        "install_linux": "curl -fsSL https://ollama.ai/install.sh | sh",
        "url": "https://ollama.ai",
        "description": "Open-source local LLM runner",
        "default_port": "11434",
    },
    "lm_studio": {
        "install_macos": "Download from https://lmstudio.ai/",
        "install_linux": "Download from https://lmstudio.ai/",
        "url": "https://lmstudio.ai/",
        "description": "Desktop app for running local LLMs",
        "default_port": "1234",
    },
    "jan": {
        "install_macos": "Download from https://jan.ai/",
        "install_linux": "Download from https://jan.ai/",
        "url": "https://jan.ai/",
        "description": "Open-source ChatGPT alternative",
        "default_port": "1337",
    },
    "mlx": {
        "install_macos": "pip install mlx-lm (Apple Silicon only)",
        "install_linux": "Not available on Linux/Windows",
        "url": "https://github.com/ml-explore/mlx-examples",
        "description": "Apple Silicon ML framework (macOS only)",
        "default_port": "8080",
    },
}

RECOMMENDED_MODELS = {
    "ollama": "qwen2.5-coder:7b, qwen2.5-coder:14b, codellama:13b",
    "lm_studio": "any CodeLlama or Qwen Coder variant from HuggingFace",
    "jan": "any model via local engine (Cortex/llama.cpp)",
    "mlx": "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit",
}


def _check_backend(name: str, adapter) -> dict:
    health = adapter.health()
    reachable = health.get("reachable", False)
    models = adapter.list_models() if reachable else []
    maturity = getattr(adapter, "adapter_maturity", "unknown")
    return {
        "name": name, "reachable": reachable, "models": models,
        "maturity": maturity, "health": health,
    }


@app.command()
def doctor():
    """Check system health and local backend availability."""
    console.print(Panel.fit("[bold blue]SYNTHESIS Doctor[/bold blue]"))

    table = Table(title="Backend Health")
    table.add_column("Backend", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Models", style="yellow")
    table.add_column("Maturity", style="dim")
    table.add_column("Details")

    results = {}

    # Ollama
    try:
        from synthesis.packages.modelpool.adapters.ollama import OllamaAdapter
        results["ollama"] = _check_backend("ollama", OllamaAdapter())
    except ImportError:
        results["ollama"] = {"name": "ollama", "reachable": False, "models": [],
                            "maturity": "not_installed", "health": {"error": "requests not installed"}}

    # LM Studio
    try:
        from synthesis.packages.modelpool.adapters.lm_studio import LMStudioAdapter
        results["lm_studio"] = _check_backend("lm_studio", LMStudioAdapter())
    except ImportError:
        results["lm_studio"] = {"name": "lm_studio", "reachable": False, "models": [],
                               "maturity": "not_installed", "health": {"error": "requests not installed"}}

    # Jan
    try:
        from synthesis.packages.modelpool.adapters.jan import JanAdapter
        results["jan"] = _check_backend("jan", JanAdapter())
    except ImportError:
        results["jan"] = {"name": "jan", "reachable": False, "models": [],
                         "maturity": "not_installed", "health": {"error": "requests not installed"}}

    # MLX
    try:
        from synthesis.packages.modelpool.adapters.mlx import MLXAdapter
        adapter = MLXAdapter()
        if not adapter.is_platform_supported():
            results["mlx"] = {"name": "mlx", "reachable": False, "models": [],
                             "maturity": "unsupported_platform",
                             "health": {"error": "MLX requires Apple Silicon (macOS arm64)"}}
        else:
            results["mlx"] = _check_backend("mlx", adapter)
    except ImportError:
        results["mlx"] = {"name": "mlx", "reachable": False, "models": [],
                         "maturity": "not_installed", "health": {"error": "MLX adapter not available"}}

    for name, r in results.items():
        if r["reachable"]:
            status, style = "✅ ONLINE", "green"
            details = ""
        elif r.get("maturity") == "unsupported_platform":
            status, style = "📋 N/A (platform)", "dim"
            details = r["health"].get("error", "")
        elif r.get("maturity") == "not_installed":
            status, style = "⚠️  OFFLINE", "yellow"
            details = r["health"].get("error", "")
        else:
            status, style = "❌ OFFLINE", "red"
            details = r["health"].get("error", "")

        model_count = len(r["models"])
        model_str = f"{model_count} model(s)" if model_count > 0 else "none"

        table.add_row(
            f"[{style}]{name}[/{style}]",
            f"[{style}]{status}[/{style}]",
            model_str,
            r.get("maturity", "unknown"),
            details[:200],
        )

    console.print(table)

    offline = [n for n, r in results.items() if not r["reachable"] and r.get("maturity") not in ("not_implemented", "unsupported_platform")]
    if offline:
        console.print("\n[yellow]Backends not detected:[/yellow]")
        for name in offline:
            help_info = BACKEND_HELP.get(name, {})
            console.print(f"  [cyan]{name}[/cyan]: {help_info.get('description', '')}")
            console.print(f"    Install: {help_info.get('install_macos', '')}")
            console.print(f"    Default port: {help_info.get('default_port', 'unknown')}")
            console.print(f"    More info: {help_info.get('url', '')}")

    # Sandbox
    try:
        from synthesis.packages.sandbox.runner import run_argv
        result = run_argv(["echo", "synthesis-doctor-check"], os.getcwd(), timeout_sec=5)
        if result.returncode == 0:
            console.print("\n[green]✅ Sandbox: operational[/green]")
        else:
            console.print("\n[red]❌ Sandbox: echo failed[/red]")
    except Exception as e:
        console.print(f"\n[red]❌ Sandbox: {e}[/red]")

    # TOCTOU
    try:
        from synthesis.packages.sandbox.toctou import is_toctou_safe
        cwd_safe = is_toctou_safe(os.getcwd())
        if cwd_safe:
            console.print("[green]✅ TOCTOU protection: active[/green]")
        else:
            console.print("[yellow]⚠️  TOCTOU protection: current directory may be symlinked[/yellow]")
    except ImportError:
        console.print("[yellow]⚠️  TOCTOU protection: module not available[/yellow]")

    # Observability
    try:
        from synthesis.packages.observability.spans import spans_available
        if spans_available():
            console.print("[green]✅ Observability spans: active (Langfuse)[/green]")
        else:
            console.print("[dim]📋 Observability: spans in no-op mode (Langfuse not configured)[/dim]")
    except ImportError:
        console.print("[dim]📋 Observability: spans module not available[/dim]")

    # Model recommendations
    console.print("\n[bold]Recommended code models:[/bold]")
    for name, rec in RECOMMENDED_MODELS.items():
        console.print(f"  [cyan]{name}:[/cyan] {rec}")

    console.print("\n[dim]Doctor check complete.[/dim]")


@app.command()
def run(
    task: str = typer.Option("bugfix", "--task", "-t", help="Task type: bugfix, code_review, test_generation"),
    repo: str = typer.Option(..., "--repo", "-r", help="Path to repository"),
    ollama_host: str = typer.Option("http://localhost:11434", "--ollama-host"),
    ollama_model: str = typer.Option("qwen2.5-coder:7b", "--ollama-model"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write result JSON to file"),
):
    """Run a synthesis task against a repository."""
    task_map = {"bugfix": "bug_fix", "code_review": "code_review", "test_generation": "test_generation"}
    task_type = task_map.get(task, task)

    if not os.path.isdir(repo):
        console.print(f"[red]Error: repository not found: {repo}[/red]")
        raise typer.Exit(code=1)

    console.print(Panel.fit(f"[bold blue]SYNTHESIS Run[/bold blue]\nTask: {task_type}\nRepo: {repo}"))

    from synthesis.packages.observability.ledger import JsonlLedger
    from synthesis.packages.loop_engine.rarv import run_golden_demo_rarv

    ledger_path = os.path.join(repo, ".synthesis", "ledger.jsonl")
    ledger = JsonlLedger(ledger_path)

    t0 = time.perf_counter()
    console.print("[dim]Running golden demo RARV loop...[/dim]")
    result = run_golden_demo_rarv(
        ledger=ledger, repo_root=repo, task_type=task_type,
        ollama_host=ollama_host, ollama_model=ollama_model,
    )
    elapsed = time.perf_counter() - t0

    table = Table(title="Golden Demo Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    status_style = "green" if result.status == "success" else "red"
    table.add_row("Status", f"[{status_style}]{result.status}[/{status_style}]")
    table.add_row("Wall time", f"{elapsed:.3f}s")
    table.add_row("Iterations", str(result.iterations))
    table.add_row("CRG Confidence", f"{result.crg_confidence:.2f}")
    table.add_row("CRG Required Tests", ", ".join(result.crg_required_tests) or "none")
    table.add_row("Initial Pytest", "PASS" if result.initial_pytest_result.get("passed") else "FAIL")
    table.add_row("Final Pytest", "PASS" if result.final_pytest_result.get("passed") else "FAIL")
    table.add_row("Patch Success", "YES" if result.patch_result.get("success") else "NO")
    table.add_row("Trace Completeness", f"{result.trace_completeness.get('score', 0):.2f}")
    table.add_row("Ledger Verified", "YES" if result.ledger_verified else "NO")
    if result.model_reasoning:
        display = result.model_reasoning[:100] + "..." if len(result.model_reasoning) > 100 else result.model_reasoning
        table.add_row("Model Reasoning", display)

    console.print(table)

    if result.errors:
        console.print("\n[red]Errors:[/red]")
        for e in result.errors:
            console.print(f"  [red]• {e}[/red]")

    if output:
        output_data = {
            "status": result.status, "reason": result.reason,
            "iterations": result.iterations, "wall_time_sec": elapsed,
            "crg_confidence": result.crg_confidence,
            "crg_required_tests": result.crg_required_tests,
            "initial_pytest": result.initial_pytest_result,
            "final_pytest": result.final_pytest_result,
            "patch": result.patch_result,
            "trace_completeness": result.trace_completeness,
            "ledger_verified": result.ledger_verified,
            "model_reasoning": result.model_reasoning,
            "errors": result.errors,
        }
        with open(output, "w") as f:
            json.dump(output_data, f, indent=2)
        console.print(f"\n[dim]Output written to {output}[/dim]")

    if result.status != "success":
        raise typer.Exit(code=1)


@app.command()
def ledger(
    action: str = typer.Argument("verify", help="Action: verify"),
    path: str = typer.Option(..., "--path", "-p", help="Path to ledger file"),
):
    """Verify a ledger file."""
    from synthesis.packages.observability.ledger import JsonlLedger
    l = JsonlLedger(path)
    verification = l.verify()
    if verification.valid:
        console.print(f"[green]✅ Ledger verified: {verification.total_events} events, chain intact[/green]")
    else:
        console.print(f"[red]❌ Ledger corrupted at event {verification.error_event_index}: {verification.error_message}[/red]")
        raise typer.Exit(code=1)


@app.command()
def dashboard(
    ledger_path: str = typer.Option(..., "--ledger", "-l", help="Path to ledger file"),
):
    """Show a minimal dashboard from ledger data."""
    from synthesis.packages.observability.trace_completeness import trace_completeness_from_ledger
    console.print(Panel.fit("[bold blue]SYNTHESIS Dashboard[/bold blue]"))
    for task_type in ["bug_fix", "code_review", "test_generation"]:
        completeness = trace_completeness_from_ledger(ledger_path, task_type)
        score = completeness["score"]
        color = "green" if score == 1.0 else "yellow" if score > 0.5 else "red"
        console.print(f"  {task_type}: [{color}]{score:.2f}[/{color}] "
                      f"(missing: {', '.join(completeness['missing']) or 'none'})")
    console.print("\n[dim]Dashboard complete.[/dim]")


@app.command()
def benchmark(
    repo: str = typer.Option(..., "--repo", "-r", help="Path to golden demo repository"),
    runs: int = typer.Option(10, "--runs", "-n", help="Number of measurement runs"),
    warmup: int = typer.Option(2, "--warmup", "-w", help="Number of warmup runs"),
    ollama_model: str = typer.Option("qwen2.5-coder:7b", "--ollama-model", help="Ollama model to use"),
    json_output: Optional[str] = typer.Option(None, "--json", "-j", help="Write benchmark JSON to file"),
):
    """Benchmark the golden demo and report P50/P95/P99 latency."""
    console.print(Panel.fit("[bold blue]SYNTHESIS Benchmark[/bold blue]"))

    from synthesis.packages.observability.perf import benchmark_golden_demo

    console.print(f"[dim]Running {runs}+{warmup} golden demo iterations with model {ollama_model}...[/dim]")
    result = benchmark_golden_demo(repo, runs=runs, warmup=warmup, ollama_model=ollama_model)
    report = result["report"]

    table = Table(title=f"Golden Demo Benchmark ({runs} runs, {warmup} warmup)")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("P50", f"{report['p50_ms']:.1f}ms")
    table.add_row("P95", f"{report['p95_ms']:.1f}ms")
    table.add_row("P99", f"{report['p99_ms']:.1f}ms")
    table.add_row("Mean", f"{report['mean_ms']:.1f}ms")
    table.add_row("Min", f"{report['min_ms']:.1f}ms")
    table.add_row("Max", f"{report['max_ms']:.1f}ms")
    table.add_row("Total", f"{report['total_sec']:.3f}s")
    table.add_row("Count", str(report["count"]))

    console.print(table)

    if json_output:
        import json
        with open(json_output, "w") as f:
            json.dump(result, f, indent=2, default=str)
        console.print(f"\n[dim]Benchmark written to {json_output}[/dim]")


if __name__ == "__main__":
    app()
