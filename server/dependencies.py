from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession
from repository import BookRepository


def get_book_repository(get_async_session):
    def _get_book_repository(session: AsyncSession = Depends(get_async_session)) -> BookRepository:
        return BookRepository(session)

    return _get_book_repository
