"""Error injection tests for LM Studio adapter — verifies graceful handling."""

import os
import sys
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "synthesis", "src"))

import pytest
import requests
from synthesis.packages.modelpool.adapters.lm_studio import LMStudioAdapter
from synthesis.packages.modelpool.adapters.base import ChatRequest


class TestLMStudioErrors:
    """Tests that LM Studio adapter handles error responses gracefully."""

    @pytest.fixture
    def adapter(self):
        return LMStudioAdapter(host="http://localhost:1234")

    def test_discovery_503_model_loading(self, adapter):
        """503 Service Unavailable should return empty list, not crash."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.HTTPError("503 Server Error")
            models = adapter.discover()
            assert models == []  # Should not raise

    def test_discovery_malformed_json(self, adapter):
        """Malformed JSON response should return empty list."""
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.side_effect = ValueError("Invalid JSON")
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp
            models = adapter.discover()
            assert models == []

    def test_discovery_empty_data(self, adapter):
        """Response with no models should return empty list."""
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"object": "list", "data": []}
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp
            models = adapter.discover()
            assert models == []

    def test_chat_empty_choices(self, adapter):
        """Empty choices in chat response should return empty content."""
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "model": "test-model",
                "choices": [],
                "usage": {"prompt_tokens": 10, "completion_tokens": 0},
            }
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp

            response = adapter.chat(ChatRequest(
                model="test-model",
                messages=[{"role": "user", "content": "hi"}],
            ))
            assert response.content == ""  # Empty is OK — model validator catches this

    def test_chat_missing_message_field(self, adapter):
        """Response with missing message.content should return empty content."""
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "model": "test-model",
                "choices": [{"message": {}}],  # No content field
                "usage": {},
            }
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp

            response = adapter.chat(ChatRequest(
                model="test-model",
                messages=[{"role": "user", "content": "hi"}],
            ))
            assert response.content == ""

    def test_health_connection_refused(self, adapter):
        """Connection refused should report unreachable."""
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.ConnectionError("Connection refused")
            health = adapter.health()
            assert health["reachable"] is False
            assert "Connection refused" in str(health.get("error", ""))

    def test_chat_timeout(self, adapter):
        """Chat timeout should raise TimeoutError."""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.Timeout("Request timed out")
            with pytest.raises(TimeoutError):
                adapter.chat(ChatRequest(
                    model="test-model",
                    messages=[{"role": "user", "content": "hi"}],
                ))

    def test_chat_connection_error(self, adapter):
        """Connection error should raise ConnectionError."""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.ConnectionError("No route to host")
            with pytest.raises(ConnectionError):
                adapter.chat(ChatRequest(
                    model="test-model",
                    messages=[{"role": "user", "content": "hi"}],
                ))
