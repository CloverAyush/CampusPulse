from urllib.parse import urlparse

from app.config import settings


def validate_attachment_url(value: str | None) -> str | None:
    """Reject any URL a browser could turn into script execution or a local-network probe."""
    if value is None:
        return None

    candidate = value.strip()
    if not candidate:
        return None

    if len(candidate) > settings.MAX_ATTACHMENT_URL_LENGTH:
        raise ValueError(f"URL must be at most {settings.MAX_ATTACHMENT_URL_LENGTH} characters")

    parsed = urlparse(candidate)
    if parsed.scheme.lower() not in settings.ALLOWED_ATTACHMENT_SCHEMES:
        allowed = ", ".join(settings.ALLOWED_ATTACHMENT_SCHEMES)
        raise ValueError(f"URL scheme must be one of: {allowed}")

    if not parsed.netloc:
        raise ValueError("URL must include a host")

    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("URL must include a host")

    if settings.ALLOWED_ATTACHMENT_HOSTS:
        permitted = any(
            host == allowed or host.endswith(f".{allowed}")
            for allowed in settings.ALLOWED_ATTACHMENT_HOSTS
        )
        if not permitted:
            raise ValueError("URL host is not on the allowed list for this institution")

    if host in {"localhost", "127.0.0.1", "0.0.0.0", "::1"} or host.endswith(".localhost"):
        raise ValueError("URL may not point at a local address")

    return candidate
