import asyncio
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from fastapi.websockets import WebSocket, WebSocketDisconnect

from auth.schemas import UserInfoDTO
from game.schemas import FullGameCardInfoEventDTO, NewWatcherEventDTO
from notification.schemas import LobbyEventDTO, FriendEventDTO
from schemas import ErrorEventDTO


class WSManager:
    def __init__(self) -> None:
        self._connections: dict[UUID, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def send_to_user(
        self,
        user_id: UUID,
        data: LobbyEventDTO | FriendEventDTO | FullGameCardInfoEventDTO | ErrorEventDTO,
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

    async def disconnect(self, user_id: UUID) -> None:
        async with self._lock:
            self._connections.pop(user_id, None)


class NotificationWSManager(WSManager):
    async def connect(
        self, user_id: UUID, websocket: WebSocket
    ) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[user_id] = websocket


class LobbyWSManager(WSManager):
    def __init__(self) -> None:
        super().__init__()
        self._lobby_members: dict[UUID, dict[UUID, UserInfoDTO]] = {}
        self._lobby_ready: dict[UUID, set[UUID]] = {}

    async def connect(
        self, websocket: WebSocket, user: UserInfoDTO, lobby_id: UUID
    ) -> None:
        """
        Accept a WebSocket connection and register the user to the lobby room.
        """
        await websocket.accept()
        async with self._lock:
            self._connections[user.id] = websocket
            self._lobby_members.setdefault(lobby_id, {})[user.id] = user
            self._lobby_ready.setdefault(lobby_id, set())
        await self.broadcast(lobby_id, {
            "event": "lobby_members",
            "data": [
                user for user in self._lobby_members.get(lobby_id, {}).values()
            ],
        })

    async def disconnect(
        self, user_id: UUID, lobby_id: UUID | None = None
    ) -> None:
        async with self._lock:
            self._connections.pop(user_id, None)
            if lobby_id:
                if lobby_id in self._lobby_members:
                    self._lobby_members[lobby_id].pop(user_id, None)
                    if user_id in self._lobby_ready.get(lobby_id, set()):
                        self._lobby_ready[lobby_id].discard(user_id)
                    if not self._lobby_members[lobby_id]:
                        self._lobby_members.pop(lobby_id)

    async def add_user_to_ready_list(self, user_id: UUID, lobby_id: UUID) -> None:
        async with self._lock:
            if lobby_id not in self._lobby_ready:
                self._lobby_ready[lobby_id] = set()
            self._lobby_ready[lobby_id].add(user_id)

    async def broadcast_ready_users(
        self, lobby_id: UUID
    ) -> None:
        await self.broadcast(lobby_id, {
            "event": "ready_users",
            "data": self._lobby_ready.get(lobby_id, set()),
        })

    async def broadcast(
        self, lobby_id: UUID, data: dict[str, str | set[str]]
    ) -> None:
        """
        Send a message to all users connected in a given lobby.
        """
        payload = jsonable_encoder(data)
        async with self._lock:
            websockets = [
                self._connections.get(uid)
                for uid in self._lobby_members.get(lobby_id, {}).keys()
            ]
        coroutines = [ws.send_json(payload) for ws in websockets if ws]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, (WebSocketDisconnect, RuntimeError)):
                failed_user = list(self._lobby_members.get(lobby_id, {}).keys())[i]
                await self.disconnect(failed_user, lobby_id)

    async def get_user_ids(self, lobby_id: UUID) -> list[UUID]:
        async with self._lock:
            return list(self._lobby_members.get(lobby_id, {}).keys())

    async def is_ready(self, lobby_id: UUID) -> bool:
        async with self._lock:
            return (
                lobby_id in self._lobby_ready and
                len(self._lobby_ready[lobby_id]) == len(self._lobby_members.get(lobby_id, {}))
            )


class GameWSManager(WSManager):
    def __init__(self) -> None:
        super().__init__()
        self._games: dict[UUID, dict[str, dict[UUID, UserInfoDTO]]] = {}

    async def connect_player_to_game(self, websocket: WebSocket, user: UserInfoDTO, game_id: UUID) -> None:
        await self._connect_user_to_game(websocket, user, game_id, "players")

    async def connect_spectator_to_game(self, websocket: WebSocket, user: UserInfoDTO, game_id: UUID) -> None:
        await self._connect_user_to_game(websocket, user, game_id, "spectators")

    async def disconnect_player_from_game(self, user_id: UUID, game_id: UUID) -> None:
        await self._disconnect_user_from_game(user_id, game_id, "players")

    async def disconnect_spectator_from_game(self, user_id: UUID, game_id: UUID) -> None:
        await self._disconnect_user_from_game(user_id, game_id, "spectators")

    async def broadcast_to_all(self, game_id: UUID, data: NewWatcherEventDTO) -> None:
        """
        Send a message to all users connected in a given game.
        """
        payload = jsonable_encoder(data.model_dump(by_alias=True))
        async with self._lock:
            websockets = [
                self._connections.get(uid)
                for uid in self._games.get(game_id, {}).get("players", {}).keys()
            ] + [
                self._connections.get(uid)
                for uid in self._games.get(game_id, {}).get("spectators", {}).keys()
            ]
        coroutines = [ws.send_json(payload) for ws in websockets if ws]
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, (WebSocketDisconnect, RuntimeError)):
                try:
                    failed_user = list(self._games.get(game_id, {}).get("players", {}).keys())[i]
                    await self.disconnect_player_from_game(failed_user, game_id)
                except IndexError:
                    failed_user = list(self._games.get(game_id, {}).get("spectators", {}).keys())[i - len(self._games.get(game_id, {}).get("players", {}))]
                    await self.disconnect_spectator_from_game(failed_user, game_id)

    def get_users(self, game_id: UUID, list_name: str) -> list[UserInfoDTO]:
        """
        Get users from a specific list (players or spectators) in a game.
        """
        return list(self._games.get(game_id, {}).get(list_name, {}).values())

    async def _connect_user_to_game(
        self, websocket: WebSocket, user: UserInfoDTO, game_id: UUID, list_name: str
    ) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[user.id] = websocket
            if game_id not in self._games:
                self._games[game_id] = {"players": {}, "spectators": {}}
            self._games[game_id][list_name][user.id] = user

    async def _disconnect_user_from_game(
        self, user_id: UUID, game_id: UUID, list_name: str
    ) -> None:
        await super().disconnect(user_id)
        async with self._lock:
            if game_id in self._games and list_name in self._games[game_id]:
                self._games[game_id][list_name].pop(user_id, None)
                if not self._games[game_id][list_name]:
                    del self._games[game_id][list_name]
                if not self._games[game_id]:
                    del self._games[game_id]


notification_ws_manager = NotificationWSManager()
lobby_ws_manager = LobbyWSManager()
game_ws_manager = GameWSManager()
