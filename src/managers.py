import asyncio
from types import coroutine

from fastapi.encoders import jsonable_encoder
from fastapi.websockets import WebSocket, WebSocketDisconnect

from notification.schemas import LobbyEventDTO, FriendEventDTO
from schemas import ErrorEventDTO


class WSConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}
        self._lobby_members: dict[str, set[str]] = {}
        self._lobby_ready: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect_to_notification(
        self, user_id: str, websocket: WebSocket
    ) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[user_id] = websocket

    async def connect_to_lobby(
        self, websocket: WebSocket, user_id: str, lobby_id: str
    ) -> None:
        """
        Accept a WebSocket connection and register the user to the lobby room.
        """
        await websocket.accept()
        async with self._lock:
            self._connections[user_id] = websocket
            self._lobby_members.setdefault(lobby_id, set()).add(user_id)
            self._lobby_ready.setdefault(lobby_id, set())
        await self.broadcast_to_lobby(lobby_id, {
            "event": "lobby_members",
            "data": self._lobby_members.get(lobby_id, set()),
        })

    async def disconnect(
        self, user_id: str, lobby_id: str | None = None
    ) -> None:
        """
        Remove a user from global connections and optionally from a lobby.
        """
        async with self._lock:
            # global disconnect
            self._connections.pop(user_id, None)
            # lobby-specific cleanup
            if lobby_id:
                if lobby_id in self._lobby_members:
                    self._lobby_members[lobby_id].discard(user_id)
                    if user_id in self._lobby_ready.get(lobby_id, set()):
                        self._lobby_ready[lobby_id].discard(user_id)
                    if not self._lobby_members[lobby_id]:
                        self._lobby_members.pop(lobby_id)

    async def add_user_to_ready_list(self, user_id: str, lobby_id: str) -> None:
        async with self._lock:
            if lobby_id not in self._lobby_ready:
                self._lobby_ready[lobby_id] = set()
            self._lobby_ready[lobby_id].add(user_id)

    async def broadcast_to_lobby_ready_users(
        self, lobby_id: str
    ) -> None:
        await self.broadcast_to_lobby(lobby_id, {
            "event": "ready_users",
            "data": self._lobby_ready.get(lobby_id, set()),
        })

    async def broadcast_to_lobby(
        self, lobby_id: str, data: dict[str, str | set[str]]
    ) -> None:
        """
        Send a message to all users connected in a given lobby.
        """
        payload = jsonable_encoder(data)
        async with self._lock:
            websockets = [
                self._connections.get(uid)
                for uid in self._lobby_members.get(lobby_id, [])
            ]
        coroutines = [ws.send_json(payload) for ws in websockets if ws]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, (WebSocketDisconnect, RuntimeError)):
                failed_user = list(self._lobby_members.get(lobby_id, []))[i]
                await self.disconnect(failed_user, lobby_id)

    async def send_to_user(
        self,
        user_id: str,
        data: LobbyEventDTO | FriendEventDTO | ErrorEventDTO,
    ) -> None:
        async with self._lock:
            ws = self._connections.get(user_id)
        if ws:
            try:
                await ws.send_json(
                    jsonable_encoder(data.model_dump(by_alias=True))
                )
            except (WebSocketDisconnect, RuntimeError):
                await self.disconnect(user_id)

    async def get_lobby_user_ids(self, lobby_id: str) -> list[str]:
        async with self._lock:
            return list(self._lobby_members.get(lobby_id, []))

    async def is_lobby_ready(self, lobby_id: str) -> bool:
        async with self._lock:
            return (
                lobby_id in self._lobby_ready and
                len(self._lobby_ready[lobby_id]) == len(self._lobby_members.get(lobby_id, []))
            )


ws_manager = WSConnectionManager()
