from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database import get_db
from services.tm_service import import_tmx, export_tmx, clear_tm

router = APIRouter(prefix="/api/tm", tags=["translation-memory"])


@router.post("/import")
async def import_tmx_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.endswith((".tmx", ".xml")):
        raise HTTPException(status_code=400, detail="Only .tmx or .xml files are accepted")
    content = await file.read()
    count = import_tmx(db, content)
    return {"imported": count}


@router.get("/export")
def export_tmx_file(db: Session = Depends(get_db)):
    xml_bytes = export_tmx(db)
    return Response(
        content=xml_bytes,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=translation_memory.tmx"},
    )


@router.delete("", status_code=204)
def delete_tm(db: Session = Depends(get_db)):
    clear_tm(db)
