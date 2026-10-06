"""
IP Resolver Module
==================
Resolves hostnames to IP addresses (IPv4 and IPv6).
"""

import logging
import socket
from typing import Optional

logger = logging.getLogger(__name__)


def resolve_ip_addresses(hostname: str) -> dict:
    """
    Resolve a hostname to its IPv4 and IPv6 addresses.

    Args:
        hostname: The hostname to resolve.

    Returns:
        dict with keys:
            - ipv4: List of IPv4 addresses
            - ipv6: List of IPv6 addresses
            - error: Error message if resolution failed
    """
    result = {
        "ipv4": [],
        "ipv6": [],
        "error": None,
    }

    try:
        addr_infos = socket.getaddrinfo(hostname, None)
        seen_v4 = set()
        seen_v6 = set()

        for addr_info in addr_infos:
            family = addr_info[0]
            ip = addr_info[4][0]

            if family == socket.AF_INET and ip not in seen_v4:
                seen_v4.add(ip)
                result["ipv4"].append(ip)
            elif family == socket.AF_INET6 and ip not in seen_v6:
                seen_v6.add(ip)
                result["ipv6"].append(ip)

        logger.info(
            "IP resolution for %s: IPv4=%s, IPv6=%s",
            hostname, result["ipv4"], result["ipv6"],
        )

    except socket.gaierror as e:
        result["error"] = f"DNS resolution failed for '{hostname}': {str(e)}"
        logger.warning("IP resolution failed for %s: %s", hostname, e)

    except Exception as e:
        result["error"] = f"IP resolution error: {str(e)[:200]}"
        logger.error("IP resolution error for %s: %s", hostname, e)

    return result
