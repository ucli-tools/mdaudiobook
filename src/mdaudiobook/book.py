"""A book: its Markdown, its metadata, and its audiobook settings.

Metadata comes from the Markdown's YAML front matter and, when present, a
metadata.yaml beside it (the same sources mdtexpdf reads with
--read-metadata); the front matter wins. Audiobook settings live under an
`audiobook:` key and fall back to DEFAULTS.
"""
import copy
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULTS = {
    "engine": "kokoro",
    "voice": "am_michael",
    "speed": 1.0,
    # Pronunciations: {word: IPA}, a YAML or JSON file relative to the book
    "lexicon": None,
    # Headings at this level or above start a new audio file (chapter).
    # Higher headings (parts) are announced at the start of the next file.
    "chapter_level": 2,
    # "after": a display equation followed by a centred italic line is read
    # through that line, the book's own reading, instead of by the maths
    # speech engine. "none": every equation is read by the engine.
    "equation_readings": "none",
    # Credited narrator; by default the synthetic voice is named as such
    "narrator": None,
    "credits": True,
    # Stores cap a file at 120 minutes; longer chapters are split at a heading
    "max_file_minutes": 110,
    # Square cover for the audiobook (stores want at least 2400x2400);
    # without one, the book's cover_image is cropped to a square
    "cover": None,
    # Pauses in seconds
    "pauses": {"sentence": 0.35, "paragraph": 0.75, "heading": 1.2, "chapter_heading": 1.8,
               "equation": 0.6, "list_item": 0.45},
    # "required": every figure and table must have an audio description (an
    # <!-- audio-description ... --> comment after it); "optional": listed only
    "descriptions": "optional",
    # The built PDF, to check that figure and table numbers match it
    # (default: <book>.pdf beside the book, when it exists)
    "pdf": None,
    # Markers stripped before reading (docx2md writes Word index entries this way)
    "strip_patterns": [r"\[index:[^\]]*\]"],
}


def _front_matter(text):
    m = re.match(r"^---\s*\n(.*?)\n(---|\.\.\.)\s*\n", text, re.S)
    if not m:
        return {}, text
    return (yaml.safe_load(m.group(1)) or {}), text[m.end():]


def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


@dataclass
class Book:
    path: Path
    markdown: str
    meta: dict = field(default_factory=dict)
    settings: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path, overrides=None):
        path = Path(path).resolve()
        text = path.read_text(encoding="utf-8")
        meta, _ = _front_matter(text)
        side = path.parent / "metadata.yaml"
        if side.exists():
            meta = {**(yaml.safe_load(side.read_text(encoding="utf-8")) or {}), **meta}
        settings = _merge(DEFAULTS, meta.get("audiobook") or {})
        settings = _merge(settings, {k: v for k, v in (overrides or {}).items() if v is not None})
        return cls(path=path, markdown=text, meta=meta, settings=settings)

    @property
    def stem(self):
        return self.path.stem

    @property
    def title(self):
        return str(self.meta.get("title") or self.stem)

    @property
    def author(self):
        a = self.meta.get("author") or ""
        return ", ".join(a) if isinstance(a, list) else str(a)

    @property
    def narrator(self):
        return self.settings.get("narrator") or "a synthetic voice"

    def resolve(self, rel):
        """A path from the metadata, relative to the book."""
        return None if not rel else (self.path.parent / rel).resolve()

    @property
    def lexicon_path(self):
        return self.resolve(self.settings.get("lexicon"))

    @property
    def out_dir(self):
        return self.path.parent / f"{self.stem}_audiobook"

    def pdf_path(self):
        p = self.resolve(self.settings.get("pdf")) or self.path.with_suffix(".pdf")
        return p if p.exists() else None

    def cover_path(self):
        return self.resolve(self.settings.get("cover")) or self.resolve(self.meta.get("cover_image"))

    def digest(self):
        return hashlib.sha1(self.markdown.encode("utf-8")).hexdigest()[:12]
