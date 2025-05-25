from typing import Dict, Set
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from auth.schemas import UserInfoDTO
from dependencies import AuthenticatedUserDep, UOWDep, WSAuthenticatedUserDep
from game.schemas import LobbyIdDTO
from game.services.game import GameService
from game.services.lobby import LobbyService
from managers import ws_manager
from unitofwork import IUnitOfWork

router = APIRouter(prefix="/games", tags=["Game"])

_lobby_ready: Dict[str, Set[str]] = {}


@router.post("/lobbies")
async def create_lobby(
    user: AuthenticatedUserDep,
    uow: UOWDep,
) -> LobbyIdDTO:
    return await LobbyService(uow).create_lobby(user)


@router.websocket("/ws/lobby/{lobby_id}")
async def lobby_ws_endpoint(
    websocket: WebSocket,
    lobby_id: str,
    user: UserInfoDTO = Depends(WSAuthenticatedUserDep),
    uow: IUnitOfWork = Depends(UOWDep),
):
    user_id = str(user.id)
    # Register connection to lobby-specific channel
    await ws_manager.connect(websocket, user_id, lobby_id)
    _lobby_ready.setdefault(lobby_id, set())
    try:
        while True:
            message = await websocket.receive_json()
            event = message.get("event")
            payload = message.get("data", {})

            if event == "invite":
                invite = InvitePayload(**payload)
                await LobbyService(uow).add_user_to_lobby(
                    UserInfoDTO(id=UUID(invite.invitee_id), username=""),
                    invite.lobby_id,
                )
                event_dto = LobbyEventDTO(event="invite", data=invite.dict())
                # Notify via notifications channel
                await ws_manager.send_to_user(invite.invitee_id, event_dto)

            elif event == "ready":
                ready = ReadyPayload(**payload)
                _lobby_ready[lobby_id].add(ready.user_id)
                event_dto = LobbyEventDTO(event="ready", data=ready.dict())
                await ws_manager.broadcast_to_lobby(lobby_id, event_dto)
                members = await ws_manager.get_lobby_user_ids(lobby_id)
                if _lobby_ready[lobby_id] >= set(members):
                    players_info = [
                        LobbyUserInfoDTO(
                            id=UUID(uid), username="", is_leader=False
                        )
                        for uid in members
                    ]
                    game_info = await GameService(uow).create_game(
                        players_info, True
                    )
                    start = StartPayload(
                        game_id=str(game_info.id), lobby_id=lobby_id
                    )
                    event_dto = LobbyEventDTO(event="start", data=start.dict())
                    await ws_manager.broadcast_to_lobby(lobby_id, event_dto)
                    _lobby_ready[lobby_id].clear()

    except WebSocketDisconnect:
        await ws_manager.disconnect(user_id, lobby_id)
        _lobby_ready[lobby_id].discard(user_id)
