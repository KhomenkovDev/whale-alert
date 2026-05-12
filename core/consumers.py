import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class WhaleConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer that pushes live whale alerts to connected browsers.
    Clients can optionally subscribe to a specific chain.
    """

    GROUP_NAME = "whale_alerts"

    async def connect(self):
        # Accept chain filter from query string: /ws/whales/?chain=ETH
        query_string = self.scope.get("query_string", b"").decode()
        self.chain_filter = None
        for part in query_string.split("&"):
            if part.startswith("chain="):
                self.chain_filter = part.split("=", 1)[1].upper() or None

        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

        # Send history on connect (filtered if chain specified)
        history = await self.get_recent_transactions(self.chain_filter)
        await self.send(
            text_data=json.dumps(
                {
                    "type": "history",
                    "transactions": history,
                }
            )
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def receive(self, text_data):
        """Handle client messages — supports chain filter changes."""
        try:
            data = json.loads(text_data)
            if data.get("type") == "set_chain":
                self.chain_filter = data.get("chain") or None
                history = await self.get_recent_transactions(self.chain_filter)
                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "history",
                            "transactions": history,
                        }
                    )
                )
        except Exception:
            pass

    async def whale_alert(self, event):
        """Called by channel layer when a new whale is detected."""
        tx = event["transaction"]
        # Apply chain filter if set
        if self.chain_filter and tx.get("chain") != self.chain_filter:
            return
        await self.send(
            text_data=json.dumps(
                {
                    "type": "new_whale",
                    "transaction": tx,
                }
            )
        )

    @database_sync_to_async
    def get_recent_transactions(self, chain_filter=None):
        from core.models import WhaleTransaction

        qs = WhaleTransaction.objects.order_by("-timestamp")
        if chain_filter:
            qs = qs.filter(chain=chain_filter)
        return [tx.to_dict() for tx in qs[:30]]
