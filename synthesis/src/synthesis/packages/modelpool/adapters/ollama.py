"""Ollama adapter — Phase 0 full-maturity adapter."""

import requests
from dataclasses import dataclass
from typing import Optional

from synthesis.packages.modelpool.adapters.base import (
    ChatRequest, ChatResponse, StreamChunk,
)


OLLAMA_DEFAULT_HOST = "http://localhost:11434"
OLLAMA_TIMEOUT_SEC = 1.5
OLLAMA_CHAT_TIMEOUT_SEC = 30.0


@dataclass
class OllamaAdapter:
    name: str = "ollama"
    host: str = OLLAMA_DEFAULT_HOST
    adapter_maturity: str = "full"
    streaming_supported: bool = False

    def discover(self) -> list[dict]:
        """Probe Ollama for available models via GET /api/tags."""
        try:
            resp = requests.get(
                f"{self.host}/api/tags",
                timeout=OLLAMA_TIMEOUT_SEC,
            )
            resp.raise_for_status()
            data = resp.json()
            models = []
            for model in data.get("models", []):
                models.append({
                    "name": model.get("name", "unknown"),
                    "backend": self.name,
                    "locality": "local",
                    "adapter_maturity": self.adapter_maturity,
                    "lifecycle_state": "serving",
                    "supports_chat": True,
                    "supports_embeddings": False,
                    "context_window_safe": 8192,
                    "streaming_supported": self.streaming_supported,
                })
            return models
        except Exception:
            return []

    def health(self) -> dict:
        """Check Ollama backend health."""
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=OLLAMA_TIMEOUT_SEC)
            return {
                "backend": self.name,
                "reachable": True,
                "status_code": resp.status_code,
                "latency_ms": resp.elapsed.total_seconds() * 1000,
            }
        except Exception as e:
            return {
                "backend": self.name,
                "reachable": False,
                "error": str(e),
            }

    def list_models(self) -> list[dict]:
        """Return discovered models."""
        return self.discover()

    def capability_index(self) -> list[dict]:
        """Return model capability list."""
        models = self.discover()
        return [{"model": m["name"], "supports_chat": m["supports_chat"],
                 "supports_embeddings": m["supports_embeddings"],
                 "context_window": m["context_window_safe"]}
                for m in models]

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Send a chat request to Ollama POST /api/chat."""
        try:
            payload = {
                "model": request.model,
                "messages": request.messages,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens,
                },
            }
            resp = requests.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=OLLAMA_CHAT_TIMEOUT_SEC,
            )
            resp.raise_for_status()
            data = resp.json()
            return ChatResponse(
                model=data.get("model", request.model),
                content=data.get("message", {}).get("content", ""),
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0),
                raw=data,
            )
        except requests.Timeout:
            raise TimeoutError(f"Ollama chat timed out after {OLLAMA_CHAT_TIMEOUT_SEC}s")
        except requests.ConnectionError:
            raise ConnectionError(f"Ollama not reachable at {self.host}")
        except Exception as e:
            raise RuntimeError(f"Ollama chat error: {e}")

    def embeddings(self, texts: list[str], model: str) -> list[list[float]]:
        """Get embeddings from Ollama POST /api/embeddings."""
        try:
            payload = {"model": model, "prompt": texts[0] if texts else ""}
            resp = requests.post(
                f"{self.host}/api/embeddings",
                json=payload,
                timeout=OLLAMA_TIMEOUT_SEC,
            )
            resp.raise_for_status()
            data = resp.json()
            return [data.get("embedding", [])]
        except Exception as e:
            raise RuntimeError(f"Ollama embeddings error: {e}")

    def cancel(self) -> dict:
        """Ollama does not support native cancellation."""
        return {"cancellable": False, "reason": "non_cancellable: Ollama API does not support request cancellation"}
