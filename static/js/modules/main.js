import { store } from './store.js'
import { WebSocketManager } from './ws.js'
import { StatsPanel } from './stats-panel.js'
import { TransactionsTable } from './transactions-table.js'
import { ReportPanel } from './report-panel.js'

document.addEventListener('DOMContentLoaded', () => {
    const elements = {
        tableBody: document.getElementById('whale-table-body'),
        statusBadge: document.getElementById('connection-status'),
        statusText: document.querySelector('#connection-status .status-text'),
        chainBadge: document.getElementById('live-chain-badge'),
        reportPanel: document.getElementById('report-panel-body'),
        totalWhales: document.getElementById('stat-total-whales'),
        totalVolume: document.getElementById('stat-total-volume'),
        avgSize: document.getElementById('stat-avg-size'),
    }

    if (!elements.tableBody) return

    const reportPanel = new ReportPanel(elements.reportPanel)
    reportPanel.reset()

    const statsPanel = new StatsPanel(elements)
    const transactionsTable = new TransactionsTable(elements.tableBody, (tx) => {
        reportPanel.load(tx)
    })

    const ws = new WebSocketManager(window.WHALE_WS_URL)

    // Chain selector
    document.querySelectorAll('.chain-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.chain-btn').forEach(b => {
                b.className = 'chain-btn'
            })
            const chain = btn.dataset.chain
            btn.classList.add('active-' + chain.toLowerCase())
            ws.setChain(chain)
            statsPanel.updateChainBadge(chain)
            reportPanel.reset()
            _fetchStats()
        })
    })

    // Stats updates on tx changes
    store.on('transactions', () => _fetchStats())

    // Connection status updates
    store.on('connectionStatus', (status) => {
        if (elements.statusBadge && elements.statusText) {
            elements.statusBadge.classList.remove('connected', 'disconnected')
            elements.statusBadge.classList.add(status)
            elements.statusText.textContent = status === 'connected' ? 'Connected Live' : 'Disconnected'
        }
    })

    // Toast notification on new whale (dispatched from store)
    store.on('transactions', (txs) => {
        const lastCount = store.get('_lastTxCount') || 0
        if (txs.length > lastCount && lastCount > 0) {
            const newTx = txs[0]
            _showToast(`New whale: ${newTx.usd_value_formatted} ${newTx.token_symbol} on ${newTx.chain}`)
        }
        store.set('_lastTxCount', txs.length)
    })

    function _fetchStats() {
        const chain = store.get('selectedChain')
        const params = chain !== 'ALL' ? `?chain=${chain}` : ''
        fetch('/api/stats/' + params)
            .then(r => r.json())
            .then(data => statsPanel.update(data))
            .catch(err => console.error('Stats fetch error:', err))
    }

    // Theme toggle
    const savedTheme = localStorage.getItem('whale-theme') || 'dark'
    document.documentElement.setAttribute('data-theme', savedTheme)

    const themeToggle = document.getElementById('theme-toggle')
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme')
            const next = current === 'dark' ? 'light' : 'dark'
            document.documentElement.setAttribute('data-theme', next)
            localStorage.setItem('whale-theme', next)
            themeToggle.innerHTML = next === 'dark'
                ? '<i class="fa-solid fa-moon"></i>'
                : '<i class="fa-solid fa-sun"></i>'
        })
        themeToggle.innerHTML = savedTheme === 'dark'
            ? '<i class="fa-solid fa-moon"></i>'
            : '<i class="fa-solid fa-sun"></i>'
    }

    // Toast system
    function _showToast(message) {
        const container = document.getElementById('toast-container')
        if (!container) return
        const toast = document.createElement('div')
        toast.className = 'toast'
        toast.innerHTML = `
            <i class="fa-solid fa-water text-accent"></i>
            <span>${message}</span>
        `
        container.appendChild(toast)
        setTimeout(() => {
            toast.classList.add('toast-exit')
            setTimeout(() => toast.remove(), 300)
        }, 4000)
    }
})
