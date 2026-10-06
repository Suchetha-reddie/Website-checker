"""
Tests for Excel Exporter Module
===============================
Tests Excel workbook generation, sheet structures, and formatting.
"""

import sys
import os
import io
import openpyxl

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.excel_exporter import generate_excel_report


class TestExcelReportGeneration:
    """Test full workbook generation."""

    def setup_method(self):
        self.sample_scan = {
            "target": "https://secure-site.example.com",
            "hostname": "secure-site.example.com",
            "scheme": "https",
            "scan_id": "excel-test-uuid",
            "timestamp": "2026-10-07T00:00:00Z",
            "availability": {
                "status": "online",
                "response_time_ms": 78,
                "response_time_class": "fast",
            },
            "security_score": {
                "total": 92,
                "grade": "A+",
                "breakdown": {
                    "https": {"score": 20, "max": 20},
                    "ssl": {"score": 20, "max": 20},
                    "headers": {"score": 30, "max": 30},
                    "cookies": {"score": 10, "max": 10},
                    "redirects": {"score": 7, "max": 10},
                    "other": {"score": 5, "max": 10},
                },
            },
            "recommendations": [
                {
                    "severity": "medium",
                    "category": "Redirects",
                    "message": "Reduce redirect hops.",
                }
            ],
            "ssl": {
                "valid": True,
                "hostname_match": True,
                "protocol_version": "TLSv1.3",
                "cipher": {"name": "TLS_AES_256_GCM_SHA384", "bits": 256},
                "issuer": {"organizationName": "DigiCert Global Root CA"},
                "subject": {"commonName": "secure-site.example.com"},
                "days_until_expiry": 140,
                "not_before": "2026-01-01T00:00:00Z",
                "not_after": "2026-12-31T23:59:59Z",
                "san": [{"type": "DNS", "value": "secure-site.example.com"}],
                "error": None,
            },
            "security_headers": {
                "Content-Security-Policy": {"present": True, "value": "default-src 'self'"},
                "Strict-Transport-Security": {"present": True, "value": "max-age=31536000"},
                "_info_leak": [{"header": "Server", "value": "nginx"}],
                "_total_present": 6,
                "_total_checked": 6,
            },
            "ip_addresses": {
                "ipv4": ["198.51.100.1"],
                "ipv6": ["2001:db8::1"],
            },
            "dns": {
                "A": ["198.51.100.1"],
                "AAAA": ["2001:db8::1"],
                "MX": [{"exchange": "mail.example.com", "priority": 10}],
                "NS": ["ns1.example.com"],
                "SOA": {"mname": "ns1.example.com", "rname": "admin.example.com", "serial": 1234},
            },
            "http": {
                "https_available": True,
                "http_to_https_redirect": True,
                "status_code": 200,
                "final_url": "https://secure-site.example.com/",
                "server": "nginx",
                "powered_by": None,
            },
            "cookies": [
                {
                    "name": "auth_token",
                    "domain": "secure-site.example.com",
                    "secure": True,
                    "httponly": True,
                    "samesite": "Strict",
                }
            ],
            "technology": {
                "technologies": [
                    {"category": "Server", "name": "Nginx", "source": "Server header"},
                    {"category": "JavaScript Framework", "name": "React", "source": "Page source"},
                ]
            },
        }

    def test_generate_excel_creates_valid_xlsx(self):
        buf = generate_excel_report(self.sample_scan)
        assert isinstance(buf, io.BytesIO)
        assert len(buf.getvalue()) > 5000

        wb = openpyxl.load_workbook(buf)
        expected_sheets = [
            "Executive Summary",
            "Recommendations",
            "SSL & TLS Certificate",
            "Security Headers",
            "Network & DNS",
            "HTTP & Technology",
        ]
        for name in expected_sheets:
            assert name in wb.sheetnames

    def test_summary_sheet_content(self):
        buf = generate_excel_report(self.sample_scan)
        wb = openpyxl.load_workbook(buf)
        ws = wb["Executive Summary"]
        assert ws.cell(row=1, column=1).value == "Website Information & Security Audit Report"

    def test_empty_or_minimal_data_does_not_crash(self):
        minimal_scan = {
            "target": "https://minimal.example.com",
            "hostname": "minimal.example.com",
        }
        buf = generate_excel_report(minimal_scan)
        assert len(buf.getvalue()) > 0
        wb = openpyxl.load_workbook(buf)
        assert "Executive Summary" in wb.sheetnames
