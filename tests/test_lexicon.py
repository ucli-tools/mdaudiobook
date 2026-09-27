from pathlib import Path

from mdaudiobook import lexicon as lex
from mdaudiobook.engines.kokoro import ipa_to_kokoro

FIX = Path(__file__).parent / "fixtures"


def test_load_plain_and_dict_entries():
    entries, guessed = lex.load_entries(FIX / "example_lexicon.yaml")
    assert entries["Euler"] == "ˈɔɪlɚ" and entries["Hegel"] == "ˈheɪɡəl"
    assert guessed == set()


def test_guesses(tmp_path):
    p = tmp_path / "lex.yaml"
    p.write_text("Name:\n  ipa: nAm\n  guess: true\nOther: ˈʌðɚ\n", encoding="utf-8")
    assert lex.guesses(p) == {"Name"}


def test_foreign_words_and_unsayable_letters():
    words = dict(lex.foreign_words("the word λόγος and the sign 𒁹 here"))
    assert words == {"λόγος": "GREEK", "𒁹": "CUNEIFORM"}
    assert lex.unsayable("λόγος 𒁹𒁹 𓏺") == {"CUNEIFORM": 2, "EGYPTIAN": 1}


def test_pronunciations_pick_book_entries_in_the_sentence():
    pron = lex.pronunciations("Euler met nobody.", {"Euler": "ˈɔɪlɚ", "Hegel": "ˈheɪɡəl"})
    assert pron == {"Euler": "ˈɔɪlɚ"}


def test_ipa_to_kokoro():
    # stress marks move from the syllable's start to its vowel, as Kokoro expects
    assert ipa_to_kokoro("ˈheɪɡəl") == "hˈAɡəl"
    assert ipa_to_kokoro("ˈɡloʊni") == "ɡlˈOni"
    assert ipa_to_kokoro("ˈɔɪlɚ") == "ˈYləɹ"
    assert ipa_to_kokoro("fuˈɹjeɪ") == "fuɹjˈA"
    assert ipa_to_kokoro("ˌɑɹiθˈmɔɪ") == "ˌɑɹiθmˈY"
    assert ipa_to_kokoro("dʒoʊ") == "ʤO"
