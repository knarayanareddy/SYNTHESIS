"""Unit tests for deterministic router and sanitizer."""

from synthesis.packages.router.deterministic import (
    select_model, TaskSpec, RoutingResult, SELECTABLE_MATURITY, SELECTABLE_LIFECYCLE,
)
from synthesis.packages.router.sanitize import sanitize_model_name


class TestRouter:
    def _make_pool(self, models=None):
        if models is None:
            models = [{
                "name": "qwen2.5-coder:7b",
                "backend": "ollama",
                "locality": "local",
                "adapter_maturity": "full",
                "lifecycle_state": "serving",
                "supports_chat": True,
                "supports_embeddings": False,
            }]
        return {"backends": [{"name": "ollama", "models": models}]}

    def test_selects_full_local(self):
        pool = self._make_pool()
        task = TaskSpec(task_type="bug_fix", required_capability="chat")
        result = select_model(pool, task)
        assert not result.no_model_available
        assert result.selected_model == "qwen2.5-coder:7b"
        assert result.locality == "local"

    def test_rejects_non_local(self):
        pool = self._make_pool([{
            "name": "remote-model",
            "backend": "ollama",
            "locality": "remote",
            "adapter_maturity": "full",
            "lifecycle_state": "serving",
            "supports_chat": True,
        }])
        task = TaskSpec(task_type="bug_fix")
        result = select_model(pool, task)
        assert result.no_model_available
        assert len(result.rejection_reasons) > 0
        assert result.rejection_reasons[0]["reason"] == "non_local_candidate_rejected_by_default"

    def test_rejects_partial_adapter(self):
        pool = self._make_pool([{
            "name": "partial-model",
            "backend": "lm_studio",
            "locality": "local",
            "adapter_maturity": "partial",
            "lifecycle_state": "serving",
            "supports_chat": True,
        }])
        task = TaskSpec(task_type="bug_fix")
        result = select_model(pool, task)
        assert result.no_model_available

    def test_rejects_non_serving(self):
        pool = self._make_pool([{
            "name": "cold-model",
            "backend": "ollama",
            "locality": "local",
            "adapter_maturity": "full",
            "lifecycle_state": "cold",
            "supports_chat": True,
        }])
        task = TaskSpec(task_type="bug_fix")
        result = select_model(pool, task)
        assert result.no_model_available

    def test_rejects_missing_chat_capability(self):
        pool = self._make_pool([{
            "name": "no-chat-model",
            "backend": "ollama",
            "locality": "local",
            "adapter_maturity": "full",
            "lifecycle_state": "serving",
            "supports_chat": False,
            "supports_embeddings": True,
        }])
        task = TaskSpec(task_type="bug_fix", required_capability="chat")
        result = select_model(pool, task)
        assert result.no_model_available

    def test_cloud_never_selected(self):
        pool = self._make_pool([{
            "name": "cloud-model",
            "backend": "openai",
            "locality": "remote",
            "adapter_maturity": "full",
            "lifecycle_state": "serving",
            "supports_chat": True,
        }])
        task = TaskSpec(task_type="bug_fix")
        result = select_model(pool, task)
        assert result.cloud_gate_result == "not_allowed"
        assert result.no_model_available

    def test_no_model_available(self):
        pool = {"backends": []}
        task = TaskSpec(task_type="bug_fix")
        result = select_model(pool, task)
        assert result.no_model_available
        assert result.candidates_considered == 0


class TestSanitize:
    def test_sanitize_control_characters(self):
        result = sanitize_model_name("hello\x00world")
        assert "\ufffd" in result

    def test_sanitize_angle_brackets(self):
        result = sanitize_model_name("<script>alert('xss')</script>")
        assert "<" not in result
        assert ">" not in result

    def test_sanitize_truncation(self):
        result = sanitize_model_name("a" * 200, max_len=10)
        assert len(result) <= 10

    def test_sanitize_normal_name(self):
        result = sanitize_model_name("qwen2.5-coder:7b")
        assert result == "qwen2.5-coder:7b"
