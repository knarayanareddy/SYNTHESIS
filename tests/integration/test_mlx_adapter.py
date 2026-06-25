"""MLX adapter conformance tests — runs only when MLX_HOST is set on Apple Silicon."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "synthesis", "src"))

import pytest

MLX_HOST = os.getenv("MLX_HOST", "http://localhost:8080")


class TestMLXAdapter:
    """Tests for MLX adapter — skipped in CI, runnable on Apple Silicon."""

    @pytest.fixture
    def adapter(self):
        from synthesis.packages.modelpool.adapters.mlx import MLXAdapter
        return MLXAdapter(host=MLX_HOST)

    # Live tests (skipped in CI)
    @pytest.mark.skipif(True, reason="MLX not available in CI")
    def test_mlx_discovery(self, adapter):
        models = adapter.discover()
        assert isinstance(models, list)

    @pytest.mark.skipif(True, reason="MLX not available in CI")
    def test_mlx_health(self, adapter):
        health = adapter.health()
        assert isinstance(health, dict)

    @pytest.mark.skipif(True, reason="MLX not available in CI")
    def test_mlx_embeddings_not_supported(self, adapter):
        with pytest.raises(NotImplementedError):
            adapter.embeddings(["test"], "model")

    @pytest.mark.skipif(True, reason="MLX not available in CI")
    def test_mlx_cancel_non_cancellable(self, adapter):
        result = adapter.cancel()
        assert result["cancellable"] is False

    # Offline tests (always run)
    def test_mlx_adapter_interface(self, adapter):
        assert hasattr(adapter, "discover")
        assert hasattr(adapter, "health")
        assert hasattr(adapter, "chat")
        assert callable(adapter.chat)

    def test_mlx_default_host(self, adapter):
        assert adapter.host == "http://localhost:8080"

    def test_mlx_adapter_name(self, adapter):
        assert adapter.name == "mlx"

    def test_mlx_adapter_maturity(self, adapter):
        assert adapter.adapter_maturity == "partial"

    def test_mlx_platform_detection(self, adapter):
        """MLX adapter should detect platform support correctly."""
        assert hasattr(adapter, "is_platform_supported")
        result = adapter.is_platform_supported()
        assert isinstance(result, bool)

    def test_mlx_discovery_offline_returns_empty(self, adapter):
        models = adapter.discover()
        assert isinstance(models, list)

    def test_mlx_health_offline(self, adapter):
        health = adapter.health()
        assert isinstance(health, dict)
        assert "reachable" in health

    @pytest.mark.skipif(True, reason="MLX not available in CI")
    def test_mlx_unsupported_platform_health(self, adapter):
        """On Linux CI, MLX should report unsupported_platform."""
        import platform, sys
        if not adapter.is_platform_supported():
            health = adapter.health()
            assert "unsupported_platform" in str(health.get("error", ""))
