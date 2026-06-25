"""MLX adapter — Phase 3 partial-maturity adapter (Apple Silicon only).

MLX runs on macOS arm64/aarch64 via mlx_lm.server at localhost:8080.
Discovery: GET /v1/models (OpenAI-compatible via mlx_lm.server)
Chat: POST /v1/chat/completions (OpenAI-compatible)

IMPORTANT (per architecture Section 3.1, rules 5):
  MLX is `unsupported_platform` unless macOS arm64/aarch64.
  The adapter detects platform at init and disables itself on
  non-Apple-Silicon systems.

MLX does NOT support embeddings natively.
"""

from __future__ import annotations

import os
import sys
import platform
import requests
from dataclasses import dataclass
from typing import Optional

from synthesis.packages.modelpool.adapters.base import (
    ChatRequest, ChatResponse, StreamChunk,
)

MLX_DEFAULT_HOST = "http://localhost:8080"
MLX_TIMEOUT_SEC = 1.5
MLX_CHAT_TIMEOUT_SEC = 30.0
MLX_ADAPTER_MATURITY = "partial"  # Phase 3: partial maturity


def _is_apple_silicon() -> bool:
    """Check if running on Apple Silicon (macOS arm64)."""
    return sys.platform == "darwin" and platform.machine() in ("arm64", "aarch64")


@dataclass
class MLXAdapter:
    """MLX adapter with OpenAI-compatible API.

    MLX serves via mlx_lm.server which exposes an OpenAI-compatible endpoint.
    Only available on Apple Silicon (macOS arm64).
    On other platforms, all methods return empty/error results.
    """

    name: str = "mlx"
    host: str = MLX_DEFAULT_HOST
    adapter_maturity: str = MLX_ADAPTER_MATURITY
    streaming_supported: bool = False
    _platform_supported: bool = True

    def __post_init__(self):
        self._platform_supported = _is_apple_silicon()

    # ── Discovery ─────────────────────────────────────────────────────────

    def discover(self) -> list[dict]:
        """Discover models via GET /v1/models (OpenAI-compatible format).

        On non-Apple-Silicon platforms, returns empty list immediately.
        """
        if not self._platform_supported:
            return []

        try:
            resp = requests.get(
                f"{self.host}/v1/models",
                timeout=MLX_TIMEOUT_SEC,
            )
            resp.raise_for_status()
            data = resp.json()
            models = []
            for model in data.get("data", []):
                model_id = model.get("id", "unknown")
                models.append({
                    "name": model_id,
                    "backend": self.name,
                    "locality": "local",  # MLX is always local
                    "adapter_maturity": self.adapter_maturity,
                    "lifecycle_state": "serving",
                    "supports_chat": True,
                    "supports_embeddings": False,
                    "context_window_safe": 8192,
                    "streaming_supported": self.streaming_supported,
                    "owned_by": model.get("owned_by", "mlx"),
                })
            return models
        except requests.ConnectionError:
            return []
        except Exception:
            return []

    def health(self) -> dict:
        """Check MLX backend health.

        On non-Apple-Silicon, reports unsupported_platform immediately.
        """
        if not self._platform_supported:
            return {
                "backend": self.name,
                "reachable": False,
                "error": "unsupported_platform: MLX requires Apple Silicon (macOS arm64). "
                         f"Current platform: {sys.platform}/{platform.machine()}",
            }

        try:
            resp = requests.get(
                f"{self.host}/v1/models",
                timeout=MLX_TIMEOUT_SEC,
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
        return self.discover()

    def capability_index(self) -> list[dict]:
        models = self.discover()
        return [{"model": m["name"], "supports_chat": m["supports_chat"],
                 "supports_embeddings": m["supports_embeddings"],
                 "context_window": m["context_window_safe"]}
                for m in models]

    # ── Chat ─────────────────────────────────────────────────────────────

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Send chat request via POST /v1/chat/completions (OpenAI format)."""
        if not self._platform_supported:
            raise RuntimeError("MLX not available on this platform")

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
                timeout=MLX_CHAT_TIMEOUT_SEC,
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
            raise TimeoutError(f"MLX chat timed out after {MLX_CHAT_TIMEOUT_SEC}s")
        except requests.ConnectionError:
            raise ConnectionError(f"MLX not reachable at {self.host}")
        except Exception as e:
            raise RuntimeError(f"MLX chat error: {e}")

    # ── Embeddings ───────────────────────────────────────────────────────

    def embeddings(self, texts: list[str], model: str) -> list[list[float]]:
        raise NotImplementedError(
            "MLX does not support embeddings via the OpenAI-compatible API. "
            "Use a dedicated embedding model or a different backend."
        )

    # ── Cancel ───────────────────────────────────────────────────────────

    def cancel(self) -> dict:
        return {
            "cancellable": False,
            "reason": "non_cancellable: MLX OpenAI-compatible API does not expose "
                      "request cancellation"
        }

    # ── Platform info ────────────────────────────────────────────────────

    def is_platform_supported(self) -> bool:
        return self._platform_supported
