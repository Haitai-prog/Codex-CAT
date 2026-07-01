from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Project, SourceDocument, Segment, SegmentStatus
from schemas import SegmentUpdate, SegmentOut, TMSearchResult, TMMatch, GlossaryTermMatch
from services.tm_service import search_tm, add_to_tm
from services.glossary_service import find_terms

router = APIRouter(prefix="/api/segments", tags=["segments"])


@router.put("/{segment_id}", response_model=SegmentOut)
def update_segment(segment_id: int, data: SegmentUpdate, db: Session = Depends(get_db)):
    seg = db.get(Segment, segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")

    if data.target_text is not None:
        seg.target_text = data.target_text
    if data.status is not None:
        try:
            seg.status = SegmentStatus(data.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {data.status}")

    if seg.target_text and seg.target_text.strip():
        seg.status = SegmentStatus.translated
        doc = db.get(SourceDocument, seg.document_id)
        if doc:
            project = db.get(Project, doc.project_id)
            if project:
                add_to_tm(
                    db, seg.source_text, seg.target_text.strip(),
                    project.source_lang, project.target_lang,
                )

    db.commit()
    db.refresh(seg)

    return SegmentOut(
        id=seg.id, document_id=seg.document_id, segment_index=seg.segment_index,
        source_text=seg.source_text, target_text=seg.target_text,
        status=seg.status.value, updated_at=seg.updated_at,
    )


@router.get("/{segment_id}/matches", response_model=TMSearchResult)
def get_segment_matches(segment_id: int, db: Session = Depends(get_db)):
    seg = db.get(Segment, segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")

    doc = db.get(SourceDocument, seg.document_id)
    if not doc:
        raise HTTPException(status_code=404)
    project = db.get(Project, doc.project_id)
    if not project:
        raise HTTPException(status_code=404)

    results = search_tm(
        db, seg.source_text, project.source_lang, project.target_lang
    )

    return TMSearchResult(matches=[
        TMMatch(source_text=tu.source_text, target_text=tu.target_text, score=score)
        for tu, score in results
    ])


@router.get("/{segment_id}/terms", response_model=list[GlossaryTermMatch])
def get_segment_terms(segment_id: int, db: Session = Depends(get_db)):
    seg = db.get(Segment, segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment not found")

    doc = db.get(SourceDocument, seg.document_id)
    if not doc:
        raise HTTPException(status_code=404)
    project = db.get(Project, doc.project_id)
    if not project:
        raise HTTPException(status_code=404)

    entries = find_terms(
        db, seg.source_text, project.source_lang, project.target_lang
    )

    return [
        GlossaryTermMatch(
            source_term=e.source_term, target_term=e.target_term, note=e.note,
        )
        for e in entries
    ]
