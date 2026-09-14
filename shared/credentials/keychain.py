"""macOS Keychain credential provider."""

from __future__ import annotations

import subprocess


KEYCHAIN_ACCOUNT = "efps"


class MissingKeychainSecret(RuntimeError):
    """Raised when a required EFPS Keychain secret is unavailable."""


def get_secret(service: str, *, account: str = KEYCHAIN_ACCOUNT) -> str:
    """Return a Keychain secret without exposing it in logs."""
    if not service.strip():
        raise ValueError("service must not be empty")

    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-a",
                account,
                "-s",
                service,
                "-w",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise MissingKeychainSecret(
            "macOS security command is unavailable."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise MissingKeychainSecret(
            f"Keychain secret '{service}' is unavailable."
        ) from exc

    value = result.stdout.strip()
    if not value:
        raise MissingKeychainSecret(
            f"Keychain secret '{service}' is empty."
        )

    return value
