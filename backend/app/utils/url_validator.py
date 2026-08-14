"""
URL Validator — validates and sanitizes article URLs.
Includes SSRF protection to block internal/private network access.
"""

import ipaddress
import socket
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_SCHEMES = {"http", "https"}

# Private IPv4 ranges (RFC 1918, RFC 5737, loopback, link-local)
_PRIVATE_IPV4_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),       # loopback
    ipaddress.ip_network("169.254.0.0/16"),    # link-local
    ipaddress.ip_network("0.0.0.0/8"),         # "this" network
    ipaddress.ip_network("100.64.0.0/10"),     # shared address space
    ipaddress.ip_network("198.18.0.0/15"),     # benchmarking
    ipaddress.ip_network("240.0.0.0/4"),       # reserved
]

# Private IPv6 ranges
_PRIVATE_IPV6_NETWORKS = [
    ipaddress.ip_network("::1/128"),           # loopback
    ipaddress.ip_network("fc00::/7"),          # unique local
    ipaddress.ip_network("fe80::/10"),         # link-local
]

# Blocked hostnames (case-insensitive)
_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata",
    "metadata.google.internal",  # GCP metadata
    "169.254.169.254",           # AWS/GCP metadata IP
}


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class URLValidationError(ValueError):
    """Raised when a URL fails validation."""

    pass


class SSRFBlockedError(URLValidationError):
    """Raised when a URL targets an internal/private address (SSRF prevention)."""

    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_private_ip(ip_str: str) -> bool:
    """Return True if the IP address is in a private/reserved range."""
    try:
        addr = ipaddress.ip_address(ip_str)
        if isinstance(addr, ipaddress.IPv4Address):
            return any(addr in net for net in _PRIVATE_IPV4_NETWORKS)
        elif isinstance(addr, ipaddress.IPv6Address):
            return any(addr in net for net in _PRIVATE_IPV6_NETWORKS)
    except ValueError:
        pass
    return False


def _resolve_hostname(hostname: str) -> list[str]:
    """Resolve hostname to IP addresses. Returns empty list on failure."""
    try:
        results = socket.getaddrinfo(hostname, None)
        return [r[4][0] for r in results]
    except (socket.gaierror, OSError):
        return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_url(url: str) -> str:
    """
    Validate a URL for use as an article source.

    Checks:
    - Non-empty string
    - Valid URL structure
    - Allowed scheme (http / https only)
    - Non-empty hostname
    - Not a blocked hostname
    - Resolved IP is not in private/internal ranges (SSRF)

    Returns:
        The validated URL string (stripped).

    Raises:
        URLValidationError: If the URL is structurally invalid.
        SSRFBlockedError: If the URL targets an internal resource.
    """
    if not url or not isinstance(url, str):
        raise URLValidationError("URL must be a non-empty string.")

    url = url.strip()

    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise URLValidationError(f"Malformed URL: {exc}") from exc

    # Scheme check
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise URLValidationError(
            f"Unsupported URL scheme '{parsed.scheme}'. "
            f"Only http and https are allowed."
        )

    # Hostname check
    hostname = parsed.hostname
    if not hostname:
        raise URLValidationError("URL must contain a valid hostname.")

    # Blocked hostname check
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        raise SSRFBlockedError(
            f"Access to '{hostname}' is not allowed."
        )

    # Direct IP address check
    try:
        ipaddress.ip_address(hostname)
        # It IS an IP address — check if private
        if _is_private_ip(hostname):
            raise SSRFBlockedError(
                "Direct access to private/internal IP addresses is not allowed."
            )
    except ValueError:
        # Not a raw IP — resolve and check
        resolved_ips = _resolve_hostname(hostname)
        for ip in resolved_ips:
            if _is_private_ip(ip):
                raise SSRFBlockedError(
                    f"The hostname '{hostname}' resolves to an internal IP address. "
                    "Access is not allowed."
                )

    return url
