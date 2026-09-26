"""Verify: does the audio say what the script says?

Whisper transcribes each chapter; the transcript is aligned with the
chapter's script. Single-word differences are mostly the transcriber's
(spelling variants, homophones); what matters is a run of script words that
is missing from the audio (a dropped sentence) or a run of heard words that
is not in the script (a repeated or garbled stretch). Either fails the check.
"""
import json
import re
from pathlib import Path

import jiwer
from num2words import num2words

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
    # Capital runs (Roman numerals, initials) are spoken letter by letter and
    # transcribed either way ("MDCLXV" or "M D C L X V"): compare letters
    text = re.sub(r"\b[A-Z]{2,}\b", _letters, text)
    text = text.lower().replace("\u2019", "'").replace("\u2018", "'")
    text = re.sub(r"\d[\d,]*(?:\.\d+)?", _number, text)
    text = re.sub(r"[-\u2013\u2014]", " ", text)
    text = re.sub(r"[^a-z0-9' ]+", " ", text)
    text = re.sub(r"'s\b", "s", text)
    return re.sub(r"\s+", " ", text).strip()


def compare(script_text, heard_text):
    ref, hyp = normalize(script_text), normalize(heard_text)
    if not ref:
        return {"wer": 0.0, "dropped": [], "inserted": [], "words": 0}
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
    return {"wer": out.wer, "dropped": dropped, "inserted": inserted, "words": len(r)}


def verify(script, manifest, out_dir, model="base.en", threads=8, log=print):
    from faster_whisper import WhisperModel
    whisper = WhisperModel(model, device="cpu", compute_type="int8", cpu_threads=threads)
    out_dir = Path(out_dir)
    results, failed = [], 0
    for item, chapter in zip(manifest, script.chapters):
        audio = out_dir / "levelled" / f"{item['index']:02d}.wav"
        if not audio.exists():
            audio = out_dir / item["wav"]
        segs, _ = whisper.transcribe(str(audio), beam_size=5, vad_filter=False, condition_on_previous_text=False)
        heard = " ".join(s.text for s in segs)
        said = " ".join(s.text for s in chapter.segments)
        r = compare(said, heard)
        bad = bool(r["dropped"] or r["inserted"] or (r["words"] >= MIN_WORDS_FOR_WER and r["wer"] > MAX_WER))
        failed += bad
        results.append({"index": item["index"], "title": item["title"], **r})
        log(f"  {'FAIL' if bad else 'ok  '} {item['index']:02d} {item['title'][:50]:50} {r['words']:6} words, "
            f"differences {r['wer']:.1%}")
        for d in r["dropped"]:
            log(f"         missing from the audio: {d[:110]!r}")
        for d in r["inserted"]:
            log(f"         heard but not in the script: {d[:110]!r}")
    (out_dir / "verify.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    return failed == 0, results
