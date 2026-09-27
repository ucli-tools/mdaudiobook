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
    """A chapter's segments as plain text (letter markers removed)."""
    ch = next(c for c in s.chapters if c.title == title)
    return [script.plain(x.text) for x in ch.segments]


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
    assert "Figure 1.1. The unit circle. Every point on it is one unit from the centre." in one
    assert "Table 1.1. Angles as fractions of a turn." in one
    assert "180 degrees. Fraction of a turn: a half." in one
    assert "Footnote. The word is also the root of “symmetry”." in one
    assert any("for example, in geometry" in t for t in one)


def test_descriptions_follow_their_figure(built):
    one = texts(built[1], "Chapter 1: The Unit Circle")
    i = one.index("Figure 1.1. The unit circle. Every point on it is one unit from the centre.")
    assert one[i + 1].startswith("Here in Figure 1.1 we see a circle drawn around the origin")
    # the uncaptioned chart inside the print-only block has no number, as in the PDF
    assert [f[:2] + [f[3]] for f in built[1].floats] == [["Figure", "1.1", True], ["Table", "1.1", False],
                                                          ["Table", None, True], ["Table", None, False]]


def test_letters_in_mathematics_are_marked(built):
    ch = next(c for c in built[1].chapters if c.title == "Chapter 1: The Unit Circle")
    para = next(x.text for x in ch.segments if x.text.startswith("A circle of radius one"))
    assert "\ue010x\ue011 squared plus \ue010y\ue011 squared" in para
    assert "x squared plus y squared" in script.plain(para)


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
    assert "ok   figures without an audio description (what the picture shows): 0" in text
    assert "note code blocks (not read): 1" in text
    assert rep.failures == 2


def test_select(built):
    s = built[1]
    assert [c.title for c in script.select(s, "2-3").chapters] == ["Chapter 1: The Unit Circle", "Chapter 2: Counting"]
    assert [c.title for c in script.select(s, "counting").chapters] == ["Chapter 2: Counting"]
