from __future__ import annotations

import json
from unittest.mock import patch

from django.test import Client


class TestDashboard:
    def test_returns_200(self, db):
        client = Client()
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response["content-type"].lower()

    def test_includes_stats(self, db, multi_chain_transactions):
        client = Client()
        response = client.get("/")
        assert response.status_code == 200
        assert b"Total Whale Movements" in response.content


class TestApiTransactions:
    def test_returns_transactions(self, db, multi_chain_transactions):
        client = Client()
        response = client.get("/api/transactions/")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert len(data["transactions"]) == 4

    def test_filters_by_chain(self, db, multi_chain_transactions):
        client = Client()
        response = client.get("/api/transactions/?chain=ETH")
        assert response.status_code == 200
        data = response.json()
        assert all(tx["chain"] == "ETH" for tx in data["transactions"])

    def test_respects_limit(self, db, multi_chain_transactions):
        client = Client()
        response = client.get("/api/transactions/?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 2

    def test_returns_empty_for_unknown_chain(self, db, multi_chain_transactions):
        client = Client()
        response = client.get("/api/transactions/?chain=XRP")
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 0


class TestApiStats:
    def test_returns_aggregates(self, db, multi_chain_transactions):
        client = Client()
        response = client.get("/api/stats/")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 4
        assert data["total_volume"] > 0
        assert len(data["chain_breakdown"]) == 4

    def test_filters_by_chain(self, db, multi_chain_transactions):
        client = Client()
        response = client.get("/api/stats/?chain=ETH")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1


class TestApiWhaleReport:
    def test_returns_404_for_missing_tx(self, db):
        client = Client()
        response = client.post("/api/report/999/")
        assert response.status_code == 404
        assert "Transaction not found" in response.json()["error"]

    @patch("anthropic.Anthropic")
    def test_returns_cached_report(self, mock_anthropic, db, sample_transaction):
        sample_transaction.ai_summary = "Cached summary"
        sample_transaction.ai_intent = "Cached intent"
        sample_transaction.ai_impact = "Cached impact"
        sample_transaction.ai_risk = "LOW"
        sample_transaction.ai_tags = "tag1,tag2"
        sample_transaction.save(
            update_fields=[
                "ai_summary",
                "ai_intent",
                "ai_impact",
                "ai_risk",
                "ai_tags",
            ]
        )

        client = Client()
        response = client.post(f"/api/report/{sample_transaction.pk}/")
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True
        assert data["summary"] == "Cached summary"
        mock_anthropic.assert_not_called()

    @patch("anthropic.Anthropic")
    def test_generates_new_report(self, mock_anthropic_class, db, sample_transaction):
        mock_client = mock_anthropic_class.return_value
        mock_message = mock_client.messages.create.return_value
        mock_content = mock_message.content
        mock_block = mock_content[0]
        mock_block.text = json.dumps(
            {
                "summary": "Large USDC transfer",
                "intent": "Accumulation",
                "impact": "Minimal",
                "risk": "LOW",
                "tags": ["whale", "usdc"],
            }
        )
        mock_block.type = "text"

        client = Client()
        response = client.post(f"/api/report/{sample_transaction.pk}/")
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is False
        assert "Large USDC transfer" in data["summary"]
