from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from models import GlossaryEntry
from schemas import GlossaryEntryCreate, GlossaryEntryOut
import openpyxl, io

router = APIRouter(prefix="/api/glossary", tags=["glossary"])



@router.get("", response_model=list[GlossaryEntryOut])
def list_entries(db: Session = Depends(get_db)):
    entries = db.scalars(select(GlossaryEntry).order_by(GlossaryEntry.created_at.desc())).all()
    return [GlossaryEntryOut.model_validate(e) for e in entries]

def create_entry(data: GlossaryEntryCreate, db: Session = Depends(get_db)):
    entry = GlossaryEntry(
        source_lang=data.source_lang,
        target_lang=data.target_lang,
        source_term=data.source_term,
        target_term=data.target_term,
        note=data.note,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return GlossaryEntryOut.model_validate(entry)


@router.put("/{entry_id}", response_model=GlossaryEntryOut)
def update_entry(entry_id: int, data: GlossaryEntryCreate, db: Session = Depends(get_db)):
    entry = db.get(GlossaryEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Glossary entry not found")
    entry.source_lang = data.source_lang
    entry.target_lang = data.target_lang
    entry.source_term = data.source_term
    entry.target_term = data.target_term
    entry.note = data.note
    db.commit()
    db.refresh(entry)
    return GlossaryEntryOut.model_validate(entry)


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(GlossaryEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Glossary entry not found")
    db.delete(entry)
    db.commit()
