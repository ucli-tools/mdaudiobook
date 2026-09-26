"""Synthesis: script -> one WAV per chapter.

Each sentence is voiced once and cached under a key made of the engine's
identity, the sentence and the pronunciations it uses, so editing a book
re-voices only the sentences that changed. Chapters are written to disk as
they are assembled (a long book never sits in memory) and several chapters
are voiced in parallel.
"""
import hashlib
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import soundfile as sf

from . import engines, lexicon as lex
from .text import sentences

SENTENCE_GAP = "sentence"


def _key(identity, sentence, pron):
    blob = json.dumps([identity, sentence, sorted(pron.items())], ensure_ascii=False)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


def _voice_chapter(job):
    """Worker: voice one chapter into its WAV. Returns (index, seconds, new, cached)."""
    (index, chapter, out_wav, cache_dir, engine_name, engine_kw, book_lexicon, pauses) = job
    engine = engines.get(engine_name, **engine_kw)
    sr = engine.sample_rate
    new = cached = 0
    frames = 0
    times = []          # where each sentence starts and ends in the chapter, in seconds
    tmp = Path(str(out_wav) + ".part")
    with sf.SoundFile(tmp, "w", samplerate=sr, channels=1, format="WAV", subtype="PCM_16") as out:
        for seg in chapter["segments"]:
            parts = sentences(seg["text"])
            for k, sentence in enumerate(parts):
                pron = lex.pronunciations(sentence, book_lexicon)
                key = _key(engine.identity, sentence, pron)
                path = Path(cache_dir) / key[:2] / f"{key}.flac"
                if path.exists():
                    audio, _ = sf.read(path, dtype="float32")
                    cached += 1
                else:
                    audio = engine.synthesize(sentence, pron)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    sf.write(str(path) + ".tmp.flac", audio, sr)
                    os.replace(str(path) + ".tmp.flac", path)
                    new += 1
                out.write(audio)
                gap = pauses[SENTENCE_GAP] if k < len(parts) - 1 else seg["pause"]
                silence = np.zeros(int(gap * sr), dtype=np.float32)
                out.write(silence)
                times.append([round(frames / sr, 3), round((frames + len(audio)) / sr, 3)])
                frames += len(audio) + len(silence)
    os.replace(tmp, out_wav)
    return index, sf.info(str(out_wav)).duration, new, cached, times


def voice(script, book, out_dir, engine_name, engine_kw, workers=1, threads=None, log=print):
    """Voice every chapter of `script` into out_dir/chapters/NN.wav."""
    out_dir = Path(out_dir)
    chapters_dir = out_dir / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = out_dir / "cache"
    book_lexicon = lex.load(book.lexicon_path)
    kw = dict(engine_kw)
    if threads:
        kw["threads"] = threads
    jobs = []
    for i, ch in enumerate(script.chapters, 1):
        data = {"title": ch.title, "segments": [{"text": s.text, "pause": s.pause} for s in ch.segments]}
        jobs.append((i, data, chapters_dir / f"{i:02d}.wav", str(cache_dir), engine_name, kw, book_lexicon,
                     book.settings["pauses"]))
    results, seg_times = {}, {}
    t0 = time.time()
    if workers <= 1:
        for job in jobs:
            i, secs, new, cached, times = _voice_chapter(job)
            results[i] = secs
            seg_times[i] = times
            log(f"  {i:02d}/{len(jobs)} {script.chapters[i - 1].title[:50]:50} {secs / 60:5.1f} min "
                f"({new} new, {cached} cached sentences)")
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_voice_chapter, job) for job in jobs]
            for f in as_completed(futures):
                i, secs, new, cached, times = f.result()
                results[i] = secs
                seg_times[i] = times
                log(f"  {i:02d}/{len(jobs)} {script.chapters[i - 1].title[:50]:50} {secs / 60:5.1f} min "
                    f"({new} new, {cached} cached sentences)")
    total = sum(results.values())
    log(f"voiced {len(jobs)} chapters, {total / 3600:.2f} h of audio in {(time.time() - t0) / 60:.1f} min")
    manifest = [{"index": i, "title": ch.title, "wav": f"chapters/{i:02d}.wav", "seconds": results[i],
                 "sentences": seg_times[i]}
                for i, ch in enumerate(script.chapters, 1)]
    (out_dir / "chapters.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    return manifest
