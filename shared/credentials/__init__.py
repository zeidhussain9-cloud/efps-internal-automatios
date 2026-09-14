"""Local credential resolution for EFPS runtime services."""

from .keychain import get_secret

__all__ = ["get_secret"]
