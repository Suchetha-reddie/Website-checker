"""
URL Validator Module
====================
Validates, normalizes, and sanitizes user-supplied URLs.
Implements SSRF protection to block requests to internal/private networks.
"""

import ipaddress
import logging
import re
import socket
from typing import Optional
from urllib.parse import urlparse, urlunparse

import config

logger = logging.getLogger(__name__)


class URLValidationError(Exception):
    """Raised when URL validation fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class URLValidationResult:
    """Holds the result of URL validation."""

    def __init__(
        self,
        is_valid: bool,
        normalized_url: Optional[str] = None,
        scheme: Optional[str] = None,
        hostname: Optional[str] = None,
        port: Optional[int] = None,
        path: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.is_valid = is_valid
        self.normalized_url = normalized_url
        self.scheme = scheme
        self.hostname = hostname
        self.port = port
        self.path = path
        self.error = error

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "normalized_url": self.normalized_url,
            "scheme": self.scheme,
            "hostname": self.hostname,
            "port": self.port,
            "path": self.path,
            "error": self.error,
        }


def validate_url(url: str) -> URLValidationResult:
    """
    Validate and normalize a user-supplied URL.

    Accepts formats like:
        - https://example.com
        - http://example.com
        - example.com

    Returns a URLValidationResult with normalized URL components or an error.
    """
    # Step 1: Check for empty input
    if not url or not url.strip():
        return URLValidationResult(is_valid=False, error="URL cannot be empty.")

    url = url.strip()

    # Step 2: Block dangerous schemes early
    dangerous_schemes = ["javascript:", "data:", "file:", "ftp:", "gopher:", "ldap:", "telnet:"]
    url_lower = url.lower()
    for scheme in dangerous_schemes:
        if url_lower.startswith(scheme):
            return URLValidationResult(
                is_valid=False,
                error=f"Unsupported or dangerous URL scheme: '{scheme.rstrip(':')}'. Only HTTP and HTTPS are allowed.",
            )

    # Step 3: Add scheme if missing
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url

    # Step 4: Parse the URL
    try:
        parsed = urlparse(url)
    except Exception:
        return URLValidationResult(is_valid=False, error="Unable to parse the URL.")

    # Step 5: Validate scheme
    if parsed.scheme.lower() not in config.ALLOWED_SCHEMES:
        return URLValidationResult(
            is_valid=False,
            error=f"Unsupported URL scheme: '{parsed.scheme}'. Only HTTP and HTTPS are allowed.",
        )

    # Step 6: Validate hostname exists
    hostname = parsed.hostname
    if not hostname:
        return URLValidationResult(is_valid=False, error="URL must contain a valid hostname.")

    # Step 7: Validate hostname format
    hostname_lower = hostname.lower()

    # Block empty or whitespace hostnames
    if not hostname_lower or hostname_lower.isspace():
        return URLValidationResult(is_valid=False, error="Invalid hostname.")

    # Basic hostname format check (allows domains and IPs)
    hostname_pattern = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$"
    )

    # Allow IP addresses or valid hostnames
    if not hostname_pattern.match(hostname_lower):
        # Check if it's a valid IP address
        try:
            ipaddress.ip_address(hostname_lower)
        except ValueError:
            return URLValidationResult(
                is_valid=False,
                error=f"Invalid hostname format: '{hostname}'.",
            )

    # Step 8: SSRF Protection — Block dangerous hosts
    ssrf_error = _check_ssrf(hostname_lower)
    if ssrf_error:
        return URLValidationResult(is_valid=False, error=ssrf_error)

    # Step 9: Extract port
    port = parsed.port

    # Step 10: Normalize the URL
    path = parsed.path if parsed.path else "/"
    normalized = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        path,
        parsed.params,
        parsed.query,
        "",  # Remove fragment
    ))

    logger.info("URL validated successfully: %s -> %s", url, normalized)

    return URLValidationResult(
        is_valid=True,
        normalized_url=normalized,
        scheme=parsed.scheme.lower(),
        hostname=hostname_lower,
        port=port,
        path=path,
    )


def _check_ssrf(hostname: str) -> Optional[str]:
    """
    Check for SSRF (Server-Side Request Forgery) risks.
    Returns an error message if the hostname is blocked, None otherwise.

    Protects against:
    - Localhost and loopback addresses
    - Private/internal IP ranges
    - Cloud metadata endpoints
    - Known internal hostnames
    """
    # Check against blocked hostnames
    if hostname in config.BLOCKED_HOSTS:
        logger.warning("SSRF protection: Blocked hostname '%s'", hostname)
        return "Scanning internal or localhost addresses is not allowed."

    # Check if hostname is an IP address directly
    try:
        ip = ipaddress.ip_address(hostname)
        ip_error = _check_ip_blocked(ip)
        if ip_error:
            return ip_error
    except ValueError:
        # Not an IP address — it's a hostname, will be resolved later
        pass

    return None


def check_resolved_ip(hostname: str) -> Optional[str]:
    """
    Resolve a hostname and check if the resolved IP is safe.
    Call this AFTER initial validation, BEFORE making network requests.

    Returns an error message if any resolved IP is blocked, None if safe.
    """
    try:
        # Resolve all addresses for the hostname
        addr_infos = socket.getaddrinfo(hostname, None)
        for addr_info in addr_infos:
            ip_str = addr_info[4][0]
            try:
                ip = ipaddress.ip_address(ip_str)
                ip_error = _check_ip_blocked(ip)
                if ip_error:
                    logger.warning(
                        "SSRF protection: Hostname '%s' resolved to blocked IP '%s'",
                        hostname, ip_str,
                    )
                    return ip_error
            except ValueError:
                continue
    except socket.gaierror:
        # DNS resolution failed — will be handled by the availability checker
        pass
    except Exception as e:
        logger.error("Error during IP resolution check for '%s': %s", hostname, e)

    return None


def _check_ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> Optional[str]:
    """Check if a specific IP address is in a blocked range."""
    ip_str = str(ip)

    # Check cloud metadata IPs
    if ip_str in config.BLOCKED_METADATA_IPS:
        return "Scanning cloud metadata endpoints is not allowed."

    # Check for loopback
    if ip.is_loopback:
        return "Scanning loopback addresses is not allowed."

    # Check for private/reserved ranges
    if ip.is_private:
        return "Scanning private/internal network addresses is not allowed."

    # Check for link-local
    if ip.is_link_local:
        return "Scanning link-local addresses is not allowed."

    # Check for reserved
    if ip.is_reserved:
        return "Scanning reserved addresses is not allowed."

    # Check for multicast
    if ip.is_multicast:
        return "Scanning multicast addresses is not allowed."

    return None
