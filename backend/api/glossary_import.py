from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from models import GlossaryEntry

router = APIRouter(prefix="/api", tags=["glossary-import"])

@router.post("/glossary/import")
async def import_glossary(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx or .xls files accepted")
    import openpyxl, io
    content = await file.read()
    wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    ws = wb.active
    count = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        st = str(row[0]).strip() if row[0] else ""
        tt = str(row[1]).strip() if row[1] else ""
        if not st or not tt:
            continue
        sl = str(row[2]).strip() if len(row) > 2 and row[2] else "en"
        tl = str(row[3]).strip() if len(row) > 3 and row[3] else "zh"
        nt = str(row[4]).strip() if len(row) > 4 and row[4] else None
        existing = db.scalars(select(GlossaryEntry).where(
            GlossaryEntry.source_lang == sl, GlossaryEntry.target_lang == tl,
            GlossaryEntry.source_term == st)).first()
        if existing:
            existing.target_term = tt
            existing.note = nt
        else:
            db.add(GlossaryEntry(source_lang=sl, target_lang=tl,
                source_term=st, target_term=tt, note=nt))
        count += 1
    db.commit()
    return {"imported": count}
