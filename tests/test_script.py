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


def test_equations_set_out_in_lines(built):
    one = texts(built[1], "Chapter 1: The Unit Circle")
    assert "x squared plus y squared equals 1," in one          # one line: only the equation
    assert "x equals cosine t, y equals sine t." in one         # two lines: a pause between them
    assert not any("lines" in t or "Line" in t for t in one)
    # a line that starts with + carries on the line above
    said = mathspeech.speak([(r"\begin{array}{r} a = b + c \\ + d + e, \\ = f. \end{array}", True)])[0]
    assert script.plain(said) == "a equals b plus c; plus d plus e, equals f."
    # what the speech engine says of a table of lines that reaches it anyway
    def polish(said):
        return script.plain(mathspeech._polish(said))
    assert polish("1 lines Line 1: blank equals 1") == "equals 1"
    assert polish("3 lines Line 1: 1 zero Line 2: blank Line 3: zero 1") == "1 zero; zero 1"
    assert polish("the 2 by 2 matrix Row 1: Column 1, blank Column 2, 1") == \
        "the 2 by 2 matrix Row 1: Column 1, blank Column 2, 1"
    assert polish("2 cases Case 1: 1 if x is greater than 0") == "2 cases Case 1: 1 if x is greater than 0"


def test_punctuation_in_mathematics_is_punctuation(built):
    one = texts(built[1], "Chapter 1: The Unit Circle")
    para = next(t for t in one if t.startswith("A circle of radius one"))
    assert "every point open paren x, y close paren with" in para
    said = mathspeech.speak([(r"f(x, y) = 1.", False), (r"a_1, a_2, \ldots, a_n", False), (r"1, 2, 3, ...", False),
                             (r"x = 1;", True), (r"\left\{ x \right.", True), (r"T_{\text{period}} = 2\pi.", False),
                             (r"0.5", False)])
    assert [script.plain(s) for s in said] == [
        "f of open paren x, y close paren equals 1.", "a sub 1, a sub 2, and so on, a sub n", "1, 2, 3, and so on",
        "x equals 1;", "open brace x", "T sub period equals 2 pi.", "0.5"]
    # a control space after the mark; an empty equation array with only its number: nothing to say
    said = mathspeech.speak([(r"\begin{array}{r} [X,Y] = 0,\ \end{array}", True), (r"x = 1,\ ", True),
                             (r"\begin{array}{r} \ \square\ \end{array}", True),
                             ("\\begin{array}{r}\n\\end{array} \\tag{1.7}", True), (r"\tag{2}", True)])
    assert [script.plain(s) for s in said] == ["open bracket X, Y close bracket equals 0,", "x equals 1,",
                                               "white small square", "", ""]
    # a word the expression holds itself is not a punctuation mark
    assert script.plain(mathspeech._polish("x comma T sub period", r"x, T_{\text{period}}")) == "x, T sub period"
    assert script.plain(mathspeech._polish("x period T sub comma", r"x. T_{\text{comma}}")) == "x. T sub comma"


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
    ch = next(c for c in built[1].chapters if c.title == "Chapter 1: The Unit Circle")
    assert "the point where \ue010x\ue011 is one and \ue010y\ue011 is zero" in ch.segments[i + 1].text   # letters by name
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
    assert "ok   equations the maths engine cannot speak: 0" in text      # an empty one says nothing
    assert "ok   figures without an audio description (what the picture shows): 0" in text
    assert "note code blocks (not read): 1" in text
    assert rep.failures == 2


def test_select(built):
    s = built[1]
    assert [c.title for c in script.select(s, "2-3").chapters] == ["Chapter 1: The Unit Circle", "Chapter 2: Counting"]
    assert [c.title for c in script.select(s, "counting").chapters] == ["Chapter 2: Counting"]


@pytest.mark.parametrize("split_wrapper", [True, False])
def test_samepage_wrapper_preserves_caption(tmp_path, split_wrapper):
    caption = (r"\begin{center}\parbox{\linewidth}{\centering\itshape "
               r"Both keys are silver.}\end{center}")
    opening = r"\begin{samepage}"
    closing = r"\end{samepage}"
    if split_wrapper:
        blocks = f"```{{=latex}}\n{opening}\n```\n\nTwo small keys rest on a desk.\n\n"
        blocks += f"```{{=latex}}\n{caption}\n{closing}\n```\n"
    else:
        blocks = f"```{{=latex}}\n{opening}\n{caption}\n{closing}\n```\n"
    path = tmp_path / "example.md"
    path.write_text("## Chapter 1: Small Objects\n\n" + blocks)
    narration = script.build(Book.load(path))
    assert narration.text().count("Both keys are silver.") == 1
    assert not any(f.kind in ("unparsed_raw", "silent_raw") for f in narration.inventory)
