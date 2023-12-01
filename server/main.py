import asyncio

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from server.vivid import Vivid

import logging

# Create a custom logger
logger = logging.getLogger(__name__)

# Set level of logger
logger.setLevel(logging.DEBUG)

# Create handlers
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.DEBUG)

# Create formatters and add it to handlers
c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)

# Add handlers to the logger
logger.addHandler(c_handler)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешает все методы
    allow_headers=["*"],  # Разрешает все заголовки
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.vivid_instances: dict[str, Vivid] = {}

    async def connect(self, websocket: WebSocket):
        session_name = "aboba"
        await websocket.accept()
        self.active_connections[session_name] = websocket
        if session_name not in self.vivid_instances:
            self.vivid_instances[session_name] = Vivid()  # Initialize Vivid with default parameters
        logger.info(f'New connection established with session: {session_name}')
        return session_name

    def disconnect(self, session_name: str):
        self.active_connections.pop(session_name, None)
        self.vivid_instances.pop(session_name, None)
        logger.info(f'Connection with session {session_name} disconnected')

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        await websocket.send_text(message)
        logger.info(f'Sent personal message: {message}')

    @staticmethod
    async def send_json(data: dict, websocket: WebSocket):
        await websocket.send_json(data)
        logger.info(f'Sent JSON data: {data}')

    def get_vivid_instance(self, session_name: str):
        return self.vivid_instances.get(session_name, None)


manager = ConnectionManager()


async def generate_chapters_names_for_section(section: str, vivid_instance: Vivid, session_name) -> list[(int, str)]:
    chapters = await vivid_instance.generate_chapters(section)
    vivid_instance.chapters[section] = chapters

    await manager.send_json(
        {
            "code": 3,
            "section": section,
            "chapters": chapters,
        },
        manager.active_connections[session_name]
    )
    """
    TODO: returning chapters
    :param chapter: str(chapter_name)
    :return: list([(idx, chapter_name)])
    """
    return chapters


async def generate_chapter(section: dict, chapter: int, vivid_instance: Vivid, session_name: str):
    # TODO: вывод процентов готовности на фронт
    chapter = await vivid_instance.generate_chapter(chapter, section["chapters"])
    logger.info(f'Chapter generated: {chapter}')


@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket):
    session_name = await manager.connect(websocket)
    logger.info(f'Websocket endpoint connected with session: {session_name}')
    vivid_instance = manager.get_vivid_instance(session_name)
    if vivid_instance:
        # Send initial data from Vivid instance as JSON
        await manager.send_json(
            {
                "code": 1,
                "genre": vivid_instance.genre,
                "bookName": vivid_instance.book,
                "sectionsCount": vivid_instance.SECTIONS_COUNT,
                "chaptersCount": vivid_instance.CHAPTERS_COUNT,
                "chaptersLength": vivid_instance.CHAPTERS_LENGTH,
                "gptVersion": "3.5",  # TODO: в vivid gpt это функция, надо бы сделать как-то получение просто версии
                "pregeneration": vivid_instance.pregeneration
            },
            websocket,
        )
    try:
        while True:
            data = await websocket.receive_json()  # receive data as JSON
            # Parse the data from JSON
            if "cmd" in data and data["cmd"] == "create_or_update_vivid":
                logger.info(f'Command create_or_update_vivid executed with data: {data}')
                sections_count = data["sectionsCount"]
                chapters_count = data["chaptersCount"]
                chapters_length = data["chaptersLength"]
                gpt_version = data["gptVersion"]
                genre = data["genre"]
                book_name = data["bookName"]
                vivid = Vivid(sections_count=int(sections_count),
                              chapters_count=int(chapters_count),
                              chapters_length=int(chapters_length),
                              v=gpt_version,
                              genre=genre,
                              book=book_name)
                manager.vivid_instances[session_name] = vivid
                vivid_instance = vivid
            elif "cmd" in data and vivid_instance:
                match data["cmd"]:
                    case "generate_sections":
                        logger.info(f'Command generate_sections executed')
                        sections = await vivid_instance.generate_sections()
                        await manager.send_json(
                            {
                                "code": 2,
                                "sections": sections,
                            },
                            websocket
                        )
                    case "confirm_sections":
                        logger.info(f'Command confirm_sections executed with sections: {data.get("sections")}')
                        if "sections" in data:
                            vivid_instance.sections = []
                            for idx, section in enumerate(data["sections"]):
                                vivid_instance.sections += [(idx + 1, section["name"])]
                            for idx, section in vivid_instance.sections:
                                asyncio.get_running_loop().create_task(
                                    generate_chapters_names_for_section(section, vivid_instance, session_name)
                                )
                                # TODO: asyncio - запуск генерации глав для каждого раздела,
                                #  асинхронно, когда заканчивается генерация какой-либо из глав, она отправляется
                                #  на фронт, когда сгенерируются все главы, отправляется сигнал об этом.
                                #  Добавить пользователю кнопку продолжения генерации или пере-генерации.
                        await manager.send_json(
                            {
                                "code": 200,
                            },
                            websocket
                        )
                    case "confirm_chapters":
                        logger.info(f'Command confirm_chapters executed with sections: {data.get("sections")}')
                        if "sections" in data:
                            vivid_instance.chapters = data["sections"]
                        print(vivid_instance.chapters)

                        pregeneration = await vivid_instance.generate_pregeneration()
                        await manager.send_json(
                            {
                                "code": 4,
                                "pregeneration": pregeneration,
                            },
                            websocket
                        )
                    case "generate_book":
                        logger.info(f'Command generate_book executed with sections: {data.get("sections")}')
                        for section in vivid_instance.chapters:
                            for i in range(len(section.get("chapters"))):
                                asyncio.get_running_loop().create_task(
                                    generate_chapter(section, i, vivid_instance, session_name)
                                )
                        await manager.send_json(
                            {
                                "code": 200,
                            },
                            websocket
                        )
                        # TODO: генерация каждой главы, сборка в книгу
            elif not vivid_instance:
                logger.warning(f'Instance does not exist')
                await manager.send_json(
                    {
                        "message": "Instance does not exist",
                    },
                    websocket
                )

            # result = await vivid()
            # await manager.send_personal_message(result.replace('\n\n', '<br>'), websocket)
    except WebSocketDisconnect:
        manager.disconnect(session_name)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8081)
