"""
SSL/TLS Checker Module
=======================
Retrieves and validates SSL/TLS certificate details for a given hostname.
"""

import logging
import socket
import ssl
from datetime import datetime, timezone
from typing import Optional

import config

logger = logging.getLogger(__name__)

try:
    import certifi
    CA_FILE = certifi.where()
except ImportError:
    CA_FILE = None


def check_ssl(hostname: str, port: int = 443) -> dict:
    """
    Check SSL/TLS certificate for a hostname.

    Args:
        hostname: The hostname to check.
        port: The port to connect on (default 443).

    Returns:
        dict with SSL/TLS certificate details.
    """
    result = {
        "valid": False,
        "issuer": None,
        "subject": None,
        "serial_number": None,
        "version": None,
        "not_before": None,
        "not_after": None,
        "days_until_expiry": None,
        "expired": None,
        "san": [],
        "hostname_match": None,
        "protocol_version": None,
        "cipher": None,
        "error": None,
    }

    try:
        # Create SSL context with certifi CA bundle if available
        if CA_FILE:
            context = ssl.create_default_context(cafile=CA_FILE)
        else:
            context = ssl.create_default_context()

        conn = context.wrap_socket(
            socket.socket(socket.AF_INET),
            server_hostname=hostname,
        )
        conn.settimeout(config.CONNECTION_TIMEOUT)

        try:
            conn.connect((hostname, port))

            # Get certificate
            cert = conn.getpeercert()
            if not cert:
                result["error"] = "No certificate returned by server."
                return result

            # Protocol and cipher info
            result["protocol_version"] = conn.version()
            cipher_info = conn.cipher()
            if cipher_info:
                result["cipher"] = {
                    "name": cipher_info[0],
                    "protocol": cipher_info[1],
                    "bits": cipher_info[2],
                }

            # Parse subject
            subject_dict = {}
            for field in cert.get("subject", ()):
                for key, value in field:
                    subject_dict[key] = value
            result["subject"] = subject_dict

            # Parse issuer
            issuer_dict = {}
            for field in cert.get("issuer", ()):
                for key, value in field:
                    issuer_dict[key] = value
            result["issuer"] = issuer_dict

            # Serial number
            result["serial_number"] = cert.get("serialNumber")
            result["version"] = cert.get("version")

            # Validity dates
            not_before_str = cert.get("notBefore")
            not_after_str = cert.get("notAfter")

            if not_before_str:
                not_before = _parse_ssl_date(not_before_str)
                result["not_before"] = not_before.isoformat() if not_before else not_before_str

            if not_after_str:
                not_after = _parse_ssl_date(not_after_str)
                if not_after:
                    result["not_after"] = not_after.isoformat()
                    now = datetime.now(timezone.utc)
                    delta = not_after - now
                    result["days_until_expiry"] = delta.days
                    result["expired"] = delta.days < 0
                else:
                    result["not_after"] = not_after_str
                    result["expired"] = False

            # Subject Alternative Names
            san_list = []
            for type_name, value in cert.get("subjectAltName", ()):
                san_list.append({"type": type_name, "value": value})
            result["san"] = san_list

            # Hostname verification (already verified by ssl.create_default_context)
            result["hostname_match"] = True
            result["valid"] = not result.get("expired", False)

            logger.info(
                "SSL check for %s: valid=%s, expires in %s days",
                hostname, result["valid"], result["days_until_expiry"],
            )

        finally:
            conn.close()

    except ssl.SSLCertVerificationError as e:
        result["error"] = f"Certificate verification failed: {str(e)[:200]}"
        result["hostname_match"] = False
        logger.warning("SSL verification error for %s: %s", hostname, e)

    except ssl.SSLError as e:
        result["error"] = f"SSL error: {str(e)[:200]}"
        logger.warning("SSL error for %s: %s", hostname, e)

    except socket.timeout:
        result["error"] = f"Connection timed out after {config.CONNECTION_TIMEOUT}s."
        logger.warning("SSL check timeout for %s", hostname)

    except ConnectionRefusedError:
        result["error"] = f"Connection refused on port {port}."
        logger.warning("SSL check connection refused for %s:%d", hostname, port)

    except socket.gaierror as e:
        result["error"] = f"DNS resolution failed: {str(e)}"
        logger.warning("SSL check DNS error for %s: %s", hostname, e)

    except Exception as e:
        result["error"] = f"SSL check failed: {str(e)[:200]}"
        logger.error("SSL check error for %s: %s", hostname, e)

    return result


def _parse_ssl_date(date_str: str) -> Optional[datetime]:
    """Parse SSL certificate date string to datetime."""
    if not date_str:
        return None
    # Normalize multiple whitespaces (e.g., 'May  4' -> 'May 4')
    normalized = " ".join(date_str.strip().split())
    formats = [
        "%b %d %H:%M:%S %Y %Z",
        "%b %d %H:%M:%S %Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(normalized, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None
