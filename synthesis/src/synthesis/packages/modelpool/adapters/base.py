"""Model backend adapter protocol and shared types."""

from dataclasses import dataclass, field
from typing import Optional, Protocol


@dataclass
class ChatRequest:
    model: str
    messages: list[dict]
    max_tokens: int = 2048
    temperature: float = 0.7
    stream: bool = False


@dataclass
class ChatResponse:
    model: str
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    raw: Optional[dict] = None


@dataclass
class StreamChunk:
    delta: str
    finish_reason: Optional[str] = None
    raw: Optional[dict] = None


class ModelBackendAdapter(Protocol):
    """Protocol for backend adapters."""

    def discover(self) -> list[dict]: ...
    def health(self) -> dict: ...
    def list_models(self) -> list[dict]: ...
    def capability_index(self) -> list[dict]: ...
    def chat(self, request: ChatRequest) -> ChatResponse: ...
    def embeddings(self, texts: list[str], model: str) -> list[list[float]]: ...
    def cancel(self) -> dict: ...
