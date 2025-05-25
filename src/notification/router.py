from fastapi import APIRouter
from fastapi.websockets import WebSocket, WebSocketDisconnect

from dependencies import WSAuthenticatedUserDep, UOWDep
from managers import ws_manager
from notification.ws_events import EVENT_MAP
from schemas import ErrorEventDTO

ws_router = APIRouter(prefix="/ws/notifications", tags=["WS Notification"])


@ws_router.websocket("/")
async def notifications_ws(
    websocket: WebSocket,
    uow: UOWDep,
    user: WSAuthenticatedUserDep,
):
    user_id = str(user.id)
    await ws_manager.connect_to_notification(user_id, websocket)
    try:
        while True:
            data: dict = await websocket.receive_json()
            event = data.get("event")
            payload = data.get("data", {})
            try:
                await EVENT_MAP[event](ws_manager, user_id, payload, uow)
            except KeyError:
                await ws_manager.send_to_user(
                    user_id,
                    ErrorEventDTO(
                        event="error", data={"message": "Invalid event type"}
                    ),
                )
    except WebSocketDisconnect:
        await ws_manager.disconnect(user_id)
