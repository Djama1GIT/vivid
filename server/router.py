import asyncio
import time
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from config import settings
from utils.connection_manager import ConnectionManager
from vivid import Vivid
from utils.logger import logger

from schemas import BookOfSessionBaseWithExtra, ChapterBase, BookOfSessionBase, SectionBase
from repository import BookRepository
from dependencies import get_book_repository

from db import get_async_session

router = APIRouter(
    prefix='',
    tags=['Main']
)

manager = ConnectionManager()


# manager.content_instances["3d56977b-8383-462b-a77c-645277bbd3bb"] = Vivid(chapters_length=500)
# _instance = {
#     'genre': 'Фэнтези',
#     'book': 'Абоба',
#     'SECTIONS_COUNT': 2,
#     # 'SECTIONS_COUNT': 3,
#     'sections': [
#         (1, 'Путешествия сквозь Абобу'),
#         (2, 'Загадки и тайны Абобы'),
#         # (3, 'Сражения и судьбы в мире Абобы')
#     ],
#     'CHAPTERS_COUNT': 2,
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
#             ['2', 'Охота на магический источник Великой Реки', """
# 12312312
#
# 1231231
#             """],
#             # ['3', 'Подземелья таинственного Храма Забытых Руин'],
#             # ['4', 'Встреча с Древним Драконом Горных Вершин']
#         ],
#         'Загадки и тайны Абобы': [
#             ['1', "Загадки затерянного леса", """
# Lorem Ipsum is simply dummy text of the printing and typesetting industry.
#
# Lorem Ipsum has been the industry's standard dummy text ever since the 1500s,
#
# when an unknown printer took a galley of type and scrambled it to make a type specimen book.
#
# It has survived not only five centuries, but also the leap into electronic typesetting,
#
# remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset
#
# sheets containing Lorem Ipsum passages, and more recently with desktop publishing software
#
# like Aldus PageMaker including versions of Lorem Ipsum.
#             """],
#             ['2', "Тайна магического амулета", """
# Lorem Ipsum is simply dummy text of the printing and typesetting industry.
#
# Lorem Ipsum has been the industry's standard dummy text ever since the 1500s,
#
# when an unknown printer took a galley of type and scrambled it to make a type specimen book.
#
# It has survived not only five centuries, but also the leap into electronic typesetting,
#
# remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset
#
# sheets containing Lorem Ipsum passages, and more recently with desktop publishing software
#
# like Aldus PageMaker including versions of Lorem Ipsum.
#             """],
#             # ['3', "Секреты древнего храма Абобы"],
#             # ['4', "Погоня за пропавшей мудростью"]
#         ],
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
#     manager.content_instances["3d56977b-8383-462b-a77c-645277bbd3bb"].__dict__[key] = _instance[key]

async def generate_chapters_names_for_section(
        section: str,
        book: BookOfSessionBaseWithExtra,
        book_repository: BookRepository,
        session_name,
) -> list[(int, str)]:
    logger.info(f'The generation names of chapters of the section "{section}" has begun')
    chapters = await Vivid.generate_chapters(BookOfSessionBaseWithExtra(**book.__dict__), section)
    await book_repository.add_section(
        SectionBase(
            id=uuid.uuid4(),
            book_id=book.id,
            name=section,
            chapters_list=chapters,
        )
    )
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


async def generate_chapter(
        section: str,
        chapter: int,
        book: BookOfSessionBaseWithExtra,
        book_repository: BookRepository,
        session_name: str
):
    chapters = book.chapters.get(section)
    logger.info(f'The generation of the chapter "{chapters[chapter]}" has begun')
    chapter_text: str = await Vivid.generate_chapter(
        BookOfSessionBaseWithExtra(**book.__dict__),
        section,
        chapter,
        chapters
    )
    if len(chapters[chapter]) >= 3:
        chapters[chapter][2] = chapter_text
    elif len(chapters[chapter]):
        chapters[chapter].append(chapter_text)
    section_uuid = await book_repository.get_section_uuid(
        book.id,
        section,
    )
    await book_repository.add_chapter(
        ChapterBase(
            id=uuid.uuid4(),
            book_id=book.id,
            section_id=section_uuid,
            name=chapters[chapter][1],
            text=chapter_text
        )
    )
    await manager.send_json(
        {
            "code": 5,
            "section": section,
            "chapter": chapter,
            "chapter_text": chapter_text,
        },
        manager.active_connections[session_name]
    )


async def generate_book(
        book: BookOfSessionBaseWithExtra,
        book_repository: BookRepository,
        session_name: str
):
    logger.info(f'The generation of the book "{book.book}" ({book.id}) has begun')
    for section in book.chapters:
        logger.info(f'Now generating section: {section}')
        tasks = []
        for i in range(len(book.chapters.get(section))):
            task = asyncio.create_task(
                generate_chapter(  # TODO
                    section,
                    i,
                    book,
                    book_repository,
                    session_name)
            )
            tasks.append(task)
            time.sleep(1)
        await asyncio.gather(*tasks)


async def assemble_to_pdf(book: BookOfSessionBaseWithExtra, book_repository: BookRepository, session_name: str):
    logger.info(f'The saving the book "{book.book}" ({book.id}) in pdf has begun')
    Vivid.save_book_to_file(
        BookOfSessionBaseWithExtra(**book.__dict__)
    )  # TODO
    filename = f"/books/book-{book.id}-{book.book}.md"
    await book_repository.update_session(
        BookOfSessionBase(
            **book.__dict__ | {"filename": filename},
        )
    )
    await manager.send_json(
        {
            "code": 6,
            "link": f"http://localhost:{settings.SERVER_PORT}{filename}",
        },
        manager.active_connections[session_name],
    )


async def serialize_chapters(sections, sections_list, session):
    indexes = list(
                {
                    idx: sec for idx, sec in sections_list
                }.values()
            )
    return {
        (_s := await section.json(session))["name"]: _s.get("chapters", [])
        for section in sorted(
            sections,
            key=lambda x: indexes.index(x.name)
        )
    }


@router.websocket("/ws/")
async def websocket_endpoint(
        websocket: WebSocket,
        book_repository: BookRepository = Depends(get_book_repository(get_async_session))
):
    session_name = await manager.connect(websocket)
    logger.info(f'Websocket endpoint connected with session: {session_name}')
    book_of_session: BookOfSessionBaseWithExtra = await book_repository.get_session(session_name)
    if book_of_session:
        # Send initial data from Vivid instance as JSON
        sections = await book_repository.session.run_sync(lambda s: book_of_session.sections)
        chapters = await serialize_chapters(sections, book_of_session.sections_list, book_repository.session)
        await manager.send_json(
            {
                "code": 1,
                "genre": book_of_session.genre,
                "bookName": book_of_session.book,
                "sectionsCount": book_of_session.sections_count,
                "sections": book_of_session.sections_list,
                "chaptersCount": book_of_session.chapters_count,
                "chapters": chapters,
                "chaptersLength": book_of_session.chapters_length,
                "gptVersion": book_of_session.v,
                "pregeneration": book_of_session.pregeneration,
                "link": f"http://localhost:{settings.SERVER_PORT}{book_of_session.filename}"
                if book_of_session.filename else "",
            },
            websocket,
        )
        book_of_session.chapters = chapters
    try:
        while manager.active_connections.get(session_name) is not None:
            data = await websocket.receive_json()
            if "cmd" in data and data["cmd"] == "create_or_update_vivid":
                logger.info(f'Command create_or_update_vivid executed with data: {data}')
                sections_count = data["sectionsCount"]
                chapters_count = data["chaptersCount"]
                chapters_length = data["chaptersLength"]
                gpt_version = data["gptVersion"]
                genre = data["genre"]
                book_name = data["bookName"]
                book_of_session = BookOfSessionBaseWithExtra(
                    id=session_name,
                    book=book_name,
                    genre=genre,
                    sections_count=sections_count,
                    chapters_count=chapters_count,
                    chapters_length=chapters_length,
                    v=gpt_version,
                )
            elif "cmd" in data and book_of_session:
                match data["cmd"]:
                    case "generate_sections":
                        if not book_of_session.sections_list:
                            logger.info(f'Command generate_sections executed')
                            sections = await Vivid.generate_sections(
                                BookOfSessionBaseWithExtra(**book_of_session.__dict__)
                            )
                            book_of_session.sections_list = sections
                        new_session = await book_repository.add_session(
                            BookOfSessionBase(**book_of_session.__dict__)
                        )
                        if not new_session:
                            logger.error("An error occurred while creating a new session")
                            await manager.send_error(
                                session_name,
                                "Произошла ошибка сервера"
                            )
                            await websocket.close()
                        await manager.send_json(
                            {
                                "code": 2,
                                "sections": book_of_session.sections_list,
                            },
                            websocket
                        )
                    case "confirm_sections":
                        logger.info(f'Command confirm_sections executed with sections: {data.get("sections")}')
                        if "sections" in data:
                            book_of_session.sections_list = []
                            for idx, section in enumerate(data["sections"]):
                                book_of_session.sections_list += [(idx + 1, section["name"])]
                            await book_repository.update_session(
                                BookOfSessionBase(**book_of_session.__dict__)
                            )
                            for idx, section in book_of_session.sections_list:
                                asyncio.get_running_loop().create_task(
                                    generate_chapters_names_for_section(
                                        section,
                                        BookOfSessionBaseWithExtra(**book_of_session.__dict__),
                                        book_repository,
                                        session_name
                                    )  # TODO save chapters_list
                                )
                    case "confirm_chapters":
                        logger.info(f'Command confirm_chapters executed with sections: {data.get("sections")}')
                        if "sections" in data:
                            book_of_session.chapters = {}
                            for section in data["sections"]:
                                book_of_session.chapters[section["name"]] = section.get("chapters") or []
                                section_uuid = await book_repository.get_section_uuid(
                                    session_name,
                                    section["name"],
                                )
                                await book_repository.update_section(
                                    SectionBase(
                                        id=section_uuid,
                                        book_id=session_name,
                                        name=section["name"],
                                        chapters_list=section.get("chapters") or []
                                    )
                                )
                        book_of_session.pregeneration = await Vivid.generate_pregeneration(
                            BookOfSessionBaseWithExtra(**book_of_session.__dict__)
                        )
                        await book_repository.update_session(
                            BookOfSessionBase(**book_of_session.__dict__)
                        )
                        await manager.send_json(
                            {
                                "code": 4,
                                "pregeneration": book_of_session.pregeneration,
                            },
                            websocket
                        )
                    case "generate_book":
                        logger.info(f'Command generate_book executed with sections: {data.get("sections")}')
                        asyncio.get_running_loop().create_task(
                            generate_book(
                                BookOfSessionBaseWithExtra(**book_of_session.__dict__),
                                book_repository,
                                session_name,
                            )
                        )
                    case "assemble_to_pdf":
                        logger.info(f'Command assemble_to_pdf executed')
                        asyncio.get_running_loop().create_task(
                            assemble_to_pdf(
                                BookOfSessionBaseWithExtra(**book_of_session.__dict__),
                                book_repository,
                                session_name,
                            )
                        )

            elif not book_of_session:
                logger.warning(f'Instance does not exist')
                await manager.send_json(
                    {
                        "message": "Instance does not exist",
                    },
                    websocket
                )

    except WebSocketDisconnect:
        await manager.disconnect(session_name)
