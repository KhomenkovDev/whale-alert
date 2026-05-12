export class StatsPanel {
    constructor(els) {
        this.totalWhalesEl = els.totalWhales
        this.totalVolumeEl = els.totalVolume
        this.avgSizeEl = els.avgSize
        this.chainBadge = els.chainBadge
    }

    update(data) {
        this._animateNumber(this.totalWhalesEl, data.total_count)
        this.totalVolumeEl.textContent = this._formatUSD(data.total_volume)
        this.avgSizeEl.textContent = this._formatUSD(data.avg_size)
    }

    updateChainBadge(chain) {
        const names = { ALL: 'All Chains', ETH: 'Ethereum', BNB: 'BNB Chain', POL: 'Polygon', AVAX: 'Avalanche' }
        if (this.chainBadge) {
            this.chainBadge.textContent = 'Live Network: ' + (names[chain] || chain)
        }
    }

    _formatUSD(value) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
    }

    _animateNumber(el, end) {
        if (!el) return
        const start = parseInt(el.textContent.replace(/\D/g, '')) || 0
        if (start === end) return
        const dur = 800
        const startTs = performance.now()
        const step = (ts) => {
            const p = Math.min((ts - startTs) / dur, 1)
            el.textContent = Math.floor(p * (end - start) + start).toLocaleString()
            if (p < 1) requestAnimationFrame(step)
        }
        requestAnimationFrame(step)
    }
}
