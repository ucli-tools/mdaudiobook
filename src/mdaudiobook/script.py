"""The narration script: the exact words the listener will hear.

pandoc reads the book (Markdown, and the raw LaTeX figures and tables in it)
into its syntax tree; this module walks the tree and writes what a narrator
would say. What a reader sees but a listener cannot is spoken or described:
figure captions are read, table rows are read with their column names,
equations are read by the maths speech engine or through the book's own
reading, and content marked for print is replaced by its spoken form.
Everything met on the way is recorded in an inventory for `check`.

Markup a book can use (PDF and EPUB builds print the content as usual):
  ::: {.print-only speak="..."}   read the attribute instead of the block
  ::: {.print-only}               skip the block (reported by `check`)
  [text]{speak="..."}             read the attribute instead of the text
  [text]{speak=""}                skip the text (for example glyphs already
                                  described in words next to them)
  {number} in a speak attribute   the number of the figure or table inside
  <!-- audio-description          after a figure or table: what the picture
  Here in Figure 9.2 we see ...   shows, read after its caption (an HTML
  -->                             comment: invisible in print and on screen)

Figures and tables are announced with their numbers as the PDF prints them:
per chapter, prefixed by the chapter's own label ("Chapter 9" gives 9.1,
9.2 ...; "Appendix B" gives B.1 ...).
"""
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field

from . import latex, mathspeech
from .text import normalize

M_OPEN, M_CLOSE = "\ue000", "\ue001"   # maths placeholders, never in a book
L_OPEN, L_CLOSE = "\ue010", "\ue011"   # a letter in mathematics, spoken by its name


def plain(text):
    """Text without the letter markers, for reading and review."""
    return text.replace(L_OPEN, "").replace(L_CLOSE, "")


@dataclass
class Segment:
    text: str
    pause: float
    kind: str = "text"      # text, heading, equation, reading, figure, table, note, credit


@dataclass
class Chapter:
    title: str
    level: int
    segments: list = field(default_factory=list)

    @property
    def words(self):
        return sum(len(s.text.split()) for s in self.segments)


@dataclass
class Finding:
    kind: str
    detail: str
    where: str


@dataclass
class Script:
    chapters: list
    inventory: list
    maths: int
    floats: list = field(default_factory=list)     # [kind, number, caption, described]

    def to_json(self):
        return {"chapters": [asdict(c) for c in self.chapters], "inventory": [asdict(f) for f in self.inventory],
                "maths": self.maths, "floats": self.floats}

    def text(self):
        """The script as plain text, one paragraph per segment, for reading and review."""
        lines = []
        for i, ch in enumerate(self.chapters, 1):
            lines.append(f"=== {i:02d}. {ch.title} ===\n")
            lines.extend(plain(s.text) + "\n" for s in ch.segments)
        return "\n".join(lines)


def pandoc_blocks(text, fmt):
    res = subprocess.run(["pandoc", "-f", fmt, "-t", "json"], input=text, capture_output=True, text=True)
    if res.returncode != 0:
        raise ValueError(res.stderr.strip()[:300])
    return json.loads(res.stdout)["blocks"]


def _attrs(attr):
    ident, classes, kv = attr
    return ident, classes, dict(kv)


class Walker:
    def __init__(self, settings):
        self.s = settings
        self.p = settings["pauses"]
        self.maths = []          # (tex, display)
        self.inventory = []
        self.chapters = []
        self.heading = ""
        self._raw_open = set()
        self._chapter_title = "Opening"
        self.label = None                   # the chapter's label for numbering: "9", "B"
        self.counts = {"Figure": 0, "Table": 0}
        self.floats = []                    # [kind, number, caption, described]
        self._last_float = None             # index in self.floats, while its description may follow

    # ---- bookkeeping -------------------------------------------------------
    def where(self):
        chapter = self._chapter_title
        return chapter if self.heading in ("", chapter) else f"{chapter} / {self.heading}"

    def note(self, kind, detail=""):
        self.inventory.append(Finding(kind, re.sub(r"\s+", " ", str(detail))[:200], self.where()))

    def chapter(self):
        if not self.chapters:
            self.chapters.append(Chapter("Opening", 0))
        return self.chapters[-1]

    def add(self, text, pause, kind="text"):
        text = text.strip()
        if text:
            self.chapter().segments.append(Segment(text, pause, kind))

    # ---- inlines -----------------------------------------------------------
    def inlines(self, xs, notes):
        out = []
        for x in xs:
            t, c = x["t"], x.get("c")
            if t == "Str":
                out.append(c)
            elif t in ("Space", "SoftBreak", "LineBreak"):
                out.append(" ")
            elif t in ("Emph", "Strong", "Underline", "SmallCaps", "Strikeout", "Superscript", "Subscript"):
                out.append(self.inlines(c, notes))
            elif t == "Span":
                _, classes, kv = _attrs(c[0])
                if "speak" in kv:
                    out.append(kv["speak"])
                elif "print-only" not in classes:
                    out.append(self.inlines(c[1], notes))
            elif t == "Quoted":
                out.append("“" + self.inlines(c[1], notes) + "”")
            elif t == "Math":
                display = c[0]["t"] == "DisplayMath"
                self.maths.append((c[1], display))
                out.append(f" {M_OPEN}{len(self.maths) - 1}{M_CLOSE} ")
            elif t == "Link":
                out.append(self.inlines(c[1], notes))
            elif t == "Image":
                alt = self.inlines(c[1], notes)
                if not alt:
                    self.note("image_without_text", c[2][0])
                out.append(alt)
            elif t == "Code":
                out.append(c[1])
            elif t == "Note":
                notes.append(" ".join(s for s in self.blocks_text(c)))
            elif t == "RawInline" and c[0] in ("latex", "tex"):
                out.append(self.raw_inline(c[1], notes))
            elif t == "Cite":
                out.append(self.inlines(c[1], notes))
        return re.sub(r"\s+", " ", "".join(out)).strip()

    def raw_inline(self, tex, notes):
        # pandoc returns a command it cannot read as raw LaTeX again: parse
        # each fragment once, and count what stays unread
        if tex in self._raw_open:
            self.note("layout" if latex.is_layout(tex) else "silent_raw", tex)
            return ""
        self._raw_open.add(tex)
        try:
            return " ".join(self.blocks_text(pandoc_blocks(latex.prepare(tex), "latex")))
        except ValueError:
            self.note("unparsed_raw", tex)
            return ""
        finally:
            self._raw_open.discard(tex)

    def blocks_text(self, bs):
        """The words of some blocks, without adding them to the script or
        counting any figure or table in them a second time."""
        saved = (self.chapters, self.heading, dict(self.counts), len(self.floats), self._last_float)
        self.chapters = [Chapter("", 0)]
        try:
            self.blocks(bs, nested=True)
            return [s.text for s in self.chapters[0].segments]
        finally:
            self.chapters, self.heading, self.counts, n, self._last_float = saved
            del self.floats[n:]

    # ---- blocks ------------------------------------------------------------
    def blocks(self, bs, nested=False):
        for b in bs:
            self.block(b, nested)

    def block(self, b, nested):
        t, c = b["t"], b.get("c")
        notes = []
        if t == "Header":
            level, attr, content = c
            title = self.inlines(content, notes)
            if not nested and level <= self.s["chapter_level"]:
                self.start_chapter(title, level)
            self.heading = title
            pause = self.p["chapter_heading"] if level <= self.s["chapter_level"] else self.p["heading"]
            self.add(title + ("" if title[-1:] in ".!?:" else "."), pause, "heading")
        elif t in ("Para", "Plain"):
            self._last_float = None
            text = self.inlines(c, notes)
            alone = re.fullmatch(f"{M_OPEN}\\d+{M_CLOSE}", text.strip())
            self.add(text, self.p["equation"] if alone else self.p["paragraph"], "equation" if alone else "text")
        elif t == "LineBlock":
            for line in c:
                self.add(self.inlines(line, notes), self.p["sentence"])
        elif t == "BlockQuote":
            self.blocks(c, nested)
        elif t in ("BulletList", "OrderedList"):
            items = c if t == "BulletList" else c[1]
            for item in items:
                before = len(self.chapter().segments)
                self.blocks(item, nested)
                segs = self.chapter().segments
                if len(segs) > before:
                    segs[-1].pause = self.p["list_item"]
        elif t == "DefinitionList":
            for term, defs in c:
                self.add(self.inlines(term, notes) + ".", self.p["sentence"])
                for d in defs:
                    self.blocks(d, nested)
        elif t == "Div":
            _, classes, kv = _attrs(c[0])
            if "speak" in kv:
                nums = self.count_floats(c[1])
                said = kv["speak"].replace("{number}", nums[0] if nums and nums[0] else "")
                self.note("spoken_form", said[:80])
                self._last_float = None
                self.add(said, self.p["paragraph"])
            elif "print-only" in classes:
                self.count_floats(c[1])
                self._last_float = None
                self.note("print_only_unspoken", self.first_words(c[1]))
            else:
                self.blocks(c[1], nested)
        elif t == "RawBlock" and c[0] in ("latex", "tex"):
            self.raw_block(c[1], nested)
        elif t == "RawBlock" and c[0] == "html":
            self.description(c[1])
        elif t == "Figure":
            caption = " ".join(self.blocks_text(c[1][1]))
            self.note("figure", caption or "(no caption)")
            said = self.float_seen("Figure", caption)
            if caption:
                self.add(said + " " + caption, self.p["paragraph"], "figure")
        elif t == "Table":
            self.table(c)
        elif t == "CodeBlock":
            self.note("code_block", c[1][:80])
        elif t == "HorizontalRule":
            segs = self.chapter().segments
            if segs:
                segs[-1].pause = max(segs[-1].pause, self.p["heading"])
        for n in notes:
            self.add("Footnote. " + n, self.p["paragraph"], "note")

    def number(self, kind, caption):
        """Next number of a figure or table, as the PDF prints it: LaTeX
        numbers a float at its caption, so one without a caption has none."""
        if not caption.strip():
            return None
        self.counts[kind] += 1
        return f"{self.label}.{self.counts[kind]}" if self.label else None

    def float_seen(self, kind, caption):
        num = self.number(kind, caption)
        self.floats.append([kind, num, caption, False])
        self._last_float = len(self.floats) - 1
        if caption.strip() and not num:
            self.note("unnumbered_float", f"{kind} in a chapter without a label: {caption[:60]}")
        return f"{kind} {num}." if num else f"{kind}."

    def count_floats(self, bs):
        """Figures and tables inside content that is not read (print-only):
        they are numbered in the PDF, so they are counted here too."""
        found = []
        for b in bs:
            t, c = b["t"], b.get("c")
            if t == "RawBlock" and c[0] in ("latex", "tex") and not latex.is_layout(c[1]):
                try:
                    found += self.count_floats(pandoc_blocks(latex.prepare(c[1]), "latex"))
                except ValueError:
                    pass
            elif t in ("Figure", "Table"):
                caption = " ".join(self.blocks_text((c[1] if t == "Figure" else c[1])[1]))
                kind = "Figure" if t == "Figure" else "Table"
                num = self.number(kind, caption)
                self.floats.append([kind, num, caption, True])
                found.append(num)
            elif t == "Div":
                found += self.count_floats(c[1])
        return found

    def description(self, html):
        m = re.match(r"\s*<!--\s*audio-description\b(.*?)-->\s*$", html, re.S)
        if not m:
            return False
        text = re.sub(r"\s+", " ", m.group(1)).strip()
        if self._last_float is None:
            self.note("orphan_description", text[:80])
        else:
            self.floats[self._last_float][3] = True
        self.add(text, self.p["paragraph"], "description")
        return True

    def first_words(self, bs):
        text = " ".join(self.blocks_text(bs))
        return text[:80] or "(no text)"

    def raw_block(self, tex, nested):
        if latex.is_layout(tex):
            self.note("layout", tex)
            return
        try:
            blocks = pandoc_blocks(latex.prepare(tex), "latex")
        except ValueError:
            self.note("unparsed_raw", tex)
            return
        before = len(self.chapter().segments)
        self.blocks(blocks, nested)
        segs = self.chapter().segments
        if len(segs) == before:
            self.note("silent_drawing" if latex.DRAWING.search(tex) else "silent_raw", tex)
        elif latex.CENTRED_ITALIC.match(tex) and len(segs) == before + 1:
            segs[-1].kind = "reading"

    def table(self, c):
        caption = " ".join(self.blocks_text(c[1][1]))
        head_rows = c[3][1]
        header = []
        for row in head_rows:
            cells = [" ".join(self.blocks_text(cell[4])) for cell in row[1]]
            header = cells if not header else [f"{a} {b}".strip() for a, b in zip(header, cells)]
        self.note("table", caption or "(no caption)")
        if not any(header):
            self.note("table_without_header", caption or "(no caption)")
        said = self.float_seen("Table", caption)
        if caption:
            self.add(said + " " + caption, self.p["paragraph"], "table")
        for body in c[4]:
            for row in body[3]:
                cells = [" ".join(self.blocks_text(cell[4])) for cell in row[1]]
                if not any(cells):
                    continue
                if any(header):
                    parts = [cells[0]] + [f"{h}: {v}" if h else v for h, v in zip(header[1:], cells[1:]) if v]
                    self.add(". ".join(p.rstrip(".") for p in parts if p) + ".", self.p["list_item"], "table")
                else:
                    self.add(", ".join(v for v in cells if v) + ".", self.p["list_item"], "table")

    def start_chapter(self, title, level):
        current = self.chapters[-1] if self.chapters else None
        # A part title with nothing under it is announced at the start of
        # the next chapter instead of standing alone as a file
        carry = []
        if current and all(s.kind == "heading" for s in current.segments) and current.level < level:
            carry = current.segments
            self.chapters.pop()
        elif current and not current.segments:
            self.chapters.pop()
        self.chapters.append(Chapter(title, level, list(carry)))
        self.heading = title
        self._chapter_title = title
        m = re.match(r"(?:Chapter|Appendix)\s+([0-9]+|[A-Z]{1,3})\b", title)
        self.label = m.group(1) if m else None
        self.counts = {"Figure": 0, "Table": 0}
        self._last_float = None


def _apply_equation_readings(chapters):
    for ch in chapters:
        keep = []
        for i, s in enumerate(ch.segments):
            nxt = ch.segments[i + 1] if i + 1 < len(ch.segments) else None
            if s.kind == "equation" and nxt is not None and nxt.kind == "reading":
                continue
            keep.append(s)
        ch.segments = keep


def _split_long(chapters, settings):
    """Stores cap a file at 120 minutes: cut long chapters at a heading."""
    limit = settings["max_file_minutes"] * 150       # words at a narrator's pace
    out = []
    for ch in chapters:
        if ch.words <= limit:
            out.append(ch)
            continue
        part, n, words = Chapter(ch.title, ch.level), 1, 0
        for s in ch.segments:
            if s.kind == "heading" and words > limit * 0.6 and part.segments:
                out.append(part)
                n += 1
                part, words = Chapter(f"{ch.title} (part {n})", ch.level), 0
            part.segments.append(s)
            words += len(s.text.split())
        out.append(part)
        if n > 1:
            out[-n].title = f"{ch.title} (part 1)"
    return out


def credits(book):
    s = book.settings
    title = book.title + (f": {book.meta['subtitle']}" if book.meta.get("subtitle") else "")
    opening = Chapter("Opening credits", 0, [
        Segment(f"{title}.", s["pauses"]["heading"], "credit"),
        Segment(f"Written by {book.author}." if book.author else "", s["pauses"]["paragraph"], "credit"),
        Segment(f"Narrated by {book.narrator}.", s["pauses"]["chapter_heading"], "credit")])
    closing = Chapter("End credits", 0, [
        Segment(f"This is the end of {title}" + (f", written by {book.author}" if book.author else "")
                + f", narrated by {book.narrator}.", s["pauses"]["paragraph"], "credit")])
    if book.meta.get("copyright"):
        closing.segments.append(Segment(str(book.meta["copyright"]), s["pauses"]["paragraph"], "credit"))
    for ch in (opening, closing):
        ch.segments = [x for x in ch.segments if x.text]
    return opening, closing


def build(book, style="clearspeak"):
    """Book -> Script."""
    s = book.settings
    body = book.markdown
    for pat in s["strip_patterns"]:
        body = re.sub(pat, "", body)
    w = Walker(s)
    w.blocks(pandoc_blocks(body, "markdown"))

    spoken = mathspeech.speak(w.maths, style=style) if w.maths else []
    for (tex, display), said in zip(w.maths, spoken):
        if not said:
            w.inventory.append(Finding("unspoken_math", tex[:200], ""))
    spoken = [said or "an equation" for said in spoken]
    for f in w.floats:
        f.append(f[2])                                   # the caption as written, with maths marked
        f[2] = re.sub(f"{M_OPEN}(\\d+){M_CLOSE}", lambda m: plain(spoken[int(m.group(1))]), f[2])

    chapters = [c for c in w.chapters if c.segments]
    if s["equation_readings"] == "after":
        _apply_equation_readings(chapters)
    for ch in chapters:
        for seg in ch.segments:
            seg.text = normalize(re.sub(f"{M_OPEN}(\\d+){M_CLOSE}", lambda m: spoken[int(m.group(1))], seg.text))
    chapters = _split_long(chapters, s)
    if s["credits"]:
        opening, closing = credits(book)
        chapters = [opening] + chapters + [closing]
    return Script(chapters=chapters, inventory=w.inventory, maths=len(w.maths), floats=w.floats)


def select(script, spec):
    """Keep the chapters named by a spec: "3", "2-5", "1,4-6", or text found in a title."""
    if not spec:
        return script
    chosen = set()
    n = len(script.chapters)
    for part in str(spec).split(","):
        part = part.strip()
        if re.fullmatch(r"\d+(-\d+)?", part):
            a, _, b = part.partition("-")
            chosen.update(range(int(a), int(b or a) + 1))
        else:
            chosen.update(i for i, c in enumerate(script.chapters, 1) if part.lower() in c.title.lower())
    keep = [c for i, c in enumerate(script.chapters, 1) if i in chosen and i <= n]
    return Script(chapters=keep, inventory=script.inventory, maths=script.maths, floats=script.floats)
