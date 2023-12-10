import re
import uuid

from starlette.websockets import WebSocketState

from .logger import logger

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        try:
            cache = await websocket.receive_json()
        except Exception as exc:
            logger.warn(exc.args[0])
            cache = {"session": str(uuid.uuid4())}
        session_name = cache.get("session")
        pattern = re.compile(r'^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$', re.IGNORECASE)
        if not session_name or not pattern.match(session_name):
            session_name = str(uuid.uuid4())
        if session_name in self.active_connections.keys():
            await self.send_error(
                session_name,
                "Произошла ошибка, возможно Вы подключились к данной сессии через другое устройство.",
            )
            await self.send_json(
                {
                    "code": -1,
                    "session": "",
                },
                self.active_connections[session_name])
            await self.disconnect(session_name)
            logger.warning(f'Parallel connection session_name: {session_name}')
        await self.send_json(
            {
                "code": -1,
                "session": session_name,
            },
            websocket)
        self.active_connections[session_name] = websocket
        logger.info(f'New connection established with session: {session_name}')
        return session_name

    async def disconnect(self, session_name: str):
        websocket = self.active_connections.pop(session_name, None)
        if websocket is not None and websocket.client_state is not WebSocketState.DISCONNECTED:
            if session_name in self.active_connections:
                await self.send_json(
                    {
                        "code": -1,
                        "session": "",
                    },
                    self.active_connections[session_name])
            await websocket.close()
            del websocket
        logger.info(f'Connection with session {session_name} disconnected')

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        await websocket.send_text(message)
        logger.info(f'Sent personal message: {message}')

    @staticmethod
    async def send_json(data: dict, websocket: WebSocket):
        if websocket.client_state is WebSocketState.CONNECTED:
            await websocket.send_json(data)
            logger.info(f'Sent JSON data: {data}')
        else:
            logger.error(f'The client has already disconnected')

    async def send_error(self, session_name, message):
        await self.send_json(
            {
                "code": 418,
                "message": "",
            },
            self.active_connections[session_name])
