"""Mathematics read aloud: pandoc renders TeX to MathML, the Speech Rule
Engine (the engine screen readers use) speaks it in ClearSpeak style.

The engine is a Node package installed once by `mdaudiobook setup` into the
user's data directory, so the Python package stays free of Node.
"""
import json
import os
import re
import shutil
import subprocess
from importlib import resources
from pathlib import Path

from .latex import prepare_math, trailing_punctuation

SRE_VERSION = "4"


def node_dir():
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(os.environ.get("MDAUDIOBOOK_NODE_DIR", Path(base) / "mdaudiobook" / "node"))


class MathSpeechUnavailable(RuntimeError):
    pass


def available():
    return shutil.which("node") is not None and (node_dir() / "node_modules" / "speech-rule-engine").is_dir()


def setup():
    if not shutil.which("npm"):
        raise MathSpeechUnavailable("npm (Node.js) is needed for mathematics; install Node.js first")
    target = node_dir()
    target.mkdir(parents=True, exist_ok=True)
    subprocess.run(["npm", "install", "--silent", "--prefix", str(target), f"speech-rule-engine@{SRE_VERSION}"],
                   check=True)


def prepare(tex):
    """TeX -> (what pandoc renders, the sentence punctuation taken off its end)."""
    return trailing_punctuation(prepare_math(tex))


# An expression with nothing in it but space and braces: an empty equation
# array, a number (\tag) with no equation. There is nothing to say.
_NOTHING = re.compile(r"(\s|[{}]|\\[,;:! ]|\\q?quad\b|~)*")


def to_mathml(items):
    """[(tex, display)] -> [MathML or None]: one pandoc call for the batch.

    Each expression is its own paragraph, so one that pandoc cannot render
    comes back as text and is reported as None instead of shifting the rest.
    """
    if not items:
        return []
    md = "\n\n".join(("$$%s$$" if display else "$%s$") % prepare(tex)[0] for tex, display in items)
    html = subprocess.run(["pandoc", "-f", "markdown", "-t", "html", "--mathml"], input=md,
                          capture_output=True, text=True, check=True).stdout
    paras = re.findall(r"<p>(.*?)</p>", html, re.S)
    if len(paras) != len(items):
        raise RuntimeError(f"pandoc returned {len(paras)} paragraphs for {len(items)} expressions")
    out = []
    for p in paras:
        m = re.search(r"<math.*?</math>", p, re.S)
        out.append(m.group(0) if m else None)
    return out


def _polish(said, tex=""):
    """The engine's reading of an expression, as a narrator says it. `tex` is
    the expression: a word it holds itself (\\text{period}) is not taken for
    the engine's name of a punctuation mark."""
    said = said.replace("\u0302", " hat")
    said = re.sub(r"\s+hat", " hat", said)
    said = re.sub(r"\balmost equals\b", "is approximately", said)
    said = re.sub(r"\s*dot dot dot\b", " and so on", said)
    # "x to the n-th power" reads better as "x to the power n"
    said = re.sub(r"\bto the (\w+)-th power\b", r"to the power \1", said)
    said = re.sub(r"\b([A-Za-z])-th\b", r"\1th", said)
    # Punctuation is read out as a word ("f of x comma y"): it is punctuation
    # the voice pauses on. (The book's own sentence punctuation at the end of
    # an expression never reaches the engine: speak() puts it back after.)
    if "period" not in tex.lower():
        said = re.sub(r"\s*\bperiod period period\b", " and so on", said)
        said = re.sub(r"\s*\bperiod\b", ".", said)
    if "comma" not in tex.lower():
        said = re.sub(r"\s*\bcomma\b", ",", said)
    # An equation set out in lines is announced "2 lines Line 1: ... Line 2:
    # ...": a listener needs only a pause between the lines, and a cell left
    # empty to line them up is not "blank". (One line is not a table at all:
    # latex.prepare_math unwraps it.)
    said = re.sub(r"\b\d+ lines? Line 1:(\s*blank\b)?", "", said)
    said = re.sub(r"\s*\bLine \d+:(\s*blank\b)?", ";", said)
    said = re.sub(r"([,.;:])(\s*[,;])+", r"\1", said)     # a line ending in its own mark keeps it
    said = re.sub(r"^[\s;]+|[\s;]+$", "", said)
    # A single letter in mathematics is a letter, not a word: "e" is not read
    # like the article "a", "a" not like "uh", "i" not like "I"
    said = re.sub(r"(?<![\w'\u2019])([A-Za-z])(?![\w'\u2019])", "\ue010\\1\ue011", said)
    return re.sub(r"\s+", " ", said).strip()


def speak(items, style="clearspeak"):
    """[(tex, display)] -> [spoken text, "" where there is nothing to say, or
    None where it cannot be spoken]."""
    if not items:
        return []
    if not available():
        raise MathSpeechUnavailable("the maths speech engine is not installed: run `mdaudiobook setup`")
    prepared = [prepare(tex) for tex, _ in items]
    loud = [i for i, (tex, _) in enumerate(prepared) if not _NOTHING.fullmatch(tex)]
    mathml = to_mathml([items[i] for i in loud])
    js = resources.files("mdaudiobook").joinpath("js/sre_batch.js")
    env = dict(os.environ, NODE_PATH=str(node_dir() / "node_modules"))
    with resources.as_file(js) as script:
        res = subprocess.run(["node", str(script)], input=json.dumps({"style": style, "items": mathml}),
                             capture_output=True, text=True, env=env)
    if res.returncode != 0:
        raise RuntimeError("speech-rule-engine failed: " + res.stderr[-500:])
    out = [""] * len(items)
    for i, said in zip(loud, json.loads(res.stdout)):
        tex, mark = prepared[i]
        out[i] = _polish(said, tex) + mark if said and said.strip() else None
    return out
