from typing import Sequence
from io import BytesIO
from lxml import etree
from rapidfuzz import fuzz
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from models import TranslationUnit


TMX_NS = "http://www.lissland.org/tmx14"


def search_tm(
    db: Session,
    source_text: str,
    source_lang: str,
    target_lang: str,
    top_k: int = 5,
    threshold: int = 70,
) -> list[tuple[TranslationUnit, float]]:
    units = db.scalars(
        select(TranslationUnit).where(
            TranslationUnit.source_lang == source_lang,
            TranslationUnit.target_lang == target_lang,
        )
    ).all()

    results: list[tuple[TranslationUnit, float]] = []
    for tu in units:
        score = fuzz.token_sort_ratio(source_text, tu.source_text)
        if score >= threshold:
            results.append((tu, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def import_tmx(db: Session, file_bytes: bytes) -> int:
    tree = etree.parse(BytesIO(file_bytes))
    root = tree.getroot()

    nsmap = {"tmx": TMX_NS} if TMX_NS in (root.nsmap or {}).values() else {}
    body = root.find("tmx:body", nsmap) if nsmap else root.find("body")
    if body is None:
        return 0

    count = 0
    for tu_el in body.findall("tmx:tu", nsmap) if nsmap else body.findall("tu"):
        tuvs = {}
        for tuv_el in (
            tu_el.findall("tmx:tuv", nsmap) if nsmap else tu_el.findall("tuv")
        ):
            lang = tuv_el.get("{http://www.w3.org/XML/1998/namespace}lang") or tuv_el.get("lang", "")
            seg_el = tuv_el.find("tmx:seg", nsmap) if nsmap else tuv_el.find("seg")
            if seg_el is not None and seg_el.text:
                tuvs[lang.lower()] = seg_el.text.strip()

        if len(tuvs) < 2:
            continue

        langs = list(tuvs.keys())
        for i in range(len(langs)):
            for j in range(i + 1, len(langs)):
                src_lang, tgt_lang = langs[i], langs[j]
                src_text, tgt_text = tuvs[src_lang], tuvs[tgt_lang]

                existing = db.scalars(
                    select(TranslationUnit).where(
                        TranslationUnit.source_lang == src_lang,
                        TranslationUnit.target_lang == tgt_lang,
                        TranslationUnit.source_text == src_text,
                    )
                ).first()

                if existing:
                    existing.target_text = tgt_text
                else:
                    db.add(TranslationUnit(
                        source_lang=src_lang,
                        target_lang=tgt_lang,
                        source_text=src_text,
                        target_text=tgt_text,
                    ))
                count += 1

    db.commit()
    return count


def export_tmx(db: Session) -> bytes:
    units = db.scalars(select(TranslationUnit)).all()

    tmx_el = etree.Element("tmx", version="1.4")
    header = etree.SubElement(tmx_el, "header", {
        "creationtool": "Codex CAT",
        "creationtoolversion": "1.0",
        "segtype": "paragraph",
        "adminlang": "en",
        "srclang": "*all*",
        "datatype": "plaintext",
    })
    body = etree.SubElement(tmx_el, "body")

    for tu in units:
        tu_el = etree.SubElement(body, "tu")
        for lang, text in [(tu.source_lang, tu.source_text), (tu.target_lang, tu.target_text)]:
            tuv_el = etree.SubElement(tu_el, "tuv")
            tuv_el.set("{http://www.w3.org/XML/1998/namespace}lang", lang)
            seg_el = etree.SubElement(tuv_el, "seg")
            seg_el.text = text

    return etree.tostring(
        tmx_el, encoding="UTF-8", xml_declaration=True, pretty_print=True
    )


def add_to_tm(db: Session, source_text: str, target_text: str, source_lang: str, target_lang: str):
    existing = db.scalars(
        select(TranslationUnit).where(
            TranslationUnit.source_lang == source_lang,
            TranslationUnit.target_lang == target_lang,
            TranslationUnit.source_text == source_text,
        )
    ).first()
    if existing:
        existing.target_text = target_text
        existing.usage_count += 1
    else:
        db.add(TranslationUnit(
            source_lang=source_lang,
            target_lang=target_lang,
            source_text=source_text,
            target_text=target_text,
            usage_count=1,
        ))
    db.commit()


def clear_tm(db: Session):
    db.execute(delete(TranslationUnit))
    db.commit()
