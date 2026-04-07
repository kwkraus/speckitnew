from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuntimeStore:
    documents: dict[str, dict[str, Any]] = field(default_factory=dict)
    conversations: dict[str, dict[str, Any]] = field(default_factory=dict)
    chunks: dict[str, dict[str, Any]] = field(default_factory=dict)
    blobs: dict[str, bytes] = field(default_factory=dict)
    search_index_ready: bool = False
    cosmos_ready: bool = False

