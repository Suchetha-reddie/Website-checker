"""
Tests for Flask Application (app.py)
=====================================
Tests all routes, API endpoints, and error handlers.
"""

import json
import sys
import os
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from modules.url_validator import URLValidationResult


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def valid_scan_payload():
    """Standard valid scan request payload."""
    return {"url": "https://example.com"}


# =============================================================================
# Page Route Tests
# =============================================================================

class TestIndexPage:
    """Tests for the homepage route."""

    def test_index_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_index_returns_html(self, client):
        response = client.get("/")
        assert response.content_type.startswith("text/html")


class TestReportPage:
    """Tests for the report page route."""

    def test_report_page_returns_200(self, client):
        response = client.get("/report/some-scan-id")
        assert response.status_code == 200

    def test_report_page_returns_html(self, client):
        response = client.get("/report/test-uuid-1234")
        assert response.content_type.startswith("text/html")


class TestHistoryPage:
    """Tests for the scan history page route."""

    def test_history_page_returns_200(self, client):
        response = client.get("/history")
        assert response.status_code == 200

    def test_history_page_returns_html(self, client):
        response = client.get("/history")
        assert response.content_type.startswith("text/html")


# =============================================================================
# Health Endpoint Tests
# =============================================================================

class TestHealthEndpoint:
    """Tests for the /api/health endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        response = client.get("/api/health")
        assert response.content_type == "application/json"

    def test_health_response_fields(self, client):
        response = client.get("/api/health")
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["application"] == "Website Information & Security Checker"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data

    def test_health_timestamp_is_iso_format(self, client):
        response = client.get("/api/health")
        data = response.get_json()
        # ISO 8601 timestamps contain 'T' separator
        assert "T" in data["timestamp"]


# =============================================================================
# Scan Endpoint — Request Validation Tests
# =============================================================================

class TestScanEndpointValidation:
    """Tests for /api/scan request validation."""

    def test_scan_requires_post(self, client):
        """GET requests to /api/scan should return 405."""
        response = client.get("/api/scan")
        assert response.status_code == 405

    def test_scan_missing_body(self, client):
        """POST with no JSON body returns 400."""
        response = client.post("/api/scan", content_type="application/json")
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "url" in data["error"].lower()

    def test_scan_empty_json(self, client):
        """POST with empty JSON object returns 400."""
        response = client.post(
            "/api/scan",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_scan_missing_url_field(self, client):
        """POST with JSON but no 'url' key returns 400."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"target": "https://example.com"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "url" in data["error"].lower()

    def test_scan_non_json_content(self, client):
        """POST with non-JSON content type returns 400."""
        response = client.post(
            "/api/scan",
            data="url=https://example.com",
            content_type="application/x-www-form-urlencoded",
        )
        assert response.status_code == 400


# =============================================================================
# Scan Endpoint — Successful Scan Tests
# =============================================================================

class TestScanEndpointSuccess:
    """Tests for /api/scan with valid URLs (mocking DNS resolution)."""

    @patch("app.check_resolved_ip", return_value=None)
    def test_scan_valid_url_returns_200(self, mock_ip_check, client, valid_scan_payload):
        response = client.post(
            "/api/scan",
            data=json.dumps(valid_scan_payload),
            content_type="application/json",
        )
        assert response.status_code == 200

    @patch("app.check_resolved_ip", return_value=None)
    def test_scan_valid_url_returns_success(self, mock_ip_check, client, valid_scan_payload):
        response = client.post(
            "/api/scan",
            data=json.dumps(valid_scan_payload),
            content_type="application/json",
        )
        data = response.get_json()
        assert data["success"] is True

    @patch("app.check_resolved_ip", return_value=None)
    def test_scan_result_has_scan_id(self, mock_ip_check, client, valid_scan_payload):
        response = client.post(
            "/api/scan",
            data=json.dumps(valid_scan_payload),
            content_type="application/json",
        )
        data = response.get_json()
        assert "scan_id" in data
        assert len(data["scan_id"]) == 36  # UUID format

    @patch("app.check_resolved_ip", return_value=None)
    def test_scan_result_has_timestamp(self, mock_ip_check, client, valid_scan_payload):
        response = client.post(
            "/api/scan",
            data=json.dumps(valid_scan_payload),
            content_type="application/json",
        )
        data = response.get_json()
        assert "timestamp" in data
        assert "T" in data["timestamp"]

    @patch("app.check_resolved_ip", return_value=None)
    def test_scan_result_has_target_info(self, mock_ip_check, client, valid_scan_payload):
        response = client.post(
            "/api/scan",
            data=json.dumps(valid_scan_payload),
            content_type="application/json",
        )
        data = response.get_json()
        assert data["hostname"] == "example.com"
        assert data["scheme"] == "https"
        assert "target" in data

    @patch("app.check_resolved_ip", return_value=None)
    def test_scan_result_has_validation_dict(self, mock_ip_check, client, valid_scan_payload):
        response = client.post(
            "/api/scan",
            data=json.dumps(valid_scan_payload),
            content_type="application/json",
        )
        data = response.get_json()
        assert "url_validation" in data
        assert data["url_validation"]["is_valid"] is True

    @patch("app.check_resolved_ip", return_value=None)
    def test_scan_result_has_all_sections(self, mock_ip_check, client, valid_scan_payload):
        """Verify all scan modules are executed and return valid sections."""
        response = client.post(
            "/api/scan",
            data=json.dumps(valid_scan_payload),
            content_type="application/json",
        )
        data = response.get_json()
        expected_keys = [
            "availability", "ip_addresses", "dns", "http",
            "redirects", "ssl", "security_headers", "cookies",
            "technology", "server_info", "security_score",
        ]
        for key in expected_keys:
            assert key in data, f"Missing scan section key: {key}"
        assert isinstance(data["recommendations"], list)
        assert data["availability"]["status"] in ("online", "offline")

    @patch("app.check_resolved_ip", return_value=None)
    def test_scan_url_without_scheme(self, mock_ip_check, client):
        """URLs without scheme should be accepted (auto-prepended with https://)."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "example.com"}),
            content_type="application/json",
        )
        data = response.get_json()
        assert data["success"] is True
        assert data["scheme"] == "https"

    @patch("app.check_resolved_ip", return_value=None)
    def test_scan_http_url(self, mock_ip_check, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "http://example.com"}),
            content_type="application/json",
        )
        data = response.get_json()
        assert data["success"] is True
        assert data["scheme"] == "http"

    @patch("app.check_resolved_ip", return_value=None)
    def test_scan_unique_ids(self, mock_ip_check, client, valid_scan_payload):
        """Each scan should generate a unique scan_id."""
        r1 = client.post(
            "/api/scan",
            data=json.dumps(valid_scan_payload),
            content_type="application/json",
        )
        r2 = client.post(
            "/api/scan",
            data=json.dumps(valid_scan_payload),
            content_type="application/json",
        )
        assert r1.get_json()["scan_id"] != r2.get_json()["scan_id"]


# =============================================================================
# Scan Endpoint — Invalid URL Tests
# =============================================================================

class TestScanEndpointInvalidURL:
    """Tests for /api/scan with invalid URLs."""

    def test_scan_empty_url(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert data["step"] == "url_validation"

    def test_scan_whitespace_url(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "   "}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_scan_javascript_scheme(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "javascript:alert(1)"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_scan_file_scheme(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "file:///etc/passwd"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_scan_ftp_scheme(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "ftp://example.com"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_scan_data_scheme(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "data:text/html,<h1>test</h1>"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_scan_just_protocol(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "https://"}),
            content_type="application/json",
        )
        assert response.status_code == 400


# =============================================================================
# Scan Endpoint — SSRF Protection Tests
# =============================================================================

class TestScanEndpointSSRF:
    """Tests for /api/scan SSRF protection."""

    def test_scan_localhost(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "http://localhost"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_scan_localhost_with_port(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "http://localhost:8080"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_scan_loopback_ip(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "http://127.0.0.1"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_scan_private_class_a(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "http://10.0.0.1"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_scan_private_class_b(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "http://172.16.0.1"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_scan_private_class_c(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "http://192.168.1.1"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_scan_metadata_ip(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "http://169.254.169.254"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_scan_metadata_hostname(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "http://metadata.google.internal"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    @patch("app.check_resolved_ip", return_value="Scanning private/internal network addresses is not allowed.")
    def test_scan_ssrf_via_dns_rebinding(self, mock_ip_check, client):
        """If DNS resolves to a private IP, the scan should be blocked with 403."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "https://evil-rebind.example.com"}),
            content_type="application/json",
        )
        assert response.status_code == 403
        data = response.get_json()
        assert data["success"] is False
        assert data["step"] == "ssrf_check"

    def test_scan_zero_ip(self, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "http://0.0.0.0"}),
            content_type="application/json",
        )
        assert response.status_code == 400


# =============================================================================
# Error Handler Tests
# =============================================================================

class TestErrorHandlers:
    """Tests for custom error handlers (404 and 500)."""

    def test_404_api_route_returns_json(self, client):
        """API 404s should return JSON error response."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    def test_404_page_route_returns_html(self, client):
        """Non-API 404s should return the index page as HTML."""
        response = client.get("/nonexistent-page")
        assert response.status_code == 404
        assert response.content_type.startswith("text/html")

    def test_500_api_route_returns_json(self, client):
        """API 500 errors should return JSON."""
        # Disable exception propagation so Flask invokes the 500 handler
        app.config["TESTING"] = False
        app.config["PROPAGATE_EXCEPTIONS"] = False
        try:
            with patch("app.validate_url", side_effect=Exception("boom")):
                response = client.post(
                    "/api/scan",
                    data=json.dumps({"url": "https://example.com"}),
                    content_type="application/json",
                )
                assert response.status_code == 500
                data = response.get_json()
                assert data["success"] is False
                assert "internal" in data["error"].lower()
        finally:
            app.config["TESTING"] = True


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Edge cases and boundary tests."""

    @patch("app.check_resolved_ip", return_value=None)
    def test_scan_url_with_query_params(self, mock_ip_check, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "https://example.com/search?q=test&page=1"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    @patch("app.check_resolved_ip", return_value=None)
    def test_scan_url_with_fragment_stripped(self, mock_ip_check, client):
        """Fragments (#section) should be stripped during normalization."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "https://example.com/page#section"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "#" not in data["target"]

    @patch("app.check_resolved_ip", return_value=None)
    def test_scan_url_with_port(self, mock_ip_check, client):
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "https://example.com:8443"}),
            content_type="application/json",
        )
        data = response.get_json()
        assert data["success"] is True
        assert data["port"] == 8443

    @patch("app.check_resolved_ip", return_value=None)
    def test_scan_url_case_insensitive(self, mock_ip_check, client):
        """Hostname should be normalized to lowercase."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"url": "https://EXAMPLE.COM"}),
            content_type="application/json",
        )
        data = response.get_json()
        assert data["hostname"] == "example.com"

    def test_scan_with_extra_fields_ignored(self, client):
        """Extra fields in the request body should not cause errors."""
        with patch("app.check_resolved_ip", return_value=None):
            response = client.post(
                "/api/scan",
                data=json.dumps({"url": "https://example.com", "extra": "ignored"}),
                content_type="application/json",
            )
            assert response.status_code == 200

    def test_health_method_not_allowed(self, client):
        """POST to /api/health should return 405."""
        response = client.post("/api/health")
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
