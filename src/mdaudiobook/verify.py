"""Verify: does the audio say what the script says?

Each chapter is checked in windows of whole sentences, cut from the audio at
the times synthesis recorded and never longer than Whisper's own 30-second
window: over longer audio it drifts, repeats itself and skips, and would
report as missing what was said. Every problem comes with its time and text. Single-word differences are mostly the transcriber's (spelling
variants, homophones); what matters is a run of script words missing from
the audio (a dropped sentence) or a run of heard words not in the script (a
repeated or garbled stretch). Either fails the check.
"""
import json
import re
from pathlib import Path

import jiwer
from num2words import num2words

from .text import sentences

DROP_RUN = 4          # consecutive script words missing from the audio
INSERT_RUN = 6        # consecutive heard words not in the script
MAX_WER = 0.15
MIN_WORDS_FOR_WER = 150   # below this, a few misheard names swing the rate


def _number(m):
    s = m.group(0).replace(",", "")
    try:
        if "." in s:
            whole, frac = s.split(".", 1)
            return num2words(int(whole or 0)) + " point " + " ".join(num2words(int(d)) for d in frac)
        return num2words(int(s))
    except (ValueError, OverflowError):
        return s


def _letters(m):
    """Roman numerals and short initialisms are spoken letter by letter; a
    longer capital word is a word (the transcriber sometimes writes one)."""
    run = m.group(0)
    if set(run) <= set("IVXLCDM") or len(run) <= 4:
        return " ".join(run)
    return run


def normalize(text):
    text = text.replace("\ue010", "").replace("\ue011", "")
    # Capital runs (Roman numerals, initials) are spoken letter by letter and
    # transcribed either way ("MDCLXV" or "M D C L X V"): compare letters
    text = re.sub(r"\b[A-Z]{2,}\b", _letters, text)
    text = text.lower().replace("\u2019", "'").replace("\u2018", "'")
    # Letters spoken by name come back as words ("I I I" heard "aye aye aye");
    # mapped the same way on both sides, a real word still matches itself
    text = re.sub(r"\b(aye|eye)\b", "i", text)
    text = re.sub(r"\b(ex)\b", "x", text)
    text = re.sub(r"\b(vee)\b", "v", text)
    text = re.sub(r"\d[\d,]*(?:\.\d+)?", _number, text)
    text = re.sub(r"[-\u2013\u2014]", " ", text)
    text = re.sub(r"[^a-z0-9' ]+", " ", text)
    text = re.sub(r"'s\b", "s", text)
    return re.sub(r"\s+", " ", text).strip()


def compare(script_text, heard_text):
    ref, hyp = normalize(script_text), normalize(heard_text)
    if not ref:
        return {"wer": 0.0, "dropped": [], "inserted": [], "words": 0, "errors": 0}
    if not hyp:
        return {"wer": 1.0, "dropped": [ref] if len(ref.split()) >= DROP_RUN else [], "inserted": [],
                "words": len(ref.split()), "errors": len(ref.split())}
    out = jiwer.process_words(ref, hyp)
    r, h = ref.split(), hyp.split()
    dropped, inserted = [], []
    for a in out.alignments[0]:
        span_r = r[a.ref_start_idx:a.ref_end_idx]
        span_h = h[a.hyp_start_idx:a.hyp_end_idx]
        if a.type == "delete" and len(span_r) >= DROP_RUN:
            dropped.append(" ".join(span_r))
        elif a.type == "substitute" and len(span_r) >= DROP_RUN and len(span_h) < len(span_r) / 2:
            dropped.append(" ".join(span_r))
        elif a.type == "insert" and len(span_h) >= INSERT_RUN:
            inserted.append(" ".join(span_h))
    errors = out.substitutions + out.deletions + out.insertions
    return {"wer": out.wer, "dropped": dropped, "inserted": inserted, "words": len(r), "errors": errors}


WINDOW = 15.0        # a window closes once it holds this many seconds of speech
MAX_WINDOW = 28.0    # and never grows past Whisper's 30-second window
HEAD = 0.75          # silence mastering adds before each chapter (master.HEAD)


def _audio16k(path):
    import subprocess
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def _windows(times, texts):
    """Consecutive sentences grouped into windows of WINDOW to MAX_WINDOW seconds."""
    out, start, end, group = [], None, None, []
    for (s, e), text in zip(times, texts):
        if group and e - start > MAX_WINDOW:
            out.append((start, end, " ".join(group)))
            start, group = None, []
        start = s if start is None else start
        end = e
        group.append(text)
        if end - start >= WINDOW:
            out.append((start, end, " ".join(group)))
            start, group = None, []
    if group:
        out.append((start, end, " ".join(group)))
    return out


def _clock(t):
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


def verify(script, manifest, out_dir, model="base.en", threads=8, log=print):
    from faster_whisper import WhisperModel
    whisper = WhisperModel(model, device="cpu", compute_type="int8", cpu_threads=threads)
    out_dir = Path(out_dir)
    results, failed = [], 0
    for item, chapter in zip(manifest, script.chapters):
        levelled = out_dir / "levelled" / f"{item['index']:02d}.wav"
        path, offset = (levelled, HEAD) if levelled.exists() else (out_dir / item["wav"], 0.0)
        audio = _audio16k(path)
        times = item.get("sentences")
        texts = [t for seg in chapter.segments for t in sentences(seg.text)]
        if not times or len(times) != len(texts):
            raise RuntimeError(f"{item['title']}: no sentence times for this build; build it again")
        windows = _windows(times, texts)
        words = errors = 0
        problems = []
        for start, end, text in windows:
            a, b = int((start + offset) * 16000), int((end + offset) * 16000)
            segs, _ = whisper.transcribe(audio[a:b], beam_size=5, language="en", vad_filter=False,
                                         condition_on_previous_text=False)
            r = compare(text, " ".join(s.text for s in segs))
            words += r["words"]
            errors += r["errors"]
            problems += [(start, "missing from the audio", d) for d in r["dropped"]]
            problems += [(start, "heard but not in the script", d) for d in r["inserted"]]
        wer = errors / words if words else 0.0
        bad = bool(problems or (words >= MIN_WORDS_FOR_WER and wer > MAX_WER))
        failed += bad
        results.append({"index": item["index"], "title": item["title"], "words": words, "wer": wer,
                        "problems": [{"at": _clock(t), "kind": k, "text": d} for t, k, d in problems]})
        log(f"  {'FAIL' if bad else 'ok  '} {item['index']:02d} {item['title'][:50]:50} {words:6} words, "
            f"differences {wer:.1%}")
        for t, kind, d in problems:
            log(f"         {_clock(t)} {kind}: {d[:100]!r}")
    (out_dir / "verify.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    return failed == 0, results
