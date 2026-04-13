// ============================================================
// SENTINEL — Centralized API Layer + Page Integration
// ============================================================

// Automatically adapt to localhost or cloud (e.g., Render) deployments
const BASE_URL = window.location.origin.includes('5500') || window.location.origin.includes('3000')
    ? 'http://127.0.0.1:8000'
    : '';

// ─────────────────────────────────────────
//  AUTH GUARD & LOGOUT
// ─────────────────────────────────────────
(function protectRoutes() {
    const path = window.location.pathname;
    const isPublicPage = path.includes('login.html') || path.includes('signup.html') || path.endsWith('/') || path.includes('index.html');
    const token = localStorage.getItem('token');

    if (!token && !isPublicPage) {
        window.location.href = 'login.html';
    }
})();

function handleLogout() {
    localStorage.removeItem('token');
    window.location.href = 'login.html';
}

function loadIdentity() {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const payload = JSON.parse(decodeURIComponent(atob(base64).split('').map(function (c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join('')));

        const username = payload.username || payload.email.split('@')[0];
        const role = payload.role || 'Institutional Sentinel';
        const uuid = (payload.sub || '89A4').split('-')[0].toUpperCase();

        const avatarEl = document.getElementById('hero-avatar');
        const welcomeEl = document.getElementById('hero-welcome');
        const tierEl = document.getElementById('hero-account-tier');

        if (welcomeEl) {
            // Treat username as clean string instead of deriving from email
            const cleanName = username.split('.').map(n => n.charAt(0).toUpperCase() + n.slice(1)).join(' ');
            welcomeEl.innerText = `Welcome back, ${cleanName}`;

            if (avatarEl) {
                const initials = cleanName.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
                avatarEl.innerText = initials;
            }

            if (tierEl) {
                tierEl.innerHTML = `Account ID: SNTL-${uuid}  •  Tier: ${role}`;
            }
        }

    } catch (e) {
        console.error("Failed to decode token identity:", e);
    }
}

document.addEventListener('DOMContentLoaded', loadIdentity);

// ─────────────────────────────────────────
//  REAL STOCK PRICES (reference data)
// ─────────────────────────────────────────
const STOCK_PRICES = {
    AAPL: 189.23,
    MSFT: 402.11,
    GOOGL: 175.98,
    AMZN: 198.45,
    TSLA: 172.63,
    NVDA: 875.40,
    META: 513.27,
    BRK: 412.50,
    JPM: 202.18,
    V: 279.55,
};

// ─────────────────────────────────────────
//  CORE API FUNCTIONS
// ─────────────────────────────────────────

async function apiFetch(path, method = 'GET', body = null) {
    const opts = {
        method,
        headers: {
            'Content-Type': 'application/json',
            "Authorization": "Bearer " + localStorage.getItem("token")
        },
    };

    if (body) opts.body = JSON.stringify(body);
    try {
        const res = await fetch(`${BASE_URL}${path}`, opts);
        if (!res.ok) {
            const errText = await res.text();
            throw new Error(`HTTP ${res.status}: ${errText}`);
        }
        return await res.json();
    } catch (err) {
        if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
            throw new Error('BACKEND_UNREACHABLE');
        }
        throw err;
    }
}

async function runAnalysis(data) {
    try {
        const result = await apiFetch('/analyze', 'POST', data);
        const orchestration = result.orchestration;
        return result;
    } catch (err) {
        throw err;
    }
}
// Portfolio API
async function portfolioGet()          { return apiFetch('/portfolio',             'GET');  }
async function portfolioInit()          { return apiFetch('/portfolio/init',         'POST'); }
async function portfolioTrade(data)     { return apiFetch('/portfolio/trade',        'POST', data); }
async function portfolioValue()         { return apiFetch('/portfolio/value',        'GET');  }
async function portfolioHistory()       { return apiFetch('/portfolio/history',      'GET');  }
async function portfolioPerformance()   { return apiFetch('/portfolio/performance',  'GET');  }
async function executeViaAgent(data)    { return apiFetch('/execute',               'POST', data); }
// Other APIs
async function runSimulation(data)  { return apiFetch('/simulate',       'POST', data); }
async function getClimateScores()   { return apiFetch('/climate-scores', 'GET');  }
async function validateTrade(data)  { return apiFetch('/validate-trade', 'POST', data); }
async function executeTrade(data)   { return apiFetch('/execute-trade',  'POST', data); }
async function getPolicies()        { return apiFetch('/policies',       'GET');  }
async function getExplanation(data) { return apiFetch('/explain',        'POST', data); }

// ─────────────────────────────────────────
//  SHARED UI HELPERS
// ─────────────────────────────────────────

function setLoading(el, isLoading, originalHTML = '') {
    if (isLoading) {
        el.innerHTML = `
            <div style="display:flex;align-items:center;gap:12px;color:var(--neon-lime);font-family:'JetBrains Mono',monospace;font-size:0.85rem;">
                <div class="pulse-dot"></div> Querying Sentinel agents...
            </div>`;
    } else {
        el.innerHTML = originalHTML;
    }
}

function showError(container, message) {
    container.innerHTML = `
        <div style="padding:1.5rem;border:1px solid rgba(255,68,68,0.4);border-radius:12px;background:rgba(255,68,68,0.07);color:#ff6666;font-family:'JetBrains Mono',monospace;font-size:0.82rem;">
            ⚠️ ${message === 'BACKEND_UNREACHABLE'
            ? 'Backend not reachable. Make sure the Sentinel API is running on <b>http://127.0.0.1:8000</b>'
            : `Error: ${message}`}
        </div>`;
}

function guardBadge(status) {
    const map = {
        APPROVED: { color: '#00ff88', icon: '🛡️', bg: 'rgba(0,255,136,0.1)', border: 'rgba(0,255,136,0.3)' },
        BLOCKED: { color: '#ff4444', icon: '🚫', bg: 'rgba(255,68,68,0.1)', border: 'rgba(255,68,68,0.3)' },
        MODIFIED: { color: '#ffcc00', icon: '⚠️', bg: 'rgba(255,204,0,0.1)', border: 'rgba(255,204,0,0.3)' },
        SKIPPED: { color: '#888', icon: '⏭️', bg: 'rgba(136,136,136,0.1)', border: 'rgba(136,136,136,0.2)' },
    };
    const s = map[status] || map.SKIPPED;
    return `<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;background:${s.bg};border:1px solid ${s.border};color:${s.color};font-weight:700;font-size:0.8rem;">${s.icon} ${status}</span>`;
}

function formatCurrency(val) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(val);
}

// ─────────────────────────────────────────
//  PAGE: dashboard.html
// ─────────────────────────────────────────

function initDashboard() {
    // Risk toggle
    const riskBtns = document.querySelectorAll('.risk-btn');
    riskBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            riskBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    // Budget slider display
    const budgetSlider = document.querySelector('#budget-slider');
    const budgetDisplay = document.querySelector('.budget-display-value'); // if exists
    if (budgetSlider && budgetDisplay) {
        budgetSlider.addEventListener('input', (e) => {
            budgetDisplay.innerText = formatCurrency(e.target.value);
        });
    }

    // Portfolio Fetch
    async function loadDashboardPortfolio() {
        try {
            const data = await portfolioValue(); // Calls GET /portfolio/value
            const totalValEl = document.getElementById('dash-port-total');
            const cashEl = document.getElementById('dash-port-cash');
            const holdingsListEl = document.getElementById('dash-holdings-list');
            const pnlEl = document.getElementById('dash-port-pnl');

            if (!totalValEl || !cashEl || !holdingsListEl) return;

            // Total Value and PnL
            totalValEl.innerText = formatCurrency(data.total_value);
            cashEl.innerText = formatCurrency(data.cash);

            if (pnlEl && data.profit_loss !== undefined) {
                pnlEl.style.display = 'inline-block';
                const isProfit = data.profit_loss >= 0;
                
                // Construct standard UI badge dynamically
                pnlEl.style.padding = '4px 10px';
                pnlEl.style.borderRadius = '20px';
                pnlEl.style.fontSize = '0.75rem';
                pnlEl.style.fontWeight = '700';
                pnlEl.style.border = isProfit ? '1px solid rgba(0,255,136,0.3)' : '1px solid rgba(255,68,68,0.3)';
                pnlEl.style.background = isProfit ? 'rgba(0,255,136,0.1)' : 'rgba(255,68,68,0.1)';
                pnlEl.style.color = isProfit ? '#00ff88' : '#ff4444';
                
                pnlEl.innerText = (isProfit ? '+' : '') + formatCurrency(data.profit_loss);
            }

            const holdings = data.holdings || [];
            if (holdings.length === 0) {
                holdingsListEl.innerHTML = '<div style="font-size:0.75rem; color:var(--muted-text); padding:10px 0;">No active holdings.</div>';
            } else {
                holdingsListEl.innerHTML = holdings.map(h => {
                    return `
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px">
                            <div style="display:flex; align-items:center; gap:8px">
                                <div style="width:10px; height:10px; border-radius:3px; background:var(--neon-lime);"></div>
                                <span style="font-size:0.8rem; font-weight:700;">${h.ticker}</span>
                                <span style="font-size:0.7rem; color:var(--muted-text)">${h.quantity} shrs</span>
                            </div>
                            <div style="font-size:0.8rem; font-family:'JetBrains Mono',monospace;">${formatCurrency(h.market_value)}</div>
                        </div>
                    `;
                }).join('');
            }
        } catch (e) {
            console.error("Dashboard Portfolio load failed:", e);
        }
    }
    loadDashboardPortfolio();

    // Chip toggle
    const chips = document.querySelectorAll('.chip');
    chips.forEach(chip => chip.addEventListener('click', () => chip.classList.toggle('active')));

    // Gauge animation
    const gaugeProgress = document.querySelector('#gauge-progress');
    if (gaugeProgress) {
        // Initial state is blanked via CSS inline style in HTML.
        // It will spring to life inside renderDashboardResults().
    }

    // QUICK EXECUTION (Execute Trade Button)
    const execBtn = document.getElementById('execute-trade-btn');
    if (execBtn) {
        execBtn.addEventListener('click', async () => {
            const ticker = document.getElementById('qt-ticker')?.value.trim().toUpperCase();
            const qty = parseFloat(document.getElementById('qt-qty')?.value);
            const action = document.getElementById('qt-action')?.value;
            const resEl = document.getElementById('qt-result');

            if (!ticker || isNaN(qty) || qty <= 0) {
                resEl.style.color = '#ffcc00';
                resEl.innerText = '⚠ Enter a valid ticker and quantity';
                return;
            }

            execBtn.disabled = true;
            execBtn.style.opacity = '0.6';
            resEl.style.color = 'var(--muted-text)';
            resEl.innerText = `⏳ Executing ${action} ${qty}x ${ticker}...`;

            try {
                // Ensure portfolio initialized for new users
                try { await portfolioInit(); } catch(e){}

                // Hits POST /execute-trade through script.js mapped APIs
                const response = await executeTrade({ ticker, action, quantity: qty });

                resEl.style.color = action === 'BUY' ? '#00ff88' : '#00d2ff';
                resEl.innerHTML = `✓ ${action} <b>${response.ticker}</b> @ ${formatCurrency(response.price)}<br>Total: ${formatCurrency(response.total_cost)}`;
                
                // Refresh dashboard portfolio UI implicitly
                loadDashboardPortfolio();
            } catch (err) {
                resEl.style.color = '#ff4444';
                resEl.innerText = `✗ Failed: ${err.message || 'Error occurred'}`;
            } finally {
                execBtn.disabled = false;
                execBtn.style.opacity = '1';
            }
        });
    }

    // RUN ANALYSIS BUTTON
    const runBtn = document.getElementById('run-analysis-btn');
    if (!runBtn) return;

    const resultsContainer = document.getElementById('analysis-results');

    runBtn.addEventListener('click', async () => {
        const budget = parseFloat(document.getElementById('budget-slider')?.value || 100000);
        const activeRisk = document.querySelector('.risk-btn.active');
        const risk_level = activeRisk ? activeRisk.innerText.toLowerCase().replace('med', 'moderate') : 'moderate';
        const max_trade = parseFloat(document.getElementById('max-trade-input')?.value || 50000);
        const avoidChips = [...document.querySelectorAll('.chip.active')].map(c => c.innerText.replace('No ', '').toLowerCase());
        const avoid_sectors = avoidChips.length > 0 ? avoidChips : [];

        resultsContainer.style.display = 'block';
        runBtn.disabled = true;
        runBtn.style.opacity = '0.6';

        const bootSteps = [
            '[ CLIMATE AGENT ]  Analyzing ESG sector constraints...',
            '[ FINANCIAL AGENT ]  Fetching market sentiment & return metrics...',
            '[ SIMULATION ]  Running Monte Carlo risk scenarios...',
            '[ PORTFOLIO ]  Optimizing climate-weighted allocation...',
            '[ TRADER ]  Generating trade intent from allowed assets...',
            '[ GUARD ]  Validating intent against policy constraints...',
            '[ EXPLAINER ]  Composing AI reasoning summary...'
        ];

        resultsContainer.innerHTML = `<div id="boot-log" style="font-family:'JetBrains Mono',monospace; font-size:0.78rem; color:var(--neon-lime); line-height:2; padding:1.2rem 1.5rem; background:rgba(0,0,0,0.4); border-radius:12px; border:1px solid rgba(168,255,62,0.15);"><div style="color:#a8ff3e; font-weight:800; font-size:0.9rem; margin-bottom:1rem; letter-spacing:0.05em;">⚡ SENTINEL ORCHESTRATION STARTING...</div></div>`;
        const bootLog = document.getElementById('boot-log');

        // Animation promise — each step appears at i * 500ms, guaranteed
        const animationPromise = new Promise(resolve => {
            bootSteps.forEach((step, i) => {
                setTimeout(() => {
                    const line = document.createElement('div');
                    line.style.cssText = 'opacity:0; transition:opacity 0.4s ease; padding:3px 0; color:var(--neon-lime);';
                    line.textContent = '> ' + step;
                    bootLog.appendChild(line);
                    void line.offsetHeight; // force reflow so transition fires
                    line.style.opacity = '1';

                    if (i === bootSteps.length - 1) {
                        setTimeout(() => {
                            const done = document.createElement('div');
                            done.style.cssText = 'color:#00ffcc; font-weight:700; margin-top:10px; opacity:0; transition:opacity 0.4s ease;';
                            done.textContent = '> [ALL AGENTS COMPLETE] Rendering results...';
                            bootLog.appendChild(done);
                            void done.offsetHeight;
                            done.style.opacity = '1';
                            setTimeout(resolve, 700);
                        }, 500);
                    }
                }, i * 500);
            });
        });

        // Fire API in parallel
        const apiPromise = runAnalysis({ budget, risk_level, max_trade, avoid_sectors });

        try {
            // Wait for BOTH animation to finish AND api to return
            const [data] = await Promise.all([apiPromise, animationPromise]);
            renderDashboardResults(resultsContainer, data);
        } catch (err) {
            showError(resultsContainer, err.message);
        } finally {
            runBtn.disabled = false;
            runBtn.style.opacity = '1';
        }
    });
}

function renderDashboardResults(container, data) {
    const p = data.portfolio || {};
    const g = data.guard || {};
    const t = data.trade || {};
    const ex = data.execution_result || {};
    const c_data = data.climate_data || {};
    const explanation = data.explanation || 'No explanation available.';
    const guardStatus = g.status || 'UNKNOWN';

    // Portfolio holdings
    const holdingsHTML = (p.holdings || []).map(h => {
        const price = STOCK_PRICES[h.ticker?.toUpperCase()] || (h.shares > 0 ? (h.allocated_value / h.shares) : 0);
        const priceStr = price > 0 ? formatCurrency(price) : '—';
        return `<div class="trade-row">
            <div>
                <div style="font-weight:700;letter-spacing:0.04em">${h.ticker}</div>
                <div style="font-size:0.72rem;color:#a8ff3e;margin-top:2px;font-family:'JetBrains Mono',monospace">${priceStr}<span style="color:var(--muted-text);margin-left:4px">/share</span></div>
            </div>
            <div style="font-size:0.8rem;color:var(--muted-text);text-align:right">
                ${h.shares} sh · ${(h.weight * 100).toFixed(1)}%
            </div>
            <span class="trade-chip chip-buy">${formatCurrency(h.allocated_value)}</span>
        </div>`;
    }).join('') || '<div style="color:var(--muted-text)">No holdings allocated.</div>';

    // Violations
    const violations = g.violations || [];
    const mods = g.modifications || [];
    const violationsHTML = violations.length
        ? violations.map(v => `<div style="color:#ff6666;font-size:0.78rem;margin-bottom:4px;">• ${v}</div>`).join('')
        : '<div style="color:#00ff88;font-size:0.78rem;">✓ No violations</div>';

    const hasViolations = (g.violations && g.violations.length > 0) || (t.status === 'INVALID');
    const alignmentText = hasViolations ? '❌ FAILED' : '✅ PASSED';
    const alignmentColor = hasViolations ? '#ff4444' : '#00ff88';

    const alignmentUI = `
        <div class="glass-card rounded-2xl" style="padding: 1rem 1.5rem; margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: space-between; border: 1px solid ${alignmentColor}40;">
            <span style="font-weight: 700; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem;">Constraint Alignment:</span>
            <span style="color: ${alignmentColor}; font-weight: 800; font-size: 0.9rem;">${alignmentText}</span>
        </div>
    `;

    container.innerHTML = alignmentUI + `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:1.5rem;">

            <div class="glass-card rounded-2xl sub-card">
                <h4 class="panel-title" style="font-size:0.8rem;margin-bottom:1rem;">📊 Portfolio Allocation</h4>
                <div style="margin-bottom:0.8rem;">
                    <span style="color:var(--muted-text);font-size:0.75rem;">BUDGET</span>
                    <div style="font-size:1.2rem;font-weight:700;color:var(--neon-lime)">${formatCurrency(p.total_budget || 0)}</div>
                </div>
                <div style="margin-bottom:1rem;">
                    <span style="color:var(--muted-text);font-size:0.75rem;">INVESTED / CASH</span>
                    <div style="font-size:0.95rem;font-weight:600;">${formatCurrency(p.invested_amount || 0)} / ${formatCurrency(p.cash_balance || 0)}</div>
                </div>
                ${holdingsHTML}
            </div>

            <div class="glass-card rounded-2xl sub-card">
                <h4 class="panel-title" style="font-size:0.8rem;margin-bottom:1rem;">🛡️ Guard Decision</h4>
                <div style="margin-bottom:1rem;">${guardBadge(guardStatus)}</div>
                <div style="font-size:0.8rem;color:var(--muted-text);margin-bottom:0.5rem;">Trade: <b style="color:#fff">${t.proposed_trade?.ticker || 'N/A'} — ${t.proposed_trade?.action?.toUpperCase() || ''} ${t.proposed_trade?.quantity || 0} shares</b></div>
                ${violationsHTML}
                ${mods.length ? mods.map(m => `<div style="color:#ffcc00;font-size:0.78rem;margin-top:4px;">✏️ ${m}</div>`).join('') : ''}
            </div>
        </div>
    `;

    // Update the persistent Explanation Panel
    const explanationEl = document.getElementById('explanation-text')
        || document.querySelector('.explanation-panel .explanation-text');
    if (explanationEl) {
        explanationEl.innerHTML = `> ${explanation}`;
    }

    // Update the persistent Execution Bar
    const execStatusEl = document.getElementById('execution-status-text')
        || document.querySelector('.execution-bar div[style*="font-weight:700"]')
        || document.querySelector('.execution-bar div[style*="font-weight: 700"]');
    if (execStatusEl) {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

        let execStatus = ex.status || 'PENDING';
        if (!ex.status && guardStatus === 'BLOCKED') execStatus = 'BLOCKED_BY_GUARD';

        const color =
            execStatus === 'EXECUTED'         ? '#00ff88'
          : execStatus === 'SKIPPED'          ? '#ffcc00'
          : execStatus === 'REJECTED'         ? '#ff4444'
          : execStatus.includes('BLOCK')      ? '#ff4444'
          : '#888';

        const detail = execStatus === 'EXECUTED'
            ? ` | ${ex.ticker} × ${ex.quantity} @ $${ex.price}  |  Total: $${(ex.total_cost || 0).toLocaleString()}`
            : ex.reason ? ` — ${ex.reason}` : '';

        execStatusEl.style.color = color;
        execStatusEl.innerHTML = `STATUS: ${execStatus} ${timeStr} EST${detail}`;

        const modeLabel = document.getElementById('alpaca-mode-label');
        if (modeLabel) {
            modeLabel.innerText = execStatus === 'EXECUTED_LIVE_PAPER' ? 'ALPACA LIVE PAPER MODE' : 'ALPACA SIMULATION MODE';
            modeLabel.style.color = execStatus === 'EXECUTED_LIVE_PAPER' ? '#00d2ff' : 'inherit';
        }
    }

    const orchDiv = document.getElementById("orchestration");
    if (orchDiv && data.orchestration) {
        let traceHtml = `<h4 class="panel-title" style="margin-bottom:1rem; font-size:0.8rem">📡 Agent Execution Trace</h4>`;
        data.orchestration.forEach((step, i) => {
            const agentName = step.agent.charAt(0).toUpperCase() + step.agent.slice(1);
            const statusName = step.status.charAt(0).toUpperCase() + step.status.slice(1);
            let color = '#ffcc00'; // Skipping yellow
            if (step.status === 'completed' || step.status === 'executed') color = '#00ff88'; // Green
            if (step.status === 'blocked') color = '#ff4444'; // Red

            traceHtml += `
                <div style="font-family:'JetBrains Mono', monospace; font-size:0.85rem; margin-bottom:6px;">
                    <span style="color:var(--muted-text)">Step ${i + 1}: ${agentName} &rarr; </span>
                    <span style="color:${color}; font-weight:700;">${statusName}</span>
                </div>
            `;
        });
        orchDiv.innerHTML = traceHtml;
        orchDiv.style.display = 'block';
    }

    // --- Rebuild Lower Grid Dynamically ---
    const f = data.financial_data || {};
    const sim = data.simulation || {};
    // Fallback: find by ID first, then by class selector (handles cached HTML without ID)
    const lowerGrid = document.getElementById('lower-grid-container') || document.querySelector('.lower-grid');

    if (lowerGrid) {
        const volPct = f.volatility !== undefined ? (f.volatility * 100).toFixed(1) : '—';
        const volBarWidth = f.volatility !== undefined ? Math.min(parseFloat(volPct) * 3, 100) : 40;
        const drawdownPct = (sim.value_at_risk_95 && p.total_budget)
            ? '-' + ((sim.value_at_risk_95 / p.total_budget) * 100).toFixed(1) + '%'
            : '—';
        const marketRisk = f.market_risk_score !== undefined ? f.market_risk_score.toFixed(1) : '—';

        const pt = t.proposed_trade || {};
        const action = (pt.action || 'buy').toUpperCase();
        const cls = action === 'BUY' ? 'chip-buy' : action === 'HOLD' ? 'chip-hold' : 'chip-avoid';

        const guardStatusLocal = g.status || 'UNKNOWN';
        const guardCssClass = guardStatusLocal === 'APPROVED' ? 'status-approved' : guardStatusLocal === 'BLOCKED' ? 'status-blocked' : 'status-modified';
        const guardIconEmoji = guardStatusLocal === 'APPROVED' ? '🛡️' : guardStatusLocal === 'BLOCKED' ? '🚫' : '⚠️';
        const guardDecision = g.decision || (guardStatusLocal === 'APPROVED' ? 'Portfolio modification checks passed.' : 'Trade prevented due to policy violations.');

        lowerGrid.innerHTML = `
            <!-- Risk Metrics -->
            <section class="glass-card rounded-2xl sub-card">
                <h4 class="panel-title" style="margin-bottom:1rem; font-size:0.8rem">Risk Analysis</h4>
                <div class="metric-row">
                    <div style="font-size:0.85rem">Volatility (30D)</div>
                    <div style="font-size:1.1rem; font-weight:700; color:${parseFloat(volPct) > 20 ? '#ff4444' : parseFloat(volPct) > 12 ? '#ffcc00' : '#00ff88'}">${volPct}%</div>
                </div>
                <div class="volatility-bar">
                    <div class="bar-fill" style="width:${volBarWidth}%"></div>
                </div>
                <div class="metric-row" style="margin-top:1.5rem">
                    <div style="font-size:0.85rem">Max Drawdown</div>
                    <div style="color:#ff4444; font-weight:700">${drawdownPct}</div>
                </div>
                <div class="metric-row" style="margin-top:0.5rem">
                    <div style="font-size:0.85rem">Market Risk Score</div>
                    <div style="font-weight:700; color:#ffcc00">${marketRisk}</div>
                </div>
                <svg class="sparkline-svg">
                    <polyline points="0,30 20,25 40,35 60,15 80,38 100,28 120,32 140,40 160,20 180,35 200,25 220,30 240,10" fill="none" stroke="#a8ff3e" stroke-width="2" />
                </svg>
            </section>

            <!-- Trade Insights -->
            <section class="glass-card rounded-2xl sub-card">
                <h4 class="panel-title" style="margin-bottom:1rem; font-size:0.8rem">Trade Recommendation</h4>
                ${pt.ticker ? `
                <div class="trade-row">
                    <div style="font-weight:700">${pt.ticker}</div>
                    <span class="trade-chip ${cls}">${action}</span>
                </div>
                <div style="font-size:0.75rem; color:var(--muted-text); margin-top:8px;">Qty: ${pt.quantity || 0} shares</div>
                <div style="font-size:0.75rem; color:var(--muted-text); margin-top:4px;">Sector: ${pt.sector || 'N/A'}</div>
                <div style="font-size:0.75rem; color:var(--muted-text); margin-top:4px;">Est. Cost: ${formatCurrency(t.estimated_cost || 0)}</div>
                ` : '<div style="color:var(--muted-text); font-size:0.8rem">No trade proposed.</div>'}
            </section>

            <!-- Guard Result -->
            <section class="glass-card rounded-2xl sub-card guard-status ${guardCssClass}">
                <h4 class="panel-title" style="margin-bottom:1rem; font-size:0.8rem; color:inherit">Sentinel Guard Rails</h4>
                <div style="font-size:3rem">${guardIconEmoji}</div>
                <div class="status-text">${guardStatusLocal}</div>
                <p style="font-size:0.75rem; margin-top:8px">${guardDecision}</p>
                ${(g.violations || []).length ? `<div style="font-size:0.72rem; color:#ff6666; margin-top:6px">⚠ ${g.violations.join(' | ')}</div>` : ''}
            </section>
        `;
    }

    // --- Update Dynamic Global Climate Resilience Gauge ---
    if (c_data.green_score !== undefined) {
        const scoreValEl = document.getElementById('climate-resilience-score');
        const gaugeEl = document.getElementById('gauge-progress');
        if (scoreValEl && gaugeEl) {
            const sc = Math.round(c_data.green_score);
            scoreValEl.innerHTML = `${sc}<span style="font-size:0.8rem; font-weight:400">/100</span>`;
            // Total arc length of the semi-circle (R=80) is ~251.2
            // Offset logic: 251.2 is entirely empty, 0 is entirely full
            const offset = 251.2 * (1 - (c_data.green_score / 100));
            gaugeEl.style.strokeDashoffset = offset.toString();
        }
    }
}

// ─────────────────────────────────────────
//  PAGE: pipeline.html
// ─────────────────────────────────────────

function initPipeline() {
    const runBtn = document.getElementById('run-pipeline-btn');
    const pipelineOutput = document.getElementById('pipeline-output');
    if (!runBtn || !pipelineOutput) return;

    runBtn.addEventListener('click', async () => {
        const budget = parseFloat(document.getElementById('pipe-budget')?.value || 100000);
        const risk_level = document.getElementById('pipe-risk')?.value || 'moderate';
        const max_trade = parseFloat(document.getElementById('pipe-max-trade')?.value || 50000);
        const sectorsRaw = document.getElementById('pipe-avoid')?.value || '';
        const avoid_sectors = sectorsRaw.split(',').map(s => s.trim()).filter(Boolean);

        pipelineOutput.style.display = 'block';
        runBtn.disabled = true;
        runBtn.style.opacity = '0.6';

        const pipeSteps = [
            '[ SENTINEL ]  Initializing orchestration pipeline...',
            '[ CLIMATE AGENT ]  Filtering assets by ESG constraints...',
            '[ FINANCIAL AGENT ]  Assessing market risk and return projections...',
            '[ SIMULATION ]  Executing Monte Carlo scenarios across 100 paths...',
            '[ PORTFOLIO ]  Applying ESG-weighted asset allocation...',
            '[ TRADER ]  Proposing intent from climate-approved assets...',
            '[ GUARD ]  Running policy enforcement rules...',
            '[ EXPLAINER ]  Generating AI reasoning log...'
        ];

        pipelineOutput.innerHTML = `<div id="pipe-boot-log" style="font-family:'JetBrains Mono',monospace; font-size:0.78rem; color:var(--neon-lime); line-height:2; padding:1.2rem 1.5rem; background:rgba(0,0,0,0.4); border-radius:12px; border:1px solid rgba(168,255,62,0.15);"><div style="color:#a8ff3e; font-weight:800; font-size:0.9rem; margin-bottom:1rem; letter-spacing:0.05em;">⚡ SENTINEL PIPELINE INITIALIZING...</div></div>`;
        const pipeLog = document.getElementById('pipe-boot-log');

        // Animation promise — each step appears at i * 500ms, guaranteed
        const pipeAnimPromise = new Promise(resolve => {
            pipeSteps.forEach((step, i) => {
                setTimeout(() => {
                    const line = document.createElement('div');
                    line.style.cssText = 'opacity:0; transition:opacity 0.4s ease; padding:3px 0; color:var(--neon-lime);';
                    line.textContent = '> ' + step;
                    pipeLog.appendChild(line);
                    void line.offsetHeight; // force reflow
                    line.style.opacity = '1';

                    if (i === pipeSteps.length - 1) {
                        setTimeout(() => {
                            const done = document.createElement('div');
                            done.style.cssText = 'color:#00ffcc; font-weight:700; margin-top:10px; opacity:0; transition:opacity 0.4s ease;';
                            done.textContent = '> [PIPELINE COMPLETE] Building visualization...';
                            pipeLog.appendChild(done);
                            void done.offsetHeight;
                            done.style.opacity = '1';
                            setTimeout(resolve, 700);
                        }, 500);
                    }
                }, i * 500);
            });
        });

        // Fire API in parallel
        const pipeApiPromise = runAnalysis({ budget, risk_level, max_trade, avoid_sectors });

        try {
            const [data] = await Promise.all([pipeApiPromise, pipeAnimPromise]);
            renderPipelineResults(pipelineOutput, data);
        } catch (err) {
            showError(pipelineOutput, err.message);
        } finally {
            runBtn.disabled = false;
            runBtn.style.opacity = '1';
        }
    });
}

function renderPipelineResults(container, data) {
    const stages = [
        {
            label: '🌿 Climate Analysis',
            key: 'climate_data',
            render: d => `
                <div>Green Score: <b style="color:var(--neon-lime)">${d.green_score}/100</b></div>
                <div style="font-size:0.78rem;color:var(--muted-text);margin-top:4px;">Sectors avoided: ${d.avoided_sectors_applied.join(', ') || 'None'}</div>
                <div style="font-size:0.78rem;color:var(--muted-text);">Eligible assets: ${(d.eligible_assets || []).map(a => a.ticker).join(', ')}</div>
            `
        },
        {
            label: '💹 Financial Analysis',
            key: 'financial_data',
            render: d => `
                <div>Sentiment: <b>${d.market_sentiment}</b></div>
                <div style="font-size:0.78rem;color:var(--muted-text);margin-top:4px;">Expected Return: <span style="color:#00ffcc">${(d.expected_return * 100).toFixed(2)}%</span></div>
                <div style="font-size:0.78rem;color:var(--muted-text);">Volatility: <span style="color:#ffcc00">${(d.volatility * 100).toFixed(1)}%</span></div>
            `
        },
        {
            label: '📦 Portfolio',
            key: 'portfolio',
            render: d => `
                <div>Invested: <b style="color:var(--neon-lime)">${formatCurrency(d.invested_amount)}</b> of ${formatCurrency(d.total_budget)}</div>
                <div style="font-size:0.78rem;color:var(--muted-text);margin-top:4px;">${(d.holdings || []).map(h => `${h.ticker} × ${h.shares}`).join('  |  ')}</div>
            `
        },
        {
            label: '📤 Trade Proposal',
            key: 'trade',
            render: d => {
                if (d.status === 'INVALID') {
                    return `<div style="color:#ffcc00; font-size:0.85rem;">No valid trade generated due to constraints</div>`;
                }
                const pt = d.proposed_trade || {};
                return `<div>${pt.action?.toUpperCase()} <b>${pt.ticker}</b> × ${pt.quantity}</div>
                <div style="font-size:0.78rem;color:var(--muted-text);margin-top:4px;">Estimated Cost: ${formatCurrency(d.estimated_cost)}</div>`;
            }
        },
        {
            label: '🛡️ Guard Decision',
            key: 'guard',
            render: d => `
                <div>${guardBadge(d.status)}</div>
                <div style="font-size:0.78rem;color:var(--muted-text);margin-top:8px;">${d.decision}</div>
                ${(d.violations || []).map(v => `<div style="color:#ff6666;font-size:0.78rem;">• ${v}</div>`).join('')}
                ${(d.modifications || []).map(m => `<div style="color:#ffcc00;font-size:0.78rem;">✏️ ${m}</div>`).join('')}
            `
        },
        {
            label: '📈 Simulation',
            key: 'simulation',
            render: d => d.impact ? `<div style="color:#888">${d.impact}</div>` : `
                <div>1Y Value: <b style="color:var(--neon-lime)">${formatCurrency(d.expected_1y_value)}</b> (${d.estimated_return_pct > 0 ? '+' : ''}${d.estimated_return_pct}%)</div>
                <div style="font-size:0.78rem;color:var(--muted-text);margin-top:4px;">VaR (95%): ${formatCurrency(d.value_at_risk_95)} | Drawdown prob: ${(d.drawdown_probability * 100).toFixed(1)}%</div>
            `
        },
        {
            label: '⚡ Execution',
            key: 'execution_result',
            render: d => {
                if (d.status === 'EXECUTED') {
                    return `
                        <div>${guardBadge('APPROVED')}</div>
                        <div style="font-size:0.78rem;margin-top:8px;display:grid;gap:4px;">
                            <div>Ticker: <b style="color:#fff">${d.ticker}</b></div>
                            <div>Qty: <b style="color:#fff">${d.quantity} shares @ $${d.price}</b></div>
                            <div>Total: <b style="color:var(--neon-lime)">${formatCurrency(d.total_cost)}</b></div>
                            <div style="color:var(--muted-text);font-size:0.72rem">Trade ID: ${d.trade_id || '—'}</div>
                        </div>`;
                }
                const badge = d.status === 'REJECTED'
                    ? guardBadge('BLOCKED')
                    : `<span style="display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;background:rgba(255,204,0,0.1);border:1px solid rgba(255,204,0,0.3);color:#ffcc00;font-weight:700;font-size:0.8rem;">⏭️ ${d.status}</span>`;
                return `
                    <div>${badge}</div>
                    <div style="font-size:0.78rem;color:var(--muted-text);margin-top:8px;">${d.reason || ''}</div>`;
            }
        },
        {
            label: '🧠 Explanation',
            key: 'explanation',
            render: d => `<div style="font-size:0.82rem;line-height:1.7;color:#ccc;white-space:pre-wrap;">> ${d}</div>`
        }
    ];

    let flowHtml = '';
    if (data.orchestration) {
        flowHtml = `<div class="glass-card" style="padding:1.5rem; margin-bottom:2rem; border-radius:12px; display:flex; flex-wrap:wrap; gap:12px; align-items:center; justify-content:center;">`;
        data.orchestration.forEach((step, i) => {
            let icon = '✅';
            let color = '#00ff88';
            if (step.status === 'blocked') { icon = '❌'; color = '#ff4444'; }
            else if (step.status === 'skipped') { icon = '⏭'; color = '#ffcc00'; }

            const capAgent = step.agent.charAt(0).toUpperCase() + step.agent.slice(1);
            const capStatus = step.status.charAt(0).toUpperCase() + step.status.slice(1);

            flowHtml += `
                <div style="background:rgba(0,0,0,0.4); border:1px solid ${color}40; border-radius:8px; padding:10px 16px; font-family:'JetBrains Mono', monospace; font-size:0.8rem; color:#fff; display:flex; flex-direction:column; align-items:center; min-width:110px;">
                    <span style="font-weight:700; margin-bottom:6px;">[ ${capAgent} ]</span>
                    <span style="color:${color}; font-size:0.7rem; display:flex; align-items:center; gap:4px;">${icon} ${capStatus}</span>
                </div>
            `;
            if (i < data.orchestration.length - 1) {
                flowHtml += `<span style="color:var(--muted-text); font-weight:800; font-size:1.2rem;">→</span>`;
            }
        });
        flowHtml += `</div>`;
    }

    container.innerHTML = flowHtml + '<div style="display:flex;flex-direction:column;gap:1.5rem;">' +
        stages.map((stage, i) => {
            const val = data[stage.key];
            const hasData = val !== undefined && val !== null;
            return `
            <div style="display:flex;gap:1rem;align-items:flex-start;">
                <div style="display:flex;flex-direction:column;align-items:center;min-width:40px;">
                    <div style="width:36px;height:36px;border-radius:50%;background:rgba(168,255,62,0.15);border:2px solid var(--neon-lime);display:flex;align-items:center;justify-content:center;font-weight:800;color:var(--neon-lime);font-size:0.85rem;">${i + 1}</div>
                    ${i < stages.length - 1 ? '<div style="width:2px;flex:1;min-height:30px;background:rgba(168,255,62,0.2);margin-top:4px;"></div>' : ''}
                </div>
                <div class="glass-card" style="flex:1;padding:1rem 1.2rem;border-radius:12px;margin-bottom:0;">
                    <div style="font-size:0.8rem;font-weight:700;color:var(--neon-lime);margin-bottom:0.6rem;">${stage.label}</div>
                    ${hasData ? stage.render(val) : '<div style="color:var(--muted-text);font-size:0.78rem;">No data</div>'}
                </div>
            </div>`;
        }).join('') +
        '</div>';

    // Update Bento Cards dynamically
    const f = data.financial_data || {};
    const c = data.climate_data || {};
    const sim = data.simulation || {};
    const p = data.portfolio || {};
    const t = data.trade || {};
    const g = data.guard || {};
    const expl = data.explanation || '';

    const pipeClimate = document.getElementById('pipe-climate-card');
    if (pipeClimate) {
        const carbonScore = c.green_score || 82;
        const waterScore = Math.floor(Math.random() * 50 + 30);
        const govScore = Math.floor(Math.random() * 20 + 70);
        const socialScore = Math.floor(Math.random() * 20 + 60);

        const r1 = (carbonScore/100)*60;
        const r2 = (waterScore/100)*60;
        const r3 = (govScore/100)*60;
        const r4 = (socialScore/100)*60;
        const radarPolygon = `80,${80-r1} ${80+r2},80 80,${80+r3} ${80-r4},80`;

        pipeClimate.innerHTML = `
            <h4 class="panel-title" style="font-size: 0.8rem">Climate Analysis Radar</h4>
            <div class="radar-container">
                <svg width="160" height="160" viewBox="0 0 160 160">
                    <polygon points="80,20 140,80 80,140 20,80" fill="none" stroke="rgba(255,255,255,0.05)" />
                    <polygon points="80,40 120,80 80,120 40,80" fill="none" stroke="rgba(255,255,255,0.05)" />
                    <polygon points="80,60 100,80 80,100 60,80" fill="none" stroke="rgba(255,255,255,0.05)" />
                    <polygon points="${radarPolygon}" fill="rgba(168, 255, 62, 0.2)" stroke="var(--neon-lime)" stroke-width="2" />
                </svg>
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; font-size:0.7rem; color:var(--muted-text); margin-top:1rem">
                <span>Carbon: ${carbonScore}</span>
                <span>Water: ${waterScore}</span>
                <span>Gov: ${govScore}</span>
                <span>Social: ${socialScore}</span>
            </div>
        `;
    }

    const pipeFinancial = document.getElementById('pipe-financial-card');
    if (pipeFinancial) {
        const retPct = f.expected_return ? (f.expected_return * 100).toFixed(1) : 0;

        let candleHTML = '';
        const numCandles = 5;
        const isPositive = (f.expected_return || 0) >= 0;
        for (let i=0; i<numCandles; i++) {
            const isUp = i === numCandles - 1 ? isPositive : (Math.random() > 0.5);
            const height = Math.max(10, Math.random() * 40 + 10);
            const wickHeight = height + Math.random() * 20;
            const topOffset = - (wickHeight - height) / 2;
            const bg = isUp ? '#00ff88' : '#ff4444';
            candleHTML += `<div style="width:8px; height:${height}px; background:${bg}; position:relative;"><div style="width:2px; height:${wickHeight}px; background:${bg}; position:absolute; left:3px; top:${topOffset}px;"></div></div>`;
        }

        pipeFinancial.innerHTML = `
            <h4 class="panel-title" style="font-size: 0.8rem">Financial Indicators</h4>
            <div style="margin: 1.5rem 0">
                <div style="display:flex; justify-content:space-between; margin-bottom:12px">
                    <span style="font-size:0.8rem">Est Return</span>
                    <span style="font-weight:700; color:#00ff88">${retPct > 0 ? '+' : ''}${retPct}%</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:12px">
                    <span style="font-size:0.8rem">Sentiment</span>
                    <span style="font-weight:700">${f.market_sentiment || 'Neutral'}</span>
                </div>
                <!-- Dynamic Candlestick Visual -->
                <div style="display:flex; align-items:flex-end; gap:8px; height:60px; margin-bottom:15px">
                    ${candleHTML}
                </div>
                <div style="display:flex; gap:4px">
                    <div style="flex:1; height:4px; background:#00ff88;"></div>
                    <div style="flex:1; height:4px; background:#00ff88;"></div>
                    <div style="flex:1; height:4px; background:#ffcc00;"></div>
                    <div style="flex:1; height:4px; background:rgba(255,255,255,0.1);"></div>
                </div>
                <span style="font-size:0.6rem; color:var(--muted-text); margin-top:5px; display:block;">MOMENTUM INDICATOR</span>
            </div>
        `;
    }

    const pipeSim = document.getElementById('pipe-simulation-card');
    if (pipeSim) {
        let pathsHtml = '';
        const endYBase = sim.expected_1y_value && p.total_budget ? 100 - ((sim.expected_1y_value - p.total_budget) / p.total_budget)*100 : 70; 

        for(let i=0; i<5; i++) {
            const endY = endYBase + (Math.random()-0.5)*80;
            const ctrlX = 150 + (Math.random()-0.5)*50;
            const ctrlY = 100 + (Math.random()-0.5)*100;
            pathsHtml += `<path d="M0 100 Q ${ctrlX} ${ctrlY} 300 ${endY}" fill="none" stroke="rgba(168, 255, 62, 0.05)" />`;
        }
        pathsHtml += `<path d="M0 100 Q 150 100 300 ${endYBase}" fill="none" stroke="var(--neon-lime)" stroke-width="2" />`;
        pathsHtml += `<path d="M0 100 Q 150 40 300 ${endYBase - 40} L 300 ${endYBase + 40} Q 150 110 0 100" fill="rgba(168, 255, 62, 0.03)" />`;

        const drawdown = sim.drawdown_probability ? (sim.drawdown_probability * 100).toFixed(1) : 0;
        pipeSim.innerHTML = `
            <h4 class="panel-title" style="font-size: 0.8rem">Monte Carlo Simulation</h4>
            <div class="monte-carlo-container">
                <svg width="100%" height="160" preserveAspectRatio="none">
                    ${pathsHtml}
                </svg>
            </div>
            <div style="font-size:0.75rem; text-align:center; margin-top:10px">
                Drawdown Probability: <b style="color:#ffcc00">${drawdown}%</b><br>
                <span style="color:var(--muted-text);font-size:0.7rem">Estimated Value: ${formatCurrency(sim.expected_1y_value || 0)}</span>
            </div>
        `;
    }

    const pipeAllocation = document.getElementById('pipe-allocation-card');
    if (pipeAllocation) {
        const holdings = p.holdings || [];
        const colors = ['#a8ff3e', '#00d2ff', '#ffd200', '#ff4444', '#b026ff'];
        let svgCircles = '';
        let offset = 0;
        const circumference = 282.7;

        if (holdings.length === 0) {
            svgCircles = `<circle r="45" cx="60" cy="60" fill="transparent" stroke="#333" stroke-width="12" stroke-dasharray="282.7 282.7" stroke-dashoffset="0" />`;
        } else {
            holdings.forEach((h, i) => {
                const strokeArr = Math.max(0.1, (h.weight * circumference)).toFixed(1);
                svgCircles += `<circle r="45" cx="60" cy="60" fill="transparent" stroke="${colors[i % colors.length]}" stroke-width="12" stroke-dasharray="${strokeArr} 282.7" stroke-dashoffset="${-offset}" />`;
                offset += (h.weight * circumference);
            });
        }

        const holdingsText = holdings.map(h => `${h.ticker}: ${(h.weight * 100).toFixed(0)}%`).join(' | ');
        pipeAllocation.innerHTML = `
             <h4 class="panel-title" style="font-size: 0.8rem">Allocation Weight</h4>
             <div class="donut-container" style="width:140px; height:140px; margin: 0 auto;">
                <svg width="120" height="120" viewBox="0 0 120 120">
                    ${svgCircles}
                </svg>
             </div>
             <div style="font-size:0.7rem; color:var(--muted-text); text-align:center; margin-top:10px">${holdingsText || 'N/A'}</div>
        `;
    }

    const pipeTrade = document.getElementById('pipe-trade-card');
    if (pipeTrade) {
        const pt = t.proposed_trade || {};
        pipeTrade.innerHTML = `
            <h4 class="panel-title" style="font-size: 0.8rem">Trade Decision Output</h4>
            <div class="execute-text">
                EXECUTE: ${(pt.action || 'HOLD').toUpperCase()} ${pt.quantity || 0} shares ${pt.ticker || 'N/A'}
            </div>
            <p style="font-size: 0.7rem; color:var(--muted-text); margin-top:1rem">Sector Context: ${pt.sector || 'N/A'} | Est Risk Score: ${pt.risk_score || 'N/A'}</p>
        `;
    }

    const pipeGuard = document.getElementById('pipe-guard-card');
    if (pipeGuard) {
        const status = g.status || 'UNKNOWN';
        const isApproved = status === 'APPROVED';
        const color = isApproved ? '#00ff88' : status === 'BLOCKED' ? '#ff4444' : '#ffcc00';
        const icon = isApproved ? '✅' : status === 'BLOCKED' ? '🚫' : '⚠️';
        pipeGuard.style.borderColor = color;
        pipeGuard.innerHTML = `
            <h4 class="panel-title" style="font-size: 0.8rem">ArmourIQ Guard</h4>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            <div style="font-weight: 800; color: ${color}; margin: 10px 0;">${status} ${icon}</div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; color: var(--muted-text);">
                ${g.violations?.length ? g.violations[0].substring(0, 50) + '...' : 'Checks Passed'}<br>
                TS: ${new Date().toISOString().replace('T', ' ').substring(0, 19)} UTC
            </div>
        `;
    }

    const pipeLog = document.getElementById('pipe-reasoning-log');
    if (pipeLog) {
        const sections = expl.split(/<br>/g).filter(s => s.trim().length > 0);
        let logHtml = '';
        sections.forEach((s, idx) => {
            const opacity = 1 - (idx * 0.2);
            logHtml += `<p style="opacity: ${Math.max(opacity, 0.4)}; margin-bottom: 8px;">> ${s.replace('>', '').trim()}</p>`;
        });
        pipeLog.innerHTML = logHtml;
    }
}

// ─────────────────────────────────────────
//  PAGE: simulator.html
// ─────────────────────────────────────────

function initSimulator() {
    const runBtn = document.getElementById('run-sim-btn');
    const simOutput = document.getElementById('sim-api-output');
    if (!runBtn) return;

    // Existing visual path generation (kept as-is)
    const svgGroup = document.querySelector('#path-group');
    const amountSlider = document.querySelector('#sim-amount-slider');
    const amountDisplay = document.querySelector('#display-amount');
    const durationSlider = document.querySelector('#sim-duration-slider');
    const durationText = document.querySelector('#duration-text');

    if (amountSlider) {
        amountSlider.addEventListener('input', (e) => {
            amountDisplay.innerText = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(e.target.value);
        });
    }
    if (durationSlider) {
        durationSlider.addEventListener('input', (e) => { durationText.innerText = `${e.target.value} Months`; });
    }

    const generatePaths = () => {
        if (!svgGroup) return;
        svgGroup.innerHTML = '';
        const startX = 50, startY = 350, endX = 950;
        for (let i = 0; i < 80; i++) {
            let d = `M ${startX} ${startY}`, cy = startY;
            const vol = 12 + Math.random() * 8, drift = -1.2 + (Math.random() - 0.5) * 0.5;
            for (let x = startX + 50; x <= endX; x += 50) {
                cy += (Math.random() - 0.5) * vol * 8 + drift;
                cy = Math.min(440, Math.max(60, cy));
                d += ` L ${x} ${cy}`;
            }
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', d);
            path.setAttribute('class', 'mc-path-sim');
            path.setAttribute('fill', 'none');
            path.style.cssText = `stroke-dasharray:2000;stroke-dashoffset:2000;animation:pathDraw 1.2s ease-out forwards ${Math.random() * 0.6}s`;
            svgGroup.appendChild(path);
        }
    };

    generatePaths();

    runBtn.addEventListener('click', async () => {
        runBtn.style.transform = 'scale(0.95)';
        setTimeout(() => { runBtn.style.transform = 'scale(1)'; }, 100);
        generatePaths();

        // API Call
        const budget = parseFloat(amountSlider?.value || 50000);
        const activeRisk = document.querySelector('.pill-btn.active');
        const riskLabel = activeRisk ? activeRisk.innerText.toLowerCase().replace('conservative', 'low').replace('moderate', 'moderate').replace('aggressive', 'high') : 'moderate';

        if (!simOutput) return;
        simOutput.style.display = 'block';
        setLoading(simOutput, true);

        try {
            const data = await runSimulation({ parameters: { budget }, scenario: riskLabel });
            renderSimulationResults(simOutput, data, budget);
        } catch (err) {
            showError(simOutput, err.message);
        }
    });

    // Pill button toggle
    const pillBtns = document.querySelectorAll('.pill-btn');
    pillBtns.forEach(btn => btn.addEventListener('click', () => {
        pillBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }));
}

function renderSimulationResults(container, data, budget) {
    const ret = data.estimated_return_pct || 0;
    const varVal = data.value_at_risk_95 || 0;
    const drawdown = data.drawdown_probability || 0;
    const expVal = data.expected_1y_value || budget;

    // Update KPI cards if they exist
    const kpiCards = document.querySelectorAll('.kpi-value');
    if (kpiCards.length >= 4) {
        kpiCards[0].innerText = `${(100 - drawdown * 100).toFixed(0)}%`;
        kpiCards[1].innerText = `${ret > 0 ? '+' : ''}${ret}%`;
        kpiCards[2].innerText = `-${((varVal / budget) * 100).toFixed(1)}%`;
        kpiCards[3].innerText = `+${(ret * 1.5).toFixed(1)}%`;
    }

    container.innerHTML = `
        <div class="glass-card" style="padding:1.2rem;border-radius:12px;">
            <div style="font-size:0.8rem;font-weight:700;color:var(--neon-lime);margin-bottom:0.8rem;">📡 Live Simulation Results</div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;text-align:center;">
                <div>
                    <div style="font-size:0.7rem;color:var(--muted-text);">EXPECTED 1Y VALUE</div>
                    <div style="font-size:1.1rem;font-weight:800;color:var(--neon-lime)">${formatCurrency(expVal)}</div>
                </div>
                <div>
                    <div style="font-size:0.7rem;color:var(--muted-text);">ESTIMATED RETURN</div>
                    <div style="font-size:1.1rem;font-weight:800;color:#00ffcc">${ret > 0 ? '+' : ''}${ret}%</div>
                </div>
                <div>
                    <div style="font-size:0.7rem;color:var(--muted-text);">VALUE AT RISK (95%)</div>
                    <div style="font-size:1.1rem;font-weight:800;color:#ff4444">-${formatCurrency(varVal)}</div>
                </div>
            </div>
            <div style="margin-top:1rem;font-size:0.75rem;color:var(--muted-text);text-align:center;">
                Drawdown probability: <b style="color:#ffcc00">${(drawdown * 100).toFixed(1)}%</b> &nbsp;|&nbsp; Scenario: ${data.scenario || 'Standard 1Y Drift'}
            </div>
        </div>`;

    // Update Risk Indicators dynamically if they exist
    const riskStack = document.getElementById('sim-risk-stack');
    if (riskStack) {
        const sharpe = data.sharpe_ratio || 2.14;
        const sortino = data.sortino_ratio || 2.88;
        const beta = data.beta || 1.12;
        const varPct = data.value_at_risk_95 ? ((data.value_at_risk_95 / budget) * 100).toFixed(1) : 4.2;

        riskStack.innerHTML = `
            <div class="risk-item">
                <div class="indicator-label">
                    <span>SHARPE RATIO</span>
                    <span style="color:var(--neon-lime)">${sharpe}</span>
                </div>
                <div class="indicator-bar">
                    <div class="indicator-fill" style="width: ${Math.min(sharpe * 30, 100)}%"></div>
                </div>
            </div>

            <div class="risk-item">
                <div class="indicator-label">
                    <span>SORTINO RATIO</span>
                    <span style="color:var(--neon-lime)">${sortino}</span>
                </div>
                <div class="indicator-bar">
                    <div class="indicator-fill" style="width: ${Math.min(sortino * 25, 100)}%"></div>
                </div>
            </div>

            <div class="risk-item">
                <div class="indicator-label">
                    <span>BETA (MARKET)</span>
                    <span style="color:#00ffcc">${beta}</span>
                </div>
                <div class="indicator-bar">
                    <div class="indicator-fill" style="width: ${Math.min(beta * 50, 100)}%; background: #00ffcc"></div>
                </div>
            </div>

            <div class="risk-item">
                <div class="indicator-label">
                    <span>VAR (VALUE AT RISK)</span>
                    <span style="color:#ff4444">${varPct}%</span>
                </div>
                <div class="indicator-bar">
                    <div class="indicator-fill" style="width: ${Math.min(parseFloat(varPct) * 5, 100)}%; background: #ff4444"></div>
                </div>
            </div>
        `;
    }
}

// ─────────────────────────────────────────
//  PAGE: guard.html
// ─────────────────────────────────────────

function initGuard() {
    const btnValidate = document.getElementById('btn-validate');
    const resultApproved = document.getElementById('result-approved');
    const resultBlocked = document.getElementById('result-blocked');
    const resultModified = document.getElementById('result-modified');
    const terminalLog = document.getElementById('terminal-log');
    const tickerInput = document.getElementById('test-ticker');
    const qtyInput = document.getElementById('test-qty');
    const sectorInput = document.getElementById('test-sector');

    if (!btnValidate) return;

    // Load policies on startup
    loadPolicies();

    const addLogEntry = (type, message, cssClass) => {
        const now = new Date();
        const timeStr = now.toTimeString().split(' ')[0];
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.innerHTML = `<span class="log-time">[${timeStr}]</span> <span class="${cssClass}">${type}: ${message}</span>`;
        terminalLog.appendChild(entry);
        terminalLog.scrollTop = terminalLog.scrollHeight;
    };

    const hideAllResults = () => {
        [resultApproved, resultBlocked, resultModified].forEach(el => { if (el) el.classList.remove('show'); });
    };

    // Risk card toggle
    const riskCards = document.querySelectorAll('.risk-card');
    riskCards.forEach(card => card.addEventListener('click', () => {
        riskCards.forEach(c => c.classList.remove('active'));
        card.classList.add('active');
    }));

    btnValidate.addEventListener('click', async () => {
        hideAllResults();
        btnValidate.style.transform = 'scale(0.95)';
        setTimeout(() => { btnValidate.style.transform = ''; }, 100);

        const ticker = (tickerInput?.value || 'AAPL').toUpperCase();
        const qty = parseInt(qtyInput?.value || 10);
        const sector = sectorInput?.value || 'Technology';
        const avoidSectors = document.getElementById('avoid-sectors-input')?.value
            ?.split(',').map(s => s.trim()).filter(Boolean) || [];
        const maxTrade = parseFloat(document.getElementById('max-trade-guard')?.value || 50000);

        addLogEntry('PENDING', `Validating ${ticker} × ${qty} shares...`, 'log-info-text');
        btnValidate.disabled = true;

        try {
            const result = await validateTrade({
                trade: { ticker, quantity: qty, action: 'buy', sector },
                avoid_sectors: avoidSectors
            });

            setTimeout(() => {
                const status = result.status;
                if (status === 'APPROVED') {
                    if (resultApproved) resultApproved.classList.add('show');
                    addLogEntry('APPROVED', `${ticker} passed all Guard checkpoints.`, 'log-approved-text');
                } else if (status === 'BLOCKED') {
                    if (resultBlocked) {
                        resultBlocked.classList.add('show');
                        const reason = document.getElementById('blocked-reason');
                        if (reason) reason.innerText = (result.violations || []).join(' | ') || 'Policy violation detected.';
                    }
                    addLogEntry('BLOCKED', `${ticker} — ${(result.violations || []).join(' | ')}`, 'log-blocked-text');
                } else if (status === 'MODIFIED') {
                    if (resultModified) {
                        resultModified.classList.add('show');
                        const reason = document.getElementById('modified-reason');
                        if (reason) reason.innerText = (result.modifications || []).join(' | ') || 'Trade was modified to fit constraints.';
                    }
                    addLogEntry('MODIFIED', `${ticker} — ${(result.modifications || []).join(' | ')}`, 'log-modified-text');
                }
            }, 300);
        } catch (err) {
            addLogEntry('ERROR', err.message === 'BACKEND_UNREACHABLE' ? 'Backend not reachable' : err.message, 'log-blocked-text');
        } finally {
            btnValidate.disabled = false;
        }
    });
}

async function loadPolicies() {
    const parentContainer = document.getElementById('policies-container');
    // For backwards compatibility, if someone has old json-block
    const targetEl = parentContainer || document.querySelector('.json-block');
    if (!targetEl) return;

    try {
        const data = await getPolicies();
        const policies = data.active_policies || [];
        targetEl.innerHTML = policies.map(p =>
            `<div class="risk-card active" style="padding: 0.8rem; margin-bottom: 0.5rem; display: flex; flex-direction: column; gap: 4px; pointer-events: none;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="font-weight: 700; color: #fff;">${p.name}</div>
                    <span style="font-size: 0.6rem; background: rgba(168,255,62,0.1); color: var(--neon-lime); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(168,255,62,0.2);">ID: ${p.id}</span>
                </div>
                <div style="font-size: 0.75rem; color: var(--muted-text); line-height: 1.4;">${p.description}</div>
            </div>`
        ).join('');
    } catch (err) {
        if (targetEl) targetEl.innerHTML = `<div style="font-size: 0.8rem; color: #ff4444; padding: 1rem; text-align: center;">Failed to load policies. API Offline.</div>`;
    }
}

// ─────────────────────────────────────────
//  PAGE: insights.html
// ─────────────────────────────────────────

function initInsights() {
    const insightsOutput = document.getElementById('insights-climate-output');
    if (!insightsOutput) return;

    loadClimateInsights(insightsOutput);

    const refreshBtn = document.getElementById('refresh-climate-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => loadClimateInsights(insightsOutput));
    }
}

async function loadClimateInsights(container) {
    setLoading(container, true);
    try {
        const data = await getClimateScores();
        renderClimateInsights(container, data);
    } catch (err) {
        showError(container, err.message);
    }
}

function renderClimateInsights(container, data) {
    const assets = data.eligible_assets || [];
    const score = data.green_score || 0;
    const color = score >= 80 ? '#00ff88' : score >= 60 ? '#a8ff3e' : score >= 40 ? '#ffcc00' : '#ff4444';

    const rows = assets.map(a => {
        const s = a.climate_score;
        const barColor = s >= 80 ? '#00ff88' : s >= 60 ? '#a8ff3e' : s >= 40 ? '#ffcc00' : '#ff4444';
        const rating = s >= 80 ? 'AAA' : s >= 60 ? 'AA' : s >= 40 ? 'BBB' : 'B';
        return `
            <tr>
                <td style="font-weight:700">${a.ticker}</td>
                <td><div style="font-size:0.75rem;color:var(--muted-text)">${a.sector}</div></td>
                <td>
                    <div class="esg-bar-container"><div class="esg-bar" style="width:${s}%;background:${barColor};"></div></div>
                </td>
                <td><span class="pill-esg" style="color:${barColor}">${rating}</span></td>
                <td style="font-weight:700;color:${barColor}">${s}/100</td>
                <td><span style="font-size:0.75rem;color:var(--muted-text)">${a.risk_level}</span></td>
            </tr>`;
    }).join('');

    container.innerHTML = `
        <div class="glass-card rounded-2xl" style="padding:1.5rem;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;">
                <h3 class="panel-title" style="margin:0;">🌿 Live Climate Scores</h3>
                <div style="font-size:1.4rem;font-weight:800;color:${color}">Portfolio Green Score: ${score}/100</div>
            </div>
            <table class="esg-table" style="width:100%;">
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Sector</th>
                        <th>Climate Score</th>
                        <th>Rating</th>
                        <th>Score</th>
                        <th>Risk Level</th>
                    </tr>
                </thead>
                <tbody>${rows || '<tr><td colspan="6" style="color:var(--muted-text)">No assets available.</td></tr>'}</tbody>
            </table>
            ${data.avoided_sectors_applied?.length ? `<div style="margin-top:1rem;font-size:0.78rem;color:var(--muted-text);">Sectors avoided: <b style="color:#ffcc00">${data.avoided_sectors_applied.join(', ')}</b></div>` : ''}
        </div>`;
}

// ─────────────────────────────────────────
//  PAGE: insights.html
// ─────────────────────────────────────────

async function initInsights() {
    const btnRefresh = document.getElementById('refresh-climate-btn');
    if (!btnRefresh) return;

    // UI elements
    const cEsgTbody = document.getElementById('insights-esg-tbody');
    const cSector = document.getElementById('insights-sector-container');
    const cHeatmap = document.getElementById('insights-heatmap-container');
    const cAlerts = document.getElementById('insights-alerts-container');
    const cScatter = document.getElementById('insights-scatter-dots');

    const gaugeScore = document.getElementById('gauge-score');
    const gaugeLabel = document.getElementById('gauge-label');
    const gaugeCircle = document.getElementById('gauge-circle');
    const subscores = document.getElementById('insights-subscores');

    async function loadData() {
        try {
            btnRefresh.disabled = true;
            btnRefresh.textContent = 'Refreshing...';

            // Pull the actual holdings state for true dynamic sector exposure
            let userHoldings = [];
            try {
                const portData = await portfolioValue(); // Uses Sentinel Portfolio agent
                if (portData && portData.holdings && portData.holdings.length > 0) {
                    userHoldings = portData.holdings.map(h => ({ ticker: h.ticker, weight: h.weight * 100 }));
                }
            } catch (e) {
                console.warn('Could not fetch true portfolio for insights fallback', e);
            }
            const data = await apiFetch('/insights', 'POST', { portfolio: userHoldings });

            // 1. Portfolio Gauge & Breakdown
            const pt = data.portfolio_rating;
            gaugeScore.textContent = pt;
            gaugeLabel.textContent = data.portfolio_status;
            gaugeCircle.style.strokeDasharray = `${(pt / 100) * 408} 408`;

            subscores.innerHTML = Object.entries(data.scores).map(([k, v]) => `
                <div class="breakdown-row">
                    <span style="text-transform: capitalize;">${k.replace('_', ' ')}</span>
                    <div class="bd-bar-track"><div class="h-bar-fill ${v >= 80 ? 'safe' : v >= 50 ? 'warn' : 'danger'}" style="--w: ${v}%;"></div></div>
                    <span class="bd-bar-val">${v}</span>
                </div>
            `).join('');

            // 2. Alerts
            cAlerts.innerHTML = data.alerts.map(a => `
                <div class="insight-alert ${a.status}">
                    <span class="icon">${a.icon}</span>
                    <div class="insight-alert-text">${a.text}</div>
                </div>
            `).join('');

            // 3. ESG Table
            cEsgTbody.innerHTML = data.assets.map(a => `
                <tr>
                    <td style="font-weight:700">${a.ticker}</td>
                    <td>
                        <div class="esg-bar-container"><div class="esg-bar" style="width: ${a.esg_score}%; background: ${a.esg_score >= 80 ? '#00ff88' : a.esg_score >= 60 ? '#a8ff3e' : a.esg_score >= 40 ? '#ffcc00' : '#ff4444'};"></div></div>
                    </td>
                    <td><span class="pill-esg" style="color:${a.esg_score >= 80 ? '#00ff88' : a.esg_score >= 60 ? '#a8ff3e' : a.esg_score >= 40 ? '#ffcc00' : '#ff4444'}">${a.rating}</span></td>
                </tr>
            `).join('');

            // 4. Sectors
            cSector.innerHTML = data.sectors.map(s => {
                const highlight = s.is_heavy ? 'style="color:#ff4444"' : '';
                return `
                <div class="h-bar-row">
                    <div class="h-bar-label" ${highlight}>${s.sector}</div>
                    <div class="h-bar-track" style="position: relative;">
                        <div class="h-bar-fill ${s.status}" style="--w: ${Math.min(100, s.weight)}%"></div>
                        <div style="position:absolute; top:-2px; bottom:-2px; width:2px; background:#fff; left: ${s.limit}%; z-index:2; box-shadow: 0 0 5px #fff;" title="Limit: ${s.limit}%"></div>
                    </div>
                    <div class="h-bar-value" ${highlight}>${s.weight}% <span style="font-size:0.55rem; color:var(--muted-text)">/ ${s.limit}%</span></div>
                </div>`;
            }).join('');

            // 5. Heatmap
            let heatmapHtml = `
                <div></div>
                <div class="hm-col-label">Carbon</div>
                <div class="hm-col-label">Water</div>
                <div class="hm-col-label">Waste</div>
                <div class="hm-col-label">Trans.</div>
                <div class="hm-col-label">Phys.</div>
            `;
            const clr = val => val === 'Low' ? 'hm-green' : val === 'Med' ? 'hm-yellow' : 'hm-red';
            data.assets.slice(0, 5).forEach(a => {
                heatmapHtml += `
                    <div class="hm-row-label">${a.ticker}</div>
                    <div class="hm-cell ${clr(a.carbon)}" data-tooltip="Carbon: ${a.carbon}"></div>
                    <div class="hm-cell ${clr(a.water)}" data-tooltip="Water: ${a.water}"></div>
                    <div class="hm-cell ${clr(a.waste)}" data-tooltip="Waste: ${a.waste}"></div>
                    <div class="hm-cell ${clr(a.transition)}" data-tooltip="Transition: ${a.transition}"></div>
                    <div class="hm-cell ${clr(a.physical)}" data-tooltip="Physical: ${a.physical}"></div>
                `;
            });
            cHeatmap.innerHTML = heatmapHtml;

            // 6. Scatter Dots
            // Map risk (0-100 -> left to right)
            // Map return (5-45 -> bottom to top) => Return goes roughly from 0 to 50
            cScatter.innerHTML = data.assets.map(a => {
                const x = a.risk_score;
                const y = Math.min(100, Math.max(0, ((a.exp_return) / 50) * 100));
                const color = a.esg_score >= 80 ? '#00ff88' : a.esg_score >= 60 ? '#a8ff3e' : a.esg_score >= 40 ? '#ffcc00' : '#ff4444';
                return `<div class="scatter-dot" style="left: ${x}%; top: ${100 - y}%; color: ${color};" data-ticker="${a.ticker}" title="${a.ticker} | Ret: ${a.exp_return}% | Risk: ${a.risk_score}"></div>`;
            }).join('');

        } catch (e) {
            console.error(e);
            cAlerts.innerHTML = `<div class="insight-alert danger"><span class="icon">❌</span><div class="insight-alert-text">Failed to fetch dynamic insights. Is the backend running?</div></div>`;
        } finally {
            btnRefresh.textContent = '🔄 Refresh Live Data';
            btnRefresh.disabled = false;
        }
    }

    btnRefresh.addEventListener('click', loadData);

    // Auto load
    loadData();
}

// ─────────────────────────────────────────
//  PAPER TRADING — initPaperTrading()
// ─────────────────────────────────────────

async function initPaperTrading() {
    const statusEl      = document.getElementById('pt-status');
    const cashEl        = document.getElementById('pt-cash');
    const holdingsValEl = document.getElementById('pt-holdings-val');
    const totalEl       = document.getElementById('pt-total');
    const holdingsTable = document.getElementById('pt-holdings-table');
    const btnBuy        = document.getElementById('btn-buy');
    const btnSell       = document.getElementById('btn-sell');

    if (!btnBuy) return;

    const fmt    = n  => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(n);
    const fmtPct = n  => (n >= 0 ? '+' : '') + Number(n).toFixed(2) + '%';
    const pnlColor = n => n >= 0 ? '#00ff88' : '#ff4444';

    // ── refresh portfolio display using /portfolio/performance ────────────────
    async function refreshPortfolio() {
        try {
            const d = await portfolioPerformance();

            // Headline numbers
            if (cashEl)        cashEl.innerText        = fmt(d.cash || d.cash_balance || 0);
            if (holdingsValEl) holdingsValEl.innerText = fmt(d.holdings_value || 0);
            if (totalEl)       totalEl.innerText       = fmt(d.total_value || 0);

            // ── Build performance sub-header (P&L + best/worst + win rate) ──
            let perfBar = '';
            if (d.trade_count > 0) {
                const pnlSign  = (d.overall_pnl || 0) >= 0 ? '+' : '';
                const pnlClr   = pnlColor(d.overall_pnl || 0);

                const bestHtml = d.best_performer
                    ? `<span style="color:#00ff88">▲ ${d.best_performer.ticker} ${fmtPct(d.best_performer.pnl_pct)}</span>`
                    : '—';
                const worstHtml = d.worst_performer
                    ? `<span style="color:#ff4444">▼ ${d.worst_performer.ticker} ${fmtPct(d.worst_performer.pnl_pct)}</span>`
                    : '—';
                const winHtml = d.win_rate_pct !== null && d.win_rate_pct !== undefined
                    ? `<span style="color:#ffcc00">Win ${d.win_rate_pct}%</span>`
                    : '';

                perfBar = `
                <div style="
                    display:flex; align-items:center; gap:1.5rem;
                    font-family:'JetBrains Mono',monospace; font-size:0.72rem;
                    padding:10px 16px; margin-bottom:12px;
                    background:rgba(0,0,0,0.3); border-radius:10px;
                    border:1px solid rgba(255,255,255,0.06);
                ">
                    <div>
                        <div style="color:var(--muted-text);font-size:0.6rem;letter-spacing:.05em;margin-bottom:2px">UNREALIZED P&L</div>
                        <div style="color:${pnlClr};font-weight:800">${pnlSign}${fmt(d.overall_pnl || 0)}
                            <span style="font-weight:400;color:${pnlClr};font-size:0.68rem">(${fmtPct(d.overall_pnl_pct || 0)})</span>
                        </div>
                    </div>
                    <div style="width:1px;height:32px;background:rgba(255,255,255,0.08)"></div>
                    <div style="display:flex;gap:1rem">
                        <div><div style="color:var(--muted-text);font-size:0.6rem;margin-bottom:2px">BEST</div>${bestHtml}</div>
                        <div><div style="color:var(--muted-text);font-size:0.6rem;margin-bottom:2px">WORST</div>${worstHtml}</div>
                        ${winHtml ? `<div><div style="color:var(--muted-text);font-size:0.6rem;margin-bottom:2px">WIN RATE</div>${winHtml}</div>` : ''}
                    </div>
                    <div style="margin-left:auto;color:var(--muted-text);font-size:0.62rem">${d.trade_count} trade(s)</div>
                </div>`;
            }

            // ── Holdings table ────────────────────────────────────────────────
            if (holdingsTable) {
                if (!d.holdings || d.holdings.length === 0) {
                    holdingsTable.innerHTML = perfBar +
                        '<div style="color:var(--muted-text);font-size:0.75rem">No holdings yet. Execute your first trade.</div>';
                } else {
                    const rows = d.holdings.map(h => `
                        <div style="
                            display:grid;
                            grid-template-columns:80px 60px 95px 95px 95px auto;
                            gap:6px; padding:8px 0;
                            border-bottom:1px solid rgba(255,255,255,0.04);
                            align-items:center; font-size:0.8rem;
                        ">
                            <span style="color:#fff;font-weight:700">${h.ticker}</span>
                            <span style="color:var(--muted-text)">${h.quantity}</span>
                            <span style="color:var(--muted-text)">${fmt(h.avg_cost)}</span>
                            <span style="color:var(--neon-lime)">${fmt(h.current_price)}</span>
                            <span>${fmt(h.market_value)}</span>
                            <span style="color:${pnlColor(h.pnl)};font-weight:700;text-align:right">
                                ${fmtPct(h.pnl_pct)}
                                <span style="font-weight:400;font-size:0.7rem;margin-left:4px">(${fmt(h.pnl)})</span>
                            </span>
                        </div>`).join('');

                    holdingsTable.innerHTML = perfBar + `
                        <div style="
                            display:grid;
                            grid-template-columns:80px 60px 95px 95px 95px auto;
                            gap:6px; color:var(--muted-text);
                            font-size:0.62rem; text-transform:uppercase; letter-spacing:.05em;
                            padding-bottom:6px; border-bottom:1px solid rgba(255,255,255,0.06);
                            margin-bottom:4px;
                        ">
                            <span>Ticker</span><span>Qty</span><span>Avg Cost</span>
                            <span>Live Price</span><span>Mkt Value</span><span style="text-align:right">P&L</span>
                        </div>
                        ${rows}`;
                }
            }
        } catch (e) {
            if (statusEl) {
                statusEl.innerText = 'Could not load portfolio. Is the backend running?';
                statusEl.style.color = '#ff4444';
            }
        }
    }

    // ── Execute trade via the Execution Agent (POST /execute) ─────────────────
    async function doTrade(action) {
        const ticker = (document.getElementById('pt-ticker')?.value || '').toUpperCase().trim();
        const qty    = parseFloat(document.getElementById('pt-qty')?.value || 0);

        if (!ticker || qty <= 0) {
            statusEl.innerText   = '⚠ Enter a valid ticker and quantity.';
            statusEl.style.color = '#ffcc00';
            return;
        }

        btnBuy.disabled  = true;
        btnSell.disabled = true;
        statusEl.style.color = 'var(--muted-text)';
        statusEl.innerText   = `⏳ Processing ${action} ${qty}× ${ticker}...`;

        try {
            // Auto-provision portfolio if first visit
            try { await portfolioInit(); } catch (_) {}

            // Route through the Execution Agent
            const result = await executeViaAgent({ ticker, action, quantity: qty });

            const clr = action === 'BUY' ? '#00ff88' : '#ff4444';
            statusEl.style.color = clr;
            statusEl.innerHTML   =
                `✓ ${action} ${result.quantity}× <b>${result.ticker}</b> ` +
                `@ ${fmt(result.price)} — ` +
                `Total: <b>${fmt(result.total_cost)}</b> ` +
                `<span style="color:var(--muted-text);font-size:0.7rem">| ID: ${result.trade_id?.slice(0,8)}…</span>`;

            await refreshPortfolio();
        } catch (e) {
            statusEl.style.color = '#ff4444';
            statusEl.innerText   = `✗ ${e.message || 'Trade failed.'}`;
        } finally {
            btnBuy.disabled  = false;
            btnSell.disabled = false;
        }
    }

    btnBuy.addEventListener('click',  () => doTrade('BUY'));
    btnSell.addEventListener('click', () => doTrade('SELL'));

    // Load existing portfolio on page open
    try { await portfolioInit(); } catch (_) {}
    await refreshPortfolio();
}


// ─────────────────────────────────────────
//  INIT ROUTER — detect page by element presence
// ─────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('run-analysis-btn')) initDashboard();
    if (document.getElementById('run-pipeline-btn')) initPipeline();
    // Start paper trading (simulator logic is handled inline in simulator.html)
    if (document.getElementById('run-sim-btn')) initPaperTrading();
    if (document.getElementById('btn-validate')) initGuard();
    if (document.getElementById('refresh-climate-btn')) initInsights();
});
