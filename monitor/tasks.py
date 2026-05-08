"""
Celery tasks for monitoring multiple blockchains for whale transactions.

Supports: Ethereum, BNB Chain, Polygon, Avalanche (EVM-compatible chains).
Each chain scans ERC-20 Transfer events for the configured stablecoins/tokens,
filters by USD threshold, persists to DB, and broadcasts via Django Channels.
"""

import logging
from decimal import Decimal
from datetime import datetime, timezone

from celery import shared_task
from django.conf import settings
from django.utils import timezone as django_tz
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

ERC20_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,  "name": "from",  "type": "address"},
            {"indexed": True,  "name": "to",    "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    }
]

# Chain configs: rpc_url_setting, explorer, tokens {symbol: (contract, decimals)}
CHAIN_CONFIGS = {
    'ETH': {
        'rpc_setting': 'ETHEREUM_RPC_URL',
        'explorer': 'https://etherscan.io/tx/',
        'name': 'Ethereum',
        'tokens': {
            'USDC': ('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 6),
            'USDT': ('0xdAC17F958D2ee523a2206206994597C13D831ec7', 6),
            'DAI':  ('0x6B175474E89094C44Da98b954EedeAC495271d0F', 18),
        },
    },
    'BNB': {
        'rpc_setting': 'BNB_RPC_URL',
        'explorer': 'https://bscscan.com/tx/',
        'name': 'BNB Chain',
        'tokens': {
            'USDT': ('0x55d398326f99059fF775485246999027B3197955', 18),
            'USDC': ('0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d', 18),
            'BUSD': ('0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56', 18),
        },
    },
    'POL': {
        'rpc_setting': 'POLYGON_RPC_URL',
        'explorer': 'https://polygonscan.com/tx/',
        'name': 'Polygon',
        'tokens': {
            'USDC': ('0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', 6),
            'USDT': ('0xc2132D05D31c914a87C6611C10748AEb04B58e8F', 6),
        },
    },
    'AVAX': {
        'rpc_setting': 'AVALANCHE_RPC_URL',
        'explorer': 'https://snowtrace.io/tx/',
        'name': 'Avalanche',
        'tokens': {
            'USDC': ('0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E', 6),
            'USDT': ('0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7', 6),
        },
    },
}


def _get_web3(rpc_url: str):
    from web3 import Web3
    if rpc_url.startswith('wss://') or rpc_url.startswith('ws://'):
        provider = Web3.WebsocketProvider(rpc_url)
    else:
        provider = Web3.HTTPProvider(rpc_url)
    return Web3(provider)


def _broadcast_whale(tx_dict: dict):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'whale_alerts',
        {'type': 'whale_alert', 'transaction': tx_dict}
    )


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def scan_chain_transfers(self, chain: str = 'ETH', from_block: int = None, to_block: int = None):
    """
    Scan recent token Transfer events on the given chain for whale-sized moves.

    Args:
        chain:      Chain key — 'ETH', 'BNB', 'POL', 'AVAX'
        from_block: Start block (default: latest - 10)
        to_block:   End block (default: 'latest')
    """
    from core.models import WhaleTransaction

    if chain not in CHAIN_CONFIGS:
        logger.warning("Unknown chain: %s", chain)
        return {'status': 'unknown_chain'}

    config = CHAIN_CONFIGS[chain]
    rpc_url = getattr(settings, config['rpc_setting'], None)
    if not rpc_url:
        logger.warning("No RPC URL configured for %s", chain)
        return {'status': 'no_rpc'}

    try:
        w3 = _get_web3(rpc_url)
        if not w3.is_connected():
            logger.warning("Web3 not connected for %s. Skipping.", chain)
            return {'status': 'disconnected'}

        latest = w3.eth.block_number
        if from_block is None:
            from_block = max(0, latest - 10)
        if to_block is None:
            to_block = latest

        threshold = Decimal(str(settings.WHALE_THRESHOLD_USD))
        new_whales = 0

        for symbol, (contract_addr, decimals) in config['tokens'].items():
            try:
                address = w3.to_checksum_address(contract_addr)
                contract = w3.eth.contract(address=address, abi=ERC20_ABI)
                transfer_filter = contract.events.Transfer.create_filter(
                    fromBlock=from_block, toBlock=to_block
                )
                events = transfer_filter.get_all_entries()
            except Exception as e:
                logger.warning("Failed to fetch %s on %s: %s", symbol, chain, e)
                continue

            for event in events:
                raw_value = event['args']['value']
                usd_amount = Decimal(raw_value) / Decimal(10 ** decimals)

                if usd_amount < threshold:
                    continue

                tx_hash = event['transactionHash'].hex()
                block_num = event['blockNumber']

                if WhaleTransaction.objects.filter(tx_hash=tx_hash).exists():
                    continue

                block_info = w3.eth.get_block(block_num)
                timestamp = datetime.fromtimestamp(block_info['timestamp'], tz=timezone.utc)

                whale_tx = WhaleTransaction.objects.create(
                    tx_hash=tx_hash,
                    block_number=block_num,
                    from_address=event['args']['from'],
                    to_address=event['args']['to'],
                    token_symbol=symbol,
                    token_amount=usd_amount,
                    usd_value=usd_amount,
                    timestamp=timestamp,
                    chain=chain,
                    explorer_url=config['explorer'] + tx_hash,
                )

                logger.info("🐋 %s | %s $%.2f — tx %s", chain, symbol, float(usd_amount), tx_hash[:12])

                try:
                    _broadcast_whale(whale_tx.to_dict())
                except Exception as e:
                    logger.error("WS broadcast failed: %s", e)

                new_whales += 1

        return {'status': 'ok', 'chain': chain, 'blocks': to_block - from_block + 1, 'new_whales': new_whales}

    except Exception as exc:
        logger.error("scan_chain_transfers failed for %s: %s", chain, exc, exc_info=True)
        raise self.retry(exc=exc)


@shared_task
def scan_all_chains():
    """Fan-out task: triggers a scan on every configured chain in parallel."""
    for chain in CHAIN_CONFIGS:
        scan_chain_transfers.delay(chain)
    return {'triggered': list(CHAIN_CONFIGS.keys())}


# Backward-compatible alias
@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def scan_usdc_transfers(self, from_block: int = None, to_block: int = None):
    """Legacy task — scans Ethereum USDC only. Use scan_chain_transfers instead."""
    return scan_chain_transfers.apply(args=['ETH', from_block, to_block]).get()


@shared_task
def seed_demo_transactions():
    """Inject realistic multi-chain demo whale transactions for development."""
    import random
    from core.models import WhaleTransaction

    demo_data = [
        ('ETH', 'USDC', '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', '0x40B38765696e3d5d8d9d834D8AaD4bB6e418E489', 34_726_445),
        ('ETH', 'USDT', '0x28C6c06298d514Db089934071355E5743bf21d60', '0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549', 12_500_000),
        ('BNB', 'USDT', '0xF977814e90dA44bFA03b6295A0616a897441aceC', '0x8894E0a0c962CB723c1976a4421c95949bE2D4E5', 8_200_000),
        ('BNB', 'BUSD', '0xDFd5293D8e347dFe59E90eFd55b2956a1343963d', '0x1111111254EEB25477B68fb85Ed929f73A960582', 5_100_000),
        ('POL', 'USDC', '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', '0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD', 3_800_000),
        ('AVAX', 'USDC', '0xAbcDef1234567890AbcDef1234567890AbcDef12', '0x9876543210FeDcBa9876543210FeDcBa98765432', 7_450_000),
        ('ETH', 'DAI',  '0x1234567890123456789012345678901234567890', '0x0987654321098765432109876543210987654321', 22_000_000),
    ]

    explorer_map = {c: CHAIN_CONFIGS[c]['explorer'] for c in CHAIN_CONFIGS}
    now = django_tz.now()
    created = 0

    for i, (chain, symbol, from_addr, to_addr, base_val) in enumerate(demo_data):
        fake_hash = '0x' + ''.join(random.choices('0123456789abcdef', k=64))
        usd_val = Decimal(str(round(base_val * random.uniform(0.9, 1.1), 2)))
        ts = now - django_tz.timedelta(minutes=i * 5)

        whale, was_created = WhaleTransaction.objects.get_or_create(
            tx_hash=fake_hash,
            defaults=dict(
                block_number=22_000_000 - i * 3,
                from_address=from_addr,
                to_address=to_addr,
                token_symbol=symbol,
                token_amount=usd_val,
                usd_value=usd_val,
                timestamp=ts,
                chain=chain,
                explorer_url=explorer_map.get(chain, 'https://etherscan.io/tx/') + fake_hash,
            ),
        )

        if was_created:
            try:
                _broadcast_whale(whale.to_dict())
            except Exception:
                pass
            created += 1

    logger.info("Seeded %d multi-chain demo whale transactions.", created)
    return {'seeded': created}
