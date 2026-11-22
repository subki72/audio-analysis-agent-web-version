"""Unit tests for AudioAnalysisAgent orchestrator metadata and tool schemas."""

from src.agent.orchestrator import SYSTEM_PROMPT
from src.tools import TOOL_REGISTRY, TOOL_SCHEMAS


def test_system_prompt_contains_required_tools() -> None:
    """Ensures ReAct system prompt declares all four core ffmpeg tools."""
    assert "get_audio_metadata" in SYSTEM_PROMPT
    assert "detect_silence" in SYSTEM_PROMPT
    assert "detect_clipping" in SYSTEM_PROMPT
    assert "detect_noise" in SYSTEM_PROMPT


def test_tool_registry_populated() -> None:
    """Verifies tool auto-discovery registers callable tools and schemas."""
    assert len(TOOL_REGISTRY) >= 4
    assert len(TOOL_SCHEMAS) >= 4
