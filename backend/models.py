from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from database import Base
import enum


class SegmentStatus(enum.Enum):
    untranslated = "untranslated"
    draft = "draft"
    translated = "translated"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    source_lang = Column(String(20), nullable=False)
    target_lang = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("SourceDocument", back_populates="project", cascade="all, delete-orphan")


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String(300), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="documents")
    segments = relationship("Segment", back_populates="document", cascade="all, delete-orphan",
                            order_by="Segment.segment_index")


class Segment(Base):
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("source_documents.id"), nullable=False)
    segment_index = Column(Integer, nullable=False)
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=True)
    status = Column(SAEnum(SegmentStatus), default=SegmentStatus.untranslated)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("SourceDocument", back_populates="segments")


class TranslationUnit(Base):
    __tablename__ = "translation_units"

    id = Column(Integer, primary_key=True, index=True)
    source_lang = Column(String(20), nullable=False)
    target_lang = Column(String(20), nullable=False)
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    usage_count = Column(Integer, default=0)


class GlossaryEntry(Base):
    __tablename__ = "glossary_entries"

    id = Column(Integer, primary_key=True, index=True)
    source_lang = Column(String(20), nullable=False)
    target_lang = Column(String(20), nullable=False)
    source_term = Column(String(500), nullable=False)
    target_term = Column(String(500), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TokenUsage(Base):
    __tablename__ = "token_usage"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=True)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    model = Column(String(100), nullable=False, default="gpt-4o")
    created_at = Column(DateTime, default=datetime.utcnow)
    duration_ms = Column(Integer, nullable=False, default=0)

    project = relationship("Project")
