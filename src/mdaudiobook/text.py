"""Written text into speakable text, and speakable text into sentences.

Voices read what they are given: an abbreviation, a URL or a symbol has to be
written out the way a narrator would say it. Sentences are the unit of
synthesis: a voice model limits how much it takes at once and may silently
drop the end of a longer input, so long sentences are cut at clause breaks.
"""
import re

ABBREVIATIONS = [
    (r"\be\.g\.,?", "for example,"),
    (r"\bi\.e\.,?", "that is,"),
    (r"\betc\.", "et cetera."),
    (r"\bcf\.", "compare"),
    (r"\bvs\.", "versus"),
    (r"\bviz\.", "namely"),
    (r"\bet al\.", "and colleagues"),
    (r"\bca\.\s*(?=\d)", "circa "),
    (r"\bc\.\s*(?=\d)", "circa "),
    (r"\bpp\.\s*(?=\d)", "pages "),
    (r"\bp\.\s*(?=\d)", "page "),
    (r"\bvol\.\s*(?=\d)", "volume "),
    (r"\bch\.\s*(?=\d)", "chapter "),
    (r"\bfig\.\s*(?=\d)", "figure "),
    (r"\beq\.\s*(?=\d)", "equation "),
    (r"\bNo\.\s*(?=\d)", "number "),
    (r"\bSt\.\s+(?=[A-Z])", "Saint "),
    (r"\bDr\.\s+(?=[A-Z])", "Doctor "),
    (r"\bMr\.\s+(?=[A-Z])", "Mister "),
    (r"\bMrs\.\s+(?=[A-Z])", "Missus "),
    (r"\bBCE\b", "B C E"),
    (r"\bCE\b", "C E"),
    (r"\bBC\b", "B C"),
    (r"\bAD\b(?=\s*\d)", "A D"),
]

UNITS = {"Hz": "hertz", "kHz": "kilohertz", "MHz": "megahertz", "GHz": "gigahertz", "THz": "terahertz",
         "eV": "electron volts", "keV": "kilo electron volts", "MeV": "mega electron volts",
         "GeV": "giga electron volts", "km": "kilometres", "cm": "centimetres", "mm": "millimetres",
         "nm": "nanometres", "kg": "kilograms", "mg": "milligrams", "ms": "milliseconds", "ns": "nanoseconds",
         "km/s": "kilometres per second", "m/s": "metres per second"}

SYMBOLS = [
    (r"(?<=\d)\s*%", " percent"),
    (r"(?<=\d)\s*°\s*C\b", " degrees Celsius"),
    (r"(?<=\d)\s*°", " degrees"),
    (r"\s&\s", " and "),
    (r"§\s*", "section "),
    (r"(?<=\d)\s*×\s*(?=\d)", " by "),
    (r"(?<=\d)\s*[–—]\s*(?=\d)", " to "),
    (r"\s*→\s*", " to "),
    (r"…", "..."),
]

# Capitals used for stress are words, not initials: "IS" is read "is"
STRESS_WORDS = r"\b(IS|NOT|ARE|WAS|WERE|THE|AND|OR|NO|ALL|ONE|NOW|NEVER|MUST|ONLY|EVERY|NOTHING|EVERYTHING|BE)\b"

ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roman_to_int(s):
    total, prev = 0, 0
    for ch in reversed(s):
        v = ROMAN[ch]
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


def _url(m):
    u = re.sub(r"^https?://(www\.)?", "", m.group(0)).rstrip("/.,;")
    tail = m.group(0)[len(m.group(0).rstrip("/.,;")):]
    return u.replace(".", " dot ").replace("/", " slash ").replace("-", " dash ").replace("_", " underscore ") + tail


def normalize(text):
    text = re.sub(r"https?://\S+|\b(?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:org|com|net|io|edu|gov|tf)(?:/\S*)?",
                  _url, text)
    for pat, rep in ABBREVIATIONS:
        text = re.sub(pat, rep, text)
    for pat, rep in SYMBOLS:
        text = re.sub(pat, rep, text)
    for unit, words in sorted(UNITS.items(), key=lambda u: -len(u[0])):
        text = re.sub(r"(?<=\d)\s*%s(?![\w/])" % re.escape(unit), " " + words, text)
    text = re.sub(r"\bHz\b", "hertz", text)
    text = re.sub(r"\s=\s", " equals ", text)
    text = re.sub(r"(?<=\d)\s*\+\s*(?=\d)", " plus ", text)
    # Punctuation left before a full stop by a silenced span: "wedges: ."
    text = re.sub(r"[:;,]\s*([.!?])", r"\1", text)
    text = re.sub(STRESS_WORDS, lambda m: m.group(1).lower(), text)
    # Roman numerals after a division name are numbers
    text = re.sub(r"\b(Chapter|Part|Book|Volume|Appendix|Section|Act|Scene|Canto)\s+([IVXLCDM]+)\b",
                  lambda m: f"{m.group(1)} {roman_to_int(m.group(2))}", text)
    text = re.sub(r"\s+([,.;:!?)])", r"\1", text)
    text = re.sub(r"([(“])\s+", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


# A sentence ends at . ! ? (and any closing quote or bracket) before a space
# and a capital, a digit or an opening quote; not after an initial ("J. S.")
_SENTENCE_END = re.compile(r"(?<=[.!?])[”’\"')\]]*\s+(?=[A-Z0-9“‘\"'(])")
_INITIAL = re.compile(r"(?:^|\s)[A-Z]\.$")


def sentences(text, max_chars=300):
    out, start = [], 0
    for m in _SENTENCE_END.finditer(text):
        piece = text[start:m.start()] + m.group(0).rstrip()
        if _INITIAL.search(text[start:m.start()]):
            continue
        out.append(piece.strip())
        start = m.end()
    out.append(text[start:].strip())
    result = []
    for s in filter(None, out):
        result.extend(_cut(s, max_chars))
    return result


def _cut(s, max_chars):
    """Cut a long sentence at the clause break nearest its middle."""
    if len(s) <= max_chars:
        return [s]
    mid = len(s) // 2
    breaks = [m.end() for m in re.finditer(r"[;:]\s+|,\s+(?=(?:and|but|or|so|which|while|whereas|because)\b)|,\s+|\s[—–]\s", s)]
    if not breaks:
        breaks = [m.end() for m in re.finditer(r"\s+", s)]
    cut = min(breaks, key=lambda b: abs(b - mid))
    return _cut(s[:cut].strip(), max_chars) + _cut(s[cut:].strip(), max_chars)
