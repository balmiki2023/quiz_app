from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from datetime import datetime


@dataclass
class Category:
    id: UUID
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_premium: bool = False
    is_published: bool = True
    created_at: Optional[datetime] = None


@dataclass
class Quiz:
    id: UUID
    category_id: Optional[UUID]
    title: str
    description: Optional[str] = None
    difficulty: Optional[str] = None
    is_premium: bool = False
    is_published: bool = False
    time_limit_seconds: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class Question:
    id: UUID
    quiz_id: Optional[UUID]
    question_text: str
    explanation: Optional[str] = None
    question_order: int = 0
    created_at: Optional[datetime] = None


@dataclass
class QuizAnswer:
    id: UUID
    question_id: Optional[UUID]
    answer_text: str
    is_correct: bool = False
    answer_order: int = 0