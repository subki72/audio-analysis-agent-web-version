"""
Tool registry with auto-discovery via @register_tool decorator.

Import order below determines tool ordering in TOOL_SCHEMAS.
"""
from .registry import TOOL_REGISTRY, TOOL_SCHEMAS, register_tool  # noqa: F401

from .metadata import get_audio_metadata   # noqa: F401, E402
from .silence import detect_silence        # noqa: F401, E402
from .volume import detect_clipping        # noqa: F401, E402
from .noise import detect_noise            # noqa: F401, E402

__all__ = [
    "TOOL_REGISTRY",
    "TOOL_SCHEMAS",
    "register_tool",
    "get_audio_metadata",
    "detect_silence",
    "detect_clipping",
    "detect_noise",
]
