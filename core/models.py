from django.db import models

CHAIN_CHOICES = [
    ("ETH", "Ethereum"),
    ("BNB", "BNB Chain"),
    ("POL", "Polygon"),
    ("AVAX", "Avalanche"),
]

CHAIN_COLORS = {
    "ETH": "#627eea",
    "BNB": "#f0b90b",
    "POL": "#8247e5",
    "AVAX": "#e84142",
}

STABLECOINS = {"USDC", "USDT", "DAI", "BUSD"}


class WhaleTransaction(models.Model):
    tx_hash = models.CharField(max_length=66, unique=True, db_index=True)
    block_number = models.BigIntegerField()
    from_address = models.CharField(max_length=42)
    to_address = models.CharField(max_length=42)

    token_symbol = models.CharField(max_length=20, default="USDC")
    token_amount = models.DecimalField(max_digits=30, decimal_places=6)
    usd_value = models.DecimalField(max_digits=30, decimal_places=2)

    chain = models.CharField(max_length=10, choices=CHAIN_CHOICES, default="ETH", db_index=True)
    explorer_url = models.CharField(max_length=200, blank=True, default="")

    timestamp = models.DateTimeField()
    discovered_at = models.DateTimeField(auto_now_add=True)

    ai_summary = models.TextField(blank=True, default="")
    ai_intent = models.CharField(max_length=300, blank=True, default="")
    ai_impact = models.CharField(max_length=300, blank=True, default="")
    ai_risk = models.CharField(max_length=10, blank=True, default="")
    ai_tags = models.CharField(max_length=300, blank=True, default="")

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Whale Transaction"
        verbose_name_plural = "Whale Transactions"

    def __str__(self):
        return f"[{self.chain}] ${self.usd_value:,.0f} {self.token_symbol} — {self.tx_hash[:12]}…"

    @property
    def short_tx(self):
        return f"{self.tx_hash[:6]}…{self.tx_hash[-4:]}"

    @property
    def short_from(self):
        return f"{self.from_address[:6]}…{self.from_address[-4:]}"

    @property
    def short_to(self):
        return f"{self.to_address[:6]}…{self.to_address[-4:]}"

    @property
    def chain_color(self):
        return CHAIN_COLORS.get(self.chain, "#A855F7")

    @property
    def explorer_url_computed(self):
        if self.explorer_url:
            return self.explorer_url
        explorers = {
            "ETH": "https://etherscan.io/tx/",
            "BNB": "https://bscscan.com/tx/",
            "POL": "https://polygonscan.com/tx/",
            "AVAX": "https://snowtrace.io/tx/",
        }
        return explorers.get(self.chain, "https://etherscan.io/tx/") + self.tx_hash

    def to_dict(self):
        return {
            "id": self.pk,
            "tx_hash": self.tx_hash,
            "short_tx": self.short_tx,
            "block_number": self.block_number,
            "from_address": self.from_address,
            "short_from": self.short_from,
            "to_address": self.to_address,
            "short_to": self.short_to,
            "token_symbol": self.token_symbol,
            "token_amount": str(self.token_amount),
            "usd_value": str(self.usd_value),
            "usd_value_formatted": f"${float(self.usd_value):,.2f}",
            "timestamp": self.timestamp.isoformat(),
            "chain": self.chain,
            "chain_color": self.chain_color,
            "explorer_url": self.explorer_url_computed,
            "ai_summary": self.ai_summary,
            "ai_intent": self.ai_intent,
            "ai_impact": self.ai_impact,
            "ai_risk": self.ai_risk,
            "ai_tags": self.ai_tags,
        }


class ChainScanState(models.Model):
    chain = models.CharField(max_length=10, unique=True, choices=CHAIN_CHOICES)
    last_scanned_block = models.BigIntegerField(default=0)
    last_scanned_at = models.DateTimeField(auto_now=True)
    is_scanning = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Chain Scan State"
        verbose_name_plural = "Chain Scan States"

    def __str__(self):
        return f"{self.chain} @ block {self.last_scanned_block}"
