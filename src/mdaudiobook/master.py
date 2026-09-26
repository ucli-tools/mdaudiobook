"""Mastering: chapter WAVs -> store-ready files, measured against store specs.

Audiobook stores (ACX/Audible's rules are the strictest and the others
accept them) ask for: MP3 at 192 kbps CBR, 44.1 kHz; one file per chapter,
none over 120 minutes; overall RMS between -23 and -18 dB; peaks no higher
than -3 dB; a noise floor no higher than -60 dB; 0.5 to 1 s of silence at the
head and 1 to 5 s at the tail. Each chapter is levelled to an RMS of -20 dB
under a -5.5 dB peak limit, padded, encoded, then measured again as encoded.
The whole book also goes into one M4B with chapter marks and the cover.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

SPEC = {"rms_min": -23.0, "rms_max": -18.0, "peak_max": -3.0, "floor_max": -60.0, "file_max_min": 120.0}
TARGET_RMS = -20.0
LIMIT = 10 ** (-5.5 / 20)   # -5.5 dB sample peak before encoding
HEAD, TAIL = 0.75, 2.5


def _ffmpeg(*args):
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-y", *args], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError("ffmpeg failed: " + res.stderr[-800:])
    return res.stderr


def measure(path):
    """RMS, peak and noise floor (dB), and length (s) of an audio file."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path), "-af", "astats=measure_overall="
                          "RMS_level+Peak_level+Noise_floor:measure_perchannel=none", "-f", "null", "-"],
                         capture_output=True, text=True).stderr

    def val(name):
        m = re.findall(rf"{name}:\s*(-?[\d.]+|-inf)", err)
        return float(m[-1]) if m else None
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(path)], capture_output=True, text=True).stdout.strip()
    return {"rms": val("RMS level dB"), "peak": val("Peak level dB"), "floor": val("Noise floor dB"),
            "seconds": float(dur or 0)}


def within_spec(m):
    problems = []
    if m["rms"] is None or not (SPEC["rms_min"] <= m["rms"] <= SPEC["rms_max"]):
        problems.append(f"RMS {m['rms']} dB outside {SPEC['rms_min']}..{SPEC['rms_max']}")
    if m["peak"] is not None and m["peak"] > SPEC["peak_max"]:
        problems.append(f"peak {m['peak']} dB above {SPEC['peak_max']}")
    if m["floor"] is not None and m["floor"] > SPEC["floor_max"]:
        problems.append(f"noise floor {m['floor']} dB above {SPEC['floor_max']}")
    if m["seconds"] > SPEC["file_max_min"] * 60:
        problems.append(f"{m['seconds'] / 60:.0f} min, over {SPEC['file_max_min']:.0f}")
    return problems


def square_cover(src, dst, size=2400):
    """A square cover: the centre of `src`, at most `size` pixels (never enlarged)."""
    _ffmpeg("-i", str(src), "-vf", f"crop='min(iw,ih)':'min(iw,ih)',scale='min({size},iw)':-2", "-q:v", "2",
            str(dst))
    w = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width",
                        "-of", "csv=p=0", str(dst)], capture_output=True, text=True).stdout.strip()
    return int(w or 0)


def _level(wav, out_wav):
    """Level a chapter to TARGET_RMS under a peak limit, pad head and tail, 44.1 kHz mono.

    The limiter and the silent head and tail lower the level of the result,
    most in a short file, so it is measured and the gain corrected once."""
    rms = measure(wav)["rms"]
    gain = TARGET_RMS - (rms if rms not in (None, float("-inf")) else TARGET_RMS)
    for _ in range(2):
        # The limiter runs at the final rate and leaves room for the MP3
        # encoder, which overshoots sample peaks by up to about 1.5 dB
        _ffmpeg("-i", str(wav), "-af",
                f"volume={gain:.2f}dB,aresample=44100,alimiter=limit={LIMIT:.3f}:level=false:attack=5:release=50,"
                f"adelay={int(HEAD * 1000)}:all=1,apad=pad_dur={TAIL}",
                "-ac", "1", "-c:a", "pcm_s16le", str(out_wav))
        got = measure(out_wav)["rms"]
        if got is None or abs(got - TARGET_RMS) < 0.5:
            break
        gain += TARGET_RMS - got


def _tags(book, title, track=None, total=None):
    t = ["-metadata", f"title={title}", "-metadata", f"album={book.title}", "-metadata", f"artist={book.author}",
         "-metadata", f"album_artist={book.author}", "-metadata", "genre=Audiobook",
         "-metadata", f"composer={book.narrator}"]
    if book.meta.get("date"):
        t += ["-metadata", f"date={str(book.meta['date'])[:4]}"]
    if track:
        t += ["-metadata", f"track={track}/{total}"]
    return t


def master(book, manifest, out_dir, log=print):
    out_dir = Path(out_dir)
    lev = out_dir / "levelled"
    mp3 = out_dir / "mp3"
    for d in (lev, mp3):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
    cover = None
    src = book.cover_path()
    if src and src.exists():
        cover = out_dir / "cover_square.jpg"
        side = square_cover(src, cover)
        if side < 2400:
            log(f"  note: the square cover is {side}px; stores ask for at least 2400")
    else:
        log("  note: no cover image (metadata cover_image or audiobook.cover)")

    report = []
    total = len(manifest)
    for item in manifest:
        i = item["index"]
        wav = out_dir / item["wav"]
        lw = lev / f"{i:02d}.wav"
        _level(wav, lw)
        safe = re.sub(r"[^\w\s.-]", "", item["title"]).strip()[:60] or f"Chapter {i}"
        target = mp3 / f"{i:02d} - {safe}.mp3"
        args = ["-i", str(lw)]
        if cover:
            args += ["-i", str(cover), "-map", "0:a", "-map", "1:v", "-c:v", "mjpeg", "-disposition:v",
                     "attached_pic", "-metadata:s:v", "title=Album cover", "-metadata:s:v", "comment=Cover (front)"]
        args += ["-c:a", "libmp3lame", "-b:a", "192k", "-ar", "44100", "-ac", "1", "-id3v2_version", "3",
                 *_tags(book, item["title"], i, total), str(target)]
        _ffmpeg(*args)
        m = measure(target)
        problems = within_spec(m)
        report.append({"index": i, "title": item["title"], "file": target.name, **m, "problems": problems})
        flag = "ok  " if not problems else "FAIL"
        log(f"  {flag} {target.name[:60]:60} {m['seconds'] / 60:5.1f} min  RMS {m['rms']:.1f}  "
            f"peak {m['peak']:.1f}  floor {m['floor']}" + (f"  <- {'; '.join(problems)}" if problems else ""))

    # One M4B: all chapters, chapter marks, cover, tags
    listing = out_dir / "concat.txt"
    names = [(lev / ("%02d.wav" % it["index"])).as_posix() for it in manifest]
    listing.write_text("".join(f"file '{n}'\n" for n in names))
    meta = [";FFMETADATA1", f"title={book.title}", f"artist={book.author}", f"album={book.title}",
            "genre=Audiobook", f"composer={book.narrator}"]
    start = 0.0
    for it in manifest:
        secs = measure(lev / f"{it['index']:02d}.wav")["seconds"]
        meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(start * 1000)}",
                 f"END={int((start + secs) * 1000)}", "title=" + it["title"].replace("=", "\\=")]
        start += secs
    (out_dir / "chapters.ffmeta").write_text("\n".join(meta) + "\n", encoding="utf-8")
    m4b = out_dir / f"{book.stem}.m4b"
    args = ["-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(out_dir / "chapters.ffmeta")]
    if cover:
        args += ["-i", str(cover), "-map", "0:a", "-map", "2:v", "-c:v", "mjpeg", "-disposition:v", "attached_pic"]
    else:
        args += ["-map", "0:a"]
    args += ["-map_metadata", "1", "-map_chapters", "1", "-c:a", "aac", "-b:a", "96k", "-ac", "1",
             "-movflags", "+faststart", "-f", "mp4", str(m4b)]
    _ffmpeg(*args)
    listing.unlink()
    log(f"  {m4b.name}: {start / 3600:.2f} h, {len(manifest)} chapters")
    (out_dir / "master.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    return report, m4b
