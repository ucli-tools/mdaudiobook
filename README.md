# mdaudiobook

Markdown books to audiobooks. The same Markdown that
[mdtexpdf](https://github.com/ucli-tools/mdtexpdf) turns into a PDF and an EPUB
(and that [docx2md](https://github.com/ucli-tools/docx2md) can produce from a
Word file) becomes store-ready audio: one MP3 per chapter and an M4B with
chapter marks and cover, narrated by a neural voice that runs on your own
computer.

The pipeline is **script → check → voice → master → verify**, and every step
can be checked against the one before it.

- **Script.** pandoc reads the book, including raw LaTeX figures and tables,
  and mdaudiobook writes the exact words the listener will hear, as a text
  file you can read before any audio exists.
- **Check.** Can a listener get everything a reader sees? A figure without a
  caption, a drawing outside a figure, a table without a caption, an equation
  that cannot be spoken, letters no voice can pronounce, a name the voice does
  not know: each fails the check, before a minute of audio is spent.
- **Voice.** Sentence by sentence, cached, so an edited book re-voices only the
  sentences that changed. Chapters are written to disk as they are made, so a
  fifty-hour book never sits in memory, and several chapters are voiced at once.
- **Master.** Levelled and encoded to the audiobook stores' rules, then measured
  again as encoded.
- **Verify.** Whisper transcribes the audio in windows of whole sentences, cut
  at the times synthesis recorded and never longer than Whisper's own
  30-second window (over longer audio it drifts and skips, and would report as
  missing what was said); each window is aligned with its script: a dropped
  sentence or a garbled stretch fails the build, with its time and its text.

## What the listener hears for what the reader sees

| In the book | In the audiobook |
|---|---|
| Headings | Read, with a longer pause; chapter headings start a new file, part titles are announced at the start of the next chapter |
| Mathematics | Read by the [Speech Rule Engine](https://github.com/Speech-Rule-Engine/speech-rule-engine) (the engine screen readers use) in ClearSpeak style: "the fraction with numerator 1 and denominator n squared"; a letter in mathematics is spoken by its name ("e" as "ee", never like the article "a") |
| A display equation the book itself reads aloud in the next line | The book's own reading (setting `equation_readings: after`) |
| Figures | "Figure 9.2." and the caption, then the book's audio description of the picture, if it gives one (see below) |
| Tables | "Table 3.1." and the caption, then each row with its column names: "180 degrees. Fraction of a turn: a half." |
| Footnotes | "Footnote." and the note, after its paragraph |
| Abbreviations, units, symbols, URLs | Said the way a narrator says them: "for example", "40 hertz", "50 percent", "library dot example dot org" |
| Words in Greek, Cyrillic, Hebrew, ... | Pronounced in their own language (through espeak-ng) |
| Hieroglyphs, cuneiform, other signs with no reading | A spoken form the book gives (see below); `check` fails until it does |
| Code blocks | Not read (reported by `check`) |

## Install

Needs `pandoc`, `ffmpeg`, Node.js (`node` and `npm`, for the mathematics) and
[uv](https://docs.astral.sh/uv/).

```bash
make build            # installs the mdaudiobook command (CPU)
mdaudiobook setup     # once: the maths speech engine and the voice model
```

On a machine with an NVIDIA GPU use `make build-gpu` and build with
`--device cuda`: the same code, much faster voicing.

## Use

```bash
mdaudiobook script book.md          # book_audiobook/script.txt: read it, it is what will be spoken
mdaudiobook check book.md           # what a listener would miss; exit 1 if anything
mdaudiobook names book.md           # every name the voice guesses, spoken, with a list, for review
mdaudiobook build book.md --chapters 3      # one chapter: listen before committing to the whole book
mdaudiobook build book.md --workers 3 --threads 8
mdaudiobook verify book.md          # compare built audio with its script again
mdaudiobook voices                  # the available voices
```

`build` runs check, voice, master and verify. `--chapters` takes `3`, `2-5`,
`1,4` or words from a chapter title. Output goes to `<book>_audiobook/` beside
the book:

```
script.txt, script.json    the narration script
cache/                     one audio file per sentence (keep it: rebuilds reuse it)
chapters/NN.wav            voiced chapters
mp3/NN - Title.mp3         store files: 192 kbps CBR, 44.1 kHz, tagged, with cover
<book>.m4b                 the whole book with chapter marks and cover
master.json, verify.json   measurements and the verify report
```

## Settings in the book

Under an `audiobook:` key in the YAML front matter (or in `metadata.yaml`
beside the book); the title, subtitle, author, date and `cover_image` come from
the book's ordinary metadata.

```yaml
audiobook:
  voice: am_michael               # see `mdaudiobook voices`
  speed: 1.0
  lexicon: audiobook/pronunciations.yaml
  equation_readings: after        # or none
  chapter_level: 2                # headings at this level or above start a new file
  cover: img/cover_square.jpg     # square, at least 2400x2400; else cover_image cropped to a square
  descriptions: required          # every figure needs an audio description (default: optional)
  pdf: book.pdf                   # the built PDF to check numbers against (default: <book>.pdf)
  narrator: "a synthetic voice"   # credited in the opening and closing credits
  credits: true
  max_file_minutes: 110           # longer chapters are split at a heading
```

## Markup for listeners

The PDF and EPUB print these as usual; only the audiobook reads them
differently.

```markdown
The tally [𓏺𓏺𓏺]{speak="three vertical strokes"} stands for three.

Three strokes [(𓏺𓏺𓏺)]{speak=""} mean three.

::: {.print-only speak="In the chart, each number from one to nine is that many strokes."}
(a chart of numerals, as a table or raw LaTeX)
:::
```

`speak="..."` replaces the content in the audiobook; `speak=""` silences it
(for signs already described in words beside them); a `.print-only` block
without `speak` is skipped and reported by `check`. In a `speak` attribute,
`{number}` stands for the number of the figure or table inside the block.

A listener cannot see a figure, so a book can say what it shows. An HTML
comment right after the figure is read after its caption, and appears nowhere
else (not in the PDF, the EPUB or rendered Markdown), while it stays in the
Markdown for the author to review:

```markdown
<!-- audio-description
Here in Figure 9.2 we see a circle drawn around the origin, with a point
turning around it ...
-->
```

The description is Markdown: a letter or symbol written as maths (`$a$`,
`$\theta$`) is spoken as it is in the text, so a side labelled $a$ is "a" by
name and not the article.

`check` lists every figure without one; with `descriptions: required` in
the book's `audiobook:` settings it fails until each has one.

Figures and tables are numbered as the PDF numbers them: per chapter, with the
chapter's label ("Chapter 9" gives 9.1, 9.2 ...; "Appendix B" gives B.1 ...),
and only when captioned. When the book's PDF is built (`<book>.pdf` beside it,
or `audiobook.pdf`), `check` compares every number and caption with it.

## Pronunciations

The voice guesses words its dictionary lacks. Names matter, and a guess is
often wrong ("Hegel" read "Hejel"), so a book keeps a lexicon of IPA:

```yaml
Leibniz: ˈlaɪbnɪts
Hegel: ˈheɪɡəl
Nguyen:
  ipa: ˈŋwɪn
  guess: true          # not yet checked by ear: `check` lists it, `names` marks it
```

`check` fails on any name the voice does not know that the lexicon does not
give, and lists entries still marked `guess`. `mdaudiobook names` speaks every
name, one after another, with a timed list, so a whole book's names can be
checked by ear in minutes.

## Store specifications

The mastering step targets the strictest common rules (Audible's ACX), which
the other stores accept: MP3 192 kbps constant bit rate, 44.1 kHz; one file per
chapter and none over 120 minutes; RMS between -23 and -18 dB; peaks at or
below -3 dB; noise floor at or below -60 dB; half a second to a second of
silence at the head and one to five seconds at the tail. Every file is measured
after encoding and reported. A square cover of at least 2400 by 2400 pixels
goes into every file.

Stores differ on narration by a synthetic voice; check each store's current
rules before publishing. The opening and closing credits name the narrator,
"a synthetic voice" unless the book says otherwise.

## Voices and engines

The default engine is [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
(Apache-2.0), which runs on a CPU at roughly real time and much faster on a
GPU. Everything but the voicing (script, cache, mastering, checks) is shared,
so a book can move to another engine by a setting once it exists: subclass
`Engine` in `src/mdaudiobook/engines/`, register it, and make its `identity`
change whenever its sound would, because the sentence cache is keyed on it.

## Tests

```bash
make test
```

The tests build the example book in `tests/fixtures/`, which exercises every
case above.

## Licence

Apache-2.0.
