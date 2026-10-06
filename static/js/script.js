/**
 * Website Information & Security Checker — Frontend Logic
 * ========================================================
 * Handles form submission, API communication, loading states,
 * and result rendering.
 */

document.addEventListener('DOMContentLoaded', () => {
    // =========================================================
    // DOM Element References
    // =========================================================
    const scanForm = document.getElementById('scanForm');
    const urlInput = document.getElementById('urlInput');
    const scanBtn = document.getElementById('scanBtn');
    const urlError = document.getElementById('urlError');
    const urlErrorText = document.getElementById('urlErrorText');

    const heroSection = document.querySelector('.hero-section');
    const featuresSection = document.querySelector('.features-section');
    const loadingSection = document.getElementById('loadingSection');
    const loadingTarget = document.getElementById('loadingTarget');
    const loadingSteps = document.getElementById('loadingSteps');
    const resultsSection = document.getElementById('resultsSection');
    const resultsTarget = document.getElementById('resultsTarget');
    const newScanBtn = document.getElementById('newScanBtn');

    // =========================================================
    // Loading Step Definitions
    // =========================================================
    const SCAN_STEPS = [
        'validate',
        'availability',
        'ip',
        'dns',
        'http',
        'ssl',
        'headers',
        'technology',
        'report',
    ];

    // =========================================================
    // Event Handlers
    // =========================================================

    if (scanForm) {
        scanForm.addEventListener('submit', handleScanSubmit);
    }

    if (newScanBtn) {
        newScanBtn.addEventListener('click', resetToHomepage);
    }

    // Clear error when user types
    if (urlInput) {
        urlInput.addEventListener('input', () => {
            hideError();
        });
    }

    // =========================================================
    // Scan Submission
    // =========================================================

    async function handleScanSubmit(event) {
        event.preventDefault();

        const url = urlInput.value.trim();
        if (!url) {
            showError('Please enter a website URL.');
            return;
        }

        // Disable form
        scanBtn.disabled = true;
        scanBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Scanning...';
        hideError();

        // Show loading UI
        showLoadingSection(url);

        try {
            // Simulate step-by-step progress with the actual API call
            await animateStep('validate');

            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url }),
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                // Mark validate as error if validation failed
                if (data.step === 'url_validation' || data.step === 'ssrf_check') {
                    markStepError('validate');
                }
                throw new Error(data.error || 'Scan failed.');
            }

            markStepCompleted('validate');

            // Simulate remaining steps completing (Phase 1 — actual modules not yet wired)
            const remainingSteps = SCAN_STEPS.slice(1);
            for (const step of remainingSteps) {
                await animateStep(step);
                markStepCompleted(step);
            }

            // Small pause before showing results
            await sleep(300);

            // Show results
            displayResults(data);
        } catch (error) {
            console.error('Scan error:', error);
            showError(error.message);
            resetLoadingSection();
            showHomepage();
        } finally {
            // Re-enable form
            scanBtn.disabled = false;
            scanBtn.innerHTML = '<i class="bi bi-search me-2"></i><span>CHECK WEBSITE</span>';
        }
    }

    // =========================================================
    // UI State Management
    // =========================================================

    function showLoadingSection(url) {
        if (heroSection) heroSection.style.display = 'none';
        if (featuresSection) featuresSection.style.display = 'none';
        if (resultsSection) resultsSection.style.display = 'none';

        loadingTarget.textContent = url;
        resetLoadingSteps();
        loadingSection.style.display = 'block';
        loadingSection.classList.add('fade-in');
    }

    function showHomepage() {
        loadingSection.style.display = 'none';
        resultsSection.style.display = 'none';

        if (heroSection) heroSection.style.display = '';
        if (featuresSection) featuresSection.style.display = '';
    }

    function resetToHomepage() {
        urlInput.value = '';
        showHomepage();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function showError(message) {
        urlErrorText.textContent = message;
        urlError.style.display = 'block';
    }

    function hideError() {
        urlError.style.display = 'none';
        urlErrorText.textContent = '';
    }

    // =========================================================
    // Loading Steps Animation
    // =========================================================

    function resetLoadingSteps() {
        const steps = loadingSteps.querySelectorAll('.loading-step');
        steps.forEach(step => {
            step.classList.remove('active', 'completed', 'error');
        });
    }

    function resetLoadingSection() {
        resetLoadingSteps();
    }

    async function animateStep(stepName) {
        const stepEl = loadingSteps.querySelector(`[data-step="${stepName}"]`);
        if (stepEl) {
            stepEl.classList.add('active');
            // Simulate processing time (will be replaced with real progress in later phases)
            await sleep(200 + Math.random() * 200);
        }
    }

    function markStepCompleted(stepName) {
        const stepEl = loadingSteps.querySelector(`[data-step="${stepName}"]`);
        if (stepEl) {
            stepEl.classList.remove('active');
            stepEl.classList.add('completed');
        }
    }

    function markStepError(stepName) {
        const stepEl = loadingSteps.querySelector(`[data-step="${stepName}"]`);
        if (stepEl) {
            stepEl.classList.remove('active');
            stepEl.classList.add('error');
        }
    }

    // =========================================================
    // Results Display
    // =========================================================

    function displayResults(data) {
        loadingSection.style.display = 'none';
        if (heroSection) heroSection.style.display = 'none';
        if (featuresSection) featuresSection.style.display = 'none';

        // Set target
        resultsTarget.textContent = data.target || data.hostname;

        // Populate summary cards with available data (Phase 1: mostly placeholders)
        populateSummaryCards(data);

        // Populate overview tab
        populateOverview(data);

        // Show results
        resultsSection.style.display = 'block';
        resultsSection.classList.add('fade-in');

        // Scroll to results
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function populateSummaryCards(data) {
        const valStatus = document.getElementById('valStatus');
        const valIP = document.getElementById('valIP');
        const valHTTPS = document.getElementById('valHTTPS');
        const valSSL = document.getElementById('valSSL');
        const valHeaders = document.getElementById('valHeaders');
        const valResponseTime = document.getElementById('valResponseTime');
        const valScore = document.getElementById('valScore');

        // Availability
        if (data.availability) {
            const avail = data.availability;
            valStatus.textContent = avail.status === 'online' ? '🟢 Online' : '🔴 Offline';
            valStatus.className = 'card-value ' + (avail.status === 'online' ? 'status-success' : 'status-danger');
            valResponseTime.textContent = avail.response_time_ms ? `${avail.response_time_ms} ms` : '—';
        } else {
            valStatus.textContent = '—';
            valResponseTime.textContent = '—';
        }

        // IP
        if (data.ip_addresses && data.ip_addresses.ipv4 && data.ip_addresses.ipv4.length > 0) {
            valIP.textContent = data.ip_addresses.ipv4[0];
        } else {
            valIP.textContent = '—';
        }

        // HTTPS
        if (data.http) {
            valHTTPS.textContent = data.http.https_available ? '✓ Enabled' : '✗ Disabled';
            valHTTPS.className = 'card-value ' + (data.http.https_available ? 'status-success' : 'status-warning');
        } else {
            // Phase 1: show scheme info
            if (data.scheme === 'https') {
                valHTTPS.textContent = '✓ HTTPS URL';
                valHTTPS.className = 'card-value status-info';
            } else {
                valHTTPS.textContent = '—';
            }
        }

        // SSL
        if (data.ssl) {
            valSSL.textContent = data.ssl.valid ? '✓ Valid' : '✗ Invalid';
            valSSL.className = 'card-value ' + (data.ssl.valid ? 'status-success' : 'status-danger');
        } else {
            valSSL.textContent = '—';
        }

        // Security Headers
        if (data.security_headers) {
            const secHeaders = data.security_headers;
            const present = typeof secHeaders._total_present === 'number'
                ? secHeaders._total_present
                : Object.entries(secHeaders).filter(([k, v]) => !k.startsWith('_') && v && v.present).length;
            const total = typeof secHeaders._total_checked === 'number'
                ? secHeaders._total_checked
                : Object.entries(secHeaders).filter(([k, _]) => !k.startsWith('_')).length;

            valHeaders.textContent = `${present} / ${total}`;
            valHeaders.className = 'card-value ' + (present === total && total > 0 ? 'status-success' : present > 0 ? 'status-warning' : 'status-danger');
        } else {
            valHeaders.textContent = '—';
        }

        // Score
        if (data.security_score) {
            valScore.textContent = data.security_score.total;
            const score = data.security_score.total;
            if (score >= 80) valScore.className = 'card-value card-value-lg status-success';
            else if (score >= 50) valScore.className = 'card-value card-value-lg status-warning';
            else valScore.className = 'card-value card-value-lg status-danger';
        } else {
            valScore.textContent = '—';
        }
    }

    function populateOverview(data) {
        const overviewContent = document.getElementById('overviewContent');
        if (!overviewContent) return;

        const rows = [
            { label: 'Target URL', value: data.target || '—' },
            { label: 'Hostname', value: data.hostname || '—' },
            { label: 'Scheme', value: (data.scheme || '—').toUpperCase() },
            { label: 'Port', value: data.port || 'Default' },
            { label: 'Path', value: data.path || '/' },
            { label: 'Scan ID', value: data.scan_id || '—' },
            { label: 'Timestamp', value: data.timestamp ? new Date(data.timestamp).toLocaleString() : '—' },
        ];

        if (data.availability) {
            rows.push({ label: 'Status', value: data.availability.status === 'online' ? '🟢 Online' : '🔴 Offline' });
            if (data.availability.response_time_ms) {
                rows.push({ label: 'Response Time', value: `${data.availability.response_time_ms} ms` });
            }
            if (data.availability.status_code) {
                rows.push({ label: 'HTTP Status Code', value: data.availability.status_code });
            }
        }

        if (data.security_score) {
            rows.push({ label: 'Security Score', value: `${data.security_score.total}/100 (Grade: ${data.security_score.grade})` });
        }

        overviewContent.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Property</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map(r => `
                        <tr>
                            <td class="label-cell">${escapeHtml(r.label)}</td>
                            <td class="value-cell">${escapeHtml(String(r.value))}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        // Populate all detail tabs
        populateNetworkTab(data);
        populateDnsTab(data);
        populateHttpTab(data);
        populateSslTab(data);
        populateHeadersTab(data);
        populateTechTab(data);
        populateAnalysisTab(data);
    }

    function populateNetworkTab(data) {
        const el = document.getElementById('networkContent');
        if (!el) return;

        let html = '';

        // IP Addresses
        if (data.ip_addresses) {
            html += '<h4 class="subsection-title"><i class="bi bi-hdd-network me-2"></i>IP Addresses</h4>';
            if (data.ip_addresses.ipv4 && data.ip_addresses.ipv4.length > 0) {
                html += '<div class="info-group"><span class="info-label">IPv4:</span>';
                data.ip_addresses.ipv4.forEach(ip => {
                    html += `<span class="info-badge">${escapeHtml(ip)}</span> `;
                });
                html += '</div>';
            }
            if (data.ip_addresses.ipv6 && data.ip_addresses.ipv6.length > 0) {
                html += '<div class="info-group"><span class="info-label">IPv6:</span>';
                data.ip_addresses.ipv6.forEach(ip => {
                    html += `<span class="info-badge info-badge-sm">${escapeHtml(ip)}</span> `;
                });
                html += '</div>';
            }
            if (data.ip_addresses.error) {
                html += `<p class="text-warning"><i class="bi bi-exclamation-triangle me-1"></i>${escapeHtml(data.ip_addresses.error)}</p>`;
            }
        }

        // Availability
        if (data.availability) {
            html += '<h4 class="subsection-title mt-3"><i class="bi bi-activity me-2"></i>Availability</h4>';
            html += `<table class="data-table">
                <tbody>
                    <tr><td class="label-cell">Status</td><td class="value-cell">${data.availability.status === 'online' ? '<span class="status-badge status-badge-success">Online</span>' : '<span class="status-badge status-badge-danger">Offline</span>'}</td></tr>
                    ${data.availability.status_code ? `<tr><td class="label-cell">HTTP Status</td><td class="value-cell">${data.availability.status_code}</td></tr>` : ''}
                    ${data.availability.response_time_ms ? `<tr><td class="label-cell">Response Time</td><td class="value-cell">${data.availability.response_time_ms} ms <span class="status-badge status-badge-${data.availability.response_time_class === 'fast' ? 'success' : data.availability.response_time_class === 'moderate' ? 'warning' : 'danger'}">${data.availability.response_time_class || ''}</span></td></tr>` : ''}
                    ${data.availability.error ? `<tr><td class="label-cell">Error</td><td class="value-cell text-warning">${escapeHtml(data.availability.error)}</td></tr>` : ''}
                </tbody>
            </table>`;
        }

        // Server Info
        if (data.server_info && (data.server_info.server || data.server_info.powered_by)) {
            html += '<h4 class="subsection-title mt-3"><i class="bi bi-server me-2"></i>Server</h4>';
            html += '<table class="data-table"><tbody>';
            if (data.server_info.server) html += `<tr><td class="label-cell">Server</td><td class="value-cell">${escapeHtml(data.server_info.server)}</td></tr>`;
            if (data.server_info.powered_by) html += `<tr><td class="label-cell">Powered By</td><td class="value-cell">${escapeHtml(data.server_info.powered_by)}</td></tr>`;
            html += '</tbody></table>';
        }

        el.innerHTML = html || '<p class="text-muted">No network information available.</p>';
    }

    function populateDnsTab(data) {
        const el = document.getElementById('dnsContent');
        if (!el || !data.dns) {
            if (el) el.innerHTML = '<p class="text-muted">DNS data not available.</p>';
            return;
        }

        let html = '';
        const dns = data.dns;

        if (dns.error) {
            html += `<p class="text-warning"><i class="bi bi-exclamation-triangle me-1"></i>${escapeHtml(dns.error)}</p>`;
        }

        const recordTypes = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT'];
        recordTypes.forEach(type => {
            const records = dns[type];
            if (records && records.length > 0) {
                html += `<h4 class="subsection-title"><i class="bi bi-record-circle me-2"></i>${type} Records</h4>`;
                html += '<table class="data-table"><thead><tr><th>#</th><th>Value</th></tr></thead><tbody>';
                records.forEach((rec, i) => {
                    let value;
                    if (type === 'MX') {
                        value = `${rec.exchange} (priority: ${rec.priority})`;
                    } else {
                        value = typeof rec === 'string' ? rec : JSON.stringify(rec);
                    }
                    html += `<tr><td class="label-cell">${i + 1}</td><td class="value-cell">${escapeHtml(value)}</td></tr>`;
                });
                html += '</tbody></table>';
            }
        });

        if (dns.SOA) {
            html += '<h4 class="subsection-title"><i class="bi bi-record-circle me-2"></i>SOA Record</h4>';
            html += '<table class="data-table"><tbody>';
            html += `<tr><td class="label-cell">Primary NS</td><td class="value-cell">${escapeHtml(dns.SOA.mname)}</td></tr>`;
            html += `<tr><td class="label-cell">Admin Email</td><td class="value-cell">${escapeHtml(dns.SOA.rname)}</td></tr>`;
            html += `<tr><td class="label-cell">Serial</td><td class="value-cell">${dns.SOA.serial}</td></tr>`;
            html += `<tr><td class="label-cell">Refresh</td><td class="value-cell">${dns.SOA.refresh}s</td></tr>`;
            html += `<tr><td class="label-cell">Retry</td><td class="value-cell">${dns.SOA.retry}s</td></tr>`;
            html += `<tr><td class="label-cell">Expire</td><td class="value-cell">${dns.SOA.expire}s</td></tr>`;
            html += '</tbody></table>';
        }

        el.innerHTML = html || '<p class="text-muted">No DNS records found.</p>';
    }

    function populateHttpTab(data) {
        const el = document.getElementById('httpContent');
        if (!el || !data.http) {
            if (el) el.innerHTML = '<p class="text-muted">HTTP data not available.</p>';
            return;
        }

        const http = data.http;
        let html = '<h4 class="subsection-title"><i class="bi bi-arrow-left-right me-2"></i>HTTPS Status</h4>';
        html += '<table class="data-table"><tbody>';
        html += `<tr><td class="label-cell">HTTPS Available</td><td class="value-cell">${http.https_available ? '<span class="status-badge status-badge-success">Yes</span>' : '<span class="status-badge status-badge-danger">No</span>'}</td></tr>`;
        html += `<tr><td class="label-cell">HTTP→HTTPS Redirect</td><td class="value-cell">${http.http_to_https_redirect ? '<span class="status-badge status-badge-success">Yes</span>' : '<span class="status-badge status-badge-warning">No</span>'}</td></tr>`;
        html += `<tr><td class="label-cell">Status Code</td><td class="value-cell">${http.status_code || '—'}</td></tr>`;
        html += `<tr><td class="label-cell">Final URL</td><td class="value-cell">${escapeHtml(http.final_url || '—')}</td></tr>`;
        if (http.content_type) html += `<tr><td class="label-cell">Content Type</td><td class="value-cell">${escapeHtml(http.content_type)}</td></tr>`;
        html += '</tbody></table>';

        // Redirect chain
        if (http.redirect_chain && http.redirect_chain.length > 0) {
            html += '<h4 class="subsection-title mt-3"><i class="bi bi-arrow-repeat me-2"></i>Redirect Chain</h4>';
            html += '<table class="data-table"><thead><tr><th>#</th><th>URL</th><th>Status</th><th>Location</th></tr></thead><tbody>';
            http.redirect_chain.forEach((r, i) => {
                html += `<tr>
                    <td class="label-cell">${i + 1}</td>
                    <td class="value-cell">${escapeHtml(r.url || '—')}</td>
                    <td class="value-cell">${r.status_code}</td>
                    <td class="value-cell">${escapeHtml(r.location || '—')}</td>
                </tr>`;
            });
            html += '</tbody></table>';
        }

        // Cookies
        if (data.cookies && data.cookies.length > 0) {
            html += '<h4 class="subsection-title mt-3"><i class="bi bi-cookie me-2"></i>Cookies</h4>';
            html += '<table class="data-table"><thead><tr><th>Name</th><th>Domain</th><th>Secure</th><th>HttpOnly</th><th>SameSite</th></tr></thead><tbody>';
            data.cookies.forEach(c => {
                html += `<tr>
                    <td class="value-cell">${escapeHtml(c.name)}</td>
                    <td class="value-cell">${escapeHtml(c.domain || '—')}</td>
                    <td class="value-cell">${c.secure ? '<span class="status-badge status-badge-success">Yes</span>' : '<span class="status-badge status-badge-danger">No</span>'}</td>
                    <td class="value-cell">${c.httponly ? '<span class="status-badge status-badge-success">Yes</span>' : '<span class="status-badge status-badge-danger">No</span>'}</td>
                    <td class="value-cell">${escapeHtml(c.samesite || 'Not set')}</td>
                </tr>`;
            });
            html += '</tbody></table>';
        }

        el.innerHTML = html;
    }

    function populateSslTab(data) {
        const el = document.getElementById('sslContent');
        if (!el || !data.ssl) {
            if (el) el.innerHTML = '<p class="text-muted">SSL/TLS data not available (site may not use HTTPS).</p>';
            return;
        }

        const ssl = data.ssl;
        let html = '';

        if (ssl.error) {
            html += `<div class="alert-banner alert-banner-warning"><i class="bi bi-exclamation-triangle me-2"></i>${escapeHtml(ssl.error)}</div>`;
        }

        html += '<table class="data-table"><tbody>';
        html += `<tr><td class="label-cell">Valid</td><td class="value-cell">${ssl.valid ? '<span class="status-badge status-badge-success">Yes</span>' : '<span class="status-badge status-badge-danger">No</span>'}</td></tr>`;
        html += `<tr><td class="label-cell">Hostname Match</td><td class="value-cell">${ssl.hostname_match ? '<span class="status-badge status-badge-success">Yes</span>' : ssl.hostname_match === false ? '<span class="status-badge status-badge-danger">No</span>' : '—'}</td></tr>`;

        if (ssl.protocol_version) html += `<tr><td class="label-cell">TLS Version</td><td class="value-cell">${escapeHtml(ssl.protocol_version)}</td></tr>`;
        if (ssl.cipher) html += `<tr><td class="label-cell">Cipher</td><td class="value-cell">${escapeHtml(ssl.cipher.name)} (${ssl.cipher.bits} bits)</td></tr>`;
        if (ssl.not_before) html += `<tr><td class="label-cell">Valid From</td><td class="value-cell">${escapeHtml(ssl.not_before)}</td></tr>`;
        if (ssl.not_after) html += `<tr><td class="label-cell">Valid Until</td><td class="value-cell">${escapeHtml(ssl.not_after)}</td></tr>`;
        if (ssl.days_until_expiry !== null && ssl.days_until_expiry !== undefined) {
            const daysClass = ssl.days_until_expiry > 30 ? 'success' : ssl.days_until_expiry > 7 ? 'warning' : 'danger';
            html += `<tr><td class="label-cell">Days Until Expiry</td><td class="value-cell"><span class="status-badge status-badge-${daysClass}">${ssl.days_until_expiry} days</span></td></tr>`;
        }

        if (ssl.subject) {
            const cn = ssl.subject.commonName || ssl.subject.organizationName || '—';
            html += `<tr><td class="label-cell">Subject (CN)</td><td class="value-cell">${escapeHtml(cn)}</td></tr>`;
        }
        if (ssl.issuer) {
            const issuerName = ssl.issuer.organizationName || ssl.issuer.commonName || '—';
            html += `<tr><td class="label-cell">Issuer</td><td class="value-cell">${escapeHtml(issuerName)}</td></tr>`;
        }
        html += '</tbody></table>';

        // SANs
        if (ssl.san && ssl.san.length > 0) {
            html += '<h4 class="subsection-title mt-3"><i class="bi bi-card-list me-2"></i>Subject Alternative Names</h4>';
            html += '<div class="san-list">';
            ssl.san.forEach(s => {
                html += `<span class="info-badge">${escapeHtml(s.value)}</span> `;
            });
            html += '</div>';
        }

        el.innerHTML = html;
    }

    function populateHeadersTab(data) {
        const el = document.getElementById('headersContent');
        if (!el || !data.security_headers) {
            if (el) el.innerHTML = '<p class="text-muted">Security headers data not available.</p>';
            return;
        }

        const headers = data.security_headers;
        const headerNames = [
            'Content-Security-Policy', 'Strict-Transport-Security',
            'X-Content-Type-Options', 'X-Frame-Options',
            'Referrer-Policy', 'Permissions-Policy',
        ];

        let bannerHtml = '';
        if (headers._error) {
            bannerHtml += `<div class="alert-banner alert-banner-warning mb-3"><i class="bi bi-exclamation-triangle me-2"></i>${escapeHtml(headers._error)}</div>`;
        }
        if (headers._warning) {
            bannerHtml += `<div class="alert-banner alert-banner-warning mb-3"><i class="bi bi-info-circle me-2"></i>${escapeHtml(headers._warning)}</div>`;
        }

        let html = bannerHtml + '<table class="data-table"><thead><tr><th>Header</th><th>Status</th><th>Value</th></tr></thead><tbody>';
        headerNames.forEach(name => {
            const h = headers[name];
            if (!h) return;
            const statusBadge = h.present
                ? '<span class="status-badge status-badge-success">Present</span>'
                : '<span class="status-badge status-badge-danger">Missing</span>';
            html += `<tr>
                <td class="label-cell">${escapeHtml(name)}</td>
                <td class="value-cell">${statusBadge}</td>
                <td class="value-cell" style="max-width: 300px; word-break: break-all;">${h.value ? escapeHtml(h.value.substring(0, 200)) : '<span class="text-muted">—</span>'}</td>
            </tr>`;
        });
        html += '</tbody></table>';

        // Information leaking headers
        if (headers._info_leak && headers._info_leak.length > 0) {
            html += '<h4 class="subsection-title mt-3"><i class="bi bi-exclamation-triangle me-2"></i>Information Disclosure</h4>';
            html += '<table class="data-table"><thead><tr><th>Header</th><th>Value</th></tr></thead><tbody>';
            headers._info_leak.forEach(leak => {
                html += `<tr><td class="label-cell">${escapeHtml(leak.header)}</td><td class="value-cell text-warning">${escapeHtml(leak.value)}</td></tr>`;
            });
            html += '</tbody></table>';
        }

        el.innerHTML = html;
    }

    function populateTechTab(data) {
        const el = document.getElementById('techContent');
        if (!el || !data.technology) {
            if (el) el.innerHTML = '<p class="text-muted">Technology data not available.</p>';
            return;
        }

        const tech = data.technology;
        let html = '';

        if (tech.error) {
            html += `<p class="text-warning"><i class="bi bi-exclamation-triangle me-1"></i>${escapeHtml(tech.error)}</p>`;
        }

        if (tech.technologies && tech.technologies.length > 0) {
            // Group by category
            const categories = {};
            tech.technologies.forEach(t => {
                if (!categories[t.category]) categories[t.category] = [];
                categories[t.category].push(t);
            });

            Object.keys(categories).forEach(cat => {
                html += `<h4 class="subsection-title"><i class="bi bi-cpu me-2"></i>${escapeHtml(cat)}</h4>`;
                html += '<div class="tech-badges">';
                categories[cat].forEach(t => {
                    html += `<span class="info-badge info-badge-tech">${escapeHtml(t.name)}</span> `;
                });
                html += '</div>';
            });
        } else {
            html += '<p class="text-muted">No technologies detected.</p>';
        }

        if (tech.server) {
            html += `<div class="info-group mt-3"><span class="info-label">Server:</span> <span class="info-badge">${escapeHtml(tech.server)}</span></div>`;
        }

        el.innerHTML = html;
    }

    function populateAnalysisTab(data) {
        const el = document.getElementById('analysisContent');
        if (!el) return;

        let html = '';

        // Security Score Breakdown
        if (data.security_score && data.security_score.breakdown) {
            html += '<h4 class="subsection-title"><i class="bi bi-trophy me-2"></i>Score Breakdown</h4>';
            html += '<table class="data-table"><thead><tr><th>Category</th><th>Score</th><th>Max</th><th>Progress</th></tr></thead><tbody>';
            const labels = {
                https: 'HTTPS', ssl: 'SSL/TLS', headers: 'Security Headers',
                cookies: 'Cookies', redirects: 'Redirects', other: 'Other',
            };
            Object.entries(data.security_score.breakdown).forEach(([key, val]) => {
                const pct = Math.round((val.score / val.max) * 100);
                const barClass = pct >= 80 ? 'progress-success' : pct >= 50 ? 'progress-warning' : 'progress-danger';
                html += `<tr>
                    <td class="label-cell">${labels[key] || key}</td>
                    <td class="value-cell">${val.score}</td>
                    <td class="value-cell">${val.max}</td>
                    <td class="value-cell"><div class="progress-bar-mini"><div class="progress-bar-fill ${barClass}" style="width: ${pct}%"></div></div></td>
                </tr>`;
            });
            html += '</tbody></table>';
            html += `<div class="score-total mt-2">Total: <strong>${data.security_score.total}/100</strong> — Grade: <strong class="${data.security_score.grade.startsWith('A') ? 'text-success' : data.security_score.grade === 'B' ? 'text-info' : 'text-warning'}">${data.security_score.grade}</strong></div>`;
        }

        // Recommendations
        if (data.recommendations && data.recommendations.length > 0) {
            html += '<h4 class="subsection-title mt-3"><i class="bi bi-lightbulb me-2"></i>Recommendations</h4>';
            data.recommendations.forEach(rec => {
                const icon = rec.severity === 'high' ? 'exclamation-triangle-fill' : rec.severity === 'medium' ? 'exclamation-circle' : 'info-circle';
                const cls = rec.severity === 'high' ? 'danger' : rec.severity === 'medium' ? 'warning' : 'info';
                html += `<div class="recommendation-item recommendation-${cls}">
                    <i class="bi bi-${icon} me-2"></i>
                    <span class="rec-category">[${escapeHtml(rec.category)}]</span>
                    ${escapeHtml(rec.message)}
                </div>`;
            });
        } else {
            html += '<p class="text-muted mt-3">No specific recommendations — looking good!</p>';
        }

        el.innerHTML = html || '<p class="text-muted">Analysis data not available.</p>';
    }

    // =========================================================
    // Utilities
    // =========================================================

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
