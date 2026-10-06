"""
Security Headers Checker Module
================================
Checks for the presence and values of important security headers.
"""

import logging
from typing import Optional

import requests

import config

logger = logging.getLogger(__name__)

# Headers to check and their descriptions
HEADER_CHECKS = {
    "Content-Security-Policy": {
        "description": "Controls resources the browser is allowed to load.",
        "recommendation": "Implement a Content-Security-Policy header to prevent XSS and data injection attacks.",
    },
    "Strict-Transport-Security": {
        "description": "Forces browsers to use HTTPS for all future requests.",
        "recommendation": "Add 'Strict-Transport-Security: max-age=31536000; includeSubDomains' to enforce HTTPS.",
    },
    "X-Content-Type-Options": {
        "description": "Prevents MIME type sniffing.",
        "expected": "nosniff",
        "recommendation": "Add 'X-Content-Type-Options: nosniff' to prevent MIME type sniffing.",
    },
    "X-Frame-Options": {
        "description": "Prevents clickjacking by controlling iframe embedding.",
        "expected_values": ["DENY", "SAMEORIGIN"],
        "recommendation": "Add 'X-Frame-Options: DENY' or 'SAMEORIGIN' to prevent clickjacking.",
    },
    "Referrer-Policy": {
        "description": "Controls how much referrer information is sent.",
        "recommendation": "Add a Referrer-Policy header (e.g., 'strict-origin-when-cross-origin').",
    },
    "Permissions-Policy": {
        "description": "Controls which browser features can be used.",
        "recommendation": "Add a Permissions-Policy header to restrict access to browser features.",
    },
}


def _default_headers_result() -> dict:
    """Return default empty result structure when headers cannot be retrieved."""
    result = {}
    for header_name, check_info in HEADER_CHECKS.items():
        result[header_name] = {
            "present": False,
            "value": None,
            "description": check_info["description"],
            "recommendation": check_info["recommendation"],
            "correct_value": None,
        }
    result["_info_leak"] = []
    result["_total_present"] = 0
    result["_total_checked"] = len(HEADER_CHECKS)
    result["_error"] = None
    return result


def _evaluate_headers(response_headers) -> dict:
    """Evaluate response headers against security header specifications."""
    result = {}
    for header_name, check_info in HEADER_CHECKS.items():
        header_value = response_headers.get(header_name)
        header_result = {
            "present": header_value is not None,
            "value": header_value,
            "description": check_info["description"],
            "recommendation": None,
            "correct_value": None,
        }

        if header_value is not None:
            if "expected" in check_info:
                header_result["correct_value"] = (
                    header_value.lower() == check_info["expected"].lower()
                )
            elif "expected_values" in check_info:
                header_result["correct_value"] = (
                    header_value.upper() in [v.upper() for v in check_info["expected_values"]]
                )
            else:
                header_result["correct_value"] = True
        else:
            header_result["recommendation"] = check_info["recommendation"]

        result[header_name] = header_result

    # Check for information-leaking headers
    info_leak_headers = ["Server", "X-Powered-By", "X-AspNet-Version", "X-AspNetMvc-Version"]
    leaking = []
    for h in info_leak_headers:
        val = response_headers.get(h)
        if val:
            leaking.append({"header": h, "value": val})

    result["_info_leak"] = leaking
    result["_total_present"] = sum(1 for h in HEADER_CHECKS if result.get(h, {}).get("present"))
    result["_total_checked"] = len(HEADER_CHECKS)
    result["_error"] = None
    return result


def check_security_headers(url: str) -> dict:
    """
    Check for security headers on a URL.

    Args:
        url: The URL to check.

    Returns:
        dict mapping header names to their check results.
    """
    try:
        response = requests.get(
            url,
            timeout=config.REQUEST_TIMEOUT,
            allow_redirects=True,
            headers={"User-Agent": config.USER_AGENT},
            verify=True,
        )
        result = _evaluate_headers(response.headers)
        logger.info(
            "Security headers check for %s: %d/%d present",
            url, result["_total_present"], result["_total_checked"],
        )
        return result

    except requests.exceptions.SSLError as ssl_err:
        logger.warning("SSL error during header check for %s, retrying with verify=False: %s", url, ssl_err)
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(
                url,
                timeout=config.REQUEST_TIMEOUT,
                allow_redirects=True,
                headers={"User-Agent": config.USER_AGENT},
                verify=False,
            )
            result = _evaluate_headers(response.headers)
            result["_warning"] = "Headers inspected over unverified SSL connection."
            logger.info(
                "Security headers check (unverified) for %s: %d/%d present",
                url, result["_total_present"], result["_total_checked"],
            )
            return result
        except Exception as fallback_err:
            result = _default_headers_result()
            result["_error"] = f"SSL error and fallback failed: {str(fallback_err)[:200]}"
            logger.warning("Header fallback error for %s: %s", url, fallback_err)
            return result

    except Exception as e:
        result = _default_headers_result()
        result["_error"] = f"Header check failed: {str(e)[:200]}"
        logger.warning("Security headers check error for %s: %s", url, e)
        return result
