"""
Technology Detector Module
===========================
Passively detects web technologies from HTTP response headers and body.
"""

import logging
import re
from typing import Optional

import requests

import config

logger = logging.getLogger(__name__)

# Technology signatures — header-based detection
HEADER_SIGNATURES = {
    "Server": {
        "nginx": "Nginx",
        "apache": "Apache",
        "cloudflare": "Cloudflare",
        "microsoft-iis": "Microsoft IIS",
        "litespeed": "LiteSpeed",
        "gunicorn": "Gunicorn",
        "caddy": "Caddy",
        "openresty": "OpenResty",
        "tengine": "Tengine",
    },
    "X-Powered-By": {
        "php": "PHP",
        "asp.net": "ASP.NET",
        "express": "Express.js",
        "next.js": "Next.js",
        "nuxt": "Nuxt.js",
        "flask": "Flask",
        "django": "Django",
    },
}

# Technology signatures — body/meta-based detection
BODY_SIGNATURES = [
    {"pattern": r"wp-content|wp-includes|wordpress", "name": "WordPress", "category": "CMS"},
    {"pattern": r"Joomla", "name": "Joomla", "category": "CMS"},
    {"pattern": r"Drupal\.settings|drupal\.js", "name": "Drupal", "category": "CMS"},
    {"pattern": r"shopify\.com|cdn\.shopify", "name": "Shopify", "category": "E-Commerce"},
    {"pattern": r"woocommerce", "name": "WooCommerce", "category": "E-Commerce"},
    {"pattern": r"react|reactDOM|__NEXT_DATA__", "name": "React", "category": "JavaScript Framework"},
    {"pattern": r"vue\.js|__vue__|nuxt", "name": "Vue.js", "category": "JavaScript Framework"},
    {"pattern": r"angular|ng-app|ng-controller", "name": "Angular", "category": "JavaScript Framework"},
    {"pattern": r"jquery|jQuery", "name": "jQuery", "category": "JavaScript Library"},
    {"pattern": r"bootstrap\.css|bootstrap\.min\.css|bootstrap\.js", "name": "Bootstrap", "category": "CSS Framework"},
    {"pattern": r"tailwindcss|tailwind\.css", "name": "Tailwind CSS", "category": "CSS Framework"},
    {"pattern": r"google-analytics\.com|gtag|GoogleAnalyticsObject", "name": "Google Analytics", "category": "Analytics"},
    {"pattern": r"googletagmanager\.com", "name": "Google Tag Manager", "category": "Analytics"},
    {"pattern": r"fonts\.googleapis\.com|fonts\.gstatic\.com", "name": "Google Fonts", "category": "Font Service"},
    {"pattern": r"cloudflare\.com|cf-ray|__cf_bm", "name": "Cloudflare", "category": "CDN/Security"},
    {"pattern": r"cdn\.jsdelivr\.net", "name": "jsDelivr", "category": "CDN"},
    {"pattern": r"cdnjs\.cloudflare\.com", "name": "cdnjs", "category": "CDN"},
    {"pattern": r"recaptcha|grecaptcha", "name": "reCAPTCHA", "category": "Security"},
]


def detect_technologies(url: str) -> dict:
    """
    Detect technologies used by a website.

    Args:
        url: The URL to analyze.

    Returns:
        dict with detected technologies grouped by category.
    """
    result = {
        "technologies": [],
        "server": None,
        "powered_by": None,
        "categories": {},
        "error": None,
    }

    try:
        response = requests.get(
            url,
            timeout=config.REQUEST_TIMEOUT,
            allow_redirects=True,
            headers={"User-Agent": config.USER_AGENT},
            verify=True,
            stream=True,
        )

        # Read limited body content
        body = ""
        content_length = 0
        for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
            if isinstance(chunk, bytes):
                chunk = chunk.decode("utf-8", errors="ignore")
            body += chunk
            content_length += len(chunk)
            if content_length >= config.MAX_CONTENT_LENGTH:
                break
        response.close()

        # Header-based detection
        for header_name, signatures in HEADER_SIGNATURES.items():
            header_value = response.headers.get(header_name, "").lower()
            if header_value:
                if header_name == "Server":
                    result["server"] = response.headers.get(header_name)
                elif header_name == "X-Powered-By":
                    result["powered_by"] = response.headers.get(header_name)

                for sig, tech_name in signatures.items():
                    if sig in header_value:
                        _add_tech(result, tech_name, "Server/Infrastructure", f"Detected in {header_name} header")

        # Cloudflare detection via headers
        if response.headers.get("CF-Ray") or response.headers.get("cf-cache-status"):
            _add_tech(result, "Cloudflare", "CDN/Security", "Detected via CF-Ray header")

        # Body-based detection
        body_lower = body.lower()
        for sig in BODY_SIGNATURES:
            if re.search(sig["pattern"], body, re.IGNORECASE):
                _add_tech(result, sig["name"], sig["category"], "Detected in page source")

        # Meta generator tag
        generator_match = re.search(
            r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)["\']',
            body, re.IGNORECASE,
        )
        if generator_match:
            gen_value = generator_match.group(1).strip()
            _add_tech(result, gen_value, "CMS/Framework", "Detected via meta generator tag")

        logger.info("Technology detection for %s: found %d technologies", url, len(result["technologies"]))

    except requests.exceptions.SSLError:
        try:
            response = requests.get(
                url,
                timeout=config.REQUEST_TIMEOUT,
                allow_redirects=True,
                headers={"User-Agent": config.USER_AGENT},
                verify=False,
            )
            result["server"] = response.headers.get("Server")
            result["powered_by"] = response.headers.get("X-Powered-By")
        except Exception:
            pass
        result["error"] = "SSL error — limited detection performed."

    except Exception as e:
        result["error"] = f"Technology detection failed: {str(e)[:200]}"
        logger.warning("Technology detection error for %s: %s", url, e)

    return result


def _add_tech(result: dict, name: str, category: str, source: str):
    """Add a detected technology to the result, avoiding duplicates."""
    # Check for duplicate
    for tech in result["technologies"]:
        if tech["name"].lower() == name.lower():
            return

    tech_entry = {"name": name, "category": category, "source": source}
    result["technologies"].append(tech_entry)

    # Group by category
    if category not in result["categories"]:
        result["categories"][category] = []
    result["categories"][category].append(name)
