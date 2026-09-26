from mdaudiobook.text import normalize, sentences


def test_abbreviations_units_and_symbols():
    out = normalize("A 40 Hz wave at 3 km/s, e.g. here; 42 is 40 + 2 and 50% of 180°.")
    assert "40 hertz" in out and "3 kilometres per second" in out and "for example," in out
    assert "40 plus 2" in out and "50 percent" in out and "180 degrees" in out


def test_urls_are_spelled_out():
    assert normalize("See https://library.example.org/books.") == "See library dot example dot org slash books."


def test_roman_numerals_after_divisions():
    assert normalize("Chapter IV and Part XII") == "Chapter 4 and Part 12"
    assert normalize("Louis XIV") == "Louis XIV"


def test_capitals_for_stress_are_words():
    assert normalize("Something IS nothing, the PSR says.") == "Something is nothing, the PSR says."


def test_punctuation_left_by_a_silenced_span():
    assert normalize("three wedges: .") == "three wedges."


def test_sentences_respect_initials_and_quotes():
    s = sentences("J. S. Bach wrote it. “Really?” she asked. Yes.")
    assert s == ["J. S. Bach wrote it.", "“Really?” she asked.", "Yes."]


def test_long_sentences_are_cut_at_clause_breaks():
    long = ("This clause runs on for quite a while, and it keeps going with more words than a voice "
            "model takes at once; then a second clause follows it, which is also rather long indeed, "
            "and a third one closes the whole thing off with yet more words to say aloud here.")
    parts = sentences(long, max_chars=120)
    assert len(parts) > 1 and all(len(p) <= 120 for p in parts)
    assert " ".join(parts) == long
