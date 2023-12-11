from sqlalchemy import Column, Integer, String, UUID, JSON, ForeignKey
from sqlalchemy.orm import relationship

from db import Base


class Session(Base):
    __tablename__ = 'sessions'

    id = Column(UUID, primary_key=True, index=True)
    book = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    sections_count = Column(Integer, nullable=False)
    chapters_count = Column(Integer, nullable=False)
    chapters_length = Column(Integer, nullable=False)
    v = Column(String, nullable=False)
    pregeneration = Column(String, nullable=True)
    filename = Column(String, nullable=True)
    sections_list = Column(JSON, nullable=True, default=list)  # only names, but in the right order
    sections = relationship("Section", back_populates="session")

    def json(self):
        return {
            "id": str(self.id),
            "book": self.book,
            "genre": self.genre,
            "sections_count": self.sections_count,
            "chapters_count": self.chapters_count,
            "v": self.v,
            "pregeneration": self.pregeneration,
            "sections_list": self.sections_list or [],
            "sections": self.sections,
            "filename": self.filename,
        }


class Section(Base):
    __tablename__ = 'sections'

    id = Column(UUID, primary_key=True, index=True)
    book_id = Column(UUID, ForeignKey('sessions.id'), nullable=False)
    name = Column(String, nullable=False)
    chapters_list = Column(JSON, nullable=True, default=list)  # only names, but in the right order
    chapters = relationship("Chapter", back_populates="section")
    session = relationship("Session", back_populates="sections")

    async def json(self, session):
        chapters = await session.run_sync(lambda s: self.chapters)
        chapters = {chapter.name: chapter.text for chapter in chapters}
        return {
            "id": self.id,
            "book_id": self.book_id,
            "name": self.name,
            "chapters_list": self.chapters_list,
            "chapters": [
                chapter + [chapters[chapter[1]]]
                if chapter[1] in chapters else chapter
                for chapter in self.chapters_list
            ]
        }


class Chapter(Base):
    __tablename__ = 'chapters'

    id = Column(UUID, primary_key=True, index=True)
    book_id = Column(UUID, ForeignKey('sessions.id'), nullable=False)
    section_id = Column(UUID, ForeignKey('sections.id'), nullable=False)
    name = Column(String, nullable=False)
    text = Column(String, nullable=True)
    section = relationship("Section", back_populates="chapters")

    def json(self):
        return {
            "id": self.id,
            "book_id": self.book_id,
            "section_id": self.section_id,
            "name": self.name,
            "text": self.text or "",
        }
