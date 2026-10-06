"""
Tests for Security Headers Checker Module
=========================================
Tests header evaluation, fallback logic on SSL error, and info leaks.
"""

import sys
import os
from unittest.mock import patch, MagicMock
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.headers_checker import check_security_headers, _evaluate_headers, _default_headers_result


class TestHeadersEvaluation:
    """Test header evaluation logic."""

    def test_all_headers_present(self):
        sample_headers = {
            "Content-Security-Policy": "default-src 'self'",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=()",
        }
        result = _evaluate_headers(sample_headers)

        assert result["_total_present"] == 6
        assert result["_total_checked"] == 6
        assert result["Content-Security-Policy"]["present"] is True
        assert result["X-Content-Type-Options"]["correct_value"] is True
        assert result["X-Frame-Options"]["correct_value"] is True

    def test_missing_headers(self):
        sample_headers = {}
        result = _evaluate_headers(sample_headers)

        assert result["_total_present"] == 0
        assert result["Content-Security-Policy"]["present"] is False
        assert result["Content-Security-Policy"]["recommendation"] is not None

    def test_info_leak_headers(self):
        sample_headers = {
            "Server": "Apache/2.4.41",
            "X-Powered-By": "PHP/7.4.3",
        }
        result = _evaluate_headers(sample_headers)

        assert len(result["_info_leak"]) == 2
        leak_names = [leak["header"] for leak in result["_info_leak"]]
        assert "Server" in leak_names
        assert "X-Powered-By" in leak_names


class TestHeadersCheckerNetwork:
    """Test check_security_headers with mocked requests."""

    @patch("requests.get")
    def test_check_headers_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.headers = {
            "Strict-Transport-Security": "max-age=31536000",
            "X-Content-Type-Options": "nosniff",
        }
        mock_get.return_value = mock_resp

        result = check_security_headers("https://example.com")
        assert result["Strict-Transport-Security"]["present"] is True
        assert result["_total_present"] == 2
        assert result["_error"] is None

    @patch("requests.get")
    def test_check_headers_ssl_fallback(self, mock_get):
        # First call fails with SSLError, second (fallback with verify=False) succeeds
        mock_fallback = MagicMock()
        mock_fallback.headers = {
            "X-Frame-Options": "SAMEORIGIN",
        }
        mock_get.side_effect = [
            requests.exceptions.SSLError("Self-signed cert"),
            mock_fallback,
        ]

        result = check_security_headers("https://self-signed.example.com")
        assert result["X-Frame-Options"]["present"] is True
        assert result["_total_present"] == 1
        assert "_warning" in result
