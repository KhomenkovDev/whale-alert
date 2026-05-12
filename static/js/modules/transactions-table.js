import { store } from './store.js'

const CHAIN_ICONS = { ETH: '⟠', BNB: '◈', POL: '⬡', AVAX: '△' }

export class TransactionsTable {
    constructor(tableBody, onTxSelect) {
        this.tableBody = tableBody
        this.onTxSelect = onTxSelect
        this.selectedId = null

        store.on('transactions', (txs) => this._render(txs))
        store.on('selectedChain', () => this._clearSelection())
    }

    _render(transactions) {
        if (!transactions || transactions.length === 0) {
            this.tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="empty-state">
                        <div class="empty-icon"><i class="fa-solid fa-satellite-dish"></i></div>
                        <p>No whale transactions detected yet.</p>
                    </td>
                </tr>`
            return
        }
        this.tableBody.innerHTML = ''
        for (const tx of transactions) {
            this.tableBody.appendChild(this._createRow(tx))
        }
        this._highlightSelected()
    }

    addNewWhale(tx) {
        const empty = this.tableBody.querySelector('.empty-state')
        if (empty) this.tableBody.innerHTML = ''
        const firstRow = this.tableBody.firstChild
        const row = this._createRow(tx, true)
        this.tableBody.insertBefore(row, firstRow)
        if (this.tableBody.children.length > 100) {
            this.tableBody.removeChild(this.tableBody.lastChild)
        }
    }

    _createRow(tx, isNew = false) {
        const tr = document.createElement('tr')
        tr.className = 'whale-row' + (isNew ? ' new-row' : '')
        tr.dataset.id = tx.id

        const time = new Date(tx.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
        const chainIcon = CHAIN_ICONS[tx.chain] || ''

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
                <div class="tx-token-sub">${tx.token_symbol}</div>
            </td>
            <td>
                <a href="${tx.explorer_url}" target="_blank" class="tx-hash-link" onclick="event.stopPropagation()">
                    ${tx.short_tx}
                </a>
            </td>
            <td class="hide-mobile"><span class="address-tag" title="${tx.from_address}">${tx.short_from}</span></td>
            <td class="hide-mobile"><span class="address-tag" title="${tx.to_address}">${tx.short_to}</span></td>
            <td><span class="time-stamp">${time}</span></td>
        `

        tr.addEventListener('click', () => {
            this.selectedId = tx.id
            this._highlightSelected()
            if (this.onTxSelect) this.onTxSelect(tx)
        })
        return tr
    }

    _highlightSelected() {
        this.tableBody.querySelectorAll('.whale-row').forEach(r => {
            r.classList.toggle('selected', r.dataset.id == this.selectedId)
        })
    }

    _clearSelection() {
        this.selectedId = null
        this.tableBody.querySelectorAll('.whale-row').forEach(r => r.classList.remove('selected'))
    }

    scrollToTop() {
        this.tableBody.parentElement?.scrollTo({ top: 0, behavior: 'smooth' })
    }
}
