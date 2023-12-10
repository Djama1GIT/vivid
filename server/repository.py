from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from models import Session as Book, Section, Chapter
from schemas import ChapterBase, BookOfSessionBase, SectionBase

from utils.logger import logger


class BookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_session(self, session_id: UUID):
        try:
            session = await self.session.run_sync(lambda s: s.query(Book).filter_by(id=session_id).first())
            logger.info(f"The session {session_id} extracted: {session.__dict__ if session else None}")
            return session
        except SQLAlchemyError as exc:
            logger.error(exc)
            return None

    async def get_sections(self, session_id: UUID):
        try:
            sections = await self.session.run_sync(
                lambda s: s.query(Section).filter_by(book_id=session_id).all()
            )
            logger.info(f"Sections extracted via session_id({session_id}): {sections.__dict__}")
            return sections
        except SQLAlchemyError as exc:
            logger.error(exc)
            return None

    async def get_section_uuid(self, session_id: UUID, section_name):
        try:
            section = await self.session.run_sync(
                lambda s: s.query(Section).filter_by(book_id=session_id, name=section_name).first()
            )
            logger.info(f"The section uuid extracted via session_id({session_id}) "
                        f"and section_name({section_name}): {section.id if section else None}")
            return section.id if section else None
        except SQLAlchemyError as exc:
            logger.error(f"An error occurred while getting uuid of "
                         f"the section {section_name} of the session {session_id}")
            logger.error(exc)
            return None

    async def get_chapters(self, section_id: UUID):
        try:
            chapters = await self.session.run_sync(
                lambda s: s.query(Chapter).filter_by(section_id=section_id).all()
            )
            logger.info(f"Chapters from section {section_id} extracted: {chapters.__dict__}")
            return chapters
        except SQLAlchemyError as exc:
            logger.error(f"An error occurred while pulling out chapters of the section {section_id}")
            logger.error(exc)
            return None

    async def add_session(self, session: BookOfSessionBase):
        new_session = Book(**session.model_dump())
        self.session.add(new_session)
        try:
            await self.session.commit()
            logger.info(f"The session added: {session.__dict__}")
            return True
        except Exception as exc:
            await self.session.rollback()
            logger.error(f"An error occurred while adding the session: {session.__dict__}")
            logger.error(exc)
            return False

    async def add_section(self, section: SectionBase):
        new_section = Section(**section.model_dump())
        self.session.add(new_section)
        try:
            await self.session.commit()
            logger.info(f"The section added: {section.__dict__}")
            return True
        except Exception as exc:
            await self.session.rollback()
            logger.error(f"An error occurred while adding the section: {section.__dict__}")
            logger.error(exc)
            return False

    async def add_chapter(self, chapter: ChapterBase):
        new_chapter = Chapter(**chapter.model_dump())
        self.session.add(new_chapter)
        try:
            await self.session.commit()
            logger.info(f"The chapter added: {chapter.__dict__}")
            return True
        except Exception as exc:
            await self.session.rollback()
            logger.error(f"An error occurred while adding the chapter: {chapter.__dict__}")
            logger.error(exc)
            return False

    async def update_session(self, session: BookOfSessionBase):
        update_stmt = update(Book).where(Book.id == session.id).values(**session.model_dump())
        try:
            await self.session.execute(update_stmt)
            await self.session.commit()
            logger.info(f"The session {session.id} updated: {session.__dict__}")
            return True
        except Exception as exc:
            await self.session.rollback()
            logger.error(f"An error occurred while updating the session {session.id}: {session.__dict__}")
            logger.error(exc)
            return False

    async def update_section(self, section: SectionBase):
        update_stmt = update(Section).where(Section.id == section.id).values(**section.model_dump())
        try:
            await self.session.execute(update_stmt)
            await self.session.commit()
            logger.info(f"The section {section.id} updated: {section.__dict__}")
            return True
        except Exception as exc:
            await self.session.rollback()
            logger.error(f"An error occurred while updating the section {section.id}: {section.__dict__}")
            logger.error(exc)
            return False
