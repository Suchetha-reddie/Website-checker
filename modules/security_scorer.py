"""
Security Scorer Module
=======================
Calculates an overall security score based on scan results.
"""

import logging

import config

logger = logging.getLogger(__name__)


def calculate_security_score(
    scheme: str,
    ssl_result: dict,
    http_result: dict,
    headers_result: dict,
    cookies: list,
) -> dict:
    """
    Calculate a security score (0–100) based on scan results.

    Args:
        scheme: URL scheme (http/https).
        ssl_result: SSL checker results.
        http_result: HTTP checker results.
        headers_result: Security headers checker results.
        cookies: List of cookies from HTTP checker.

    Returns:
        dict with total score, breakdown, and grade.
    """
    breakdown = {}
    recommendations = []

    # ---- HTTPS Score (max 20) ----
    https_score = 0
    https_max = config.SCORING["https"]["max"]

    if scheme == "https":
        https_score += 10  # URL uses HTTPS

    if http_result and http_result.get("https_available"):
        https_score += 5  # HTTPS is available

    if http_result and http_result.get("http_to_https_redirect"):
        https_score += 5  # HTTP redirects to HTTPS
    else:
        recommendations.append({
            "category": "HTTPS",
            "severity": "high",
            "message": "Configure HTTP to HTTPS redirect for all traffic.",
        })

    https_score = min(https_score, https_max)
    breakdown["https"] = {"score": https_score, "max": https_max}

    # ---- SSL/TLS Score (max 20) ----
    ssl_score = 0
    ssl_max = config.SCORING["ssl"]["max"]

    if ssl_result and not ssl_result.get("error"):
        if ssl_result.get("valid"):
            ssl_score += 10  # Valid certificate

        if ssl_result.get("hostname_match"):
            ssl_score += 3  # Hostname matches

        days = ssl_result.get("days_until_expiry")
        if days is not None:
            if days > 30:
                ssl_score += 4  # More than 30 days until expiry
            elif days > 7:
                ssl_score += 2
                recommendations.append({
                    "category": "SSL",
                    "severity": "medium",
                    "message": f"SSL certificate expires in {days} days. Renew soon.",
                })
            else:
                recommendations.append({
                    "category": "SSL",
                    "severity": "high",
                    "message": f"SSL certificate expires in {days} days! Renew immediately.",
                })

        protocol = ssl_result.get("protocol_version", "")
        if protocol and ("TLSv1.3" in protocol or "TLSv1.2" in protocol):
            ssl_score += 3  # Modern TLS
        elif protocol:
            recommendations.append({
                "category": "SSL",
                "severity": "medium",
                "message": f"Upgrade TLS version from {protocol} to TLSv1.2 or TLSv1.3.",
            })
    else:
        if ssl_result and ssl_result.get("error"):
            recommendations.append({
                "category": "SSL",
                "severity": "high",
                "message": f"SSL issue: {ssl_result['error'][:150]}",
            })
        else:
            recommendations.append({
                "category": "SSL",
                "severity": "high",
                "message": "No SSL/TLS certificate found. Install a valid certificate.",
            })

    ssl_score = min(ssl_score, ssl_max)
    breakdown["ssl"] = {"score": ssl_score, "max": ssl_max}

    # ---- Security Headers Score (max 30) ----
    headers_score = 0
    headers_max = config.SCORING["headers"]["max"]

    if headers_result:
        points_per_header = headers_max / len(config.SECURITY_HEADERS)
        for header_name in config.SECURITY_HEADERS:
            header_data = headers_result.get(header_name, {})
            if header_data.get("present"):
                if header_data.get("correct_value", True):
                    headers_score += points_per_header
                else:
                    headers_score += points_per_header * 0.5
                    recommendations.append({
                        "category": "Headers",
                        "severity": "low",
                        "message": f"Review the value of {header_name} header.",
                    })
            else:
                rec = header_data.get("recommendation")
                if rec:
                    recommendations.append({
                        "category": "Headers",
                        "severity": "medium",
                        "message": rec,
                    })

    headers_score = min(round(headers_score), headers_max)
    breakdown["headers"] = {"score": headers_score, "max": headers_max}

    # ---- Cookie Score (max 10) ----
    cookie_score = 0
    cookie_max = config.SCORING["cookies"]["max"]

    if cookies:
        total_cookies = len(cookies)
        secure_count = sum(1 for c in cookies if c.get("secure"))
        httponly_count = sum(1 for c in cookies if c.get("httponly"))

        if total_cookies > 0:
            secure_ratio = secure_count / total_cookies
            httponly_ratio = httponly_count / total_cookies
            cookie_score = round((secure_ratio * 5) + (httponly_ratio * 5))

            if secure_ratio < 1:
                recommendations.append({
                    "category": "Cookies",
                    "severity": "medium",
                    "message": "Set the Secure flag on all cookies.",
                })
            if httponly_ratio < 1:
                recommendations.append({
                    "category": "Cookies",
                    "severity": "medium",
                    "message": "Set the HttpOnly flag on sensitive cookies.",
                })
    else:
        cookie_score = cookie_max  # No cookies = no risk from cookies

    cookie_score = min(cookie_score, cookie_max)
    breakdown["cookies"] = {"score": cookie_score, "max": cookie_max}

    # ---- Redirect Score (max 10) ----
    redirect_score = 0
    redirect_max = config.SCORING["redirects"]["max"]

    if http_result:
        chain = http_result.get("redirect_chain", [])
        if len(chain) == 0:
            redirect_score = redirect_max  # No unnecessary redirects
        elif len(chain) <= 2:
            redirect_score = 7
        elif len(chain) <= config.MAX_REDIRECTS:
            redirect_score = 4
            recommendations.append({
                "category": "Redirects",
                "severity": "low",
                "message": f"Excessive redirect chain ({len(chain)} hops). Minimize redirects.",
            })
        else:
            redirect_score = 0
            recommendations.append({
                "category": "Redirects",
                "severity": "medium",
                "message": f"Too many redirects ({len(chain)} hops). Risk of redirect loops.",
            })

        if http_result.get("http_to_https_redirect"):
            redirect_score = min(redirect_score + 3, redirect_max)

    redirect_score = min(redirect_score, redirect_max)
    breakdown["redirects"] = {"score": redirect_score, "max": redirect_max}

    # ---- Other Score (max 10) ----
    other_score = 0
    other_max = config.SCORING["other"]["max"]

    # Check for information leakage
    if headers_result:
        info_leak = headers_result.get("_info_leak", [])
        if len(info_leak) == 0:
            other_score += 5
        else:
            for leak in info_leak:
                recommendations.append({
                    "category": "Information Disclosure",
                    "severity": "low",
                    "message": f"Remove or obfuscate the '{leak['header']}' header to reduce information leakage.",
                })

    # HTTPS bonus
    if scheme == "https" and ssl_result and ssl_result.get("valid"):
        other_score += 5

    other_score = min(other_score, other_max)
    breakdown["other"] = {"score": other_score, "max": other_max}

    # ---- Total Score ----
    total = sum(b["score"] for b in breakdown.values())
    total = min(total, 100)

    # Grade
    if total >= 90:
        grade = "A+"
    elif total >= 80:
        grade = "A"
    elif total >= 70:
        grade = "B"
    elif total >= 60:
        grade = "C"
    elif total >= 50:
        grade = "D"
    else:
        grade = "F"

    # Sort recommendations by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda r: severity_order.get(r["severity"], 3))

    result = {
        "total": total,
        "grade": grade,
        "breakdown": breakdown,
    }

    logger.info("Security score for scan: %d/100 (Grade: %s)", total, grade)

    return result, recommendations
