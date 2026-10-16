/**
 * RefundShield AI - Enterprise Fraud Investigation Console
 * Production JavaScript with defensive DOM manipulation, instant autocomplete search,
 * real-time multi-layer fraud scoring, live scenario simulator, and identity graph network.
 */

const API_BASE = '/api';

// Global State
let currentCustomerDossier = null;
let lastRequestedCustomerId = 'C0022';
let searchTimeout = null;
let cachedOrders = [];
let activeOrderFilter = 'all';
let cachedTypologies = [];
let cachedRings = [];
let cachedCouriers = [];
let cachedMerchants = [];

// ============================================================================
// Defensive DOM Helpers
// ============================================================================
function safeSetText(id, text) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = (text !== null && text !== undefined) ? String(text) : '--';
    }
}

function safeSetHtml(id, html) {
    const el = document.getElementById(id);
    if (el) {
        el.innerHTML = (html !== null && html !== undefined) ? String(html) : '';
    }
}

function safeSetStyle(id, property, value) {
    const el = document.getElementById(id);
    if (el) {
        el.style[property] = value;
    }
}

function safeSetClass(id, className) {
    const el = document.getElementById(id);
    if (el) {
        el.className = className;
    }
}

// Utility: Toast Notification
function showToast(message) {
    const existing = document.querySelector('.toast-notice');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast-notice';
    toast.innerHTML = `<span>🛡️</span> <span>${escapeHtml(message)}</span>`;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(16px)';
        setTimeout(() => toast.remove(), 300);
    }, 2800);
}

// Utility: Copy Customer ID to Clipboard
function copyCustomerId() {
    if (!currentCustomerDossier || !currentCustomerDossier.customer) {
        showToast('No customer dossier currently loaded.');
        return;
    }
    const cid = currentCustomerDossier.customer.customer_id;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(cid).then(() => {
            showToast(`Copied Customer ID: ${cid}`);
        }).catch(() => {
            showToast(`Customer ID: ${cid}`);
        });
    } else {
        showToast(`Customer ID: ${cid}`);
    }
}

// Utility: Export / Print Dossier Report
function exportDossierReport() {
    if (!currentCustomerDossier) {
        showToast('Please load a customer dossier before exporting.');
        return;
    }
    window.print();
}

// Utility: Retry Customer Lookup
function retryCustomerLookup() {
    loadCustomerDossier(lastRequestedCustomerId || 'C0022');
}

// Lifecycle Init
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initSearch();
    initSandbox();
    loadExecutiveKPIs();
    loadFraudRings();
    loadSupplyChain();

    // Default load benchmark customer on startup
    loadCustomerDossier('C0022');
});

// ============================================================================
// 1. Tab Switching System
// ============================================================================
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-nav-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll('.tab-nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
    });
    document.querySelectorAll('.tab-pane').forEach(panel => {
        panel.classList.toggle('active', panel.id === tabId);
    });
}

// ============================================================================
// 2. Global Autocomplete Search
// ============================================================================
function initSearch() {
    const input = document.getElementById('globalSearchInput');
    const dropdown = document.getElementById('autocompleteDropdown');
    const clearBtn = document.getElementById('searchClearBtn');

    if (!input || !dropdown) return;

    input.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        if (clearBtn) clearBtn.style.display = val ? 'block' : 'none';

        if (searchTimeout) clearTimeout(searchTimeout);

        if (val.length < 1) {
            dropdown.style.display = 'none';
            dropdown.innerHTML = '';
            return;
        }

        searchTimeout = setTimeout(() => {
            fetchSearchResults(val);
        }, 180);
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const val = input.value.trim().toUpperCase();
            if (val) {
                dropdown.style.display = 'none';
                if (val.startsWith('O')) {
                    inspectOrder(val);
                } else {
                    loadCustomerDossier(val);
                }
            }
        } else if (e.key === 'Escape') {
            dropdown.style.display = 'none';
        }
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            input.value = '';
            clearBtn.style.display = 'none';
            dropdown.style.display = 'none';
            input.focus();
        });
    }

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-field-wrapper')) {
            dropdown.style.display = 'none';
        }
    });
}

async function fetchSearchResults(query) {
    const dropdown = document.getElementById('autocompleteDropdown');
    if (!dropdown) return;

    try {
        const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
        if (!res.ok) return;
        const items = await res.json();

        if (items.length === 0) {
            dropdown.innerHTML = `
                <div style="padding: 12px 16px; color: #64748B; font-size: 0.85rem;">
                    No indexed entities matching "<b>${escapeHtml(query)}</b>"
                </div>`;
            dropdown.style.display = 'block';
            return;
        }

        dropdown.innerHTML = items.map(item => `
            <div class="autocomplete-item" onclick="onSelectItem('${item.type}', '${item.id}')">
                <div class="item-left">
                    <span class="item-title">${escapeHtml(item.label)}</span>
                    <span class="item-desc">${escapeHtml(item.subtitle)}</span>
                </div>
                <div>
                    <span class="item-tag" style="background: ${item.risk_hint}20; color: ${item.risk_hint}; border: 1px solid ${item.risk_hint}">
                        ${item.badge || item.type.toUpperCase()}
                    </span>
                </div>
            </div>
        `).join('');

        dropdown.style.display = 'block';
    } catch (err) {
        console.error('Search error:', err);
    }
}

function onSelectItem(type, id) {
    const dropdown = document.getElementById('autocompleteDropdown');
    const input = document.getElementById('globalSearchInput');
    if (dropdown) dropdown.style.display = 'none';
    if (input) input.value = id;

    if (type === 'customer') {
        loadCustomerDossier(id);
    } else if (type === 'order') {
        inspectOrder(id);
    } else {
        loadCustomerDossier(id);
    }
}

function quickPickCustomer(cid) {
    const input = document.getElementById('globalSearchInput');
    if (input) input.value = cid;
    loadCustomerDossier(cid);
}

// ============================================================================
// 3. Dynamic Customer 360 Dossier Fetch & Render
// ============================================================================
async function loadCustomerDossier(customerId) {
    const cid = String(customerId).trim().toUpperCase();
    lastRequestedCustomerId = cid;
    showDossierLoading(true);
    switchTab('tab-dossier');

    // Cold-start timeout handler (Render free-tier spinner guard)
    let timedOut = false;
    const timeoutTimer = setTimeout(() => {
        timedOut = true;
        const loadBox = document.getElementById('dossierLoading');
        if (loadBox && loadBox.style.display !== 'none') {
            loadBox.innerHTML = `
                <div class="spinner-ring"></div>
                <p style="margin-top: 14px; color: var(--accent-amber); font-weight: 700; font-size: 1rem;">
                    Database instance is initializing (Cloud Cold-Start)...
                </p>
                <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">
                    Render free instances take 30-50 seconds to wake up from inactivity.
                </p>
                <button type="button" class="retry-btn" onclick="retryCustomerLookup()" style="margin: 12px auto 0 auto;">
                    🔄 Retry Connection
                </button>
            `;
        }
    }, 12000);

    try {
        const res = await fetch(`${API_BASE}/customers/${cid}`);
        clearTimeout(timeoutTimer);

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            const detail = errData.detail || errData;
            const msg = detail.message || errData.message || `Customer ID "${cid}" was not found in the relational database.`;
            showDossierError(msg, detail.suggested_ids || ['C0022', 'C0061', 'C0020', 'C0001']);
            return;
        }

        const data = await res.json();
        currentCustomerDossier = data;
        renderCustomerDossier(data);
        syncSandboxWithCustomer(data);
    } catch (err) {
        clearTimeout(timeoutTimer);
        console.error('Failed to load dossier:', err);
        showDossierError(`Network or API communication error (${err.message}). The cloud server might be spinning up.`);
    } finally {
        showDossierLoading(false);
    }
}

function renderCustomerDossier(dossier) {
    if (!dossier || !dossier.customer) return;

    const cust = dossier.customer;
    const metrics = dossier.metrics || {};
    const ident = dossier.identity || {};
    const risk = dossier.risk_evaluation || {};
    const orders = dossier.orders || [];

    safeSetStyle('dossierContent', 'display', 'block');
    safeSetStyle('dossierError', 'display', 'none');

    // Customer Meta Header
    safeSetText('dossierCustId', cust.customer_id);
    safeSetText('dossierCity', cust.city);
    safeSetText('dossierRegDate', cust.registration_date);
    safeSetText('dossierStatus', cust.account_status || 'Active');
    safeSetText('customerAvatar', cust.customer_id.substring(0, 1) || 'C');

    // Animated Risk Score Gauge
    animateGauge(risk.hybrid_risk_score || 0, risk.badge_color || '#10B981');

    // Risk Badges & Verdict
    const riskLevel = risk.risk_level || 'Low Risk';
    const badgeText = `${riskLevel.toUpperCase()} (${risk.hybrid_risk_score || 0}/100)`;
    safeSetText('dossierRiskBadge', badgeText);

    let pillClass = 'risk-pill-low';
    if (riskLevel === 'High Risk') pillClass = 'risk-pill-high';
    else if (riskLevel === 'Medium Risk') pillClass = 'risk-pill-medium';
    safeSetClass('dossierRiskBadge', pillClass);

    safeSetText('dossierAction', risk.recommended_action || 'Approve');
    safeSetStyle('dossierAction', 'color', risk.badge_color || '#10B981');

    const typoConf = risk.typology_confidence ? (risk.typology_confidence * 100).toFixed(0) : '95';
    safeSetText('dossierTypology', `${risk.probable_fraud_type || 'Legitimate'} (${typoConf}% Confidence)`);

    // Decomposition Metrics
    safeSetText('valRuleScore', `${risk.rule_score || 0}/100`);
    safeSetStyle('barRuleScore', 'width', `${Math.min(100, risk.rule_score || 0)}%`);
    safeSetStyle('barRuleScore', 'backgroundColor', (risk.rule_score >= 50) ? '#EF4444' : ((risk.rule_score >= 25) ? '#F59E0B' : '#10B981'));

    const mlPct = (risk.ml_probability ? (risk.ml_probability * 100).toFixed(1) : '0.0');
    safeSetText('valMlProb', `${mlPct}%`);
    safeSetStyle('barMlProb', 'width', `${Math.min(100, (risk.ml_probability || 0) * 100)}%`);
    safeSetStyle('barMlProb', 'backgroundColor', (risk.ml_probability >= 0.6) ? '#EF4444' : ((risk.ml_probability >= 0.3) ? '#F59E0B' : '#10B981'));

    safeSetText('valNetworkPts', `+${risk.network_risk_points || 0} pts`);
    safeSetStyle('barNetworkPts', 'width', `${Math.min(100, (risk.network_risk_points || 0) * 3.33)}%`);

    // Explainability Reasons List
    const reasonsContainer = document.getElementById('dossierReasonsList');
    if (reasonsContainer && risk.reasons) {
        reasonsContainer.innerHTML = risk.reasons.map((r, i) => `
            <li class="reason-card ${r.startsWith('+') ? 'violation' : ''}">
                <b>${i + 1}.</b> ${escapeHtml(r)}
            </li>
        `).join('');
    }

    // Customer Behavioral KPIs
    safeSetText('metricOrders', metrics.total_orders || 0);
    safeSetText('metricSpend', `Rs. ${(metrics.total_spend || 0).toLocaleString()} Volume`);
    safeSetText('metricReturns', `${metrics.total_returns || 0} (${metrics.return_rate || 0}%)`);
    safeSetText('metricRefunds', `Rs. ${(metrics.total_refunds || 0).toLocaleString()} (${metrics.refund_leakage_pct || 0}%)`);
    safeSetText('metricChargebacks', metrics.chargebacks_count || 0);
    safeSetText('metricSuspiciousReturns', metrics.suspicious_returns_count || 0);
    safeSetText('metricAccountAge', `${cust.account_age_days || 0} days`);

    if (cust.previous_fraud_flag === 1) {
        safeSetHtml('metricPriorFraud', '<span style="color: #F43F5E; font-weight: 800;">YES (CONFIRMED)</span>');
    } else {
        safeSetHtml('metricPriorFraud', '<span style="color: #10B981; font-weight: 700;">CLEAN</span>');
    }

    // Identity & Syndicate Ring Card
    safeSetText('identRingSize', `${ident.ring_size || 1} account(s)`);
    if (ident.is_in_sybil_ring) {
        safeSetHtml('identSybilStatus', `<span style="color: #F43F5E; font-weight: 800;">⚠️ SYNDICATE ${ident.ring_id || ''} (${ident.ring_size} ACCOUNTS)</span>`);
    } else {
        safeSetHtml('identSybilStatus', `<span style="color: #10B981; font-weight: 700;">Independent User</span>`);
    }

    safeSetText('identFlaggedNeighbors', ident.flagged_neighbors_count || 0);
    safeSetText('identNetworkDesc', ident.network_summary || 'Clean profile');

    // Devices List
    const devContainer = document.getElementById('identDevices');
    if (devContainer) {
        if (ident.devices && ident.devices.length > 0) {
            devContainer.innerHTML = ident.devices.map(d => `
                <span class="quick-chip ${d.account_count > 1 ? 'chip-danger' : ''}">
                    📱 ${escapeHtml(d.device_id)} (${d.account_count} account${d.account_count > 1 ? 's' : ''})
                </span>
            `).join('');
        } else {
            devContainer.innerHTML = '<span style="color: #64748B; font-size: 0.8rem;">No linked hardware devices</span>';
        }
    }

    // Orders Ledger Table
    renderOrdersTable(orders);
}

function animateGauge(score, color) {
    const circle = document.getElementById('gaugeCircleProgress');
    const scoreText = document.getElementById('gaugeScoreText');
    if (!circle || !scoreText) return;

    const r = 68;
    const circumference = 2 * Math.PI * r;

    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    const offset = circumference - (score / 100) * circumference;
    circle.style.strokeDashoffset = offset;
    circle.style.stroke = color;

    let start = 0;
    const duration = 500;
    const startTime = performance.now();

    function updateScore(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1.0);
        const currentScore = Math.floor(progress * score);
        scoreText.textContent = currentScore;
        scoreText.style.color = color;
        if (progress < 1.0) {
            requestAnimationFrame(updateScore);
        } else {
            scoreText.textContent = score;
        }
    }
    requestAnimationFrame(updateScore);
}

// ============================================================================
// Order Ledger Table with Search & Filter
// ============================================================================
function renderOrdersTable(orders) {
    cachedOrders = orders || [];
    activeOrderFilter = 'all';

    // Counts
    const totalCount = cachedOrders.length;
    const returnCount = cachedOrders.filter(o => o.return_reason !== null).length;
    const deficitCount = cachedOrders.filter(o => o.weight_loss_pct && o.weight_loss_pct > 0).length;

    safeSetText('countAllOrders', totalCount);
    safeSetText('countReturnOrders', returnCount);
    safeSetText('countDeficitOrders', deficitCount);

    applyOrdersTableFilter();
}

function setOrderFilter(filterType) {
    activeOrderFilter = filterType;
    document.querySelectorAll('.table-filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-filter') === filterType);
    });
    applyOrdersTableFilter();
}

function filterOrdersTable() {
    applyOrdersTableFilter();
}

function applyOrdersTableFilter() {
    const tbody = document.getElementById('ordersTableBody');
    if (!tbody) return;

    const searchInput = document.getElementById('orderSearchInput');
    const query = (searchInput ? searchInput.value : '').trim().toLowerCase();

    const filtered = cachedOrders.filter(o => {
        if (query) {
            const matchId = (o.order_id || '').toLowerCase().includes(query);
            const matchCat = (o.category || '').toLowerCase().includes(query);
            const matchReason = (o.return_reason || '').toLowerCase().includes(query);
            if (!matchId && !matchCat && !matchReason) return false;
        }

        if (activeOrderFilter === 'returns') {
            return o.return_reason !== null;
        } else if (activeOrderFilter === 'deficits') {
            return o.weight_loss_pct && o.weight_loss_pct > 0;
        }
        return true;
    });

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 32px; color: #64748B;">No orders matching current filter criteria.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map(o => {
        const hasReturn = o.return_reason !== null;
        let retBadge = `<span style="color: #64748B;">Delivered Only</span>`;
        if (hasReturn) {
            retBadge = `<span style="color: #F59E0B; font-weight: 600;">Returned (${escapeHtml(o.return_reason)})</span>`;
        }

        let wtDisplay = '-';
        if (o.weight_loss_pct !== null && o.weight_loss_pct !== undefined) {
            const loss = o.weight_loss_pct;
            let barColor = '#10B981';
            let label = `${loss}% (Match)`;
            if (loss >= 40) {
                barColor = '#F43F5E';
                label = `-${loss}% Severe`;
            } else if (loss > 0) {
                barColor = '#F59E0B';
                label = `-${loss}%`;
            }
            wtDisplay = `
                <div class="weight-meter" data-tooltip="Delivered: ${o.original_weight_kg || 'N/A'}kg &bull; Returned: ${o.returned_weight_kg || 'N/A'}kg">
                    <div style="display: flex; justify-content: space-between; font-size: 0.72rem;">
                        <span style="color: #94A3B8;">${o.returned_weight_kg || 0}kg</span>
                        <span style="color: ${barColor}; font-weight: 700;">${label}</span>
                    </div>
                    <div class="weight-meter-bar">
                        <div class="weight-meter-fill" style="width: ${Math.min(100, Math.max(5, 100 - loss))}%; background: ${barColor};"></div>
                    </div>
                </div>
            `;
        }

        let condBadge = o.product_condition || '-';
        if (condBadge.toLowerCase() === 'missing') {
            condBadge = `<span style="color: #F43F5E; font-weight: 800; background: rgba(244,63,94,0.1); padding: 2px 6px; border-radius: 4px;">MISSING / EMPTY</span>`;
        } else if (condBadge.toLowerCase() === 'used') {
            condBadge = `<span style="color: #F59E0B; font-weight: 700; background: rgba(245,158,11,0.1); padding: 2px 6px; border-radius: 4px;">USED / WARDROBE</span>`;
        }

        let matchBadge = '-';
        if (hasReturn) {
            matchBadge = (o.item_match_flag === 1.0) ? 
                '<span style="color: #10B981; font-weight: 600;">✅ Matched SKU</span>' : 
                '<span style="color: #F43F5E; font-weight: 800; background: rgba(244,63,94,0.1); padding: 2px 6px; border-radius: 4px;">❌ SKU MISMATCH</span>';
        }

        return `
            <tr>
                <td><b style="font-family: 'JetBrains Mono', monospace; color: #38BDF8;">${o.order_id}</b></td>
                <td>${o.order_date}</td>
                <td><span style="background: rgba(255,255,255,0.04); padding: 2px 8px; border-radius: 4px;">${escapeHtml(o.category)}</span></td>
                <td><b>Rs. ${(o.order_amount || 0).toLocaleString()}</b></td>
                <td><span style="color: #94A3B8;">${escapeHtml(o.delivery_status || 'Delivered')}</span></td>
                <td>${retBadge}</td>
                <td>${wtDisplay}</td>
                <td>${condBadge}</td>
                <td>${matchBadge}</td>
                <td>
                    <button type="button" class="quick-chip" onclick="inspectOrder('${o.order_id}')" style="font-size: 0.75rem; padding: 3px 8px;">
                        Inspect &rarr;
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function showDossierLoading(isLoading) {
    safeSetStyle('dossierLoading', 'display', isLoading ? 'block' : 'none');
    if (isLoading) {
        safeSetStyle('dossierContent', 'display', 'none');
        safeSetStyle('dossierError', 'display', 'none');
    }
}

function showDossierError(msg, suggestions) {
    safeSetStyle('dossierError', 'display', 'block');
    safeSetText('dossierErrorMsg', msg);
    safeSetStyle('dossierContent', 'display', 'none');

    const sugContainer = document.getElementById('dossierErrorSuggestions');
    if (sugContainer && suggestions && suggestions.length > 0) {
        sugContainer.innerHTML = `
            <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: 600;">Benchmark Entities:</span>
            ${suggestions.map(s => `
                <button type="button" class="quick-chip" onclick="quickPickCustomer('${s}')">
                    👤 ${escapeHtml(s)}
                </button>
            `).join('')}
        `;
    }
}

// ============================================================================
// 4. Live Real-Time Fraud Simulator
// ============================================================================
function initSandbox() {
    const form = document.getElementById('sandboxForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        runSandboxEvaluation();
    });
}

function syncSandboxWithCustomer(dossier) {
    if (!dossier || !dossier.customer) return;
    const cust = dossier.customer;
    const metrics = dossier.metrics || {};
    const orders = dossier.orders || [];

    const cidEl = document.getElementById('sbCustomerId');
    if (cidEl) cidEl.value = cust.customer_id;

    const amtEl = document.getElementById('sbAmount');
    if (amtEl) amtEl.value = metrics.avg_order_value || 15000;

    const catEl = document.getElementById('sbCategory');
    if (catEl && orders.length > 0) catEl.value = orders[0].category;

    const oCntEl = document.getElementById('sbOrderCount');
    if (oCntEl) oCntEl.value = metrics.total_orders || 1;

    const rCntEl = document.getElementById('sbReturnCount');
    if (rCntEl) rCntEl.value = metrics.total_returns || 0;

    const fraudEl = document.getElementById('sbPrevFraud');
    if (fraudEl) fraudEl.value = cust.previous_fraud_flag || 0;

    const cbEl = document.getElementById('sbChargebacks');
    if (cbEl) cbEl.value = metrics.chargebacks_count || 0;

    const devEl = document.getElementById('sbDeviceAccounts');
    if (devEl) devEl.value = (dossier.identity && dossier.identity.ring_size) || 1;
}

async function runSandboxEvaluation() {
    const btn = document.getElementById('btnEvaluateSandbox');
    const spinner = document.getElementById('sbBtnSpinner');
    const btnLabel = document.getElementById('sbBtnLabel');

    const amt = parseFloat(document.getElementById('sbAmount')?.value || 0);
    if (isNaN(amt) || amt <= 0) {
        showToast('Please enter a valid order amount greater than 0.');
        return;
    }

    const payload = {
        customer_id: document.getElementById('sbCustomerId')?.value?.trim() || 'ANONYMOUS',
        order_amount: amt,
        category: document.getElementById('sbCategory')?.value || 'Electronics',
        customer_order_count: parseInt(document.getElementById('sbOrderCount')?.value || 1),
        customer_return_count: parseInt(document.getElementById('sbReturnCount')?.value || 0),
        original_weight_kg: parseFloat(document.getElementById('sbOrigWt')?.value || 3.0),
        returned_weight_kg: parseFloat(document.getElementById('sbRetWt')?.value || 1.0),
        item_match_flag: parseFloat(document.getElementById('sbItemMatch')?.value || 1.0),
        product_condition: document.getElementById('sbCondition')?.value || 'Good',
        return_reason: document.getElementById('sbReason')?.value || 'Wrong Item',
        address_changes: parseInt(document.getElementById('sbAddressChanges')?.value || 0),
        phone_changes: parseInt(document.getElementById('sbPhoneChanges')?.value || 0),
        device_account_count: parseInt(document.getElementById('sbDeviceAccounts')?.value || 1),
        previous_fraud: parseInt(document.getElementById('sbPrevFraud')?.value || 0),
        chargeback_count: parseInt(document.getElementById('sbChargebacks')?.value || 0),
        delivery_partner_risk: parseFloat(document.getElementById('sbCourierRisk')?.value || 25)
    };

    if (btn) btn.disabled = true;
    if (spinner) spinner.style.display = 'inline-block';
    if (btnLabel) btnLabel.textContent = 'Executing Multi-Layer Decision...';

    try {
        const res = await fetch(`${API_BASE}/evaluate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errJson = await res.json().catch(() => ({}));
            throw new Error(errJson.message || 'Evaluation request returned status ' + res.status);
        }
        const evalRes = await res.json();
        renderSandboxResult(evalRes);
        showToast('Scenario evaluated successfully!');
    } catch (err) {
        console.error('Simulation error:', err);
        showToast('Simulation failed: ' + err.message);
    } finally {
        if (btn) btn.disabled = false;
        if (spinner) spinner.style.display = 'none';
        if (btnLabel) btnLabel.textContent = '⚡ Evaluate Live Transaction Decision';
    }
}

function renderSandboxResult(evalRes) {
    safeSetStyle('sandboxResultsCard', 'display', 'block');

    const score = evalRes.hybrid_risk_score || 0;
    const circle = document.getElementById('sbGaugeCircleProgress');
    const scoreText = document.getElementById('sbGaugeScoreText');

    if (circle && scoreText) {
        const r = 68;
        const circumference = 2 * Math.PI * r;
        circle.style.strokeDasharray = `${circumference} ${circumference}`;
        circle.style.strokeDashoffset = circumference - (score / 100) * circumference;
        circle.style.stroke = evalRes.badge_color || '#10B981';
        scoreText.textContent = score;
        scoreText.style.color = evalRes.badge_color || '#10B981';
    }

    safeSetText('sbRiskBadge', `${(evalRes.risk_level || 'EVALUATED').toUpperCase()} (${score}/100)`);
    safeSetText('sbActionVal', evalRes.recommended_action || 'Approve');
    safeSetStyle('sbActionVal', 'color', evalRes.badge_color || '#10B981');

    const typoConf = evalRes.typology_confidence ? (evalRes.typology_confidence * 100).toFixed(0) : '90';
    safeSetText('sbTypologyVal', `${evalRes.probable_fraud_type || 'Legitimate'} (${typoConf}% Confidence)`);

    safeSetText('sbRuleScore', `${evalRes.rule_score || 0}/100`);
    safeSetText('sbMlProb', `${(evalRes.ml_probability ? (evalRes.ml_probability * 100).toFixed(1) : '0')}%`);
    safeSetText('sbNetworkPts', `+${evalRes.network_risk_points || 0} pts`);

    const reasonsList = document.getElementById('sbReasonsList');
    if (reasonsList && evalRes.reasons) {
        reasonsList.innerHTML = evalRes.reasons.map((r, i) => `
            <li class="reason-card ${r.startsWith('+') ? 'violation' : ''}">
                <b>${i + 1}.</b> ${escapeHtml(r)}
            </li>
        `).join('');
    }

    // Plain English Forensic Rationale
    safeSetText('sbVerdictText', generateForensicRationale(evalRes));

    const card = document.getElementById('sandboxResultsCard');
    if (card) card.scrollIntoView({ behavior: 'smooth' });
}

function generateForensicRationale(evalRes) {
    const score = evalRes.hybrid_risk_score || 0;
    const action = evalRes.recommended_action || 'Approve';
    const typo = evalRes.probable_fraud_type || 'Legitimate Purchaser';
    const ruleScore = evalRes.rule_score || 0;
    const mlProb = ((evalRes.ml_probability || 0) * 100).toFixed(1);

    if (score >= 70) {
        return `🚨 High Risk Verdict (${score}/100): The transaction exhibits multiple severe fraud markers aligning with "${typo}". Triggered rule severity scored ${ruleScore}/100 with an XGBoost ML probability of ${mlProb}%. The automated system recommends "${action.toUpperCase()}" to intercept potential inventory loss, counterfeit SKU swapping, or chargeback dispute leakage.`;
    } else if (score >= 35) {
        return `⚠️ Medium Risk Verdict (${score}/100): Moderate anomalies detected in returns ratio or package weight deficit. Behavioral ML probability is ${mlProb}%. System recommends "${action.toUpperCase()}" to physically inspect return contents before approving refund disbursement.`;
    } else {
        return `✅ Low Risk Verdict (${score}/100): Transaction aligns with verified benign buyer benchmarks with minimal anomaly indicators (ML fraud probability: ${mlProb}%). Safe for instant one-click automated refund release.`;
    }
}

// ============================================================================
// 5. Order Detailed Inspection Modal
// ============================================================================
async function inspectOrder(orderId) {
    try {
        const res = await fetch(`${API_BASE}/orders/${orderId}`);
        if (!res.ok) {
            showToast(`Order ID "${orderId}" not found in database.`);
            return;
        }
        const o = await res.json();
        const r = o.risk_evaluation || {};

        const origWt = o.delivery?.original_weight_kg || 0;
        const retWt = o.return_info?.returned_weight_kg || 0;
        const wtLoss = o.return_info?.weight_loss_pct || 0;

        const modalHtml = `
            <div id="orderModal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 2000; display: flex; align-items: center; justify-content: center; padding: 20px;">
                <div style="background: #0E1726; border: 1px solid #1E293B; border-radius: 16px; width: 100%; max-width: 800px; max-height: 90vh; overflow-y: auto; padding: 26px; box-shadow: 0 25px 60px rgba(0,0,0,0.9);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; border-bottom: 1px solid #1E293B; padding-bottom: 12px;">
                        <div>
                            <h2 style="margin: 0; color: #38BDF8; font-size: 1.35rem; font-family: 'JetBrains Mono', monospace;">📦 Order Telemetry: ${escapeHtml(o.order_id)}</h2>
                            <p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 0.82rem;">Date: ${o.order_date} &bull; Category: ${escapeHtml(o.category)} &bull; Amount: Rs. ${(o.order_amount || 0).toLocaleString()}</p>
                        </div>
                        <button onclick="closeOrderModal()" style="background: transparent; border: none; color: #94A3B8; font-size: 1.8rem; cursor: pointer; line-height: 1;">&times;</button>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
                        <div class="card-box">
                            <span class="kpi-title">Order Risk Assessment</span>
                            <div style="font-size: 1.6rem; font-weight: 800; color: ${r.badge_color || '#10B981'}; margin-top: 4px;">
                                ${r.hybrid_risk_score || 0}/100
                            </div>
                            <div style="margin-top: 6px;">
                                <span class="${r.risk_level === 'High Risk' ? 'risk-pill-high' : 'risk-pill-low'}" style="font-size: 0.75rem;">
                                    ${r.risk_level || 'EVALUATED'}
                                </span>
                            </div>
                            <div style="margin-top: 8px; font-size: 0.85rem;"><b>Recommended Action:</b> ${escapeHtml(r.recommended_action || 'Approve')}</div>
                        </div>

                        <div class="card-box">
                            <span class="kpi-title">Associated Customer</span>
                            <div style="font-size: 1.2rem; font-weight: 700; color: #38BDF8; margin-top: 4px;">
                                <a href="javascript:void(0)" onclick="closeOrderModal(); loadCustomerDossier('${escapeHtml(o.customer_id)}')" style="color: #38BDF8; text-decoration: underline; font-family: 'JetBrains Mono', monospace;">
                                    ${escapeHtml(o.customer_id)}
                                </a>
                            </div>
                            <div style="font-size: 0.82rem; color: #94A3B8; margin-top: 4px;">
                                Location: ${escapeHtml(o.customer_summary?.city || 'N/A')} &bull; Lifetime Return Rate: ${o.customer_summary?.return_rate || 0}%
                            </div>
                        </div>
                    </div>

                    <div class="card-box" style="margin-bottom: 16px;">
                        <h4 style="margin-bottom: 12px; color: #F8FAFC; font-size: 0.95rem;">📦 Package Physical Inspection Telemetry:</h4>
                        
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; font-size: 0.85rem; margin-bottom: 12px;">
                            <div>Delivered Package: <b>${origWt} kg</b></div>
                            <div>Returned Package: <b>${retWt ? retWt + ' kg' : 'No Return'}</b></div>
                            <div>Weight Deficit: <b style="color: ${wtLoss >= 40 ? '#F43F5E' : (wtLoss > 0 ? '#F59E0B' : '#10B981')}">${wtLoss ? '-' + wtLoss + '%' : '0%'}</b></div>
                        </div>

                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; font-size: 0.85rem; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px;">
                            <div>SKU Verification: <b>${o.return_info ? (o.return_info.item_match_flag === 1 ? '✅ Verified Match' : '❌ COUNTERFEIT SWAP') : 'N/A'}</b></div>
                            <div>Product Condition: <b>${escapeHtml(o.return_info?.product_condition || 'N/A')}</b></div>
                            <div>Claimed Reason: <b>${escapeHtml(o.return_info?.return_reason || 'None')}</b></div>
                        </div>
                    </div>

                    <div class="card-box">
                        <h4 style="margin-bottom: 8px; color: #F8FAFC; font-size: 0.9rem;">Triggered Audit Violations:</h4>
                        <ul class="reasons-timeline">
                            ${(r.reasons || ['Clean transaction profile']).map((rsn, idx) => `
                                <li class="reason-card ${rsn.startsWith('+') ? 'violation' : ''}">
                                    <b>${idx + 1}.</b> ${escapeHtml(rsn)}
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;

        const existing = document.getElementById('orderModal');
        if (existing) existing.remove();
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    } catch (err) {
        console.error('Error inspecting order:', err);
    }
}

function closeOrderModal() {
    const m = document.getElementById('orderModal');
    if (m) m.remove();
}

// ============================================================================
// 6. Analytics & Executive KPIs Fetch
// ============================================================================
async function loadExecutiveKPIs() {
    try {
        const [kpiRes, tierRes, typoRes] = await Promise.all([
            fetch(`${API_BASE}/analytics/kpis`),
            fetch(`${API_BASE}/analytics/risk-distribution`),
            fetch(`${API_BASE}/analytics/fraud-typologies`)
        ]);

        if (kpiRes.ok) {
            const kpi = await kpiRes.json();
            safeSetText('kpiTotalOrders', (kpi.total_orders || 0).toLocaleString());
            safeSetText('kpiTotalSpend', `Rs. ${((kpi.total_spend || 0) / 1e6).toFixed(1)}M Gross Volume`);
            safeSetText('kpiReturns', (kpi.total_returns || 0).toLocaleString());
            safeSetText('kpiReturnRate', `${kpi.return_rate || 0}% Return Rate`);
            safeSetText('kpiRefunds', `Rs. ${((kpi.total_refunds || 0) / 1e5).toFixed(1)} Lakh`);
            safeSetText('kpiRefundRate', `${kpi.refund_leakage_pct || 0}% Revenue Leakage`);
            safeSetText('kpiLossPrevented', `Rs. ${((kpi.fraud_loss_intercepted || 0) / 1e5).toFixed(1)} Lakh`);
            safeSetText('kpiHighRisk', (kpi.high_risk_count || 0).toLocaleString());
            safeSetText('kpiHighRiskRate', `${kpi.high_risk_rate || 0}% Flagged Entities`);
        }

        if (tierRes.ok) {
            const tiers = await tierRes.json();
            const container = document.getElementById('kpiTierBar');
            if (container) {
                container.innerHTML = tiers.map(t => `
                    <div style="flex: ${t.percentage}; background: ${t.color}; height: 26px; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; color: #080D1A;" title="${t.tier}: ${t.count} (${t.percentage}%)">
                        ${t.percentage >= 15 ? t.tier + ' ' + t.percentage + '%' : ''}
                    </div>
                `).join('');
            }
        }

        if (typoRes.ok) {
            cachedTypologies = await typoRes.json();
            renderTypologiesTable(cachedTypologies);
        }
    } catch (err) {
        console.error('Error loading KPIs:', err);
    }
}

function renderTypologiesTable(items) {
    const tbody = document.getElementById('typologiesTableBody');
    if (!tbody) return;

    if (!items || items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 24px; color: #64748B;">No matching fraud typologies found.</td></tr>`;
        return;
    }

    tbody.innerHTML = items.map(t => `
        <tr>
            <td><b>${escapeHtml(t.typology)}</b></td>
            <td>${t.count}</td>
            <td>Rs. ${(t.total_exposure || 0).toLocaleString()}</td>
            <td>
                <span class="item-tag" style="background: ${t.avg_risk_score >= 70 ? '#F43F5E' : '#F59E0B'}25; color: ${t.avg_risk_score >= 70 ? '#F43F5E' : '#F59E0B'}">
                    ${t.avg_risk_score}/100
                </span>
            </td>
        </tr>
    `).join('');
}

function filterTypologiesTable() {
    const query = (document.getElementById('typologySearchInput')?.value || '').trim().toLowerCase();
    if (!query) {
        renderTypologiesTable(cachedTypologies);
        return;
    }
    const filtered = cachedTypologies.filter(t => (t.typology || '').toLowerCase().includes(query));
    renderTypologiesTable(filtered);
}

// ============================================================================
// 7. Fraud Rings & Interactive Syndicate Network Graph
// ============================================================================
async function loadFraudRings() {
    const container = document.getElementById('ringsListContainer');
    if (container) {
        container.innerHTML = `
            <div style="text-align: center; padding: 36px 20px;">
                <div class="spinner-ring"></div>
                <p style="margin-top: 10px; color: var(--text-secondary); font-size: 0.88rem;">Scanning identity graph clusters...</p>
            </div>
        `;
    }

    try {
        const res = await fetch(`${API_BASE}/analytics/fraud-rings`);
        if (!res.ok) throw new Error('API returned ' + res.status);
        const data = await res.json();
        cachedRings = data.rings || [];
        renderFraudRings(cachedRings);
    } catch (err) {
        console.error('Error loading fraud rings:', err);
        if (container) {
            container.innerHTML = `
                <div class="error-banner">
                    <p style="margin: 0; color: #FDA4AF;">Failed to load identity syndicates (${escapeHtml(err.message)}).</p>
                    <button type="button" class="retry-btn" onclick="loadFraudRings()">🔄 Retry Graph Scan</button>
                </div>
            `;
        }
    }
}

function renderFraudRings(rings) {
    const container = document.getElementById('ringsListContainer');
    if (!container) return;

    if (!rings || rings.length === 0) {
        container.innerHTML = '<div style="padding: 32px; text-align: center; color: #64748B;">No coordinated fraud syndicates matching search.</div>';
        return;
    }

    container.innerHTML = rings.map(r => `
        <div class="card-box" style="margin-bottom: 18px; border-left: 4px solid ${r.ring_risk_level === 'High' ? '#F43F5E' : '#F59E0B'}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
                <h3 style="margin: 0; color: #F8FAFC; font-size: 1.05rem; font-family: 'JetBrains Mono', monospace;">
                    🔴 ${escapeHtml(r.ring_id)} (${r.account_count} Connected Accounts, ${r.flagged_accounts_count} Flagged)
                </h3>
                <span class="${r.ring_risk_level === 'High' ? 'risk-pill-high' : 'risk-pill-medium'}" style="font-size: 0.72rem; padding: 3px 10px;">
                    ${r.ring_risk_level.toUpperCase()} SYNDICATE
                </span>
            </div>

            <div style="margin-bottom: 8px; font-size: 0.85rem;">
                <b>Member Accounts:</b> 
                ${r.customers.map(c => `<button type="button" onclick="loadCustomerDossier('${c}')" class="quick-chip" style="margin: 2px; font-family: 'JetBrains Mono', monospace;">👤 ${c}</button>`).join('')}
            </div>

            <div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 10px;">
                <b>Shared Hardware:</b> ${r.shared_devices.length > 0 ? r.shared_devices.join(', ') : 'None'} &bull;
                <b>Shared Addresses:</b> ${r.shared_addresses.length > 0 ? r.shared_addresses.join(', ') : 'None'}
            </div>

            ${generateSyndicateSvg(r)}
        </div>
    `).join('');
}

function generateSyndicateSvg(ring) {
    const hubId = (ring.shared_devices && ring.shared_devices[0]) || (ring.shared_addresses && ring.shared_addresses[0]) || 'HUB';
    const custs = ring.customers || [];
    const width = 600;
    const height = 160;
    const cx = width / 2;
    const cy = height / 2;

    const angleStep = (2 * Math.PI) / Math.max(1, custs.length);
    const radius = 60;

    let lines = '';
    let nodes = '';

    custs.forEach((c, idx) => {
        const angle = idx * angleStep - Math.PI / 2;
        const nx = cx + radius * Math.cos(angle);
        const ny = cy + radius * Math.sin(angle);
        const isFlagged = idx < (ring.flagged_accounts_count || 1);
        const nodeColor = isFlagged ? '#F43F5E' : '#38BDF8';

        lines += `<line x1="${cx}" y1="${cy}" x2="${nx}" y2="${ny}" stroke="rgba(148, 163, 184, 0.3)" stroke-width="1.5" stroke-dasharray="3,3" />`;
        nodes += `
            <g style="cursor: pointer;" onclick="loadCustomerDossier('${c}')">
                <circle cx="${nx}" cy="${ny}" r="15" fill="#0E1726" stroke="${nodeColor}" stroke-width="2" />
                <text x="${nx}" y="${ny + 4}" fill="#FFF" font-size="8.5" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">${c.substring(0, 5)}</text>
                <text x="${nx}" y="${ny + 24}" fill="${nodeColor}" font-size="7.5" font-weight="700" text-anchor="middle">${isFlagged ? 'FLAGGED' : 'MEMBER'}</text>
            </g>
        `;
    });

    const hubNode = `
        <g>
            <circle cx="${cx}" cy="${cy}" r="20" fill="#1E1B4B" stroke="#A855F7" stroke-width="2.5" />
            <text x="${cx}" y="${cy - 2}" fill="#C084FC" font-size="11" text-anchor="middle">📱</text>
            <text x="${cx}" y="${cy + 10}" fill="#F8FAFC" font-size="7" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">HUB</text>
        </g>
    `;

    return `
        <div class="syndicate-graph-viewport">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.74rem; color: #94A3B8;">
                <span><b>Cluster Topology:</b> Linked via fingerprint <code style="color: #C084FC;">${escapeHtml(hubId)}</code></span>
                <span>Click any node to investigate 360° dossier</span>
            </div>
            <svg class="syndicate-svg" viewBox="0 0 ${width} ${height}" preserveAspectRatio="xMidYMid meet">
                ${lines}
                ${hubNode}
                ${nodes}
            </svg>
        </div>
    `;
}

function filterFraudRings() {
    const query = (document.getElementById('ringSearchInput')?.value || '').trim().toLowerCase();
    if (!query) {
        renderFraudRings(cachedRings);
        return;
    }
    const filtered = cachedRings.filter(r => {
        const matchId = (r.ring_id || '').toLowerCase().includes(query);
        const matchCust = (r.customers || []).some(c => c.toLowerCase().includes(query));
        return matchId || matchCust;
    });
    renderFraudRings(filtered);
}

// ============================================================================
// 8. Supply Chain & Courier Telemetry Fetch
// ============================================================================
async function loadSupplyChain() {
    try {
        const res = await fetch(`${API_BASE}/analytics/supply-chain`);
        if (!res.ok) return;
        const data = await res.json();
        cachedCouriers = data.couriers || [];
        cachedMerchants = data.merchants || [];

        renderCouriersTable(cachedCouriers);
        renderMerchantsTable(cachedMerchants);
    } catch (err) {
        console.error('Error loading supply chain telemetry:', err);
    }
}

function renderCouriersTable(couriers) {
    const tbody = document.getElementById('couriersTableBody');
    if (!tbody) return;

    if (!couriers || couriers.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 24px; color: #64748B;">No matching delivery partners found.</td></tr>`;
        return;
    }

    tbody.innerHTML = couriers.map(c => `
        <tr>
            <td><b>${escapeHtml(c.delivery_partner_id)}</b></td>
            <td>${(c.total_deliveries || 0).toLocaleString()}</td>
            <td>${c.tampering_cases || 0}</td>
            <td>${c.suspicious_returns || 0}</td>
            <td>
                <span class="item-tag" style="background: ${c.partner_risk_score >= 40 ? '#F43F5E' : '#10B981'}25; color: ${c.partner_risk_score >= 40 ? '#F43F5E' : '#10B981'}">
                    ${c.partner_risk_score}/100
                </span>
            </td>
        </tr>
    `).join('');
}

function filterCouriersTable() {
    const query = (document.getElementById('carrierSearchInput')?.value || '').trim().toLowerCase();
    if (!query) {
        renderCouriersTable(cachedCouriers);
        return;
    }
    const filtered = cachedCouriers.filter(c => (c.delivery_partner_id || '').toLowerCase().includes(query));
    renderCouriersTable(filtered);
}

function renderMerchantsTable(merchants) {
    const tbody = document.getElementById('merchantsTableBody');
    if (!tbody) return;

    if (!merchants || merchants.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 24px; color: #64748B;">No matching merchants found.</td></tr>`;
        return;
    }

    tbody.innerHTML = merchants.map(m => `
        <tr>
            <td><b>${escapeHtml(m.merchant_id)}</b></td>
            <td>${escapeHtml(m.category || 'General')}</td>
            <td>${(m.total_orders || 0).toLocaleString()}</td>
            <td>${m.return_rate || 0}%</td>
            <td>
                <span class="item-tag" style="background: ${m.merchant_risk_score >= 40 ? '#F43F5E' : '#10B981'}25; color: ${m.merchant_risk_score >= 40 ? '#F43F5E' : '#10B981'}">
                    ${m.merchant_risk_score}/100
                </span>
            </td>
        </tr>
    `).join('');
}

function filterMerchantsTable() {
    const query = (document.getElementById('merchantSearchInput')?.value || '').trim().toLowerCase();
    if (!query) {
        renderMerchantsTable(cachedMerchants);
        return;
    }
    const filtered = cachedMerchants.filter(m => (m.merchant_id || '').toLowerCase().includes(query) || (m.category || '').toLowerCase().includes(query));
    renderMerchantsTable(filtered);
}

// Utility: HTML Escaping
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
