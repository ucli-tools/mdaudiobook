"""The narration script built from the example book (needs pandoc and the
maths speech engine; skipped without them)."""
import shutil
from pathlib import Path

import pytest

from mdaudiobook import check, mathspeech, script
from mdaudiobook.book import Book

FIX = Path(__file__).parent / "fixtures"
pytestmark = pytest.mark.skipif(not (shutil.which("pandoc") and mathspeech.available()),
                                reason="needs pandoc and `mdaudiobook setup`")


@pytest.fixture(scope="module")
def built():
    book = Book.load(FIX / "example.md")
    return book, script.build(book)


def texts(s, title):
    ch = next(c for c in s.chapters if c.title == title)
    return [x.text for x in ch.segments]


def test_chapters_credits_and_parts(built):
    _, s = built
    assert [c.title for c in s.chapters] == ["Opening credits", "Chapter 1: The Unit Circle",
                                             "Chapter 2: Counting", "End credits"]
    one = texts(s, "Chapter 1: The Unit Circle")
    assert one[0] == "Part One: Circles." and one[1] == "Chapter 1: The Unit Circle."
    assert "Written by Jane Doe." in texts(s, "Opening credits")


def test_equations_the_book_reads_itself(built):
    one = texts(built[1], "Chapter 1: The Unit Circle")
    assert "e to the i theta equals cosine theta plus i sine theta." in one
    assert not any("raised to the i theta power" in t for t in one)      # machine reading dropped
    assert any(t.startswith("the sum from n equals 1 to infinity") for t in one)   # no reading: engine


def test_figures_tables_notes_and_normalising(built):
    one = texts(built[1], "Chapter 1: The Unit Circle")
    assert "Figure. The unit circle. Every point on it is one unit from the centre." in one
    assert "Table. Angles as fractions of a turn." in one
    assert "180 degrees. Fraction of a turn: a half." in one
    assert "Footnote. The word is also the root of “symmetry”." in one
    assert any("for example, in geometry" in t for t in one)


def test_spoken_forms_replace_what_cannot_be_said(built):
    two = texts(built[1], "Chapter 2: Counting")
    assert "Ancient scribes wrote numbers with marks. A wedge stood for one, as the chart shows." in two
    assert "Written in wedges, one to three are one, two and three vertical wedges." in two
    assert not any("𒁹" in t for t in two)


def test_check_finds_what_a_listener_would_miss(built):
    book, s = built
    rep = check.run(s, book)
    text = rep.text()
    assert "FAIL tables with no caption: 1" in text
    assert "FAIL drawings outside a captioned figure (silent for a listener): 1" in text
    assert "ok   letters no voice here can pronounce (give them a spoken form): 0" in text
    assert "note code blocks (not read): 1" in text
    assert rep.failures == 2


def test_select(built):
    s = built[1]
    assert [c.title for c in script.select(s, "2-3").chapters] == ["Chapter 1: The Unit Circle", "Chapter 2: Counting"]
    assert [c.title for c in script.select(s, "counting").chapters] == ["Chapter 2: Counting"]
