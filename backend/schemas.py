from datetime import datetime
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    source_lang: str
    target_lang: str


class ProjectOut(BaseModel):
    id: int
    name: str
    source_lang: str
    target_lang: str
    created_at: datetime
    updated_at: datetime
    total_segments: int = 0
    translated_segments: int = 0

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: int
    project_id: int
    filename: str
    created_at: datetime
    segment_count: int = 0

    model_config = {"from_attributes": True}


class SegmentOut(BaseModel):
    id: int
    document_id: int
    segment_index: int
    source_text: str
    target_text: str | None = None
    status: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class SegmentUpdate(BaseModel):
    target_text: str | None = None
    status: str | None = None


class TMMatch(BaseModel):
    source_text: str
    target_text: str
    score: float


class TMSearchResult(BaseModel):
    matches: list[TMMatch]


class GlossaryTermMatch(BaseModel):
    source_term: str
    target_term: str
    note: str | None = None


class GlossaryEntryCreate(BaseModel):
    source_lang: str
    target_lang: str
    source_term: str
    target_term: str
    note: str | None = None


class GlossaryEntryOut(BaseModel):
    id: int
    source_lang: str
    target_lang: str
    source_term: str
    target_term: str
    note: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
