from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from database import get_db
from models import Project, SourceDocument, Segment, SegmentStatus
from schemas import ProjectCreate, ProjectOut

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    projects = db.scalars(select(Project).order_by(Project.updated_at.desc())).all()
    result = []
    for p in projects:
        doc_ids = db.scalars(
            select(SourceDocument.id).where(SourceDocument.project_id == p.id)
        ).all()
        total = db.scalar(
            select(func.count(Segment.id)).where(Segment.document_id.in_(doc_ids))
        ) if doc_ids else 0
        translated = db.scalar(
            select(func.count(Segment.id)).where(
                Segment.document_id.in_(doc_ids),
                Segment.status == SegmentStatus.translated,
            )
        ) if doc_ids else 0
        result.append(ProjectOut(
            id=p.id, name=p.name, source_lang=p.source_lang,
            target_lang=p.target_lang, created_at=p.created_at,
            updated_at=p.updated_at, total_segments=total,
            translated_segments=translated,
        ))
    return result


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        name=data.name,
        source_lang=data.source_lang,
        target_lang=data.target_lang,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut(
        id=project.id, name=project.name, source_lang=project.source_lang,
        target_lang=project.target_lang, created_at=project.created_at,
        updated_at=project.updated_at, total_segments=0, translated_segments=0,
    )


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    doc_ids = db.scalars(
        select(SourceDocument.id).where(SourceDocument.project_id == project.id)
    ).all()
    total = db.scalar(
        select(func.count(Segment.id)).where(Segment.document_id.in_(doc_ids))
    ) if doc_ids else 0
    translated = db.scalar(
        select(func.count(Segment.id)).where(
            Segment.document_id.in_(doc_ids),
            Segment.status == SegmentStatus.translated,
        )
    ) if doc_ids else 0
    return ProjectOut(
        id=project.id, name=project.name, source_lang=project.source_lang,
        target_lang=project.target_lang, created_at=project.created_at,
        updated_at=project.updated_at, total_segments=total,
        translated_segments=translated,
    )


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
