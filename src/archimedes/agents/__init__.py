"""Agent layer modules."""

from .client import FoundryChatClient, create_foundry_chat_client
from .factory import AgentDefinition, AgentFactory
from .pattern_detector import PatternDetector

__all__ = [
    "AgentDefinition",
    "AgentFactory",
    "FoundryChatClient",
    "PatternDetector",
    "create_foundry_chat_client",
]
