"""Pronunciations: the book's lexicon, and words in other scripts.

A book's lexicon maps words to IPA, the one notation every serious voice
engine accepts in some form; each engine converts IPA to its own phonemes.
Words in scripts espeak-ng can read (Greek, Cyrillic, ...) get their IPA from
it in their own language; letters with no phonetic reading (hieroglyphs,
cuneiform) are left for the book to give a spoken form, and `check` reports
any it did not.
"""
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import yaml

# Scripts espeak-ng reads, by the first word of the Unicode character name
ESPEAK_LANGUAGES = {"GREEK": "el", "CYRILLIC": "ru", "HEBREW": "he", "ARABIC": "ar", "ARMENIAN": "hy",
                    "GEORGIAN": "ka", "DEVANAGARI": "hi"}


def load(path):
    """{word: IPA} from a YAML or JSON file; values may be {ipa: ..., note: ...}."""
    return load_entries(path)[0]


def guesses(path):
    """Words whose entry is marked `guess: true` (not yet checked by ear)."""
    return load_entries(path)[1]


def load_entries(path):
    if not path:
        return {}, set()
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"lexicon not found: {path}")
    data = (json.loads if path.suffix == ".json" else yaml.safe_load)(path.read_text(encoding="utf-8")) or {}
    out, guessed = {}, set()
    for word, value in data.items():
        ipa = value.get("ipa") if isinstance(value, dict) else value
        if not ipa:
            raise ValueError(f"lexicon entry {word!r} has no IPA")
        out[str(word)] = str(ipa).strip().strip("/[]")
        if isinstance(value, dict) and value.get("guess"):
            guessed.add(str(word))
    return out, guessed


def script_of(ch):
    return unicodedata.name(ch, "UNKNOWN").split()[0]


def is_foreign_letter(ch):
    return unicodedata.category(ch).startswith("L") and not ch.isascii() and "LATIN" not in unicodedata.name(ch, "")


FOREIGN_WORD = re.compile(r"[^\W\d_A-Za-zÀ-ɏ]+(?:[̀-ͯ-][^\W\d_A-Za-zÀ-ɏ]*)*")


def foreign_words(text):
    """Runs of non-Latin letters in the text, with their script."""
    for m in FOREIGN_WORD.finditer(text):
        word = m.group(0).strip("-")
        letters = [c for c in word if is_foreign_letter(c)]
        if letters:
            yield word, script_of(letters[0])


@lru_cache(maxsize=None)
def _espeak(language):
    import espeakng_loader
    from phonemizer.backend.espeak.wrapper import EspeakWrapper
    EspeakWrapper.set_library(espeakng_loader.get_library_path())
    EspeakWrapper.set_data_path(espeakng_loader.get_data_path())
    from phonemizer.backend import EspeakBackend
    return EspeakBackend(language, with_stress=True)


def foreign_ipa(word, script):
    """IPA for a word in another script, or None when espeak cannot read it."""
    lang = ESPEAK_LANGUAGES.get(script)
    if not lang:
        return None
    try:
        ipa = _espeak(lang).phonemize([word], strip=True)[0].strip()
    except Exception:
        return None
    return ipa or None


def pronunciations(text, lexicon):
    """Every word in `text` needing a given pronunciation: {word: IPA}.

    Book lexicon entries first; then words in other scripts through espeak.
    """
    found = {w: ipa for w, ipa in lexicon.items() if re.search(r"(?<!\w)%s(?!\w)" % re.escape(w), text)}
    for word, script in foreign_words(text):
        if word not in found:
            ipa = foreign_ipa(word, script)
            if ipa:
                found[word] = ipa
    return found


def unsayable(text, speakable_scripts=tuple(ESPEAK_LANGUAGES)):
    """Letters in scripts no voice here can pronounce: {script: count}."""
    out = {}
    for ch in text:
        if is_foreign_letter(ch):
            sc = script_of(ch)
            if sc not in speakable_scripts:
                out[sc] = out.get(sc, 0) + 1
    return out
