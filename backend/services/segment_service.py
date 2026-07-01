import re


def split_text(text: str) -> list[str]:
    """Split source text into segments by blank lines."""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not cleaned:
        return []
    segments = re.split(r"\n\s*\n", cleaned)
    return [s.strip() for s in segments if s.strip()]
