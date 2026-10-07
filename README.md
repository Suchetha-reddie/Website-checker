# 🛡️ Website Information & Security Checker

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask_3.0%2B-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-95%20Passing-brightgreen.svg?logo=pytest&logoColor=white)](tests/)
[![Excel Export](https://img.shields.io/badge/Export-Excel%20.xlsx-success.svg?logo=microsoft-excel&logoColor=white)](modules/excel_exporter.py)

A production-ready, passive cybersecurity reconnaissance and website auditing platform built with Python (Flask) and modern vanilla JavaScript. It inspects publicly available records and HTTP response telemetry to evaluate any website's security posture, performance, and infrastructure health.

---

## 📖 Deep-Dive Explainer Notebooks

We've crafted comprehensive, beginner-friendly companion notebooks that break down everything with plain English, real-world analogies, and architectural diagrams:

- 📘 **[PROJECT_EXPLAINER_NOTEBOOK.md](PROJECT_EXPLAINER_NOTEBOOK.md)**: Full project guide explaining passive reconnaissance, the 10-step scan life cycle, sequence diagrams, and beginner analogies for every cybersecurity concept.
- 💻 **[CODE_EXPLAINER_NOTEBOOK.md](CODE_EXPLAINER_NOTEBOOK.md)**: Code-by-code walkthrough covering every file in the project, explaining what the file does, why it exists, and how the Python/JS code functions line-by-line.

---

## 🚀 Key Features & Inspection Capabilities

### 1. 🛡️ URL Sanitization & SSRF Defense
- Strict syntax and protocol normalization (`http://` / `https://`).
- **Server-Side Request Forgery (SSRF) Protection**: Blocks attempts to probe internal/private IP blocks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.1`, `localhost`), link-local, and cloud provider metadata services (`169.254.169.254`).

### 2. ⏱️ Availability & Latency Telemetry
- Real-time HTTP ping with microsecond timing.
- Latency classification (`fast` < 300ms, `moderate` 300–1000ms, `slow` > 1000ms).
- HTTP response code verification (`200 OK`, `301/302 Redirects`, `403 Forbidden`, `500 Server Error`).

### 3. 📍 Dual-Stack IP Resolution
- Parallel DNS resolution for both **IPv4** (`A` records) and modern **IPv6** (`AAAA` records).
- Reverse DNS lookup to identify Pointer (PTR) hostnames and hosting providers.

### 4. 📖 Comprehensive DNS Record Audit
- Queries DNS zone records via `dnspython`:
  - `A` / `AAAA` (Server IP routing)
  - `MX` (Mail Exchange server priority)
  - `NS` (Authoritative Name Servers)
  - `CNAME` (Canonical Aliases)
  - `TXT` (SPF anti-spoofing authorization, DKIM, DMARC, site ownership verifications)
  - `SOA` (Start of Authority & zone serials)

### 5. 🔐 SSL/TLS Cryptographic Inspection
- Direct TLS socket handshake on port 443 validated using Mozilla's trusted root CA bundle via `certifi`.
- Certificate expiration tracking with days remaining and validity countdown.
- Issuer authority identification (Let's Encrypt, DigiCert, Cloudflare, Google Trust Services).
- Common Name & Subject Alternative Names (SANs) verification.
- Cipher suite strength audit and TLS protocol version identification (detects legacy TLS 1.0/1.1 vs modern TLS 1.3).

### 6. 🛡️ HTTP Security Headers & Cookie Defense
- Evaluates 6 vital security response headers against OWASP best practices:
  - `Content-Security-Policy` (CSP)
  - `Strict-Transport-Security` (HSTS)
  - `X-Frame-Options` (Clickjacking defense)
  - `X-Content-Type-Options` (MIME-sniffing prevention)
  - `Referrer-Policy` (Privacy leakage protection)
  - `Permissions-Policy` (Restricts microphone, camera, geolocation access)
- Detects information disclosure headers (`Server`, `X-Powered-By`, `X-AspNet-Version`).
- Audits session cookies for security flags (`Secure`, `HttpOnly`, `SameSite`).

### 7. 🔍 Passive Technology Fingerprinting
- Detects CMS platforms (WordPress, Shopify, Drupal, Joomla).
- Identifies Web Servers & Reverse Proxies (Cloudflare, NGINX, Apache, LiteSpeed).
- Detects Frontend Frameworks & Libraries (React, Vue, Angular, Bootstrap, jQuery).

### 8. 📊 100-Point Security Scoring Engine
- Transparent, weighted formula across 5 security pillars:
  - **SSL/TLS Security:** 30 points
  - **HTTP Security Headers:** 25 points
  - **DNS Health & Email Auth:** 20 points
  - **Cookie Security:** 15 points
  - **Server Information Hiding:** 10 points
- Letter grade classification (`A+`, `A`, `B`, `C`, `D`, `F`) with prioritized remediation advice.

### 9. 📑 Multi-Sheet Styled Excel Export (`.xlsx`)
- Built with `openpyxl` without requiring temporary server disk storage.
- Generates a styled Microsoft Excel workbook with:
  - **Executive Summary Sheet**: Key metrics, score, letter grade, and server details.
  - **7 Dedicated Category Sheets**: Availability, IP & DNS, SSL/TLS, Headers, Cookies, Technologies, Recommendations.
  - Color-coded status badges (Green = Pass, Red = Missing/Fail, Amber = Warning).
  - Auto-fitted column widths for instant boardroom presentation.

---

## 📁 Project Architecture

```
website_checker/
├── app.py                         # Flask web application & REST API routes
├── config.py                      # Global application configuration & score weights
├── requirements.txt               # Production Python dependencies
├── Procfile                       # Production web process definition (Render / Heroku)
├── render.yaml                    # Infrastructure-as-code deployment config
├── .gitignore                     # Git ignore rules
│
├── modules/                       # Security & analysis modules
│   ├── availability_checker.py   # Latency measurement & HTTP reachability
│   ├── dns_checker.py            # DNS records querying (A, MX, NS, TXT, SOA)
│   ├── excel_exporter.py         # Multi-tab styled Excel report builder (.xlsx)
│   ├── headers_checker.py        # Security headers auditing & info leak detection
│   ├── http_checker.py           # Redirect tracing, HTTPS verification & cookies
│   ├── ip_resolver.py            # IPv4 & IPv6 address resolution & PTR
│   ├── security_scorer.py        # 100-point scoring algorithm & grade calculator
│   ├── ssl_checker.py            # TLS socket handshake & certifi CA validation
│   ├── tech_detector.py          # Passive CMS & server technology fingerprinting
│   └── url_validator.py          # URL syntax cleaning & SSRF defense shield
│
├── templates/                     # Jinja2 HTML templates
│   ├── base.html                 # Base layout, navbar, footer & theme links
│   ├── index.html                # Main scanner dashboard & animated scan cards
│   ├── report.html               # Printable standalone audit report
│   └── history.html              # Scan history view
│
├── static/                        # Frontend UI assets
│   ├── css/style.css             # Glassmorphism dark mode styles & badge tokens
│   └── js/script.js              # Live progress steps, async fetch & UI rendering
│
├── tests/                         # Pytest test suite (95 unit & integration tests)
│   ├── test_app.py               # Flask endpoint tests & API response validations
│   ├── test_excel_exporter.py    # OpenPyXL workbook creation & tab structure tests
│   ├── test_headers_checker.py   # Security header analysis unit tests
│   ├── test_ssl_checker.py       # Certificate parsing & mock TLS tests
│   └── test_url_validator.py     # SSRF defense & URL parsing test suite
│
├── PROJECT_EXPLAINER_NOTEBOOK.md  # End-to-end architecture & concept explainer
└── CODE_EXPLAINER_NOTEBOOK.md     # Beginner-friendly code-by-code walkthrough
```

---

## ⚡ Quick Start (Local Setup)

### 1. Clone the Repository
```bash
git clone https://github.com/Suchetha-reddie/Website-checker.git
cd Website-checker
```

### 2. Create and Activate a Virtual Environment
```bash
# On macOS / Linux:
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Development Server
```bash
python app.py
```
Open **[http://127.0.0.1:5001](http://127.0.0.1:5001)** in your browser.

> **💡 Note on Port 5001**:  
> macOS uses port `5000` for its AirPlay Receiver service (`ControlCenter`). To avoid conflicts, this project defaults to port `5001`. You can configure this in `config.py` or via the `PORT` environment variable.

---

## 🧪 Running the Test Suite

The project includes **95 automated unit and integration tests** verifying SSRF protection, SSL validation, header evaluations, scoring calculations, and Excel exports.

```bash
# Ensure your virtual environment is active:
source venv/bin/activate

# Run tests:
pytest

# Run tests with detailed output:
pytest -v
```

---

## 🌐 API Reference

### 1. Scan a Website
* **Endpoint:** `POST /api/scan`
* **Content-Type:** `application/json`
* **Request Payload:**
  ```json
  {
    "url": "https://example.com"
  }
  ```
* **Success Response (200 OK):**
  Returns unified JSON containing `target`, `availability`, `ip_resolution`, `dns_records`, `ssl_certificate`, `http_analysis`, `security_headers`, `technologies`, `security_score`, and `recommendations`.

### 2. Export Audit to Excel
* **Endpoint:** `POST /api/export/excel`
* **Content-Type:** `application/json`
* **Request Payload:** The JSON scan result object returned by `/api/scan`.
* **Success Response (200 OK):**
  Binary file download (`Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`) named `{domain}_security_report.xlsx`.

### 3. Health Check
* **Endpoint:** `GET /health`
* **Response (200 OK):** `{"status": "ok"}`

---

## 🚀 Cloud Deployment

### Deploy to Render (Recommended & Free Tier Supported)

This repository includes a production `Procfile` and `render.yaml` ready for one-click deployment:

1. Push your repository to GitHub.
2. Sign in to [Render](https://render.com/) and click **New + $\to$ Web Service**.
3. Select your GitHub repository (`Suchetha-reddie/Website-checker`).
4. Configure the settings:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Click **Deploy Web Service**. Render will assign you a live HTTPS URL!

---

## 📜 Ethical Use & Legal Notice

This tool conducts **Passive Reconnaissance Only**. It performs standard, non-intrusive DNS lookups, public TLS handshakes, and analyzes public HTTP headers returned to any normal browser. It does **not** perform intrusive penetration testing, SQL injection attempts, brute-force attacks, or denial-of-service exploits.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — free for educational, personal, and commercial use.
