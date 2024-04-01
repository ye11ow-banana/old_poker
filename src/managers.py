from fastapi.websockets import WebSocket

from schemas import Response


class WSConnectionManager:
    def __init__(self) -> None:
        self._active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self._active_connections[user_id] = websocket

    def disconnect(self, user_id: str) -> None:
        del self._active_connections[user_id]

    async def broadcast(self, data: Response) -> None:
        for connection in self._active_connections.values():
            await connection.send_json(data.model_dump(by_alias=True))

    def get_connections_count(self) -> int:
        return len(self._active_connections)

    def get_active_user_ids(self) -> list[str]:
        return list(self._active_connections.keys())


ws_manager = WSConnectionManager()
