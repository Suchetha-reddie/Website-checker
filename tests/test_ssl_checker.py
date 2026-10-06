"""
Tests for SSL Checker Module
============================
Tests SSL certificate validation, date parsing, and error handling.
"""

import sys
import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import ssl

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.ssl_checker import check_ssl, _parse_ssl_date


class TestSSLDateParser:
    """Test SSL certificate date parsing."""

    def test_parse_valid_date_standard(self):
        date_str = "May  4 23:59:59 2026 GMT"
        dt = _parse_ssl_date(date_str)
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 5
        assert dt.day == 4
        assert dt.tzinfo == timezone.utc

    def test_parse_valid_date_single_space(self):
        date_str = "Dec 31 12:00:00 2025 GMT"
        dt = _parse_ssl_date(date_str)
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 12
        assert dt.day == 31

    def test_parse_invalid_date(self):
        assert _parse_ssl_date("invalid-date-string") is None
        assert _parse_ssl_date("") is None
        assert _parse_ssl_date(None) is None


class TestSSLChecker:
    """Test check_ssl with mocked and network connections."""

    @patch("ssl.create_default_context")
    @patch("socket.socket")
    def test_check_ssl_success(self, mock_socket, mock_ssl_context):
        mock_ctx = MagicMock()
        mock_conn = MagicMock()
        mock_ssl_context.return_value = mock_ctx
        mock_ctx.wrap_socket.return_value = mock_conn

        mock_conn.getpeercert.return_value = {
            "subject": ((("commonName", "example.com"),),),
            "issuer": ((("organizationName", "Let's Encrypt"),),),
            "serialNumber": "1234567890",
            "version": 3,
            "notBefore": "Jan  1 00:00:00 2026 GMT",
            "notAfter": "Dec 31 23:59:59 2026 GMT",
            "subjectAltName": (("DNS", "example.com"), ("DNS", "www.example.com")),
        }
        mock_conn.version.return_value = "TLSv1.3"
        mock_conn.cipher.return_value = ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256)

        result = check_ssl("example.com")

        assert result["valid"] is True
        assert result["hostname_match"] is True
        assert result["protocol_version"] == "TLSv1.3"
        assert result["cipher"]["name"] == "TLS_AES_256_GCM_SHA384"
        assert result["subject"]["commonName"] == "example.com"
        assert result["issuer"]["organizationName"] == "Let's Encrypt"
        assert len(result["san"]) == 2
        assert result["error"] is None

    @patch("ssl.create_default_context")
    @patch("socket.socket")
    def test_check_ssl_verification_error(self, mock_socket, mock_ssl_context):
        mock_ctx = MagicMock()
        mock_conn = MagicMock()
        mock_ssl_context.return_value = mock_ctx
        mock_ctx.wrap_socket.return_value = mock_conn
        mock_conn.connect.side_effect = ssl.SSLCertVerificationError("certificate verify failed")

        result = check_ssl("invalid-cert.com")

        assert result["valid"] is False
        assert result["hostname_match"] is False
        assert "Certificate verification failed" in result["error"]
