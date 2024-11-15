from fastapi.websockets import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        # self.queues: dict[str, asyncio.Queue] = {}

    async def connect(self, websocket: WebSocket) -> dict:
        await websocket.accept()
        data = await websocket.receive_json()
        project_name = data['project_name']
        self.active_connections.update({project_name: websocket})
        # self.queues[project_name] = asyncio.Queue()
        return data

    async def disconnect(self, project_name: str):
        self.active_connections.pop(project_name)
        # self.queues.pop(project_name)

    def get_all_connections(self):
        return self.active_connections

    def get_ws_from_project(self, project_name: str):
        return self.active_connections.get(project_name)

    # async def create_request(self, request_path: str, project_name: str, params: dict):
    #     connection = self.active_connections.get(project_name)
    #     await connection.send_json({'request_path': request_path, 'params': params})
    #     response = await self.queues[project_name].get()
    #     return response

