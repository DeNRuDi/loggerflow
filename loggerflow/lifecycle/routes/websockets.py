from fastapi.websockets import WebSocket, WebSocketDisconnect
from fastapi import Request, APIRouter

from loggerflow.lifecycle.utils.ws_manager import ConnectionManager
from loggerflow.lifecycle.database.queries import LifecycleQuery
from loggerflow.lifecycle.database.models import Status


router = APIRouter(prefix='/loggerflow')
manager = ConnectionManager()


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    backend_info = await manager.connect(websocket)
    await LifecycleQuery.create_or_update_project(backend_info)
    project_name = backend_info['project_name']
    await LifecycleQuery.set_project_status(project_name, Status.online)
    try:
        while True:
            result = await websocket.receive_json()
            if result['request_path'] == 'project_error':
                await LifecycleQuery.add_project_exception(result)
            elif result['request_path'] == 'heartbeat':
                await LifecycleQuery.update_heartbeat(result)
    except WebSocketDisconnect:
        await manager.disconnect(project_name)
        await LifecycleQuery.set_project_status(project_name, Status.offline)