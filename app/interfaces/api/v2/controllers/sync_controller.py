"""Sync Controller (v2) providing WebSocket-based bulk sync endpoint.

This version introduces a WebSocket endpoint that accepts a bulk sync payload
and streams (currently in a single final message) the notifications result
instead of relying on a status polling endpoint.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.dependencies.celery_dependencies import get_sync_service
from app.dependencies.services_dependencies import get_jwt_service
from app.schemas.sync_schema import SyncBulkRequest
from app.utils.logger_util import get_logger

router = APIRouter(prefix="/sync", tags=["sync-v2"])


@router.websocket("/bulk/ws")
async def websocket_bulk_sync(websocket: WebSocket) -> None:  # pragma: no cover (interactive)
    """WebSocket endpoint for running bulk sync and receiving notifications.

    Protocol:
      1. Connect: ws://localhost:8000/api/v2/sync/bulk/ws?token=JWT
      2. Send JSON payload of SyncBulkRequest: {"changes": [...]}.
      3. Receive ack message.
      4. Receive completed (or error) message with notifications.

    Currently sends notifications once at completion (no per-change streaming yet).
    """
    await websocket.accept()
    operation_id = str(uuid.uuid4())
    try:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.send_json(
                {
                    "type": "error",
                    "operation_id": operation_id,
                    "status": "failed",
                    "error": "Missing token query parameter.",
                },
            )
            await websocket.close(code=4401)
            return

        try:
            current_user_id = get_jwt_service().decode_token_user_id(token)
        except Exception as e:  # noqa: BLE001
            await websocket.send_json(
                {
                    "type": "error",
                    "operation_id": operation_id,
                    "status": "failed",
                    "error": f"Invalid token: {e!s}",
                },
            )
            await websocket.close(code=4403)
            return

        payload = await websocket.receive_json()
        try:
            request = SyncBulkRequest.model_validate(payload)
        except Exception as e:  # noqa: BLE001
            await websocket.send_json(
                {
                    "type": "error",
                    "operation_id": operation_id,
                    "status": "failed",
                    "error": f"Invalid payload: {e!s}",
                },
            )
            await websocket.close(code=4400)
            return

        await websocket.send_json(
            {
                "type": "ack",
                "operation_id": operation_id,
                "status": "started",
                "created_at": datetime.now(tz=UTC).isoformat(),
            },
        )

        sync_service = get_sync_service()
        result = await sync_service.handle_bulk_sync(request, current_user_id)
        notifications = result.get("notifications", [])

        await websocket.send_json(
            {
                "type": "completed",
                "operation_id": operation_id,
                "status": "completed",
                "completed_at": datetime.now(tz=UTC).isoformat(),
                "notifications": notifications,
            },
        )
        await websocket.close()
    except WebSocketDisconnect:
        get_logger().warning("WebSocket disconnected: operation_id=%s", operation_id)
    except Exception as e:  # noqa: BLE001
        get_logger().error("Error during websocket bulk sync: %s", str(e))
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "operation_id": operation_id,
                    "status": "failed",
                    "error": str(e),
                },
            )
        finally:
            await websocket.close(code=1011)
