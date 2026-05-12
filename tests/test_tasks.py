from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from monitor.tasks import (
    _broadcast_whale,
    _get_web3,
    scan_all_chains,
    scan_chain_transfers,
    seed_demo_transactions,
)


class TestGetWeb3:
    def test_returns_web3_instance(self):
        with patch("web3.Web3") as mock_w3:
            mock_w3.return_value = mock_w3
            result = _get_web3("http://localhost:8545")
        assert result is not None

    def test_uses_websocket_provider(self):
        with patch("web3.Web3") as mock_w3:
            _get_web3("wss://mainnet.infura.io/ws")
        mock_w3.WebsocketProvider.assert_called_once()

    def test_uses_http_provider(self):
        with patch("web3.Web3") as mock_w3:
            _get_web3("https://mainnet.infura.io")
        mock_w3.HTTPProvider.assert_called_once()


class TestBroadcastWhale:
    @patch("monitor.tasks.get_channel_layer")
    def test_sends_to_group(self, mock_get_layer):
        mock_layer = MagicMock()
        mock_layer.group_send = AsyncMock()
        mock_get_layer.return_value = mock_layer
        _broadcast_whale({"chain": "ETH"})
        mock_layer.group_send.assert_called_once_with(
            "whale_alerts",
            {"type": "whale_alert", "transaction": {"chain": "ETH"}},
        )


class TestScanChainTransfers:
    def test_unknown_chain(self):
        result = scan_chain_transfers.apply(args=["XRP"]).get()
        assert result["status"] == "unknown_chain"

    def test_no_rpc_url(self, settings):
        settings.ETHEREUM_RPC_URL = None
        result = scan_chain_transfers.apply(args=["ETH"]).get()
        assert result["status"] == "no_rpc"

    @patch("monitor.tasks._get_web3")
    def test_disconnected(self, mock_get_web3, settings):
        mock_w3 = MagicMock()
        mock_w3.is_connected.return_value = False
        mock_get_web3.return_value = mock_w3
        settings.ETHEREUM_RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/test"

        result = scan_chain_transfers.apply(args=["ETH"]).get()
        assert result["status"] == "disconnected"

    @patch("monitor.tasks._get_web3")
    def test_scan_successful(self, mock_get_web3, settings, db):
        mock_w3 = MagicMock()
        mock_w3.is_connected.return_value = True
        mock_w3.eth.block_number = 22_000_010
        mock_w3.to_checksum_address.side_effect = lambda x: x
        mock_get_web3.return_value = mock_w3

        # Mock contract to return no events
        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract
        mock_filter = MagicMock()
        mock_contract.events.Transfer.create_filter.return_value = mock_filter
        mock_filter.get_all_entries.return_value = []

        settings.ETHEREUM_RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/test"
        settings.WHALE_THRESHOLD_USD = 1_000_000

        result = scan_chain_transfers.apply(args=["ETH"]).get()
        assert result["status"] == "ok"
        assert result["new_whales"] == 0


class TestScanAllChains:
    @patch("monitor.tasks.scan_chain_transfers.delay")
    def test_triggers_all_chains(self, mock_delay):
        result = scan_all_chains.apply().get()
        assert len(result["triggered"]) == 4
        assert mock_delay.call_count == 4


class TestSeedDemoTransactions:
    def test_seeds_transactions(self, db):
        result = seed_demo_transactions.apply().get()
        assert result["seeded"] == 7
