"""
Configuration settings for Website Information & Security Checker.
"""

import os

# =============================================================================
# Flask Configuration
# =============================================================================
SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(32).hex())
DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", 5001))

# =============================================================================
# Network Timeouts (seconds)
# =============================================================================
CONNECTION_TIMEOUT = 10
READ_TIMEOUT = 10
REQUEST_TIMEOUT = (CONNECTION_TIMEOUT, READ_TIMEOUT)

# =============================================================================
# Scan Limits
# =============================================================================
MAX_REDIRECTS = 10
MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_CONTENT_LENGTH = 1 * 1024 * 1024   # 1 MB for response body inspection

# =============================================================================
# User-Agent for outgoing requests
# =============================================================================
USER_AGENT = "WebsiteSecurityChecker/1.0 (Educational Security Tool)"

# =============================================================================
# Allowed URL Schemes
# =============================================================================
ALLOWED_SCHEMES = {"http", "https"}

# =============================================================================
# SSRF Protection — Blocked IP Ranges & Hosts
# =============================================================================
BLOCKED_HOSTS = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
    "metadata.google.internal",
    "metadata.google.com",
}

# Private / reserved IPv4 ranges (CIDR notation for documentation)
# Actual checking done via ipaddress module in url_validator
BLOCKED_IPV4_PREFIXES = [
    "127.",        # Loopback
    "10.",         # Private Class A
    "0.",          # Current network
    "169.254.",    # Link-local
]

BLOCKED_IPV4_RANGES = [
    # 172.16.0.0 – 172.31.255.255 (Private Class B)
    ("172.16.0.0", "172.31.255.255"),
    # 192.168.0.0 – 192.168.255.255 (Private Class C)
    ("192.168.0.0", "192.168.255.255"),
]

# Cloud metadata endpoint
BLOCKED_METADATA_IPS = {"169.254.169.254", "fd00:ec2::254"}

# =============================================================================
# Security Scoring Weights (out of 100)
# =============================================================================
SCORING = {
    "https": {"max": 20, "description": "HTTPS availability and enforcement"},
    "ssl": {"max": 20, "description": "SSL/TLS certificate validity"},
    "headers": {"max": 30, "description": "Security headers presence"},
    "cookies": {"max": 10, "description": "Cookie security attributes"},
    "redirects": {"max": 10, "description": "Redirect configuration"},
    "other": {"max": 10, "description": "Other security indicators"},
}

# Security headers to check (name: max points within headers category)
SECURITY_HEADERS = {
    "Content-Security-Policy": 5,
    "Strict-Transport-Security": 5,
    "X-Content-Type-Options": 5,
    "X-Frame-Options": 5,
    "Referrer-Policy": 5,
    "Permissions-Policy": 5,
}

# =============================================================================
# Response Time Classification (ms)
# =============================================================================
RESPONSE_TIME_FAST = 500
RESPONSE_TIME_MODERATE = 1000

# =============================================================================
# Database
# =============================================================================
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "database", "scans.db")

# =============================================================================
# Reports Directory
# =============================================================================
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

# =============================================================================
# Logging
# =============================================================================
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
