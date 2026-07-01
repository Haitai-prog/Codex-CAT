import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from database import get_db
from models import Project, SourceDocument, Segment, SegmentStatus, TokenUsage
from services.llm_service import translate_text, DEFAULT_MODEL
from services.glossary_service import find_terms
from services.tm_service import add_to_tm

router = APIRouter(prefix="/api", tags=["ai-translation"])


@router.post("/projects/{project_id}/pre-translate")
async def pre_translate(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    doc_ids = db.scalars(
        select(SourceDocument.id).where(SourceDocument.project_id == project_id)
    ).all()
    if not doc_ids:
        raise HTTPException(status_code=400, detail="No documents in project")

    segments = db.scalars(
        select(Segment).where(
            Segment.document_id.in_(doc_ids),
            Segment.status != SegmentStatus.translated,
        ).order_by(Segment.segment_index)
    ).all()

    if not segments:
        return {"translated": 0, "message": "All segments already translated"}

    all_glossary = find_terms(db, "", project.source_lang, project.target_lang)
    total_input_tokens = 0
    total_output_tokens = 0
    total_duration = 0
    translated_count = 0

    for seg in segments:
        try:
            seg_glossary = find_terms(db, seg.source_text, project.source_lang, project.target_lang)
            glossary_dict = {g.source_term: g.target_term for g in seg_glossary} if seg_glossary else None

            translation, in_tokens, out_tokens, duration_ms = await translate_text(
                seg.source_text,
                project.source_lang,
                project.target_lang,
                glossary_dict,
            )

            seg.target_text = translation
            seg.status = SegmentStatus.translated
            db.add(seg)

            add_to_tm(db, seg.source_text, translation, project.source_lang, project.target_lang)

            db.add(TokenUsage(
                project_id=project_id,
                source_text=seg.source_text,
                target_text=translation,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                model=DEFAULT_MODEL,
                duration_ms=duration_ms,
            ))

            total_input_tokens += in_tokens
            total_output_tokens += out_tokens
            total_duration += duration_ms
            translated_count += 1
            db.commit()

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=502,
                detail=f"LLM translation failed at segment {seg.segment_index}: {str(e)}",
            )

    project.updated_at = func.now()
    db.commit()

    return {
        "translated": translated_count,
        "total_segments": len(segments),
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
        "duration_ms": total_duration,
    }


@router.get("/projects/{project_id}/token-stats")
def token_stats(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = db.execute(
        select(
            func.count(TokenUsage.id),
            func.coalesce(func.sum(TokenUsage.input_tokens), 0),
            func.coalesce(func.sum(TokenUsage.output_tokens), 0),
            func.coalesce(func.sum(TokenUsage.duration_ms), 0),
        ).where(TokenUsage.project_id == project_id)
    ).one()

    cnt, inp, out, dur = result

    return {
        "project_id": project_id,
        "total_calls": cnt,
        "total_input_tokens": inp or 0,
        "total_output_tokens": out or 0,
        "total_tokens": (inp or 0) + (out or 0),
        "total_duration_ms": dur or 0,
    }
