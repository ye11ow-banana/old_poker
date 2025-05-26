from fastapi import APIRouter
from fastapi.websockets import WebSocket, WebSocketDisconnect

from dependencies import WSAuthenticatedUserDep, UOWDep
from managers import notification_ws_manager
from notification.ws_events import EVENT_MAP
from schemas import ErrorEventDTO

ws_router = APIRouter(prefix="/ws/notifications", tags=["WS Notification"])


@ws_router.websocket("/")
async def notifications_ws(
    websocket: WebSocket,
    uow: UOWDep,
    user: WSAuthenticatedUserDep,
):
    await notification_ws_manager.connect(user.id, websocket)
    try:
        while True:
            data: dict = await websocket.receive_json()
            event = data.get("event")
            payload = data.get("data", {})
            try:
                await EVENT_MAP[event](notification_ws_manager, user.id, payload, uow)
            except KeyError:
                await notification_ws_manager.send_to_user(
                    user.id,
                    ErrorEventDTO(
                        event="error", data={"message": "Invalid event type"}
                    ),
                )
    except WebSocketDisconnect:
        await notification_ws_manager.disconnect(user.id)
