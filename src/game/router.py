from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from auth.services.user import UserService
from dependencies import AuthenticatedUserDep, UOWDep, WSAuthenticatedUserDep
from game.schemas import LobbyIdDTO, GameStartEventDTO, \
    GameIdPayloadDTO
from game.services.game import GameService
from game.services.lobby import LobbyService
from managers import lobby_ws_manager, game_ws_manager
from schemas import ErrorEventDTO


router = APIRouter(prefix="/games", tags=["Game"])
ws_router = APIRouter(prefix="/ws/games", tags=["WS Game"])


@router.post("/lobbies")
async def create_lobby(
    user: AuthenticatedUserDep,
    uow: UOWDep,
) -> LobbyIdDTO:
    return await LobbyService(uow).create_lobby(user)


@ws_router.websocket("/lobbies/{lobby_id}")
async def lobby_ws(
    websocket: WebSocket,
    lobby_id: UUID,
    user: WSAuthenticatedUserDep,
    uow: UOWDep,
):
    await lobby_ws_manager.connect(websocket, user, lobby_id)
    try:
        while True:
            message = await websocket.receive_json()
            event = message.get("event")
            if event == "ready":
                await lobby_ws_manager.add_user_to_ready_list(user.id, lobby_id)
                await lobby_ws_manager.broadcast_ready_users(lobby_id)
                player_ids = await lobby_ws_manager.get_user_ids(lobby_id)
                players = await UserService(uow).get_users_by_ids(player_ids)
                if await lobby_ws_manager.is_ready(lobby_id):
                    game_info = await GameService(uow).create_game(
                        players
                    )
                    await lobby_ws_manager.broadcast(lobby_id, GameStartEventDTO(
                        event="game_start",
                        data=GameIdPayloadDTO(id=game_info.id)
                    ))
            else:
                await lobby_ws_manager.send_to_user(
                    user.id,
                    ErrorEventDTO(
                        event="error", data={"message": "Invalid event type"}
                    ),
                )
    except WebSocketDisconnect:
        await lobby_ws_manager.disconnect(user.id, lobby_id)


@ws_router.websocket("/games/{game_id}")
async def game_ws(
    websocket: WebSocket,
    game_id: UUID,
    user: WSAuthenticatedUserDep,
    uow: UOWDep,
):
    await game_ws_manager.connect(websocket, user.id, game_id)
    try:
        while True:
            message = await websocket.receive_json()
            event = message.get("event")
            if event == "move":
                pass
            else:
                await game_ws_manager.send_to_user(
                    user.id,
                    ErrorEventDTO(
                        event="error", data={"message": "Invalid event type"}
                    ),
                )
    except WebSocketDisconnect:
        await game_ws_manager.disconnect(user.id, game_id)
