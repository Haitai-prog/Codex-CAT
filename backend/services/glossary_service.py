from sqlalchemy import select
from sqlalchemy.orm import Session
from models import GlossaryEntry


def find_terms(
    db: Session,
    source_text: str,
    source_lang: str,
    target_lang: str,
) -> list[GlossaryEntry]:
    """Find glossary entries whose source_term appears in source_text."""
    entries = db.scalars(
        select(GlossaryEntry).where(
            GlossaryEntry.source_lang == source_lang,
            GlossaryEntry.target_lang == target_lang,
        )
    ).all()

    lower_text = source_text.lower()
    matched = []
    for entry in entries:
        if entry.source_term.lower() in lower_text:
            matched.append(entry)
    return matched
