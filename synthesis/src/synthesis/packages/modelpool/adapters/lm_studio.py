"""LM Studio adapter — Phase 3 partial-maturity adapter.

LM Studio exposes an OpenAI-compatible API at localhost:1234/v1.
Discovery: GET /v1/models
Chat: POST /v1/chat/completions

LM Studio does NOT support embeddings natively (requires plugin).
Model loading is on first call (cold start).
Streaming is supported but not implemented in Phase 3.
"""

from __future__ import annotations

import requests
from dataclasses import dataclass
from typing import Optional

from synthesis.packages.modelpool.adapters.base import (
    ChatRequest, ChatResponse, StreamChunk,
)

LM_STUDIO_DEFAULT_HOST = "http://localhost:1234"
LM_STUDIO_TIMEOUT_SEC = 1.5
LM_STUDIO_CHAT_TIMEOUT_SEC = 30.0
LM_STUDIO_ADAPTER_MATURITY = "partial"  # Phase 3: partial maturity


@dataclass
class LMStudioAdapter:
    """LM Studio adapter with OpenAI-compatible API.

    LM Studio serves an OpenAI-compatible endpoint at /v1.
    Discovery uses GET /v1/models (OpenAI format).
    Chat uses POST /v1/chat/completions (OpenAI format).
    Embeddings are not supported without plugins.
    """

    name: str = "lm_studio"
    host: str = LM_STUDIO_DEFAULT_HOST
    adapter_maturity: str = LM_STUDIO_ADAPTER_MATURITY
    streaming_supported: bool = True  # LM Studio supports streaming natively

    # ── Discovery ─────────────────────────────────────────────────────────

    def discover(self) -> list[dict]:
        """Discover models via GET /v1/models (OpenAI-compatible format).

        Returns list of model dicts with standardized capability fields.
        LM Studio catalog is not locality-guessed; models may be remote.
        """
        try:
            resp = requests.get(
                f"{self.host}/v1/models",
                timeout=LM_STUDIO_TIMEOUT_SEC,
            )
            resp.raise_for_status()
            data = resp.json()
            models = []
            # LM Studio returns {"object": "list", "data": [{"id": "...", ...}]}
            for model in data.get("data", []):
                model_id = model.get("id", "unknown")
                models.append({
                    "name": model_id,
                    "backend": self.name,
                    "locality": "local",  # LM Studio runs locally by default
                    "adapter_maturity": self.adapter_maturity,
                    "lifecycle_state": "serving",
                    "supports_chat": True,
                    "supports_embeddings": False,  # No native embedding support
                    "context_window_safe": 8192,    # Conservative default
                    "streaming_supported": self.streaming_supported,
                    "owned_by": model.get("owned_by", "lm_studio"),
                })
            return models
        except requests.ConnectionError:
            return []
        except Exception:
            return []

    def health(self) -> dict:
        """Check LM Studio backend health."""
        try:
            resp = requests.get(
                f"{self.host}/v1/models",
                timeout=LM_STUDIO_TIMEOUT_SEC,
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
        """Send chat request via POST /v1/chat/completions (OpenAI format).

        LM Studio uses the OpenAI chat completions format.
        Messages must be in OpenAI format: [{"role": "user", "content": "..."}].
        """
        try:
            # Convert messages to OpenAI format if they're plain dicts
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
                timeout=LM_STUDIO_CHAT_TIMEOUT_SEC,
            )
            resp.raise_for_status()
            data = resp.json()

            # OpenAI format: {"choices": [{"message": {"content": "..."}}], "usage": {...}}
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
            raise TimeoutError(f"LM Studio chat timed out after {LM_STUDIO_CHAT_TIMEOUT_SEC}s")
        except requests.ConnectionError:
            raise ConnectionError(f"LM Studio not reachable at {self.host}")
        except Exception as e:
            raise RuntimeError(f"LM Studio chat error: {e}")

    # ── Embeddings ───────────────────────────────────────────────────────

    def embeddings(self, texts: list[str], model: str) -> list[list[float]]:
        """LM Studio does not support embeddings natively.

        Raises NotImplementedError — embeddings require plugin installation.
        """
        raise NotImplementedError(
            "LM Studio does not support embeddings natively. "
            "Install an embeddings plugin or use a different backend."
        )

    # ── Cancel ───────────────────────────────────────────────────────────

    def cancel(self) -> dict:
        """LM Studio does not support native request cancellation."""
        return {
            "cancellable": False,
            "reason": "non_cancellable: LM Studio OpenAI-compatible API does "
                      "not expose request cancellation"
        }

    # ── Backend-specific ─────────────────────────────────────────────────

    def is_local(self) -> bool:
        """LM Studio models are always local (runs on localhost).

        Returns True — LM Studio is a desktop application that runs locally.
        Unlike Jan, there is no remote model support.
        """
        return True
