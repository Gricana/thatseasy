"""Validation for URLs accepted by the HTTP adapter."""

from urllib.parse import urlsplit


class UrlValidationError(ValueError):
    """The input is not an absolute HTTP(S) URL with a valid authority."""


def validate_url(url: str) -> None:
    """Reject malformed or unsupported addresses before opening a connection."""
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        parsed.port
    except ValueError as exc:
        raise UrlValidationError("URL is malformed or contains an invalid port.") from exc

    if (
        parsed.scheme not in {"http", "https"}
        or not hostname
        or any(character.isspace() for character in url)
    ):
        raise UrlValidationError("URL must be an absolute HTTP(S) URL with a hostname.")
