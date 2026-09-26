"""Check: can a listener get everything a reader sees?

Runs on the script, before any audio is made, in seconds to minutes even for
a long book. Fails on: a figure or table with nothing to read for it; a
drawing outside a captioned figure; raw LaTeX that could not be read; markup
that would reach the voice; an equation the maths engine cannot speak;
letters no voice here can pronounce; names the voice does not know that the
book's lexicon does not give. Reports, without failing: content marked
print-only with no spoken form, code blocks, and ordinary words the voice's
fallback reads.
"""
import collections
import re

from . import lexicon as lex


class Report:
    def __init__(self):
        self.lines = []
        self.failures = 0

    def item(self, label, found, fail=True, limit=10, show=lambda x: x):
        bad = bool(found) and fail
        self.failures += bad
        tag = "FAIL" if bad else ("note" if found else "ok  ")
        self.lines.append(f"{tag} {label}: {len(found)}")
        for f in list(found)[:limit]:
            self.lines.append("        " + re.sub(r"\s+", " ", show(f))[:170])
        if len(found) > limit:
            self.lines.append(f"        ... and {len(found) - limit} more")

    def text(self):
        return "\n".join(self.lines)


def run(script, book, engine=None):
    inv = script.inventory
    kinds = collections.Counter(f.kind for f in inv)
    segments = [s for ch in script.chapters for s in ch.segments]
    words = sum(len(s.text.split()) for s in segments)
    rep = Report()
    rep.lines.append(f"{book.path.name}: {len(script.chapters)} audio files, {words} words "
                     f"(about {words / 150 / 60:.1f} h at a narrator's pace)")
    rep.lines.append(f"     read for the listener: {kinds['figure']} figures, {kinds['table']} tables, "
                     f"{script.maths} equations, {kinds['spoken_form']} spoken forms; "
                     f"{kinds['layout']} layout-only LaTeX fragments skipped")
    where = lambda f: f"{f.where}: {f.detail}"
    rep.item("figures with no caption to read", [f for f in inv if f.kind == "figure" and f.detail == "(no caption)"],
             show=where)
    rep.item("tables with no caption", [f for f in inv if f.kind == "table" and f.detail == "(no caption)"],
             show=lambda f: f.where)
    rep.item("tables with no header row (cells read without column names)",
             [f for f in inv if f.kind == "table_without_header"], fail=False, show=where)
    rep.item("images with no text to read", [f for f in inv if f.kind == "image_without_text"], show=where)
    rep.item("drawings outside a captioned figure (silent for a listener)",
             [f for f in inv if f.kind == "silent_drawing"], show=where)
    rep.item("raw LaTeX that produced no speech", [f for f in inv if f.kind == "silent_raw"], show=where)
    rep.item("raw LaTeX that could not be read (content lost)", [f for f in inv if f.kind == "unparsed_raw"],
             show=where)
    rep.item("equations the maths engine cannot speak", [f for f in inv if f.kind == "unspoken_math"],
             show=lambda f: f.detail)
    leaks = [(ch.title, m.group(0), s.text[max(0, m.start() - 40):m.end() + 30])
             for ch in script.chapters for s in ch.segments for m in re.finditer(r"\\[a-zA-Z]+|[{}$^_&#|<>]", s.text)]
    rep.item("markup that would reach the voice", leaks, show=lambda x: f"{x[0]}: {x[2]!r}")

    full = "\n".join(s.text for s in segments)
    unsayable = lex.unsayable(full)
    examples = {}
    for s in segments:
        for k, ch in enumerate(s.text):
            if lex.is_foreign_letter(ch):
                sc = lex.script_of(ch)
                if sc in unsayable and sc not in examples:
                    examples[sc] = s.text[max(0, k - 40):k + 30]
    rep.item("letters no voice here can pronounce (give them a spoken form)",
             [f"{sc}: {n} letters, e.g. {examples.get(sc, '')!r}" for sc, n in sorted(unsayable.items())])

    book_lexicon = lex.load(book.lexicon_path)
    if engine is not None:
        counts = collections.Counter(w for s in segments for w in re.findall(r"(?<![\d\w-])[A-Za-zÀ-ɏ'’-]+", s.text))
        unknown = {w for w in engine.unknown_words(counts) if w not in book_lexicon}
        names = collections.Counter({w: counts[w] for w in unknown if w[:1].isupper() and not w.isupper()})
        common = collections.Counter({w: counts[w] for w in unknown if w not in names})
        rep.item("names the voice does not know and the lexicon does not give", names.most_common(),
                 limit=40, show=lambda x: f"{x[0]} ({x[1]})")
        rep.item("ordinary words the voice reads through its fallback", common.most_common(), fail=False,
                 limit=12, show=lambda x: f"{x[0]} ({x[1]})")
    guessed = lex.guesses(book.lexicon_path)
    rep.item("pronunciations still marked as guesses (hear them with `mdaudiobook names`)", sorted(guessed),
             fail=False, limit=20)
    rep.item("content marked print-only with no spoken form",
             [f for f in inv if f.kind == "print_only_unspoken"], fail=False, show=where)
    rep.item("code blocks (not read)", [f for f in inv if f.kind == "code_block"], fail=False, show=where)
    return rep
