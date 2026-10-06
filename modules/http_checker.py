"""
HTTP Checker Module
====================
Analyzes HTTP/HTTPS behavior including redirect chains, HTTPS enforcement,
response headers, and cookies.
"""

import logging
from typing import Optional

import requests

import config

logger = logging.getLogger(__name__)


def check_http(url: str, hostname: str, scheme: str) -> dict:
    """
    Analyze HTTP/HTTPS behavior for a URL.

    Args:
        url: The normalized URL to check.
        hostname: The hostname.
        scheme: The URL scheme (http or https).

    Returns:
        dict with HTTP analysis results.
    """
    result = {
        "https_available": False,
        "http_to_https_redirect": False,
        "status_code": None,
        "final_url": None,
        "redirect_chain": [],
        "server": None,
        "powered_by": None,
        "content_type": None,
        "cookies": [],
        "error": None,
    }

    try:
        # Check HTTPS availability
        https_url = f"https://{hostname}"
        try:
            https_resp = requests.get(
                https_url,
                timeout=config.REQUEST_TIMEOUT,
                allow_redirects=True,
                headers={"User-Agent": config.USER_AGENT},
                verify=True,
            )
            result["https_available"] = True
            main_response = https_resp
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError):
            result["https_available"] = False
            # Fall back to HTTP
            try:
                http_resp = requests.get(
                    f"http://{hostname}",
                    timeout=config.REQUEST_TIMEOUT,
                    allow_redirects=True,
                    headers={"User-Agent": config.USER_AGENT},
                    verify=False,
                )
                main_response = http_resp
            except Exception as e:
                result["error"] = f"Neither HTTP nor HTTPS accessible: {str(e)[:200]}"
                return result

        # Check HTTP→HTTPS redirect
        try:
            http_url = f"http://{hostname}"
            http_resp = requests.get(
                http_url,
                timeout=config.REQUEST_TIMEOUT,
                allow_redirects=False,
                headers={"User-Agent": config.USER_AGENT},
                verify=False,
            )
            if http_resp.is_redirect or http_resp.status_code in (301, 302, 307, 308):
                location = http_resp.headers.get("Location", "")
                if location.startswith("https://"):
                    result["http_to_https_redirect"] = True
        except Exception:
            pass

        # Analyze the main response
        result["status_code"] = main_response.status_code
        result["final_url"] = main_response.url
        result["content_type"] = main_response.headers.get("Content-Type")

        # Redirect chain
        for resp in main_response.history:
            result["redirect_chain"].append({
                "url": resp.url,
                "status_code": resp.status_code,
                "location": resp.headers.get("Location"),
            })

        # Server info from headers
        result["server"] = main_response.headers.get("Server")
        result["powered_by"] = main_response.headers.get("X-Powered-By")

        # Cookie analysis
        for cookie in main_response.cookies:
            cookie_info = {
                "name": cookie.name,
                "domain": cookie.domain,
                "path": cookie.path,
                "secure": cookie.secure,
                "httponly": cookie.has_nonstandard_attr("httpOnly") or cookie.has_nonstandard_attr("HTTPOnly"),
                "samesite": None,
            }
            # Check SameSite attribute
            for attr in cookie._rest:
                if attr.lower() == "samesite":
                    cookie_info["samesite"] = cookie._rest[attr]
            result["cookies"].append(cookie_info)

        logger.info("HTTP check completed for %s", url)

    except requests.exceptions.Timeout:
        result["error"] = "Request timed out."
        logger.warning("HTTP check timeout for %s", url)

    except requests.exceptions.RequestException as e:
        result["error"] = f"HTTP check failed: {str(e)[:200]}"
        logger.warning("HTTP check error for %s: %s", url, e)

    return result
