import pytest
from services.segment_service import split_text
from services.tm_service import import_tmx, export_tmx, search_tm, add_to_tm, clear_tm
from services.glossary_service import find_terms
from models import GlossaryEntry


class TestSegmentService:
    def test_simple_split(self):
        text = "Hello world.\n\nThis is a test.\n\nGoodbye."
        result = split_text(text)
        assert result == ["Hello world.", "This is a test.", "Goodbye."]

    def test_multiple_blank_lines(self):
        text = "A\n\n\n\nB"
        result = split_text(text)
        assert result == ["A", "B"]

    def test_no_blank_lines(self):
        text = "Line 1\nLine 2\nLine 3"
        result = split_text(text)
        assert result == ["Line 1\nLine 2\nLine 3"]

    def test_empty_text(self):
        assert split_text("") == []
        assert split_text("  \n\n  ") == []

    def test_crlf(self):
        text = "First\r\n\r\nSecond"
        result = split_text(text)
        assert result == ["First", "Second"]

    def test_whitespace_lines(self):
        text = "First.\n  \nSecond."
        result = split_text(text)
        assert result == ["First.", "Second."]


class TestTMXRoundtrip:
    def test_import_and_export(self, db):
        tmx = '<?xml version="1.0" encoding="UTF-8"?><tmx version="1.4"><header creationtool="test" srclang="en"/><body><tu><tuv xml:lang="en"><seg>Hello</seg></tuv><tuv xml:lang="zh"><seg>ni hao</seg></tuv></tu><tu><tuv xml:lang="en"><seg>World</seg></tuv><tuv xml:lang="zh"><seg>shi jie</seg></tuv></tu></body></tmx>'
        count = import_tmx(db, tmx.encode("utf-8"))
        assert count == 2
        exported = export_tmx(db)
        assert b"Hello" in exported
        assert b"World" in exported

    def test_empty_tmx(self, db):
        tmx = '<?xml version="1.0"?><tmx version="1.4"><header/><body/></tmx>'
        count = import_tmx(db, tmx.encode("utf-8"))
        assert count == 0

    def test_duplicate_deduplication(self, db):
        tmx = '<?xml version="1.0"?><tmx version="1.4"><header/><body><tu><tuv xml:lang="en"><seg>Hello</seg></tuv><tuv xml:lang="zh"><seg>ni hao</seg></tuv></tu><tu><tuv xml:lang="en"><seg>Hello</seg></tuv><tuv xml:lang="zh"><seg>nin hao</seg></tuv></tu></body></tmx>'
        count = import_tmx(db, tmx.encode("utf-8"))
        assert count == 2


class TestFuzzyMatching:
    def test_exact_match(self, db):
        add_to_tm(db, "Hello world", "ni hao shi jie", "en", "zh")
        results = search_tm(db, "Hello world", "en", "zh")
        assert len(results) == 1
        assert results[0][1] == 100.0

    def test_partial_match(self, db):
        add_to_tm(db, "The quick brown fox jumps", "yi zhi kuai su de hu li", "en", "zh")
        results = search_tm(db, "The quick brown fox", "en", "zh", threshold=50)
        assert len(results) >= 1
        assert results[0][1] > 50.0

    def test_no_match_below_threshold(self, db):
        add_to_tm(db, "Apple", "ping guo", "en", "zh")
        results = search_tm(db, "Completely different text here", "en", "zh")
        assert len(results) == 0

    def test_language_isolation(self, db):
        add_to_tm(db, "Hello", "Hola", "en", "es")
        results = search_tm(db, "Hello", "en", "zh")
        assert len(results) == 0

    def test_clear_tm(self, db):
        add_to_tm(db, "Test", "Test", "en", "en")
        clear_tm(db)
        results = search_tm(db, "Test", "en", "en")
        assert len(results) == 0


class TestGlossaryService:
    def test_term_found(self, db):
        db.add(GlossaryEntry(source_lang="en", target_lang="zh",
                             source_term="hello", target_term="ni hao"))
        db.commit()
        results = find_terms(db, "hello world", "en", "zh")
        assert len(results) == 1
        assert results[0].source_term == "hello"

    def test_case_insensitive(self, db):
        db.add(GlossaryEntry(source_lang="en", target_lang="zh",
                             source_term="Hello", target_term="ni hao"))
        db.commit()
        results = find_terms(db, "HELLO there", "en", "zh")
        assert len(results) == 1

    def test_multiple_matches(self, db):
        db.add_all([
            GlossaryEntry(source_lang="en", target_lang="zh",
                          source_term="cat", target_term="mao"),
            GlossaryEntry(source_lang="en", target_lang="zh",
                          source_term="dog", target_term="gou"),
        ])
        db.commit()
        results = find_terms(db, "The cat and the dog", "en", "zh")
        assert len(results) == 2

    def test_no_match(self, db):
        results = find_terms(db, "nothing matches", "en", "zh")
        assert len(results) == 0
