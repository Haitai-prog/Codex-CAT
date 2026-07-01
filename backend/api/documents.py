from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from database import get_db
from models import Project, SourceDocument, Segment, SegmentStatus
from schemas import DocumentOut, SegmentOut
from services.segment_service import split_text

router = APIRouter(prefix="/api", tags=["documents"])


@router.post("/projects/{project_id}/documents", response_model=DocumentOut, status_code=201)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = (await file.read()).decode("utf-8")
    segments = split_text(content)
    if not segments:
        raise HTTPException(status_code=400, detail="Empty or unparseable file")

    doc = SourceDocument(project_id=project_id, filename=file.filename or "untitled.txt")
    db.add(doc)
    db.flush()

    for i, seg_text in enumerate(segments):
        db.add(Segment(
            document_id=doc.id,
            segment_index=i,
            source_text=seg_text,
            status=SegmentStatus.untranslated,
        ))

    project.updated_at = func.now()
    db.commit()
    db.refresh(doc)

    return DocumentOut(
        id=doc.id, project_id=doc.project_id, filename=doc.filename,
        created_at=doc.created_at, segment_count=len(segments),
    )


@router.get("/projects/{project_id}/documents", response_model=list[DocumentOut])
def list_documents(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    docs = db.scalars(
        select(SourceDocument).where(SourceDocument.project_id == project_id)
    ).all()

    result = []
    for doc in docs:
        count = db.scalar(
            select(func.count(Segment.id)).where(Segment.document_id == doc.id)
        ) or 0
        result.append(DocumentOut(
            id=doc.id, project_id=doc.project_id, filename=doc.filename,
            created_at=doc.created_at, segment_count=count,
        ))
    return result


@router.get("/documents/{document_id}", response_model=list[SegmentOut])
def get_document_segments(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(SourceDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    segments = db.scalars(
        select(Segment).where(Segment.document_id == document_id).order_by(Segment.segment_index)
    ).all()

    return [
        SegmentOut(
            id=s.id, document_id=s.document_id, segment_index=s.segment_index,
            source_text=s.source_text, target_text=s.target_text,
            status=s.status.value, updated_at=s.updated_at,
        )
        for s in segments
    ]


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(SourceDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
