"""
Website Information & Security Checker
=======================================
Flask application entry point.

A cybersecurity tool that gathers publicly available information about websites
and performs basic security configuration checks.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

import config
from modules.url_validator import validate_url, check_resolved_ip
from modules.availability_checker import check_availability
from modules.ip_resolver import resolve_ip_addresses
from modules.dns_checker import check_dns
from modules.ssl_checker import check_ssl
from modules.http_checker import check_http
from modules.headers_checker import check_security_headers
from modules.tech_detector import detect_technologies
from modules.security_scorer import calculate_security_score

# =============================================================================
# Logging Setup
# =============================================================================
logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
logger = logging.getLogger("WebsiteChecker")

# =============================================================================
# Flask App Initialization
# =============================================================================
app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Ensure required directories exist
os.makedirs(config.REPORTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)


# =============================================================================
# Page Routes
# =============================================================================

@app.route("/")
def index():
    """Render the homepage."""
    return render_template("index.html")


@app.route("/report/<scan_id>")
def report_page(scan_id):
    """Render the report page for a specific scan."""
    return render_template("report.html", scan_id=scan_id)


@app.route("/history")
def history_page():
    """Render the scan history page."""
    return render_template("history.html")


# =============================================================================
# API Routes
# =============================================================================

@app.route("/api/scan", methods=["POST"])
def api_scan():
    """
    Start a new website scan.

    Expects JSON body: {"url": "https://example.com"}
    Returns scan results as JSON.
    """
    # Parse request data
    data = request.get_json(silent=True)
    if not data or "url" not in data:
        return jsonify({
            "success": False,
            "error": "Missing required field: 'url'. Send JSON with {\"url\": \"https://example.com\"}",
        }), 400

    raw_url = data["url"]
    scan_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    logger.info("Scan started [%s] for URL: %s", scan_id, raw_url)

    # Step 1: Validate URL
    validation = validate_url(raw_url)
    if not validation.is_valid:
        logger.warning("Scan [%s] failed: URL validation error - %s", scan_id, validation.error)
        return jsonify({
            "success": False,
            "error": validation.error,
            "step": "url_validation",
        }), 400

    # Step 2: SSRF check — verify resolved IP is safe
    ssrf_error = check_resolved_ip(validation.hostname)
    if ssrf_error:
        logger.warning("Scan [%s] failed: SSRF protection - %s", scan_id, ssrf_error)
        return jsonify({
            "success": False,
            "error": ssrf_error,
            "step": "ssrf_check",
        }), 403

    # Run all scan modules
    target_url = validation.normalized_url
    hostname = validation.hostname
    scheme = validation.scheme
    port = validation.port or (443 if scheme == "https" else 80)

    # Step 3: Availability check
    logger.info("Scan [%s] Step 3: Checking availability", scan_id)
    availability = check_availability(target_url)

    # Step 4: IP resolution
    logger.info("Scan [%s] Step 4: Resolving IP addresses", scan_id)
    ip_addresses = resolve_ip_addresses(hostname)

    # Step 5: DNS records
    logger.info("Scan [%s] Step 5: Checking DNS records", scan_id)
    dns_records = check_dns(hostname)

    # Step 6: HTTP analysis
    logger.info("Scan [%s] Step 6: Analyzing HTTP/HTTPS", scan_id)
    http_result = check_http(target_url, hostname, scheme)

    # Step 7: SSL/TLS check (only for HTTPS or if HTTPS is available)
    ssl_result = None
    if scheme == "https" or (http_result and http_result.get("https_available")):
        logger.info("Scan [%s] Step 7: Checking SSL/TLS", scan_id)
        ssl_port = validation.port or 443
        ssl_result = check_ssl(hostname, ssl_port)

    # Step 8: Security headers
    logger.info("Scan [%s] Step 8: Checking security headers", scan_id)
    security_headers = check_security_headers(target_url)

    # Step 9: Technology detection
    logger.info("Scan [%s] Step 9: Detecting technologies", scan_id)
    technology = detect_technologies(target_url)

    # Step 10: Calculate security score
    logger.info("Scan [%s] Step 10: Calculating security score", scan_id)
    cookies = http_result.get("cookies", []) if http_result else []
    security_score, recommendations = calculate_security_score(
        scheme=scheme,
        ssl_result=ssl_result or {},
        http_result=http_result or {},
        headers_result=security_headers or {},
        cookies=cookies,
    )

    # Build scan result
    scan_result = {
        "success": True,
        "scan_id": scan_id,
        "timestamp": timestamp,
        "target": target_url,
        "hostname": hostname,
        "scheme": scheme,
        "port": validation.port,
        "path": validation.path,
        "url_validation": validation.to_dict(),
        "availability": availability,
        "ip_addresses": ip_addresses,
        "dns": dns_records,
        "http": http_result,
        "redirects": http_result.get("redirect_chain") if http_result else None,
        "ssl": ssl_result,
        "security_headers": security_headers,
        "cookies": cookies,
        "technology": technology,
        "server_info": {
            "server": http_result.get("server") if http_result else None,
            "powered_by": http_result.get("powered_by") if http_result else None,
        },
        "security_score": security_score,
        "recommendations": recommendations,
    }

    logger.info("Scan completed [%s] for %s — Score: %s/100", scan_id, target_url, security_score.get("total"))

    return jsonify(scan_result), 200


@app.route("/api/health", methods=["GET"])
def api_health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "application": "Website Information & Security Checker",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), 200


# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Endpoint not found."}), 404
    return render_template("index.html"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error("Internal server error: %s", error)
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Internal server error."}), 500
    return render_template("index.html"), 500


# =============================================================================
# Run Application
# =============================================================================

if __name__ == "__main__":
    logger.info("Starting Website Information & Security Checker on http://%s:%d...", config.HOST, config.PORT)
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)
