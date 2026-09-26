"""mdaudiobook command line."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import __version__
from .book import Book


def _book(args):
    overrides = {"voice": getattr(args, "voice", None), "engine": getattr(args, "engine", None),
                 "speed": getattr(args, "speed", None)}
    return Book.load(args.book, overrides)


def _engine(book, args):
    kw = {"voice": book.settings["voice"], "speed": book.settings["speed"]}
    if getattr(args, "device", None):
        kw["device"] = args.device
    return book.settings["engine"], kw


def _script(book, args):
    from . import script as sc
    t0 = time.time()
    s = sc.build(book)
    print(f"script: {len(s.chapters)} audio files, {sum(c.words for c in s.chapters)} words "
          f"({time.time() - t0:.0f}s)")
    return s


def _write_script(s, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "script.json").write_text(json.dumps(s.to_json(), indent=1, ensure_ascii=False), encoding="utf-8")
    (out_dir / "script.txt").write_text(s.text(), encoding="utf-8")


def cmd_setup(args):
    from . import mathspeech
    missing = [t for t in ("pandoc", "ffmpeg", "ffprobe", "node", "npm") if not shutil.which(t)]
    if missing:
        print("missing tools: " + ", ".join(missing) + " (install them with your package manager)")
    if not mathspeech.available():
        print("installing the maths speech engine (speech-rule-engine) ...")
        mathspeech.setup()
    print("maths speech engine: ok" if mathspeech.available() else "maths speech engine: NOT installed")
    print("fetching the voice model ...")
    from . import engines
    e = engines.get("kokoro", voice="am_michael")
    audio = e.synthesize("Ready.", {})
    print(f"voice model: ok ({len(audio) / e.sample_rate:.1f}s test)")
    import spacy  # noqa: F401  (misaki's English model is a dependency)
    return 0 if not missing else 1


def cmd_script(args):
    book = _book(args)
    s = _script(book, args)
    out = Path(args.out) if args.out else book.out_dir
    _write_script(s, out)
    print(f"written: {out / 'script.txt'} (read it: it is exactly what will be spoken)")
    return 0


def cmd_check(args):
    from . import check, engines
    book = _book(args)
    s = _script(book, args)
    name, kw = _engine(book, args)
    rep = check.run(s, book, engines.get(name, **kw))
    print(rep.text())
    return 1 if rep.failures else 0


def cmd_build(args):
    from . import check, engines, master, script as sc, synth, verify
    book = _book(args)
    out = Path(args.out) if args.out else book.out_dir
    s = _script(book, args)
    name, kw = _engine(book, args)
    if not args.no_check:
        rep = check.run(s, book, engines.get(name, **kw))
        print(rep.text())
        if rep.failures and not args.force:
            print("check failed: fix the book (or pass --force to build anyway)")
            return 1
    s = sc.select(s, args.chapters)
    if not s.chapters:
        print(f"no chapter matches {args.chapters!r}")
        return 1
    _write_script(s, out)
    print(f"voicing {len(s.chapters)} chapters with {name} {kw['voice']} ...")
    manifest = synth.voice(s, book, out, name, kw, workers=args.workers, threads=args.threads)
    print("mastering ...")
    report, m4b = master.master(book, manifest, out)
    ok = not any(r["problems"] for r in report)
    if not args.no_verify:
        print(f"verifying with whisper {args.whisper} ...")
        vok, _ = verify.verify(s, manifest, out, model=args.whisper, threads=args.threads or 8)
        ok = ok and vok
    print(("done: " if ok else "done WITH PROBLEMS: ") + str(out))
    return 0 if ok else 1


def cmd_verify(args):
    from . import script as sc, verify
    book = _book(args)
    out = Path(args.out) if args.out else book.out_dir
    data = json.loads((out / "script.json").read_text(encoding="utf-8"))
    chapters = [sc.Chapter(c["title"], c["level"], [sc.Segment(**x) for x in c["segments"]]) for c in data["chapters"]]
    s = sc.Script(chapters=chapters, inventory=[], maths=data["maths"])
    manifest = json.loads((out / "chapters.json").read_text(encoding="utf-8"))
    ok, _ = verify.verify(s, manifest, out, model=args.whisper, threads=args.threads or 8)
    return 0 if ok else 1


def cmd_names(args):
    """Every name that needs the author's ear, spoken one after another."""
    import collections
    import re

    import numpy as np
    import soundfile as sf
    from . import engines, lexicon as lex
    book = _book(args)
    s = _script(book, args)
    name, kw = _engine(book, args)
    engine = engines.get(name, **kw)
    book_lexicon, guessed = lex.load_entries(book.lexicon_path)
    counts = collections.Counter(w for ch in s.chapters for seg in ch.segments
                                 for w in re.findall(r"(?<![\d\w-])[A-Za-zÀ-ɏ'’-]+", seg.text))
    unknown = [w for w in engine.unknown_words(counts) if w[:1].isupper() and not w.isupper()]
    names = sorted(set(book_lexicon) | set(unknown), key=lambda w: (-counts.get(w, 0), w))
    out = (Path(args.out) if args.out else book.out_dir) / "names"
    out.mkdir(parents=True, exist_ok=True)
    sr = engine.sample_rate
    listing, audio, t = [], [], 0.0
    for w in names:
        pron = lex.pronunciations(w, book_lexicon)
        a = engine.synthesize(w + ".", pron)
        source = ("GUESS " if w in guessed else "") + ("lexicon /" + book_lexicon[w] + "/" if w in book_lexicon
                                                        else "voice's own guess")
        listing.append(f"{int(t // 60):02d}:{t % 60:05.2f}  {w:30} {counts.get(w, 0):5} uses  {source}")
        audio += [a, np.zeros(int(0.9 * sr), dtype=np.float32)]
        t += len(a) / sr + 0.9
    sf.write(out / "names.wav", np.concatenate(audio), sr)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(out / "names.wav"), "-b:a", "128k",
                    str(out / "names.mp3")], check=True)
    (out / "names.wav").unlink()
    (out / "names.txt").write_text("\n".join(listing) + "\n", encoding="utf-8")
    print(f"{len(names)} names ({len(unknown)} guessed, {len(book_lexicon)} from the lexicon): "
          f"{out / 'names.mp3'} with {out / 'names.txt'}")
    return 0


def cmd_voices(args):
    from .engines.kokoro import VOICES
    print("\n".join(VOICES))
    return 0


def main(argv=None):
    import warnings
    # Library notices from the voice model's dependencies, not the user's concern
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=UserWarning, module="torch")
    ap = argparse.ArgumentParser(prog="mdaudiobook", description="Markdown books to audiobooks.")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def book_cmd(name, help_):
        p = sub.add_parser(name, help=help_)
        p.add_argument("book", help="the book's Markdown file")
        p.add_argument("--voice", help="voice (default: audiobook.voice, else am_michael)")
        p.add_argument("--engine", help="voice engine (default: kokoro)")
        p.add_argument("--speed", type=float)
        p.add_argument("--out", help="output directory (default: <book>_audiobook beside the book)")
        return p

    sub.add_parser("setup", help="install the maths speech engine and fetch the voice model")
    book_cmd("script", "write the narration script (exactly what will be spoken)")
    book_cmd("check", "check that a listener gets everything a reader sees (no audio made)")
    b = book_cmd("build", "script, check, voice, master and verify")
    b.add_argument("--chapters", help='which audio files: "3", "2-5", "1,4", or words from a title')
    b.add_argument("--workers", type=int, default=1, help="chapters voiced in parallel")
    b.add_argument("--threads", type=int, help="CPU threads per worker")
    b.add_argument("--device", help="cpu (default) or cuda")
    b.add_argument("--whisper", default="base.en", help="transcription model for verify")
    b.add_argument("--no-check", action="store_true")
    b.add_argument("--no-verify", action="store_true")
    b.add_argument("--force", action="store_true", help="build even if the check fails")
    v = book_cmd("verify", "compare built audio with its script")
    v.add_argument("--whisper", default="base.en")
    v.add_argument("--threads", type=int)
    book_cmd("names", "speak every name the voice guesses or the lexicon gives, for review")
    sub.add_parser("voices", help="list the voices")

    args = ap.parse_args(argv)
    handler = {"setup": cmd_setup, "script": cmd_script, "check": cmd_check, "build": cmd_build,
               "verify": cmd_verify, "names": cmd_names, "voices": cmd_voices}[args.cmd]
    try:
        return handler(args)
    except KeyboardInterrupt:
        return 130
    except Exception as e:  # noqa: BLE001
        if os.environ.get("MDAUDIOBOOK_DEBUG"):
            raise
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
