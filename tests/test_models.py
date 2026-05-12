from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from core.models import CHAIN_COLORS, WhaleTransaction


class TestWhaleTransaction:
    def test_create_transaction(self, db):
        tx = WhaleTransaction.objects.create(
            tx_hash="0x" + "b" * 64,
            block_number=1,
            from_address="0x1111",
            to_address="0x2222",
            token_symbol="USDT",
            token_amount=Decimal("5000000"),
            usd_value=Decimal("5000000.00"),
            chain="ETH",
            timestamp=datetime.now(UTC),
        )
        assert tx.pk is not None
        assert tx.token_symbol == "USDT"

    def test_str_representation(self, sample_transaction):
        result = str(sample_transaction)
        assert "[ETH]" in result
        assert "$10,000,000" in result
        assert "USDC" in result

    def test_short_tx(self, sample_transaction):
        assert len(sample_transaction.short_tx) <= 12
        assert sample_transaction.short_tx.startswith("0x")

    def test_short_from(self, sample_transaction):
        short = sample_transaction.short_from
        assert "…" in short
        assert short.startswith("0x")

    def test_short_to(self, sample_transaction):
        short = sample_transaction.short_to
        assert "…" in short
        assert short.startswith("0x")

    def test_chain_color(self, sample_transaction):
        assert sample_transaction.chain_color == CHAIN_COLORS["ETH"]

    def test_chain_color_fallback(self, db):
        tx = WhaleTransaction.objects.create(
            tx_hash="0x" + "c" * 64,
            block_number=1,
            from_address="0x1111",
            to_address="0x2222",
            token_symbol="BTC",
            token_amount=Decimal("1000"),
            usd_value=Decimal("1000.00"),
            chain="UNKNOWN",
            timestamp=datetime.now(UTC),
        )
        assert tx.chain_color == "#A855F7"

    def test_explorer_url_computed(self, sample_transaction):
        url = sample_transaction.explorer_url_computed
        assert url.startswith("https://etherscan.io/tx/")

    def test_explorer_url_stored(self, sample_transaction):
        custom_url = "https://custom.explorer/tx/abc"
        sample_transaction.explorer_url = custom_url
        assert sample_transaction.explorer_url_computed == custom_url

    def test_to_dict(self, sample_transaction):
        data = sample_transaction.to_dict()
        assert data["id"] == sample_transaction.pk
        assert data["tx_hash"] == sample_transaction.tx_hash
        assert data["chain"] == "ETH"
        assert data["token_symbol"] == "USDC"

    def test_ordering(self, db, multi_chain_transactions):
        txs = WhaleTransaction.objects.all()
        timestamps = [tx.timestamp for tx in txs]
        assert timestamps == sorted(timestamps, reverse=True)
