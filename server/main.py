import asyncio
import os
import sys
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

server_path = os.path.join(os.getcwd(), "server")
sys.path.insert(0, server_path)

from vivid import Vivid

from config import settings

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

c_handler = logging.StreamHandler()
c_handler.setLevel(logging.DEBUG)

c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)

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
        # self.vivid_instances.pop(session_name, None)
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


# manager.vivid_instances["aboba"] = Vivid(chapters_length=500)
# _instance = {
#     'genre': 'Фэнтези',
#     'book': 'Абоба',
#     'SECTIONS_COUNT': 1,
#     # 'SECTIONS_COUNT': 3,
#     'sections': [
#         (1, 'Путешествия сквозь Абобу'),
#         # (2, 'Загадки и тайны Абобы'),
#         # (3, 'Сражения и судьбы в мире Абобы')
#     ],
#     'CHAPTERS_COUNT': 1,
#     # 'CHAPTERS_COUNT': 4,
#     'chapters': {
#         'Путешествия сквозь Абобу': [
#             ['1', 'Непроглядные тропы Абобы',
#              """
# Эльриан стоял на пороге Долины Вечной Тени, ощущая волнение и тревогу. Он знал, что перед ним длинный и опасный путь через загадочную Абобу, где каждый шаг мог оказаться ловушкой или испытанием. Но судьба принесла ему эту миссию - спасти Абобу от темных сил, жаждущих власти.
#
# Первые шаги в лес Забытых Снов были полны тайны и магии. Древние деревья шептали свои загадки, а изумрудные огоньки искрились вокруг, создавая впечатление, что время здесь не имеет значения. Эльриан продолжал свое путешествие, уверенный в своей силе и важности его задачи.
#
# Придя к Серебряному фонтану, Эльриан обнаружил странный ключ, который подсказал ему дальнейший путь. Он открыл Храм Перевернутой Звезды и сразу почувствовал власть, которая окутывала это место. Там он встретил загадочную рассветную деву Айлин, которая обладала необычными способностями и знала многое о предстоящей битве.
#
# Эльриану потребовалось все его мастерство волшебника, чтобы пройти через Башню Последнего Вздоха. Это было испытание для его силы и ума, но он смог справиться с ним благодаря своей настойчивости и решимости.
#
# В пещере Забытых Молитв Эльриан обнаружил старого мудреца Каладора, который являлся хранителем не только Долины Вечной Тени, но и тайн Абобы. Каладор рассказал ему о древнем артефакте "Ключи Времени" и о легенде Великого Волшебника, который мог спасти Абобу от гибели.
#
# Направляясь к Горе Возрождения, Эльриан и его верные спутники - отважный воин Леонард и хитрая ведьма Иллиана - понимали, что перед ними огромная битва за власть над Абобой. Они должны найти Зал Зеркал Времени, чтобы разгадать пророчество и спасти мир.
#
# Так началось путешествие сквозь Абобу, полное опасностей и тайн. Впереди ждали непроглядные тропы и испытания, но Эльриан и его команда были готовы пройти через все, чтобы вернуть мир к свету и благополучию.
#              """
#              ],
#             # ['2', 'Охота на магический источник Великой Реки'],
#             # ['3', 'Подземелья таинственного Храма Забытых Руин'],
#             # ['4', 'Встреча с Древним Драконом Горных Вершин']
#         ],
#         # 'Загадки и тайны Абобы': [
#         #     ['1', "Загадки затерянного леса"],
#         #     ['2', "Тайна магического амулета"],
#         #     ['3', "Секреты древнего храма Абобы"],
#         #     ['4', "Погоня за пропавшей мудростью"]
#         # ],
#         # 'Сражения и судьбы в мире Абобы': [
#         #     ['1', 'Под покровом тьмы'],
#         #     ['2', 'Вихрь страстей'],
#         #     ['3', 'Символы судьбы'],
#         #     ['4', 'Пробуждение героев']
#         # ]
#     },
#     'CHAPTERS_LENGTH': 500,
#     'pregeneration': 'Основные сюжетные места/темы/имена/названия мест/имена '
#                      'героев (если уместно в данной книге):'
#                      '\n\nСюжетные места:\n'
#                      '1. Долина Вечной Тени\n'
#                      '2. Город Сияющих Башен\n'
#                      '3. Лес Забытых Снов\n'
#                      '4. Остров Потерянных Чудес\n'
#                      '5. Гора Возрождения\n\n'
#                      'Темы:\n'
#                      '1. Магический артефакт "Ключи Времени"\n'
#                      '2. Пророчества и предсказания\n'
#                      '3. Загадочная рассветная дева\n'
#                      '4. Затерянная легенда о Великом Волшебнике\n'
#                      '5. Битва за власть над Абобой\n\n'
#                      'Имена героев:\n'
#                      '1. Эльриан - юный волшебник, '
#                      'избранный судьбой для спасения Абобы\n'
#                      '2. Айлин - загадочная рассветная дева, '
#                      'обладающая необычными способностями\n'
#                      '3. Каладор - старый мудрец и '
#                      'хранитель Долины Вечной Тени\n'
#                      '4. Леонард - отважный воин, '
#                      'стремящийся разгадать загадки Абобы\n'
#                      '5. Иллиана - хитрая ведьма, ставшая соперницей '
#                      'Эльриана в битве за власть\n\n'
#                      'Названия мест:\n'
#                      '1. Серебряный фонтан\n'
#                      '2. Храм Перевернутой Звезды\n'
#                      '3. Башня Последнего Вздоха\n'
#                      '4. Пещера Забытых Молитв\n'
#                      '5. Зал Зеркал Времени\n\n'
#                      'Книга "Абоба" - это захватывающий рассказ о '
#                      'приключениях юного волшебника Эльриана,'
#                      ' который отправляется в путешествие сквозь '
#                      'загадочную и опасную Абобу. '
#                      'В этом мире он сталкивается с тайнами и загадками, '
#                      'преследуемыми злыми силами и сражается '
#                      'за судьбу всего мира. Вместе со своими спутниками, '
#                      'Эльриану предстоит раскрыть запутанные загадки Абобы, '
#                      'найти древний артефакт и разгадать пророчество, '
#                      'чтобы спасти мир от неминуемой гибели.'
# }
# for key in _instance:
#     manager.vivid_instances["aboba"].__dict__[key] = _instance[key]


async def generate_chapters_names_for_section(section: str, vivid_instance: Vivid, session_name) -> list[(int, str)]:
    logger.info(f'The generation chapters of the section "{section}" has begun')
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


async def generate_chapter(section: str, chapter: int, vivid_instance: Vivid, session_name: str):
    chapters = vivid_instance.chapters.get(section)
    logger.info(f'The generation of the chapter "{chapters[chapter]}" has begun')
    chapter_text: str = await vivid_instance.generate_chapter(section, chapter, chapters)
    if len(chapters[chapter]) >= 3:
        chapters[chapter][2] = chapter_text
    elif len(chapters[chapter]):
        chapters[chapter].append(chapter_text)
    await manager.send_json(
        {
            "code": 5,
            "section": section,
            "chapter": chapter,
            "chapter_text": chapter_text,
        },
        manager.active_connections[session_name]
    )


async def generate_book(vivid_instance: Vivid, session_name: str):
    logger.info(f'The generation of the book "{vivid_instance.book}" ({vivid_instance.book_id}) has begun')
    for section in vivid_instance.chapters:
        logger.info(f'Now generating section: {section}')
        tasks = []
        for i in range(len(vivid_instance.chapters.get(section))):
            time.sleep(20)
            task = asyncio.create_task(
                generate_chapter(
                    section,
                    i,
                    vivid_instance,
                    session_name)
            )
            tasks.append(task)
        await asyncio.gather(*tasks)


async def assemble_to_pdf(vivid_instance: Vivid, session_name: str):
    # temporarily, and then it will be deleted:
    # save to md
    logger.info(f'The saving the book "{vivid_instance.book}" ({vivid_instance.book_id}) in pdf has begun')
    vivid_instance.save_book_to_file()  # TODO: change saving from .md to .pdf

    await manager.send_json(
        {
            "code": 6,
            "link": "#",
        },
        manager.active_connections[session_name],
    )


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
                "sections": vivid_instance.sections,
                "chaptersCount": vivid_instance.CHAPTERS_COUNT,
                "chapters": vivid_instance.chapters,
                "chaptersLength": vivid_instance.CHAPTERS_LENGTH,
                "gptVersion": {
                    vivid_instance.gpt35: "3.5",
                    vivid_instance.gpt37: "3.7",
                    vivid_instance.gpt4: "4",
                }[vivid_instance.gpt],
                "pregeneration": vivid_instance.pregeneration
            },
            websocket,
        )
    try:
        while True:
            data = await websocket.receive_json()
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
                        vivid_instance.sections = sections
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
                    case "confirm_chapters":
                        logger.info(f'Command confirm_chapters executed with sections: {data.get("sections")}')
                        if "sections" in data:
                            vivid_instance.chapters = {}
                            for section in data["sections"]:
                                vivid_instance.chapters[section["name"]] = section.get("chapters") or []

                        vivid_instance.pregeneration = await vivid_instance.generate_pregeneration()

                        await manager.send_json(
                            {
                                "code": 4,
                                "pregeneration": vivid_instance.pregeneration,
                            },
                            websocket
                        )
                    case "generate_book":
                        logger.info(f'Command generate_book executed with sections: {data.get("sections")}')
                        asyncio.get_running_loop().create_task(
                            generate_book(vivid_instance, session_name)
                        )
                    case "assemble_to_pdf":
                        logger.info(f'Command assemble_to_pdf executed')
                        # TODO
                        asyncio.get_running_loop().create_task(
                            assemble_to_pdf(vivid_instance, session_name)
                        )

            elif not vivid_instance:
                logger.warning(f'Instance does not exist')
                await manager.send_json(
                    {
                        "message": "Instance does not exist",
                    },
                    websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(session_name)


if __name__ == '__main__':
    directory = 'server.' if settings.NODE_ENV != 'production' and \
                             os.path.dirname(os.path.abspath(__file__)).split('/')[-1] != 'server' else ''
    os.system(f"gunicorn {directory}"
              f"main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8077")
