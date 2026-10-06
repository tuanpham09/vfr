"""WebSocket server (thư viện `websockets` >= 13) cho extension. Chỉ bind loopback."""
from __future__ import annotations

import asyncio
import json
from typing import Callable

from core.events import EventBus, ExtStatus

PROTOCOL_VERSION = 1


class WsServer:
    def __init__(self, bus: EventBus, port: int, token: str) -> None:
        self.bus, self.port, self.token = bus, port, token
        self.on_message: Callable[[dict], None] | None = None
        self._ws = None
        self._server = None

    @property
    def connected(self) -> bool:
        return self._ws is not None

    async def start(self) -> None:
        import websockets  # import muộn để core test được khi chưa cài

        self._server = await websockets.serve(self._handler, "127.0.0.1", self.port,
                                              max_size=64 * 1024 * 1024)
        self.bus.log(f"WS server lắng nghe ws://127.0.0.1:{self.port}")

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def send(self, msg: dict) -> None:
        if self._ws is None:
            raise ConnectionError("Extension chưa kết nối")
        await self._ws.send(json.dumps(msg, ensure_ascii=False))

    async def _handler(self, ws, path=None) -> None:  # noqa: ANN001
        authed = False
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except ValueError:
                    continue
                t = msg.get("type")
                if not authed:
                    if t != "hello" or (self.token and msg.get("token") != self.token):
                        self.bus.log("Extension bị từ chối: sai token (kiểm tra trang Options)", "error")
                        await ws.close(code=4001, reason="bad token")
                        return
                    if msg.get("v", PROTOCOL_VERSION) != PROTOCOL_VERSION:
                        self.bus.log("Phiên bản giao thức extension không khớp", "error")
                        await ws.close(code=4002, reason="bad version")
                        return
                    if self._ws is not None and self._ws is not ws:
                        try:
                            await self._ws.close()
                        except Exception:  # noqa: BLE001
                            pass
                    authed, self._ws = True, ws
                    self.bus.publish(ExtStatus(True, str(msg.get("ver", ""))))
                    self.bus.log(f"Extension đã kết nối (v{msg.get('ver', '?')})")
                    continue
                if t == "ping":
                    await ws.send(json.dumps({"type": "pong", "ts": msg.get("ts")}))
                    continue
                if self.on_message:
                    self.on_message(msg)
        except Exception as e:  # noqa: BLE001
            self.bus.log(f"Lỗi kết nối extension: {e}", "warn")
        finally:
            if self._ws is ws:
                self._ws = None
                self.bus.publish(ExtStatus(False))
                self.bus.log("Extension đã ngắt kết nối", "warn")
