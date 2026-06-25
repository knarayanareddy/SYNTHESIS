"""LM Studio adapter conformance tests — runs only when LM_STUDIO_HOST is set."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "synthesis", "src"))

import pytest

LM_STUDIO_HOST = os.getenv("LM_STUDIO_HOST", "http://localhost:1234")


class TestLMStudioAdapter:
    """Tests for LM Studio adapter — skipped in CI, runnable locally."""

    @pytest.fixture
    def adapter(self):
        from synthesis.packages.modelpool.adapters.lm_studio import LMStudioAdapter
        return LMStudioAdapter(host=LM_STUDIO_HOST)

    @pytest.mark.skipif(True, reason="LM Studio not available in CI. Run locally with: "
                                     "pytest tests/integration/test_lm_studio_adapter.py -p no:skip")
    def test_lm_studio_discovery(self, adapter):
        """Test LM Studio model discovery."""
        models = adapter.discover()
        assert isinstance(models, list)

    @pytest.mark.skipif(True, reason="LM Studio not available in CI")
    def test_lm_studio_health(self, adapter):
        """Test LM Studio health check."""
        health = adapter.health()
        assert isinstance(health, dict)
        assert "reachable" in health

    @pytest.mark.skipif(True, reason="LM Studio not available in CI")
    def test_lm_studio_capability_index(self, adapter):
        """Test capability index format."""
        cap = adapter.capability_index()
        assert isinstance(cap, list)
        if cap:
            assert "model" in cap[0]
            assert "supports_chat" in cap[0]

    @pytest.mark.skipif(True, reason="LM Studio not available in CI")
    def test_lm_studio_embeddings_not_supported(self, adapter):
        """LM Studio should raise NotImplementedError for embeddings."""
        with pytest.raises(NotImplementedError):
            adapter.embeddings(["test"], "model")

    @pytest.mark.skipif(True, reason="LM Studio not available in CI")
    def test_lm_studio_cancel_non_cancellable(self, adapter):
        """LM Studio should report non-cancellable."""
        result = adapter.cancel()
        assert result["cancellable"] is False

    @pytest.mark.skipif(True, reason="LM Studio not available in CI")
    def test_lm_studio_is_local(self, adapter):
        """LM Studio models should be marked as local."""
        assert adapter.is_local() is True

    # ── Offline tests (always run) ──

    def test_lm_studio_adapter_interface(self, adapter):
        """Verify LM Studio adapter implements all required methods."""
        assert hasattr(adapter, "discover")
        assert hasattr(adapter, "health")
        assert hasattr(adapter, "list_models")
        assert hasattr(adapter, "capability_index")
        assert hasattr(adapter, "chat")
        assert hasattr(adapter, "embeddings")
        assert hasattr(adapter, "cancel")
        assert callable(adapter.discover)
        assert callable(adapter.health)
        assert callable(adapter.chat)

    def test_lm_studio_adapter_default_host(self, adapter):
        """Default host should be localhost:1234."""
        assert adapter.host == "http://localhost:1234"

    def test_lm_studio_adapter_name(self, adapter):
        """Adapter name should be lm_studio."""
        assert adapter.name == "lm_studio"

    def test_lm_studio_adapter_maturity(self, adapter):
        """Adapter maturity should be partial in Phase 3."""
        assert adapter.adapter_maturity == "partial"

    def test_lm_studio_discovery_offline_returns_empty(self, adapter):
        """When LM Studio is offline, discovery should return empty list."""
        models = adapter.discover()
        assert isinstance(models, list)
        # When offline, should return empty (not fail)

    def test_lm_studio_health_offline(self, adapter):
        """When offline, health should report unreachable."""
        health = adapter.health()
        assert health["reachable"] is False
        assert "error" in health
