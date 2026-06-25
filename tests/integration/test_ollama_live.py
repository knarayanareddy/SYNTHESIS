"""Live Ollama conformance tests — runs only when OLLAMA_HOST is set."""

import os
import requests
import pytest

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

def _is_ollama_available() -> bool:
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=1.0)
        return response.status_code == 200
    except Exception:
        return False

pytestmark = pytest.mark.skipif(
    not _is_ollama_available(),
    reason=f"Ollama server not reachable at {OLLAMA_HOST}",
)


class TestOllamaLive:
    """Tests that require a real Ollama instance."""

    @pytest.mark.skipif(
        False,  # Always skipped unless explicitly enabled
        reason="Requires running Ollama — run manually with: pytest tests/integration/test_ollama_live.py --no-header -p no:skip"
    )
    def test_ollama_discovery_real(self):
        """Test Ollama discovery against a real backend."""
        from synthesis.packages.modelpool.adapters.ollama import OllamaAdapter
        adapter = OllamaAdapter(host=OLLAMA_HOST)
        models = adapter.discover()
        assert isinstance(models, list)
        # If Ollama is running with models, we should find at least one
        if models:
            assert "name" in models[0]
            assert models[0]["locality"] == "local"

    @pytest.mark.skipif(False, reason="Requires running Ollama")
    def test_ollama_chat_real(self):
        """Test real Ollama chat call."""
        from synthesis.packages.modelpool.adapters.ollama import OllamaAdapter
        from synthesis.packages.modelpool.adapters.base import ChatRequest

        adapter = OllamaAdapter(host=OLLAMA_HOST)
        models = adapter.discover()
        if not models:
            pytest.skip("No models available in Ollama")

        # Prefer qwen2.5:3b for chat test if available
        model_name = models[0]["name"]
        for m in models:
            if "qwen2.5:3b" in m["name"]:
                model_name = m["name"]
                break

        response = adapter.chat(ChatRequest(
            model=model_name,
            messages=[{"role": "user", "content": "Say 'hello synthesis' and nothing else."}],
            max_tokens=100,
            temperature=0.0,
        ))
        assert response.content
        assert "hello" in response.content.lower()

    @pytest.mark.skipif(False, reason="Requires running Ollama")
    def test_ollama_health_real(self):
        """Test Ollama health check against real backend."""
        from synthesis.packages.modelpool.adapters.ollama import OllamaAdapter
        adapter = OllamaAdapter(host=OLLAMA_HOST)
        health = adapter.health()
        assert health["reachable"]

    @pytest.mark.skipif(False, reason="Requires running Ollama")
    def test_ollama_cancel_returns_non_cancellable(self):
        """Test that cancel() returns non-cancellable for Ollama."""
        from synthesis.packages.modelpool.adapters.ollama import OllamaAdapter
        adapter = OllamaAdapter(host=OLLAMA_HOST)
        result = adapter.cancel()
        assert result["cancellable"] is False
        assert "non_cancellable" in result["reason"]
