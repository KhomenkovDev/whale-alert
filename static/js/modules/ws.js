import { store } from './store.js'

export class WebSocketManager {
    constructor(url) {
        this.url = url
        this.reconnectDelay = 1000
        this.maxReconnectDelay = 30000
        this._connect()
    }

    _connect() {
        if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
            return
        }

        this.socket = new WebSocket(this.url)

        this.socket.onopen = () => {
            this.reconnectDelay = 1000
            store.set('connectionStatus', 'connected')
            this._onReconnected()
        }

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                this._handleMessage(data)
            } catch (err) {
                console.error('WS parse error:', err)
            }
        }

        this.socket.onclose = () => {
            store.set('connectionStatus', 'disconnected')
            this._scheduleReconnect()
        }

        this.socket.onerror = () => {
            this.socket.close()
        }
    }

    _onReconnected() {
        const chain = store.get('selectedChain')
        if (chain !== 'ALL') {
            this.send({ type: 'set_chain', chain })
        }
    }

    _scheduleReconnect() {
        setTimeout(() => {
            this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay)
            this._connect()
        }, this.reconnectDelay)
    }

    _handleMessage(data) {
        if (data.type === 'history') {
            const existing = store.get('transactions')
            const merged = [...data.transactions]
            const hashes = new Set(merged.map(t => t.tx_hash))
            for (const tx of existing) {
                if (!hashes.has(tx.tx_hash)) {
                    merged.push(tx)
                }
            }
            merged.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            store.set('transactions', merged.slice(0, 500))
        } else if (data.type === 'new_whale') {
            const current = store.get('transactions')
            store.set('transactions', [data.transaction, ...current].slice(0, 500))
        }
    }

    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data))
        }
    }

    setChain(chain) {
        store.set('selectedChain', chain)
        this.send({ type: 'set_chain', chain: chain === 'ALL' ? '' : chain })
    }

    disconnect() {
        if (this.socket) {
            this.socket.onclose = null
            this.socket.close()
        }
    }
}
