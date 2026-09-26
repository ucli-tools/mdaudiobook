import shutil
import subprocess
import types

import numpy as np
import pytest
import soundfile as sf

from mdaudiobook import master
from mdaudiobook.verify import compare, normalize


def test_numbers_are_compared_as_words():
    assert normalize("It is 2.5 or 23, isn't it?") == "it is two point five or twenty three isn't it"
    assert compare("zero equals 0 and one equals 1", "0 equals zero and 1 equals one")["wer"] == 0


def test_a_dropped_sentence_is_found():
    script = "The first sentence is here. The kettle boiled over twice. The last one follows."
    heard = "The first sentence is here. The last one follows."
    r = compare(script, heard)
    # Where a repeated word ("the") sits at the edge of the gap is the aligner's choice
    assert len(r["dropped"]) == 1 and "kettle boiled over twice" in r["dropped"][0]


def test_single_misheard_words_are_not_drops():
    r = compare("An example for mdaudiobook, written by Jane Doe.", "An example for M. Daudio book, written by Jane Doe.")
    assert r["dropped"] == [] and r["inserted"] == []


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_mastering_meets_store_specs(tmp_path):
    sr = 24000
    t = np.arange(int(sr * 6)) / sr
    speechlike = 0.3 * np.sin(2 * np.pi * 180 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)) ** 2
    speechlike[int(sr * 2):int(sr * 2.5)] = 0
    (tmp_path / "chapters").mkdir()
    sf.write(tmp_path / "chapters" / "01.wav", speechlike.astype(np.float32), sr)
    book = types.SimpleNamespace(title="T", author="A", narrator="N", meta={}, stem="t",
                                 cover_path=lambda: None)
    manifest = [{"index": 1, "title": "One", "wav": "chapters/01.wav", "seconds": 6.0}]
    report, m4b = master.master(book, manifest, tmp_path, log=lambda *a: None)
    assert report[0]["problems"] == [], report
    chapters = subprocess.run(["ffprobe", "-v", "error", "-show_chapters", "-of", "csv=p=0", str(m4b)],
                              capture_output=True, text=True).stdout
    assert "One" in chapters
