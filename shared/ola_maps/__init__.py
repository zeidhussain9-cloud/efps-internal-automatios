"""Reusable Ola Maps (Krutrim) technical adapter; business decisions stay in modules."""

from .client import OlaGeocodeResult, OlaMapsClient

__all__ = ["OlaGeocodeResult", "OlaMapsClient"]
