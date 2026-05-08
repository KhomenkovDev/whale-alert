document.addEventListener('DOMContentLoaded', () => {
    const tableBody      = document.getElementById('whale-table-body');
    const statusBadge    = document.getElementById('connection-status');
    const statusText     = statusBadge.querySelector('.status-text');
    const chainBadge     = document.getElementById('live-chain-badge');
    const reportPanel    = document.getElementById('report-panel-body');

    const totalWhalesEl  = document.getElementById('stat-total-whales');
    const totalVolumeEl  = document.getElementById('stat-total-volume');
    const avgSizeEl      = document.getElementById('stat-avg-size');

    const CHAIN_NAMES = { ALL: 'All Chains', ETH: 'Ethereum', BNB: 'BNB Chain', POL: 'Polygon', AVAX: 'Avalanche' };
    const CHAIN_ICONS = { ETH: '⟠', BNB: '◈', POL: '⬡', AVAX: '△' };

    let socket;
    let activeChain = 'ALL';
    let selectedTxId = null;

    // ── Chain Selector ─────────────────────────────────────────────
    document.querySelectorAll('.chain-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.chain-btn').forEach(b => {
                b.className = 'chain-btn';
            });
            const chain = btn.dataset.chain;
            btn.classList.add('active-' + chain.toLowerCase());
            activeChain = chain;

            if (chainBadge) chainBadge.textContent = 'Live Network: ' + CHAIN_NAMES[chain];

            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: 'set_chain', chain: chain === 'ALL' ? '' : chain }));
            }

            resetReportPanel();
            updateStats();
        });
    });

    // ── WebSocket ───────────────────────────────────────────────────
    function connect() {
        socket = new WebSocket(WHALE_WS_URL);

        socket.onopen = () => {
            statusBadge.classList.remove('disconnected');
            statusBadge.classList.add('connected');
            statusText.textContent = 'Connected Live';
            // Send current chain filter on reconnect
            if (activeChain !== 'ALL') {
                socket.send(JSON.stringify({ type: 'set_chain', chain: activeChain }));
            }
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'history') {
                renderHistory(data.transactions);
                updateStats();
            } else if (data.type === 'new_whale') {
                addNewWhale(data.transaction);
                updateStats();
            }
        };

        socket.onclose = () => {
            statusBadge.classList.remove('connected');
            statusBadge.classList.add('disconnected');
            statusText.textContent = 'Disconnected';
            setTimeout(connect, 5000);
        };

        socket.onerror = (err) => {
            console.error('WebSocket error:', err);
            socket.close();
        };
    }

    // ── Render Helpers ──────────────────────────────────────────────
    function renderHistory(transactions) {
        if (!transactions || transactions.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="empty-state">
                        <div class="empty-icon"><i class="fa-solid fa-satellite-dish"></i></div>
                        <p>No whale transactions detected yet.</p>
                    </td>
                </tr>`;
            return;
        }
        tableBody.innerHTML = '';
        transactions.forEach(tx => tableBody.appendChild(createRow(tx)));
    }

    function addNewWhale(tx) {
        const empty = tableBody.querySelector('.empty-state');
        if (empty) tableBody.innerHTML = '';
        tableBody.insertBefore(createRow(tx, true), tableBody.firstChild);
        if (tableBody.children.length > 60) tableBody.removeChild(tableBody.lastChild);
        updateStats();
    }

    function createRow(tx, isNew = false) {
        const tr = document.createElement('tr');
        tr.className = 'whale-row' + (isNew ? ' new-row' : '');
        tr.dataset.id = tx.id;

        const time = new Date(tx.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const chainIcon = CHAIN_ICONS[tx.chain] || '';

        tr.innerHTML = `
            <td>
                <span class="chain-tag ${tx.chain}">
                    <span>${chainIcon}</span> ${tx.chain}
                </span>
            </td>
            <td>
                <div class="amount-badge">
                    <i class="fa-solid fa-circle-dollar-to-slot"></i>
                    ${tx.usd_value_formatted}
                </div>
                <div style="font-size:0.75rem;color:var(--text-secondary);margin-top:2px">${tx.token_symbol}</div>
            </td>
            <td>
                <a href="${tx.explorer_url}" target="_blank" class="tx-hash-link" onclick="event.stopPropagation()">
                    ${tx.short_tx}
                </a>
            </td>
            <td class="hide-mobile"><span class="address-tag" title="${tx.from_address}">${tx.short_from}</span></td>
            <td class="hide-mobile"><span class="address-tag" title="${tx.to_address}">${tx.short_to}</span></td>
            <td><span class="time-stamp">${time}</span></td>
        `;

        tr.addEventListener('click', () => selectTransaction(tx, tr));
        return tr;
    }

    // ── Transaction Selection & Report ─────────────────────────────
    function selectTransaction(tx, tr) {
        document.querySelectorAll('.whale-row').forEach(r => r.classList.remove('selected'));
        tr.classList.add('selected');
        selectedTxId = tx.id;
        loadReport(tx);
    }

    function resetReportPanel() {
        selectedTxId = null;
        document.querySelectorAll('.whale-row').forEach(r => r.classList.remove('selected'));
        reportPanel.innerHTML = `
            <div class="report-empty-state">
                <div class="report-empty-icon"><i class="fa-solid fa-magnifying-glass"></i></div>
                <p>Click any transaction to generate an AI-powered whale intelligence report.</p>
            </div>`;
    }

    async function loadReport(tx) {
        // If AI data already in the TX object (cached), render immediately
        if (tx.ai_summary) {
            renderReport(tx, {
                summary: tx.ai_summary,
                intent: tx.ai_intent,
                impact: tx.ai_impact,
                risk: tx.ai_risk,
                tags: tx.ai_tags ? tx.ai_tags.split(',') : [],
            });
            return;
        }

        reportPanel.innerHTML = `
            <div class="report-loading">
                <div class="spinner"></div>
                <p>Generating AI whale report…</p>
                <small style="color:var(--text-secondary);font-size:0.75rem;margin-top:4px;display:block">Analyzing on-chain signals</small>
            </div>`;

        try {
            const res = await fetch(`/api/report/${tx.id}/`, { method: 'POST' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const report = await res.json();
            renderReport(tx, report);
        } catch (err) {
            reportPanel.innerHTML = `
                <div class="report-empty-state" style="color:var(--error)">
                    <div class="report-empty-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
                    <p>Report generation failed.</p>
                    <small style="color:var(--text-secondary);font-size:0.75rem;margin-top:4px;display:block">${err.message}</small>
                </div>`;
        }
    }

    function renderReport(tx, report) {
        const riskClass = `risk-${report.risk || 'MEDIUM'}`;
        const tagsHtml = (report.tags || []).map(t => `<span class="report-tag">${t}</span>`).join('');
        const chainIcon = CHAIN_ICONS[tx.chain] || '';
        const chainName = CHAIN_NAMES[tx.chain] || tx.chain;
        const time = new Date(tx.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });

        reportPanel.innerHTML = `
            <div>
                <span class="report-tx-hash">${tx.tx_hash}</span>
                <div class="report-amount">${tx.usd_value_formatted}</div>
                <div class="report-meta">${tx.token_symbol} · <span class="chain-tag ${tx.chain}" style="font-size:0.75rem">${chainIcon} ${chainName}</span> · ${time}</div>

                <div class="report-section">
                    <div class="report-section-label">Summary</div>
                    <div class="report-section-text">${report.summary || '—'}</div>
                </div>

                <div class="report-section">
                    <div class="report-section-label">Whale Intent</div>
                    <div class="report-section-text">${report.intent || '—'}</div>
                </div>

                <div class="report-section">
                    <div class="report-section-label">Market Impact</div>
                    <div class="report-section-text">${report.impact || '—'}</div>
                </div>

                <div class="report-section">
                    <div class="report-section-label">Risk Level</div>
                    <span class="risk-badge ${riskClass}">${report.risk || 'MEDIUM'}</span>
                </div>

                <div class="report-section">
                    <div class="report-section-label">Signals</div>
                    <div class="report-tags">${tagsHtml}</div>
                </div>

                <a href="${tx.explorer_url}" target="_blank" class="report-explorer-link">
                    <i class="fa-solid fa-arrow-up-right-from-square"></i>
                    View on Explorer
                </a>
            </div>`;
    }

    // ── Stats ───────────────────────────────────────────────────────
    async function updateStats() {
        try {
            const chain = activeChain !== 'ALL' ? `?chain=${activeChain}` : '';
            const res = await fetch('/api/stats/' + chain);
            const data = await res.json();

            animateNumber(totalWhalesEl, data.total_count);
            totalVolumeEl.textContent = formatUSD(data.total_volume);
            avgSizeEl.textContent = formatUSD(data.avg_size);
        } catch (err) {
            console.error('Stats update failed:', err);
        }
    }

    function formatUSD(value) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
    }

    function animateNumber(el, end) {
        const start = parseInt(el.textContent.replace(/\D/g, '')) || 0;
        if (start === end) return;
        const dur = 800;
        const startTs = performance.now();
        const step = (ts) => {
            const p = Math.min((ts - startTs) / dur, 1);
            el.textContent = Math.floor(p * (end - start) + start).toLocaleString();
            if (p < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
    }

    // ── Init ────────────────────────────────────────────────────────
    resetReportPanel();
    connect();
});
