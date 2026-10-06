"""
Availability Checker Module
============================
Checks if a website is online and measures response time.
"""

import logging
import time
from typing import Optional

import requests

import config

logger = logging.getLogger(__name__)


def check_availability(url: str) -> dict:
    """
    Check if a website is reachable and measure response time.

    Args:
        url: The normalized URL to check.

    Returns:
        dict with keys:
            - status: 'online' or 'offline'
            - status_code: HTTP status code (or None)
            - response_time_ms: Response time in milliseconds (or None)
            - error: Error message if offline (or None)
    """
    result = {
        "status": "offline",
        "status_code": None,
        "response_time_ms": None,
        "error": None,
    }

    try:
        start_time = time.time()
        response = requests.get(
            url,
            timeout=config.REQUEST_TIMEOUT,
            allow_redirects=True,
            headers={"User-Agent": config.USER_AGENT},
            verify=True,
            stream=True,  # Don't download full body for availability check
        )
        elapsed = time.time() - start_time

        result["status"] = "online"
        result["status_code"] = response.status_code
        result["response_time_ms"] = round(elapsed * 1000)

        # Classify response time
        if result["response_time_ms"] <= config.RESPONSE_TIME_FAST:
            result["response_time_class"] = "fast"
        elif result["response_time_ms"] <= config.RESPONSE_TIME_MODERATE:
            result["response_time_class"] = "moderate"
        else:
            result["response_time_class"] = "slow"

        response.close()
        logger.info("Availability check: %s is online (%d ms)", url, result["response_time_ms"])

    except requests.exceptions.SSLError as e:
        result["status"] = "online"  # Site is reachable, but SSL issue
        result["error"] = f"SSL error: {str(e)[:200]}"
        logger.warning("Availability check: SSL error for %s: %s", url, e)

    except requests.exceptions.ConnectionError as e:
        result["error"] = "Connection failed. The website may be down or unreachable."
        logger.warning("Availability check: Connection error for %s: %s", url, e)

    except requests.exceptions.Timeout:
        result["error"] = f"Request timed out after {config.CONNECTION_TIMEOUT}s."
        logger.warning("Availability check: Timeout for %s", url)

    except requests.exceptions.RequestException as e:
        result["error"] = f"Request failed: {str(e)[:200]}"
        logger.warning("Availability check: Request error for %s: %s", url, e)

    return result
