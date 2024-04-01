from fastapi import APIRouter, WebSocket
from fastapi.websockets import WebSocketDisconnect

from game.dependencies import WSAuthenticatedUserDep
from game.schemas import PlayersInSearchCount
from managers import ws_manager
from schemas import Response

router = APIRouter(prefix="/games", tags=["Game"])


@router.websocket("/ws/search/")
async def search_game(websocket: WebSocket, user: WSAuthenticatedUserDep):
    await ws_manager.connect(websocket, user.id)
    user_ids = ws_manager.get_active_user_ids()
    players_in_search_count = ws_manager.get_connections_count()
    _ = PlayersInSearchCount(count=players_in_search_count)
    await ws_manager.broadcast(Response[PlayersInSearchCount](data=_))
    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.broadcast({"user": str(user.id), "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(user.id)
