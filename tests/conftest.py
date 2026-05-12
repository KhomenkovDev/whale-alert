from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from django.utils import timezone as django_tz

from core.models import WhaleTransaction


@pytest.fixture
def sample_transaction(db) -> WhaleTransaction:
    return WhaleTransaction.objects.create(
        tx_hash="0x" + "a" * 64,
        block_number=22_000_000,
        from_address="0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8",
        to_address="0x40B38765696e3d5d8d9d834D8AaD4bB6e418E489",
        token_symbol="USDC",
        token_amount=Decimal("10000000"),
        usd_value=Decimal("10000000.00"),
        timestamp=datetime.now(UTC),
        chain="ETH",
    )


@pytest.fixture
def multi_chain_transactions(db) -> list[WhaleTransaction]:
    txs = []
    chains = [
        ("ETH", Decimal("5000000.00")),
        ("BNB", Decimal("3000000.00")),
        ("POL", Decimal("2000000.00")),
        ("AVAX", Decimal("1000000.00")),
    ]
    for i, (chain, value) in enumerate(chains):
        tx = WhaleTransaction.objects.create(
            tx_hash="0x" + f"{i:064x}",
            block_number=22_000_000 - i,
            from_address=f"0x{i:040x}",
            to_address=f"0x{i + 10:040x}",
            token_symbol="USDC",
            token_amount=value,
            usd_value=value,
            timestamp=django_tz.now() - django_tz.timedelta(hours=i),
            chain=chain,
        )
        txs.append(tx)
    return txs


@pytest.fixture
def async_multi_chain_transactions(transactional_db) -> list[WhaleTransaction]:
    """Same as multi_chain_transactions but uses transactional_db for async tests."""
    txs = []
    chains = [
        ("ETH", Decimal("5000000.00")),
        ("BNB", Decimal("3000000.00")),
        ("POL", Decimal("2000000.00")),
        ("AVAX", Decimal("1000000.00")),
    ]
    for i, (chain, value) in enumerate(chains):
        tx = WhaleTransaction.objects.create(
            tx_hash="0x" + f"{i:064x}",
            block_number=22_000_000 - i,
            from_address=f"0x{i:040x}",
            to_address=f"0x{i + 10:040x}",
            token_symbol="USDC",
            token_amount=value,
            usd_value=value,
            timestamp=django_tz.now() - django_tz.timedelta(hours=i),
            chain=chain,
        )
        txs.append(tx)
    return txs
