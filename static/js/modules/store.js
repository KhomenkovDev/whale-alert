class Store {
    constructor(initial = {}) {
        this.state = { ...initial }
        this.listeners = {}
    }

    get(key) {
        return this.state[key]
    }

    set(key, value) {
        this.state[key] = value
        this._notify(key, value)
    }

    update(key, partial) {
        const current = this.state[key]
        if (typeof current === 'object' && current !== null) {
            this.state[key] = { ...current, ...partial }
            this._notify(key, this.state[key])
        }
    }

    on(key, fn) {
        ;(this.listeners[key] = this.listeners[key] || []).push(fn)
        return () => this._off(key, fn)
    }

    _notify(key, value) {
        ;(this.listeners[key] || []).forEach(fn => fn(value, key))
    }

    _off(key, fn) {
        this.listeners[key] = (this.listeners[key] || []).filter(f => f !== fn)
    }
}

export const store = new Store({
    transactions: [],
    selectedChain: 'ALL',
    connectionStatus: 'disconnected',
    stats: { total_whales: 0, total_volume: 0, avg_size: 0 },
})
