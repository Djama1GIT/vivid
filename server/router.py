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
                generate_chapter(
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
    filename = Vivid.save_book_to_file(
        BookOfSessionBaseWithExtra(**book.__dict__)
    )
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


async def get_book_with_extra(session_name: uuid.UUID, book_repository: BookRepository):
    book_of_session: BookOfSessionBaseWithExtra = await book_repository.get_session(session_name)
    if not book_of_session:
        return None
    sections = await book_repository.session.run_sync(lambda s: book_of_session.sections)
    chapters = await serialize_chapters(sections, book_of_session.sections_list, book_repository.session)
    book_of_session.chapters = chapters
    return book_of_session


async def create_or_update_vivid_handler(data, session_name):
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

    return book_of_session


async def generate_sections_handler(
        book_of_session: BookOfSessionBaseWithExtra,
        book_repository: BookRepository,
        session_name: str,
        websocket
):
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
    else:
        await manager.send_json(
            {
                "code": 2,
                "sections": book_of_session.sections_list,
            },
            websocket
        )


async def confirm_sections_handler(data, book_of_session, book_repository, session_name):
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
                )
            )


async def confirm_chapters_handler(
        data: dict,
        book_of_session: BookOfSessionBaseWithExtra,
        book_repository: BookRepository,
        session_name: str | uuid.UUID,
        websocket: WebSocket
):
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


async def generate_book_handler(
        data: dict,
        book_of_session: BookOfSessionBaseWithExtra,
        book_repository: BookRepository,
        session_name: str
):
    logger.info(f'Command generate_book executed with sections: {data.get("sections")}')
    asyncio.get_running_loop().create_task(
        generate_book(
            BookOfSessionBaseWithExtra(**book_of_session.__dict__),
            book_repository,
            session_name,
        )
    )


async def assemble_to_pdf_handler(
        book_repository: BookRepository,
        session_name: str | uuid.UUID
):
    logger.info(f'Command assemble_to_pdf executed')
    book = await get_book_with_extra(session_name, book_repository)
    asyncio.get_running_loop().create_task(
        assemble_to_pdf(
            BookOfSessionBaseWithExtra(**book.__dict__),
            book_repository,
            session_name,
        )
    )


async def send_initial_data_handler(
        book_of_session: BookOfSessionBaseWithExtra,
        websocket: WebSocket
):
    """
    Send initial data from Vivid instance as JSON

    :param book_of_session:
    :param websocket:
    :return:
    """
    await manager.send_json(
        {
            "code": 1,
            "genre": book_of_session.genre,
            "bookName": book_of_session.book,
            "sectionsCount": book_of_session.sections_count,
            "sections": book_of_session.sections_list,
            "chaptersCount": book_of_session.chapters_count,
            "chapters": book_of_session.chapters,
            "chaptersLength": book_of_session.chapters_length,
            "gptVersion": book_of_session.v,
            "pregeneration": book_of_session.pregeneration,
            "link": f"http://localhost:{settings.SERVER_PORT}{book_of_session.filename}"
            if book_of_session.filename else "",
        },
        websocket,
    )


@router.websocket("/ws/")
async def websocket_endpoint(
        websocket: WebSocket,
        book_repository: BookRepository = Depends(get_book_repository(get_async_session))
):
    session_name = await manager.connect(websocket)
    logger.info(f'Websocket endpoint connected with session: {session_name}')
    book_of_session: BookOfSessionBaseWithExtra = await get_book_with_extra(session_name, book_repository)
    if book_of_session:
        await send_initial_data_handler(book_of_session, websocket)
    try:
        while manager.active_connections.get(session_name) is not None:
            data = await websocket.receive_json()
            if "cmd" in data and data["cmd"] == "create_or_update_vivid":
                book_of_session = await create_or_update_vivid_handler(data, session_name)

            elif "cmd" in data and book_of_session:
                match data["cmd"]:
                    case "generate_sections":
                        await generate_sections_handler(book_of_session, book_repository, session_name, websocket)

                    case "confirm_sections":
                        await confirm_sections_handler(data, book_of_session, book_repository, session_name)

                    case "confirm_chapters":
                        await confirm_chapters_handler(data, book_of_session, book_repository, session_name, websocket)

                    case "generate_book":
                        await generate_book_handler(data, book_of_session, book_repository, session_name)

                    case "assemble_to_pdf":
                        await assemble_to_pdf_handler(book_repository, session_name)

            elif not book_of_session:
                logger.warning(f'Instance does not exist')

    except WebSocketDisconnect:
        await manager.disconnect(session_name)
