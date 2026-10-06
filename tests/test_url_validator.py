"""
Tests for URL Validator Module
==============================
Tests URL validation, normalization, and SSRF protection.
"""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.url_validator import validate_url, URLValidationResult


class TestValidURLs:
    """Test that valid URLs are accepted and properly normalized."""

    def test_https_url(self):
        result = validate_url("https://example.com")
        assert result.is_valid is True
        assert result.hostname == "example.com"
        assert result.scheme == "https"
        assert result.error is None

    def test_http_url(self):
        result = validate_url("http://example.com")
        assert result.is_valid is True
        assert result.hostname == "example.com"
        assert result.scheme == "http"

    def test_url_without_scheme(self):
        """URLs without a scheme should get https:// prepended."""
        result = validate_url("example.com")
        assert result.is_valid is True
        assert result.scheme == "https"
        assert result.hostname == "example.com"
        assert "https://" in result.normalized_url

    def test_url_with_path(self):
        result = validate_url("https://example.com/page/test")
        assert result.is_valid is True
        assert result.path == "/page/test"

    def test_url_with_port(self):
        result = validate_url("https://example.com:8443")
        assert result.is_valid is True
        assert result.port == 8443

    def test_url_with_subdomain(self):
        result = validate_url("https://www.sub.example.com")
        assert result.is_valid is True
        assert result.hostname == "www.sub.example.com"

    def test_url_with_trailing_slash(self):
        result = validate_url("https://example.com/")
        assert result.is_valid is True

    def test_url_case_normalization(self):
        """Hostnames should be lowercased."""
        result = validate_url("https://EXAMPLE.COM")
        assert result.is_valid is True
        assert result.hostname == "example.com"

    def test_url_with_query_string(self):
        result = validate_url("https://example.com/search?q=test")
        assert result.is_valid is True


class TestInvalidURLs:
    """Test that invalid URLs are rejected."""

    def test_empty_string(self):
        result = validate_url("")
        assert result.is_valid is False
        assert result.error is not None

    def test_whitespace_only(self):
        result = validate_url("   ")
        assert result.is_valid is False

    def test_none_value(self):
        """Passing None-like empty value."""
        result = validate_url("")
        assert result.is_valid is False

    def test_just_protocol(self):
        result = validate_url("https://")
        assert result.is_valid is False


class TestDangerousSchemes:
    """Test that dangerous URL schemes are blocked."""

    def test_javascript_scheme(self):
        result = validate_url("javascript:alert(1)")
        assert result.is_valid is False
        assert "dangerous" in result.error.lower() or "unsupported" in result.error.lower()

    def test_file_scheme(self):
        result = validate_url("file:///etc/passwd")
        assert result.is_valid is False

    def test_data_scheme(self):
        result = validate_url("data:text/html,<h1>test</h1>")
        assert result.is_valid is False

    def test_ftp_scheme(self):
        result = validate_url("ftp://example.com")
        assert result.is_valid is False

    def test_gopher_scheme(self):
        result = validate_url("gopher://example.com")
        assert result.is_valid is False


class TestSSRFProtection:
    """Test SSRF protection against internal/private targets."""

    def test_localhost(self):
        result = validate_url("http://localhost")
        assert result.is_valid is False
        assert "internal" in result.error.lower() or "localhost" in result.error.lower()

    def test_localhost_with_port(self):
        result = validate_url("http://localhost:8080")
        assert result.is_valid is False

    def test_loopback_ipv4(self):
        result = validate_url("http://127.0.0.1")
        assert result.is_valid is False

    def test_loopback_ipv4_with_port(self):
        result = validate_url("http://127.0.0.1:3000")
        assert result.is_valid is False

    def test_zero_ip(self):
        result = validate_url("http://0.0.0.0")
        assert result.is_valid is False

    def test_private_class_a(self):
        result = validate_url("http://10.0.0.1")
        assert result.is_valid is False

    def test_private_class_b(self):
        result = validate_url("http://172.16.0.1")
        assert result.is_valid is False

    def test_private_class_c(self):
        result = validate_url("http://192.168.1.1")
        assert result.is_valid is False

    def test_link_local(self):
        result = validate_url("http://169.254.169.254")
        assert result.is_valid is False

    def test_cloud_metadata(self):
        """Cloud metadata endpoint must be blocked."""
        result = validate_url("http://169.254.169.254")
        assert result.is_valid is False

    def test_metadata_hostname(self):
        result = validate_url("http://metadata.google.internal")
        assert result.is_valid is False


class TestURLValidationResult:
    """Test the URLValidationResult data class."""

    def test_to_dict_valid(self):
        result = validate_url("https://example.com")
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["is_valid"] is True
        assert d["hostname"] == "example.com"
        assert d["error"] is None

    def test_to_dict_invalid(self):
        result = validate_url("")
        d = result.to_dict()
        assert d["is_valid"] is False
        assert d["error"] is not None
        assert d["hostname"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
