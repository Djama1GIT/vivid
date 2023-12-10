from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Tuple
from uuid import UUID


class BookOfSessionBase(BaseModel):
    id: UUID = Field(..., description="Book of session ID")
    book: str = Field(..., description="Book title")
    genre: str = Field(..., description="Book genre")
    sections_count: int = Field(..., description="Count of sections in the book")
    chapters_count: int = Field(..., description="Count of chapters in a section")
    chapters_length: int = Field(..., description="The average length of chapters in the book")
    v: str = Field(..., description="The GPT version used during book generation")
    pregeneration: Optional[str] = Field(None, description="Description of the book")
    filename: Optional[str] = Field(None, description="The name of the book's file")
    sections_list: Optional[List[List[str | int] | Tuple[str | int]]] = Field(
        None,
        description="List of sections in the book"
    )


class BookOfSessionBaseWithExtra(BookOfSessionBase):
    chapters: Optional[Dict[str, List[list | int] | Tuple[str | int]]] = Field(
        None,
        description="Chapters in JSON"
    )


class SectionBase(BaseModel):
    id: Optional[UUID] = Field(None, description="Section ID")
    book_id: UUID = Field(..., description="Book ID")
    name: str = Field(..., description="Section name")
    chapters_list: Optional[List[List[str | int] | Tuple[str | int]]] = Field(
        ...,
        description="List of chapters without text"
    )


class SectionBaseWithExtra(SectionBase):
    chapters: Optional[List[list | int] | Tuple[str | int]] = Field(
        None,
        description="List of chapters in the section"
    )


class ChapterBase(BaseModel):
    id: Optional[UUID] = Field(None, description="Chapter ID")
    book_id: UUID = Field(..., description="Book ID")
    section_id: UUID = Field(..., description="Section ID")
    name: str = Field(..., description="Chapter Title")
    text: Optional[str] = Field(None, description="Chapter text")
