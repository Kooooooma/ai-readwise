"""
Data models for the AI-Readwise API.
"""

from pydantic import BaseModel
from typing import List, Optional


class Book(BaseModel):
    """Book metadata from description.md"""
    id: str
    title: str
    description: str
    file: str
    has_chapters: bool


class Chapter(BaseModel):
    """Chapter information"""
    name: str
    filename: str
    order: int


class BookDetail(BaseModel):
    """Book with chapters"""
    book: Book
    chapters: List[Chapter]


class ExtractProgress(BaseModel):
    """PDF extraction progress"""
    status: str  # 'pending', 'extracting', 'splitting', 'completed', 'error'
    progress: int  # 0-100
    message: str
    current_step: Optional[str] = None


class ExtractResult(BaseModel):
    """PDF extraction result"""
    success: bool
    message: str
    chapters_count: Optional[int] = None
