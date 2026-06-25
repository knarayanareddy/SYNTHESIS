"""Error injection tests for Jan adapter — verifies graceful handling."""

import os, sys
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "synthesis", "src"))

import pytest, requests
from synthesis.packages.modelpool.adapters.jan import JanAdapter
from synthesis.packages.modelpool.adapters.base import ChatRequest


class TestJanErrors:
    @pytest.fixture
    def adapter(self):
        return JanAdapter(host="http://localhost:1337")

    def test_discovery_503(self, adapter):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.HTTPError("503 Server Error")
            assert adapter.discover() == []

    def test_discovery_malformed_json(self, adapter):
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.side_effect = ValueError("Invalid JSON")
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp
            assert adapter.discover() == []

    def test_chat_empty_choices(self, adapter):
        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"model":"t","choices":[],"usage":{}}
            mock_resp.raise_for_status.return_value = None
            mock_post.return_value = mock_resp
            response = adapter.chat(ChatRequest(model="t", messages=[{"role":"user","content":"hi"}]))
            assert response.content == ""

    def test_health_connection_refused(self, adapter):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.ConnectionError("Connection refused")
            health = adapter.health()
            assert health["reachable"] is False

    def test_chat_timeout(self, adapter):
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.Timeout("Request timed out")
            with pytest.raises(TimeoutError):
                adapter.chat(ChatRequest(model="t", messages=[{"role":"user","content":"hi"}]))

    def test_chat_connection_error(self, adapter):
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.ConnectionError("No route to host")
            with pytest.raises(ConnectionError):
                adapter.chat(ChatRequest(model="t", messages=[{"role":"user","content":"hi"}]))

    def test_discovery_unknown_locality(self, adapter):
        """Verify Jan models default to unknown locality."""
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"object":"list","data":[
                {"id":"remote-gpt-4","owned_by":"jan","metadata":{}},
                {"id":"local-model","owned_by":"jan","metadata":{"engine":"cortex.llamacpp"}}
            ]}
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp
            models = adapter.discover()
            assert models[0]["locality"] == "unknown"  # remote-gpt-4
            assert models[1]["locality"] == "local"     # local-model
