from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from auth.services.user import UserService
from dependencies import AuthenticatedUserDep, UOWDep, WSAuthenticatedUserDep
from game.schemas import LobbyIdDTO, GameStartEventDTO, \
    GameIdPayloadDTO
from game.services.game import GameService
from game.services.lobby import LobbyService
from managers import ws_manager
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
    user_id = str(user.id)
    await ws_manager.connect_to_lobby(websocket, user_id, lobby_id)
    try:
        while True:
            message = await websocket.receive_json()
            event = message.get("event")
            if event == "ready":
                await ws_manager.add_user_to_ready_list(user_id, lobby_id)
                await ws_manager.broadcast_to_lobby_ready_users(lobby_id)
                player_ids = await ws_manager.get_lobby_user_ids(lobby_id)
                players = await UserService(uow).get_users_by_ids(player_ids)
                if await ws_manager.is_lobby_ready(lobby_id):
                    game_info = await GameService(uow).create_game(
                        players
                    )
                    await ws_manager.broadcast_to_lobby(lobby_id, GameStartEventDTO(
                        event="game_start",
                        data=GameIdPayloadDTO(id=game_info.id)
                    ))
            else:
                await ws_manager.send_to_user(
                    user_id,
                    ErrorEventDTO(
                        event="error", data={"message": "Invalid event type"}
                    ),
                )
    except WebSocketDisconnect:
        await ws_manager.disconnect(user_id, lobby_id)
