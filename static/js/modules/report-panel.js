const CHAIN_ICONS = { ETH: '⟠', BNB: '◈', POL: '⬡', AVAX: '△' }
const CHAIN_NAMES = { ALL: 'All Chains', ETH: 'Ethereum', BNB: 'BNB Chain', POL: 'Polygon', AVAX: 'Avalanche' }

export class ReportPanel {
    constructor(panelBody) {
        this.panelBody = panelBody
    }

    showLoading() {
        this.panelBody.innerHTML = `
            <div class="report-loading">
                <div class="spinner"></div>
                <p>Generating AI whale report…</p>
                <small class="report-loading-hint">Analyzing on-chain signals</small>
            </div>`
    }

    async load(tx) {
        if (tx.ai_summary) {
            this._renderReport(tx, {
                summary: tx.ai_summary,
                intent: tx.ai_intent,
                impact: tx.ai_impact,
                risk: tx.ai_risk,
                tags: tx.ai_tags ? tx.ai_tags.split(',') : [],
            })
            return
        }

        this.showLoading()

        try {
            const res = await fetch(`/api/report/${tx.id}/`, { method: 'POST' })
            if (!res.ok) throw new Error(`HTTP ${res.status}`)
            const report = await res.json()
            this._renderReport(tx, report)
        } catch (err) {
            this.panelBody.innerHTML = `
                <div class="report-empty-state" style="color:var(--error)">
                    <div class="report-empty-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>
                    <p>Report generation failed.</p>
                    <small class="report-error-hint">${err.message}</small>
                </div>`
        }
    }

    reset() {
        this.panelBody.innerHTML = `
            <div class="report-empty-state">
                <div class="report-empty-icon"><i class="fa-solid fa-magnifying-glass"></i></div>
                <p>Click any transaction to generate an AI-powered whale intelligence report.</p>
            </div>`
    }

    _renderReport(tx, report) {
        const riskClass = `risk-${report.risk || 'MEDIUM'}`
        const tagsHtml = (report.tags || []).map(t => `<span class="report-tag">${t}</span>`).join('')
        const chainIcon = CHAIN_ICONS[tx.chain] || ''
        const chainName = CHAIN_NAMES[tx.chain] || tx.chain
        const time = new Date(tx.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })

        this.panelBody.innerHTML = `
            <div>
                <span class="report-tx-hash" title="${tx.tx_hash}">${tx.tx_hash}</span>
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
            </div>`
    }
}
