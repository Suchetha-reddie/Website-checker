# Website Information & Security Checker

A Python Flask-based passive cybersecurity analysis tool that inspects publicly available information for any website and evaluates its security posture.

## Features

- **URL Validation & SSRF Protection**: Comprehensive input validation, protocol normalization, and protection against SSRF targeting private IP ranges, loopback, and cloud metadata services.
- **Availability & Latency**: Real-time HTTP availability checks with response time measurement and classification (fast, moderate, slow).
- **IP Resolution**: Dual-stack IPv4 and IPv6 DNS resolution.
- **DNS Record Inspection**: Queries A, AAAA, MX, NS, CNAME, TXT, and SOA records via `dnspython`.
- **SSL/TLS Certificate Analysis**: Inspects certificate validity, issuer, subject, expiration countdown, TLS version, cipher suites, and Subject Alternative Names (SANs) with `certifi` Mozilla root bundle verification.
- **HTTP/HTTPS & Redirect Tracing**: Evaluates HTTPS availability, HTTP-to-HTTPS redirects, status codes, full redirect chains, and cookie security flags (`Secure`, `HttpOnly`, `SameSite`).
- **Security Headers Evaluation**: Checks presence and values for key security headers:
  - `Content-Security-Policy`
  - `Strict-Transport-Security` (HSTS)
  - `X-Content-Type-Options`
  - `X-Frame-Options`
  - `Referrer-Policy`
  - `Permissions-Policy`
  - Flags information disclosure headers (`Server`, `X-Powered-By`).
- **Technology Detection**: Passive signature detection identifying servers (Nginx, Apache, Cloudflare, IIS), CMS platforms (WordPress, Joomla, Drupal, Shopify), and frontend libraries/frameworks.
- **Security Scoring Engine**: Weighted 100-point security scoring algorithm across 6 categories with letter grades (A+ through F) and actionable, prioritized recommendations.
- **Modern UI**: Dark-mode interface built with Bootstrap 5, Bootstrap Icons, responsive summary cards, animated scanning progress, and tabbed inspection details.

## Project Structure

```
website_checker/
├── app.py                     # Flask application entry point
├── config.py                  # Application configuration & thresholds
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git ignore rules
├── modules/                   # Security scan modules
│   ├── availability_checker.py
│   ├── dns_checker.py
│   ├── headers_checker.py
│   ├── http_checker.py
│   ├── ip_resolver.py
│   ├── security_scorer.py
│   ├── ssl_checker.py
│   ├── tech_detector.py
│   └── url_validator.py
├── templates/                 # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── report.html
│   └── history.html
├── static/                    # Frontend assets
│   ├── css/style.css
│   └── js/script.js
└── tests/                     # Test suite (pytest)
    ├── test_app.py
    ├── test_headers_checker.py
    ├── test_ssl_checker.py
    └── test_url_validator.py
```

## Quick Start

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd website_checker
```

### 2. Set up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```
Open **[http://127.0.0.1:5001](http://127.0.0.1:5001)** in your browser.

*(Note: Port 5001 is used by default to prevent conflicts with macOS AirPlay Receiver on port 5000).*

### 4. Run Tests
```bash
pytest
```

## License
MIT
