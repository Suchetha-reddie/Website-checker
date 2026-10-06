"""
Excel Exporter Module
=====================
Generates professional, styled multi-tab Excel (.xlsx) security audit reports
from website scan results using openpyxl.
"""

import io
from datetime import datetime
from typing import Dict, Any, List

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# =============================================================================
# Color Palette & Styles
# =============================================================================
COLOR_HEADER_BG = "1E293B"      # Dark Slate Navy
COLOR_HEADER_FG = "FFFFFF"      # White
COLOR_SECTION_BG = "0EA5E9"     # Brand Sky Blue Accent
COLOR_SECTION_FG = "FFFFFF"     # White
COLOR_ZEBRA_ROW = "F8FAFC"      # Light grey-blue for alternating rows
COLOR_BORDER = "CBD5E1"         # Border light slate

COLOR_SUCCESS_BG = "D1FAE5"     # Soft Green
COLOR_SUCCESS_FG = "065F46"     # Dark Green
COLOR_WARNING_BG = "FEF3C7"     # Soft Yellow/Amber
COLOR_WARNING_FG = "92400E"     # Dark Amber
COLOR_DANGER_BG = "FEE2E2"      # Soft Red
COLOR_DANGER_FG = "991B1B"      # Dark Red
COLOR_INFO_BG = "E0F2FE"        # Soft Blue
COLOR_INFO_FG = "075985"        # Dark Blue

THIN_BORDER_SIDE = Side(border_style="thin", color=COLOR_BORDER)
TABLE_BORDER = Border(
    left=THIN_BORDER_SIDE,
    right=THIN_BORDER_SIDE,
    top=THIN_BORDER_SIDE,
    bottom=THIN_BORDER_SIDE,
)

FONT_TITLE = Font(name="Segoe UI", size=16, bold=True, color="0F172A")
FONT_SUBTITLE = Font(name="Segoe UI", size=10, italic=True, color="64748B")
FONT_SECTION = Font(name="Segoe UI", size=12, bold=True, color=COLOR_SECTION_FG)
FONT_HEADER = Font(name="Segoe UI", size=11, bold=True, color=COLOR_HEADER_FG)
FONT_BOLD = Font(name="Segoe UI", size=10, bold=True)
FONT_REGULAR = Font(name="Segoe UI", size=10)

ALIGN_LEFT = Alignment(horizontal="left", vertical="center")
ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")


def generate_excel_report(scan_data: Dict[str, Any]) -> io.BytesIO:
    """
    Generate a full-featured Excel workbook from scan result data.

    Args:
        scan_data: Dictionary of scan results from /api/scan.

    Returns:
        io.BytesIO buffer containing the .xlsx workbook bytes.
    """
    wb = openpyxl.Workbook()
    # Remove default empty sheet
    wb.remove(wb.active)

    # 1. Executive Summary Sheet
    _build_summary_sheet(wb, scan_data)

    # 2. Security Analysis & Recommendations Sheet
    _build_recommendations_sheet(wb, scan_data)

    # 3. SSL / TLS Certificate Sheet
    _build_ssl_sheet(wb, scan_data)

    # 4. Security Headers Sheet
    _build_headers_sheet(wb, scan_data)

    # 5. Network & DNS Sheet
    _build_network_dns_sheet(wb, scan_data)

    # 6. HTTP & Technologies Sheet
    _build_http_tech_sheet(wb, scan_data)

    # Save to in-memory bytes buffer
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


# =============================================================================
# Helper Formatters & Sheet Builders
# =============================================================================

def _apply_row_style(row_cells, bg_color=None, font=None, alignment=None, border=None):
    """Utility to style a collection of cells in a row."""
    for cell in row_cells:
        if bg_color:
            cell.fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
        if font:
            cell.font = font
        if alignment:
            cell.alignment = alignment
        if border:
            cell.border = border


def _auto_fit_columns(ws, min_width=12, max_width=60):
    """Adjust column widths dynamically based on content length."""
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            val = str(cell.value or "")
            if "\n" in val:
                val = max(val.split("\n"), key=len)
            max_len = max(max_len, len(val))
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, min_width), max_width)


def _add_section_header(ws, row_idx: int, title: str, col_count: int = 4):
    """Add a bold section banner row spanning across columns."""
    cell = ws.cell(row=row_idx, column=1, value=f"  {title.upper()}")
    ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=col_count)
    _apply_row_style(
        [ws.cell(row=row_idx, column=c) for c in range(1, col_count + 1)],
        bg_color=COLOR_SECTION_BG,
        font=FONT_SECTION,
        alignment=ALIGN_LEFT,
    )
    ws.row_dimensions[row_idx].height = 24


def _add_table_headers(ws, row_idx: int, headers: List[str]):
    """Add stylized table header row."""
    for c_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=row_idx, column=c_idx, value=h)
        cell.font = FONT_HEADER
        cell.fill = PatternFill(start_color=COLOR_HEADER_BG, end_color=COLOR_HEADER_BG, fill_type="solid")
        cell.alignment = ALIGN_CENTER if "Status" in h or "#" in h or "Score" in h else ALIGN_LEFT
        cell.border = TABLE_BORDER
    ws.row_dimensions[row_idx].height = 22


# =============================================================================
# Sheet 1: Executive Summary
# =============================================================================

def _build_summary_sheet(wb, data: Dict[str, Any]):
    ws = wb.create_sheet(title="Executive Summary")
    ws.views.sheetView[0].showGridLines = True

    # Title Block
    ws.cell(row=1, column=1, value="Website Information & Security Audit Report").font = FONT_TITLE
    ws.cell(
        row=2, column=1,
        value=f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | Educational & Passive Audit Tool"
    ).font = FONT_SUBTITLE

    # General Information
    _add_section_header(ws, 4, "1. Target Overview", 4)
    general_info = [
        ("Target URL", data.get("target") or data.get("hostname") or "—"),
        ("Hostname", data.get("hostname") or "—"),
        ("Scheme", (data.get("scheme") or "—").upper()),
        ("Scan ID", data.get("scan_id") or "—"),
        ("Scan Timestamp", data.get("timestamp") or "—"),
    ]

    avail = data.get("availability") or {}
    general_info.append(("Website Status", "Online" if avail.get("status") == "online" else "Offline"))
    if avail.get("response_time_ms") is not None:
        general_info.append(("Response Time", f"{avail.get('response_time_ms')} ms ({avail.get('response_time_class', '—')})"))

    cur_row = 5
    for label, val in general_info:
        ws.cell(row=cur_row, column=1, value=label).font = FONT_BOLD
        ws.cell(row=cur_row, column=2, value=str(val)).font = FONT_REGULAR
        ws.cell(row=cur_row, column=1).border = TABLE_BORDER
        ws.cell(row=cur_row, column=2).border = TABLE_BORDER
        ws.cell(row=cur_row, column=1).alignment = ALIGN_LEFT
        ws.cell(row=cur_row, column=2).alignment = ALIGN_LEFT
        cur_row += 1

    # Security Score & KPI
    cur_row += 1
    _add_section_header(ws, cur_row, "2. Security Score & Performance", 4)
    cur_row += 1

    score_data = data.get("security_score") or {}
    total_score = score_data.get("total", 0)
    grade = score_data.get("grade", "—")

    ws.cell(row=cur_row, column=1, value="Overall Security Score").font = FONT_BOLD
    score_cell = ws.cell(row=cur_row, column=2, value=f"{total_score} / 100")
    score_cell.font = Font(name="Segoe UI", size=12, bold=True)
    score_bg = COLOR_SUCCESS_BG if total_score >= 80 else COLOR_WARNING_BG if total_score >= 50 else COLOR_DANGER_BG
    score_fg = COLOR_SUCCESS_FG if total_score >= 80 else COLOR_WARNING_FG if total_score >= 50 else COLOR_DANGER_FG
    score_cell.fill = PatternFill(start_color=score_bg, end_color=score_bg, fill_type="solid")
    score_cell.font = Font(name="Segoe UI", size=12, bold=True, color=score_fg)
    ws.cell(row=cur_row, column=1).border = TABLE_BORDER
    score_cell.border = TABLE_BORDER

    cur_row += 1
    ws.cell(row=cur_row, column=1, value="Security Grade").font = FONT_BOLD
    grade_cell = ws.cell(row=cur_row, column=2, value=grade)
    grade_cell.font = Font(name="Segoe UI", size=12, bold=True, color=score_fg)
    grade_cell.fill = PatternFill(start_color=score_bg, end_color=score_bg, fill_type="solid")
    ws.cell(row=cur_row, column=1).border = TABLE_BORDER
    grade_cell.border = TABLE_BORDER

    # Score Breakdown Table
    cur_row += 2
    _add_section_header(ws, cur_row, "3. Score Category Breakdown", 4)
    cur_row += 1
    _add_table_headers(ws, cur_row, ["Category", "Earned Score", "Max Score", "Compliance %"])

    breakdown = score_data.get("breakdown") or {}
    category_labels = {
        "https": "HTTPS Enforcement & Availability",
        "ssl": "SSL/TLS Certificate Validity & Security",
        "headers": "Security Headers Configuration",
        "cookies": "Cookie Security Flags (Secure, HttpOnly)",
        "redirects": "Redirect Health & Hops",
        "other": "Information Disclosure & Extra Checks",
    }

    cur_row += 1
    for key, info in breakdown.items():
        s = info.get("score", 0)
        m = info.get("max", 0)
        pct = round((s / m * 100)) if m else 0

        ws.cell(row=cur_row, column=1, value=category_labels.get(key, key.title())).font = FONT_REGULAR
        ws.cell(row=cur_row, column=2, value=s).alignment = ALIGN_CENTER
        ws.cell(row=cur_row, column=3, value=m).alignment = ALIGN_CENTER

        pct_cell = ws.cell(row=cur_row, column=4, value=f"{pct}%")
        pct_cell.alignment = ALIGN_CENTER
        cat_bg = COLOR_SUCCESS_BG if pct >= 80 else COLOR_WARNING_BG if pct >= 50 else COLOR_DANGER_BG
        cat_fg = COLOR_SUCCESS_FG if pct >= 80 else COLOR_WARNING_FG if pct >= 50 else COLOR_DANGER_FG
        pct_cell.fill = PatternFill(start_color=cat_bg, end_color=cat_bg, fill_type="solid")
        pct_cell.font = Font(name="Segoe UI", size=10, bold=True, color=cat_fg)

        for col in range(1, 5):
            ws.cell(row=cur_row, column=col).border = TABLE_BORDER
        cur_row += 1

    _auto_fit_columns(ws)


# =============================================================================
# Sheet 2: Recommendations
# =============================================================================

def _build_recommendations_sheet(wb, data: Dict[str, Any]):
    ws = wb.create_sheet(title="Recommendations")
    ws.views.sheetView[0].showGridLines = True

    _add_section_header(ws, 1, "Actionable Security Recommendations", 4)
    _add_table_headers(ws, 2, ["#", "Severity", "Category", "Action / Recommendation"])

    recommendations = data.get("recommendations") or []
    if not recommendations:
        ws.cell(row=3, column=1, value="—")
        ws.cell(row=3, column=2, value="NONE")
        ws.cell(row=3, column=3, value="General")
        ws.cell(row=3, column=4, value="No issues or recommendations detected. Security configuration is solid!")
        for col in range(1, 5):
            ws.cell(row=3, column=col).border = TABLE_BORDER
    else:
        for idx, rec in enumerate(recommendations, start=1):
            row_idx = idx + 2
            sev = (rec.get("severity") or "info").lower()

            c1 = ws.cell(row=row_idx, column=1, value=idx)
            c1.alignment = ALIGN_CENTER

            c2 = ws.cell(row=row_idx, column=2, value=sev.upper())
            c2.alignment = ALIGN_CENTER
            if sev == "high":
                c2.fill = PatternFill(start_color=COLOR_DANGER_BG, end_color=COLOR_DANGER_BG, fill_type="solid")
                c2.font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_DANGER_FG)
            elif sev == "medium":
                c2.fill = PatternFill(start_color=COLOR_WARNING_BG, end_color=COLOR_WARNING_BG, fill_type="solid")
                c2.font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_WARNING_FG)
            else:
                c2.fill = PatternFill(start_color=COLOR_INFO_BG, end_color=COLOR_INFO_BG, fill_type="solid")
                c2.font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_INFO_FG)

            c3 = ws.cell(row=row_idx, column=3, value=rec.get("category", "General"))
            c3.font = FONT_BOLD

            c4 = ws.cell(row=row_idx, column=4, value=rec.get("message", "—"))
            c4.font = FONT_REGULAR

            for col in range(1, 5):
                ws.cell(row=row_idx, column=col).border = TABLE_BORDER

    _auto_fit_columns(ws)


# =============================================================================
# Sheet 3: SSL / TLS Certificate
# =============================================================================

def _build_ssl_sheet(wb, data: Dict[str, Any]):
    ws = wb.create_sheet(title="SSL & TLS Certificate")
    ws.views.sheetView[0].showGridLines = True

    ssl_data = data.get("ssl") or {}
    _add_section_header(ws, 1, "SSL / TLS Certificate Details", 3)
    _add_table_headers(ws, 2, ["Property", "Value", "Status / Notes"])

    rows = []
    is_valid = ssl_data.get("valid", False)
    rows.append(("Certificate Valid", "Yes" if is_valid else "No", "PASS" if is_valid else "FAIL"))
    rows.append(("Hostname Match", "Yes" if ssl_data.get("hostname_match") else "No", "PASS" if ssl_data.get("hostname_match") else "FAIL"))
    rows.append(("TLS Protocol Version", ssl_data.get("protocol_version") or "—", "Modern" if "1.3" in str(ssl_data.get("protocol_version")) else "Standard"))

    cipher = ssl_data.get("cipher") or {}
    rows.append(("Cipher Name", cipher.get("name") or "—", f"{cipher.get('bits', '')} bits" if cipher.get("bits") else "—"))
    rows.append(("Valid From (notBefore)", ssl_data.get("not_before") or "—", "—"))
    rows.append(("Valid Until (notAfter)", ssl_data.get("not_after") or "—", "—"))

    days = ssl_data.get("days_until_expiry")
    if days is not None:
        status_txt = "CRITICAL" if days <= 7 else "WARNING" if days <= 30 else "HEALTHY"
        rows.append(("Days Until Expiration", f"{days} days", status_txt))

    subject = ssl_data.get("subject") or {}
    rows.append(("Subject Common Name", subject.get("commonName") or subject.get("organizationName") or "—", "—"))

    issuer = ssl_data.get("issuer") or {}
    rows.append(("Certificate Authority / Issuer", issuer.get("organizationName") or issuer.get("commonName") or "—", "—"))
    rows.append(("Serial Number", ssl_data.get("serial_number") or "—", "—"))

    if ssl_data.get("error"):
        rows.append(("SSL Verification Error", ssl_data.get("error"), "ERROR"))

    for idx, (prop, val, note) in enumerate(rows, start=3):
        ws.cell(row=idx, column=1, value=prop).font = FONT_BOLD
        ws.cell(row=idx, column=2, value=str(val)).font = FONT_REGULAR

        note_cell = ws.cell(row=idx, column=3, value=note)
        note_cell.alignment = ALIGN_CENTER
        if note in ("PASS", "HEALTHY"):
            note_cell.fill = PatternFill(start_color=COLOR_SUCCESS_BG, end_color=COLOR_SUCCESS_BG, fill_type="solid")
            note_cell.font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_SUCCESS_FG)
        elif note in ("FAIL", "CRITICAL", "ERROR"):
            note_cell.fill = PatternFill(start_color=COLOR_DANGER_BG, end_color=COLOR_DANGER_BG, fill_type="solid")
            note_cell.font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_DANGER_FG)
        elif note == "WARNING":
            note_cell.fill = PatternFill(start_color=COLOR_WARNING_BG, end_color=COLOR_WARNING_BG, fill_type="solid")
            note_cell.font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_WARNING_FG)
        else:
            note_cell.font = FONT_REGULAR

        for c in range(1, 4):
            ws.cell(row=idx, column=c).border = TABLE_BORDER

    # Subject Alternative Names (SANs)
    sans = ssl_data.get("san") or []
    if sans:
        start_r = len(rows) + 5
        _add_section_header(ws, start_r, "Subject Alternative Names (SAN)", 3)
        _add_table_headers(ws, start_r + 1, ["#", "Type", "DNS / IP Value"])
        for s_idx, san in enumerate(sans, start=1):
            r = start_r + 1 + s_idx
            ws.cell(row=r, column=1, value=s_idx).alignment = ALIGN_CENTER
            ws.cell(row=r, column=2, value=san.get("type", "DNS")).alignment = ALIGN_CENTER
            ws.cell(row=r, column=3, value=san.get("value", "")).font = FONT_REGULAR
            for c in range(1, 4):
                ws.cell(row=r, column=c).border = TABLE_BORDER

    _auto_fit_columns(ws)


# =============================================================================
# Sheet 4: Security Headers
# =============================================================================

def _build_headers_sheet(wb, data: Dict[str, Any]):
    ws = wb.create_sheet(title="Security Headers")
    ws.views.sheetView[0].showGridLines = True

    sec_headers = data.get("security_headers") or {}
    _add_section_header(ws, 1, "Security Headers Analysis", 5)
    _add_table_headers(ws, 2, ["Header", "Status", "Configured Value", "Description", "Best Practice Recommendation"])

    header_names = [
        "Content-Security-Policy",
        "Strict-Transport-Security",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Referrer-Policy",
        "Permissions-Policy",
    ]

    cur_row = 3
    for name in header_names:
        h_info = sec_headers.get(name) or {}
        is_present = h_info.get("present", False)

        ws.cell(row=cur_row, column=1, value=name).font = FONT_BOLD

        st_cell = ws.cell(row=cur_row, column=2, value="PRESENT" if is_present else "MISSING")
        st_cell.alignment = ALIGN_CENTER
        if is_present:
            st_cell.fill = PatternFill(start_color=COLOR_SUCCESS_BG, end_color=COLOR_SUCCESS_BG, fill_type="solid")
            st_cell.font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_SUCCESS_FG)
        else:
            st_cell.fill = PatternFill(start_color=COLOR_DANGER_BG, end_color=COLOR_DANGER_BG, fill_type="solid")
            st_cell.font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_DANGER_FG)

        ws.cell(row=cur_row, column=3, value=h_info.get("value") or "—").font = FONT_REGULAR
        ws.cell(row=cur_row, column=4, value=h_info.get("description") or "—").font = FONT_REGULAR
        ws.cell(row=cur_row, column=5, value=h_info.get("recommendation") or "Properly implemented.").font = FONT_REGULAR

        for c in range(1, 6):
            ws.cell(row=cur_row, column=c).border = TABLE_BORDER
        cur_row += 1

    # Leaked information headers
    info_leaks = sec_headers.get("_info_leak") or []
    if info_leaks:
        cur_row += 2
        _add_section_header(ws, cur_row, "Information Disclosure Headers", 5)
        cur_row += 1
        _add_table_headers(ws, cur_row, ["Header Name", "Exposed Value", "Risk", "Remediation", ""])
        cur_row += 1
        for leak in info_leaks:
            ws.cell(row=cur_row, column=1, value=leak.get("header")).font = FONT_BOLD
            ws.cell(row=cur_row, column=2, value=leak.get("value")).font = FONT_REGULAR
            r_cell = ws.cell(row=cur_row, column=3, value="LEAK")
            r_cell.alignment = ALIGN_CENTER
            r_cell.fill = PatternFill(start_color=COLOR_WARNING_BG, end_color=COLOR_WARNING_BG, fill_type="solid")
            r_cell.font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_WARNING_FG)
            ws.cell(row=cur_row, column=4, value="Remove or mask server software version headers.").font = FONT_REGULAR
            ws.cell(row=cur_row, column=5, value="")
            for c in range(1, 6):
                ws.cell(row=cur_row, column=c).border = TABLE_BORDER
            cur_row += 1

    _auto_fit_columns(ws)


# =============================================================================
# Sheet 5: Network & DNS
# =============================================================================

def _build_network_dns_sheet(wb, data: Dict[str, Any]):
    ws = wb.create_sheet(title="Network & DNS")
    ws.views.sheetView[0].showGridLines = True

    # IP Resolution
    _add_section_header(ws, 1, "IP Addresses", 4)
    _add_table_headers(ws, 2, ["Type", "IP Address", "Status", "Note"])

    cur_row = 3
    ip_data = data.get("ip_addresses") or {}
    ipv4s = ip_data.get("ipv4") or []
    ipv6s = ip_data.get("ipv6") or []

    for ip in ipv4s:
        ws.cell(row=cur_row, column=1, value="IPv4").alignment = ALIGN_CENTER
        ws.cell(row=cur_row, column=2, value=ip).font = FONT_REGULAR
        ws.cell(row=cur_row, column=3, value="RESOLVED").alignment = ALIGN_CENTER
        ws.cell(row=cur_row, column=4, value="Public IPv4 address")
        for c in range(1, 5):
            ws.cell(row=cur_row, column=c).border = TABLE_BORDER
        cur_row += 1

    for ip in ipv6s:
        ws.cell(row=cur_row, column=1, value="IPv6").alignment = ALIGN_CENTER
        ws.cell(row=cur_row, column=2, value=ip).font = FONT_REGULAR
        ws.cell(row=cur_row, column=3, value="RESOLVED").alignment = ALIGN_CENTER
        ws.cell(row=cur_row, column=4, value="Public IPv6 address")
        for c in range(1, 5):
            ws.cell(row=cur_row, column=c).border = TABLE_BORDER
        cur_row += 1

    if not ipv4s and not ipv6s:
        ws.cell(row=cur_row, column=1, value="—")
        ws.cell(row=cur_row, column=2, value="No IP records resolved")
        ws.cell(row=cur_row, column=3, value="—")
        ws.cell(row=cur_row, column=4, value="—")
        for c in range(1, 5):
            ws.cell(row=cur_row, column=c).border = TABLE_BORDER
        cur_row += 1

    # DNS Records
    cur_row += 2
    _add_section_header(ws, cur_row, "DNS Records", 4)
    cur_row += 1
    _add_table_headers(ws, cur_row, ["Record Type", "#", "Record Value / Target", "Details"])
    cur_row += 1

    dns_data = data.get("dns") or {}
    record_types = ["A", "AAAA", "MX", "NS", "CNAME", "TXT"]

    for r_type in record_types:
        records = dns_data.get(r_type) or []
        for i, rec in enumerate(records, start=1):
            ws.cell(row=cur_row, column=1, value=r_type).alignment = ALIGN_CENTER
            ws.cell(row=cur_row, column=2, value=i).alignment = ALIGN_CENTER
            if r_type == "MX" and isinstance(rec, dict):
                ws.cell(row=cur_row, column=3, value=rec.get("exchange", ""))
                ws.cell(row=cur_row, column=4, value=f"Priority: {rec.get('priority', '—')}")
            else:
                ws.cell(row=cur_row, column=3, value=str(rec))
                ws.cell(row=cur_row, column=4, value="—")
            for c in range(1, 5):
                ws.cell(row=cur_row, column=c).border = TABLE_BORDER
            cur_row += 1

    # SOA record
    soa = dns_data.get("SOA")
    if soa:
        ws.cell(row=cur_row, column=1, value="SOA").alignment = ALIGN_CENTER
        ws.cell(row=cur_row, column=2, value=1).alignment = ALIGN_CENTER
        ws.cell(row=cur_row, column=3, value=f"Primary NS: {soa.get('mname')} | Admin: {soa.get('rname')}")
        ws.cell(row=cur_row, column=4, value=f"Serial: {soa.get('serial')}, Refresh: {soa.get('refresh')}s")
        for c in range(1, 5):
            ws.cell(row=cur_row, column=c).border = TABLE_BORDER

    _auto_fit_columns(ws)


# =============================================================================
# Sheet 6: HTTP & Technologies
# =============================================================================

def _build_http_tech_sheet(wb, data: Dict[str, Any]):
    ws = wb.create_sheet(title="HTTP & Technology")
    ws.views.sheetView[0].showGridLines = True

    http_data = data.get("http") or {}
    _add_section_header(ws, 1, "HTTP Configuration", 4)
    _add_table_headers(ws, 2, ["Property", "Value", "Status", "Note"])

    http_rows = [
        ("HTTPS Available", "Yes" if http_data.get("https_available") else "No", "PASS" if http_data.get("https_available") else "FAIL"),
        ("HTTP to HTTPS Redirect", "Enforced" if http_data.get("http_to_https_redirect") else "Not enforced", "PASS" if http_data.get("http_to_https_redirect") else "WARNING"),
        ("HTTP Status Code", str(http_data.get("status_code") or "—"), "OK" if http_data.get("status_code") == 200 else "INFO"),
        ("Final Destination URL", http_data.get("final_url") or "—", "—"),
        ("Server Header", http_data.get("server") or "—", "—"),
        ("X-Powered-By Header", http_data.get("powered_by") or "—", "—"),
    ]

    for idx, (prop, val, status) in enumerate(http_rows, start=3):
        ws.cell(row=idx, column=1, value=prop).font = FONT_BOLD
        ws.cell(row=idx, column=2, value=val).font = FONT_REGULAR
        st_cell = ws.cell(row=idx, column=3, value=status)
        st_cell.alignment = ALIGN_CENTER
        if status in ("PASS", "OK"):
            st_cell.fill = PatternFill(start_color=COLOR_SUCCESS_BG, end_color=COLOR_SUCCESS_BG, fill_type="solid")
            st_cell.font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_SUCCESS_FG)
        elif status == "FAIL":
            st_cell.fill = PatternFill(start_color=COLOR_DANGER_BG, end_color=COLOR_DANGER_BG, fill_type="solid")
            st_cell.font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_DANGER_FG)
        elif status == "WARNING":
            st_cell.fill = PatternFill(start_color=COLOR_WARNING_BG, end_color=COLOR_WARNING_BG, fill_type="solid")
            st_cell.font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_WARNING_FG)
        ws.cell(row=idx, column=4, value="—")
        for c in range(1, 5):
            ws.cell(row=idx, column=c).border = TABLE_BORDER

    cur_row = len(http_rows) + 4

    # Cookies
    cookies = data.get("cookies") or []
    if cookies:
        _add_section_header(ws, cur_row, "Cookie Security Flags", 5)
        cur_row += 1
        _add_table_headers(ws, cur_row, ["Cookie Name", "Domain", "Secure Flag", "HttpOnly Flag", "SameSite"])
        cur_row += 1
        for c in cookies:
            ws.cell(row=cur_row, column=1, value=c.get("name", "—")).font = FONT_BOLD
            ws.cell(row=cur_row, column=2, value=c.get("domain", "—")).font = FONT_REGULAR

            sec_cell = ws.cell(row=cur_row, column=3, value="TRUE" if c.get("secure") else "FALSE")
            sec_cell.alignment = ALIGN_CENTER
            sec_bg = COLOR_SUCCESS_BG if c.get("secure") else COLOR_DANGER_BG
            sec_fg = COLOR_SUCCESS_FG if c.get("secure") else COLOR_DANGER_FG
            sec_cell.fill = PatternFill(start_color=sec_bg, end_color=sec_bg, fill_type="solid")
            sec_cell.font = Font(name="Segoe UI", size=10, bold=True, color=sec_fg)

            http_cell = ws.cell(row=cur_row, column=4, value="TRUE" if c.get("httponly") else "FALSE")
            http_cell.alignment = ALIGN_CENTER
            http_bg = COLOR_SUCCESS_BG if c.get("httponly") else COLOR_DANGER_BG
            http_fg = COLOR_SUCCESS_FG if c.get("httponly") else COLOR_DANGER_FG
            http_cell.fill = PatternFill(start_color=http_bg, end_color=http_bg, fill_type="solid")
            http_cell.font = Font(name="Segoe UI", size=10, bold=True, color=http_fg)

            ws.cell(row=cur_row, column=5, value=c.get("samesite") or "Not set").alignment = ALIGN_CENTER
            for col in range(1, 6):
                ws.cell(row=cur_row, column=col).border = TABLE_BORDER
            cur_row += 1
        cur_row += 1

    # Detected Technologies
    tech_data = data.get("technology") or {}
    technologies = tech_data.get("technologies") or []
    _add_section_header(ws, cur_row, "Detected Technologies & Stacks", 4)
    cur_row += 1
    _add_table_headers(ws, cur_row, ["Category", "Technology", "Detection Method / Source", ""])
    cur_row += 1

    if technologies:
        for t in technologies:
            ws.cell(row=cur_row, column=1, value=t.get("category", "General")).font = FONT_BOLD
            ws.cell(row=cur_row, column=2, value=t.get("name", "—")).font = FONT_REGULAR
            ws.cell(row=cur_row, column=3, value=t.get("source", "—")).font = FONT_REGULAR
            ws.cell(row=cur_row, column=4, value="")
            for c in range(1, 5):
                ws.cell(row=cur_row, column=c).border = TABLE_BORDER
            cur_row += 1
    else:
        ws.cell(row=cur_row, column=1, value="—")
        ws.cell(row=cur_row, column=2, value="No technologies identified")
        ws.cell(row=cur_row, column=3, value="Passive inspection found no fingerprints")
        ws.cell(row=cur_row, column=4, value="")
        for c in range(1, 5):
            ws.cell(row=cur_row, column=c).border = TABLE_BORDER

    _auto_fit_columns(ws)
