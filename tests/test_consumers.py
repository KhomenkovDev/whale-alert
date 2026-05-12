from __future__ import annotations

import pytest
from channels.testing import WebsocketCommunicator

from core.routing import websocket_urlpatterns


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_connect_receives_history(async_multi_chain_transactions):
    from channels.auth import AuthMiddlewareStack
    from channels.routing import URLRouter

    application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
    communicator = WebsocketCommunicator(application, "/ws/whales/")

    connected, _ = await communicator.connect()
    assert connected

    response = await communicator.receive_json_from()
    assert response["type"] == "history"
    assert len(response["transactions"]) == 4

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chain_filter_on_connect(async_multi_chain_transactions):
    from channels.auth import AuthMiddlewareStack
    from channels.routing import URLRouter

    application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
    communicator = WebsocketCommunicator(application, "/ws/whales/?chain=ETH")

    connected, _ = await communicator.connect()
    assert connected

    response = await communicator.receive_json_from()
    assert response["type"] == "history"
    assert all(tx["chain"] == "ETH" for tx in response["transactions"])

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_receive_set_chain(async_multi_chain_transactions):
    from channels.auth import AuthMiddlewareStack
    from channels.routing import URLRouter

    application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
    communicator = WebsocketCommunicator(application, "/ws/whales/")

    connected, _ = await communicator.connect()
    assert connected

    await communicator.receive_json_from()

    await communicator.send_json_to({"type": "set_chain", "chain": "BNB"})
    response = await communicator.receive_json_from()
    assert response["type"] == "history"
    assert all(tx["chain"] == "BNB" for tx in response["transactions"])

    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_whale_alert_group_send(async_multi_chain_transactions):
    from channels.auth import AuthMiddlewareStack
    from channels.routing import URLRouter

    application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
    communicator = WebsocketCommunicator(application, "/ws/whales/")

    connected, _ = await communicator.connect()
    assert connected

    await communicator.receive_json_from()

    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "whale_alerts",
        {
            "type": "whale_alert",
            "transaction": {"chain": "ETH", "usd_value": "5000000"},
        },
    )

    response = await communicator.receive_json_from()
    assert response["type"] == "new_whale"
    assert response["transaction"]["usd_value"] == "5000000"

    await communicator.disconnect()
