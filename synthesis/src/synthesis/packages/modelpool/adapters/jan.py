"""Jan adapter — Phase 3 partial-maturity adapter.

Jan exposes an OpenAI-compatible API at localhost:1337/v1.
Discovery: GET /v1/models (OpenAI format)
Chat: POST /v1/chat/completions (OpenAI format)

IMPORTANT (per architecture Section 3.1, rule 6):
  Jan model locality is `unknown` unless proven local.
  Jan can connect to remote models — we must not assume locality.
  Only models explicitly running locally (e.g., via local Jan server)
  are marked as `local`. Models accessed through Jan's remote connectors
  remain `unknown` and are NOT selectable for chat.

Jan does NOT support embeddings natively.
"""

from __future__ import annotations

import requests
from dataclasses import dataclass
from typing import Optional

from synthesis.packages.modelpool.adapters.base import (
    ChatRequest, ChatResponse, StreamChunk,
)

JAN_DEFAULT_HOST = "http://localhost:1337"
JAN_TIMEOUT_SEC = 1.5
JAN_CHAT_TIMEOUT_SEC = 30.0
JAN_ADAPTER_MATURITY = "partial"  # Phase 3: partial maturity


@dataclass
class JanAdapter:
    """Jan adapter with OpenAI-compatible API.

    Jan serves an OpenAI-compatible endpoint at /v1.
    Discovery uses GET /v1/models (OpenAI format).
    Chat uses POST /v1/chat/completions (OpenAI format).
    Embeddings are not supported.

    Model locality is `unknown` unless the model metadata
    indicates it's running locally (e.g., via local Jan server).
    """

    name: str = "jan"
    host: str = JAN_DEFAULT_HOST
    adapter_maturity: str = JAN_ADAPTER_MATURITY
    streaming_supported: bool = True

    # ── Discovery ─────────────────────────────────────────────────────────

    def discover(self) -> list[dict]:
        """Discover models via GET /v1/models (OpenAI-compatible format).

        Returns list of model dicts with standardized capability fields.
        Model locality is `unknown` unless proven local.
        """
        try:
            resp = requests.get(
                f"{self.host}/v1/models",
                timeout=JAN_TIMEOUT_SEC,
            )
            resp.raise_for_status()
            data = resp.json()
            models = []
            for model in data.get("data", []):
                model_id = model.get("id", "unknown")

                # Jan locality: check for indicators of local execution
                locality = "unknown"
                model_meta = model.get("metadata", {}) if isinstance(model, dict) else {}
                if model_meta.get("engine") in ("cortex.llamacpp", "llama.cpp"):
                    locality = "local"

                models.append({
                    "name": model_id,
                    "backend": self.name,
                    "locality": locality,
                    "adapter_maturity": self.adapter_maturity,
                    "lifecycle_state": "serving" if locality == "local" else "unknown",
                    "supports_chat": True,
                    "supports_embeddings": False,
                    "context_window_safe": model_meta.get("ctx_len", 8192) if isinstance(model_meta, dict) else 8192,
                    "streaming_supported": self.streaming_supported,
                    "owned_by": model.get("owned_by", "jan"),
                })
            return models
        except requests.ConnectionError:
            return []
        except Exception:
            return []

    def health(self) -> dict:
        """Check Jan backend health."""
        try:
            resp = requests.get(
                f"{self.host}/v1/models",
                timeout=JAN_TIMEOUT_SEC,
            )
            return {
                "backend": self.name,
                "reachable": True,
                "status_code": resp.status_code,
                "latency_ms": resp.elapsed.total_seconds() * 1000,
            }
        except requests.ConnectionError as e:
            return {"backend": self.name, "reachable": False, "error": str(e)}
        except Exception as e:
            return {"backend": self.name, "reachable": False, "error": str(e)}

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

    # ── Chat ─────────────────────────────────────────────────────────────

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Send chat request via POST /v1/chat/completions (OpenAI format)."""
        try:
            messages = request.messages
            if messages and isinstance(messages[0], dict) and "role" not in messages[0]:
                messages = [{"role": "user", "content": msg.get("content", str(msg))}
                           for msg in messages]

            payload = {
                "model": request.model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": False,
            }
            resp = requests.post(
                f"{self.host}/v1/chat/completions",
                json=payload,
                timeout=JAN_CHAT_TIMEOUT_SEC,
            )
            resp.raise_for_status()
            data = resp.json()

            choices = data.get("choices", [])
            message = choices[0].get("message", {}) if choices else {}
            usage = data.get("usage", {})

            return ChatResponse(
                model=data.get("model", request.model),
                content=message.get("content", ""),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                raw=data,
            )
        except requests.Timeout:
            raise TimeoutError(f"Jan chat timed out after {JAN_CHAT_TIMEOUT_SEC}s")
        except requests.ConnectionError:
            raise ConnectionError(f"Jan not reachable at {self.host}")
        except Exception as e:
            raise RuntimeError(f"Jan chat error: {e}")

    # ── Embeddings ───────────────────────────────────────────────────────

    def embeddings(self, texts: list[str], model: str) -> list[list[float]]:
        """Jan does not support embeddings via the OpenAI-compatible endpoint."""
        raise NotImplementedError(
            "Jan does not support embeddings via the OpenAI-compatible API. "
            "Use a different backend for embeddings."
        )

    # ── Cancel ───────────────────────────────────────────────────────────

    def cancel(self) -> dict:
        """Jan does not support native request cancellation."""
        return {
            "cancellable": False,
            "reason": "non_cancellable: Jan OpenAI-compatible API does not expose "
                      "request cancellation"
        }
