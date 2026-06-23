"""
Quota status middleware for Sentinel ADK.

Injects a lightweight GET /quota-status endpoint into the ADK ASGI stack
without touching FastAPI internals. Works by intercepting the request path
before it reaches the FastAPI router.
"""
import json
from app.utils.quota_tracker import get_quota_summary


class QuotaStatusMiddleware:
    """ASGI middleware that handles GET /quota-status requests."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http" and scope.get("path") == "/quota-status":
            method = scope.get("method", "GET").upper()
            if method == "GET":
                await self._send_quota_response(send)
                return
        await self.app(scope, receive, send)

    async def _send_quota_response(self, send):
        summary = get_quota_summary()
        body = json.dumps(summary).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("utf-8")),
                (b"access-control-allow-origin", b"*"),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
            "more_body": False,
        })
