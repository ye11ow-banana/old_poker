from uuid import UUID

from fastapi import APIRouter, WebSocket
from fastapi.websockets import WebSocketDisconnect

from dependencies import UOWDep
from game.dependencies import WSAuthenticatedUserDep
from game.schemas import PlayersInSearchCountDTO, LobbyUserInfoDTO, GameInfoDTO
from game.services.game import GameService
from game.services.lobby import LobbyService
from managers import ws_manager
from schemas import ResponseDTO

router = APIRouter(prefix="/games", tags=["Game"])


@router.websocket("/ws/search")
async def search_game(websocket: WebSocket, user: WSAuthenticatedUserDep):
    await ws_manager.connect(websocket, user.id)
    user_ids = ws_manager.get_active_user_ids()
    players_in_search_count = ws_manager.get_connections_count()
    _ = PlayersInSearchCountDTO(count=players_in_search_count)
    await ws_manager.broadcast(ResponseDTO[PlayersInSearchCountDTO](data=_))
    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.broadcast({"user": str(user.id), "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(user.id)


@router.websocket("/ws/lobbies/{lobby_id}")
async def get_lobby(
    websocket: WebSocket,
    user: WSAuthenticatedUserDep,
    uow: UOWDep,
    lobby_id: UUID,
) -> None:
    await ws_manager.connect(websocket, user.id)
    service = LobbyService(uow)
    try:
        await service.add_user_to_lobby(user, lobby_id=lobby_id)
    except ValueError:
        ws_manager.disconnect(user.id)
        return
    players = await service.get_players_in_lobby(lobby_id=lobby_id)
    await ws_manager.broadcast(ResponseDTO[LobbyUserInfoDTO](data=players))
    try:
        while True:
            data = await websocket.receive_json()
            create_game = data.get("create_game", False)
            players = await service.get_players_in_lobby(lobby_id=lobby_id)
            game = await GameService(uow).create_game(players, create_game)
            if game is not None:
                await ws_manager.broadcast(ResponseDTO[GameInfoDTO](data=game))
    except Exception:
        await service.remove_user_from_lobby(user, lobby_id=lobby_id)
        ws_manager.disconnect(user.id)
