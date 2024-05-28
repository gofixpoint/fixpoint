"""The Form Agent service"""

from . import steps


def info() -> str:
    """Info on the service"""
    return (
        "I am a service that uses AI agents to gather info from your users and "
        "turn that into structured forms"
    )


__all__ = ["steps"]
