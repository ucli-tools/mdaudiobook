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

from .latex import prepare_math

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


def to_mathml(items):
    """[(tex, display)] -> [MathML or None]: one pandoc call for the batch.

    Each expression is its own paragraph, so one that pandoc cannot render
    comes back as text and is reported as None instead of shifting the rest.
    """
    if not items:
        return []
    md = "\n\n".join(("$$%s$$" if display else "$%s$") % prepare_math(tex) for tex, display in items)
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


def _polish(said):
    said = said.replace("\u0302", " hat")
    said = re.sub(r"\s+hat", " hat", said)
    said = re.sub(r"\balmost equals\b", "is approximately", said)
    said = re.sub(r"\s*dot dot dot\b", " and so on", said)
    # "x to the n-th power" reads better as "x to the power n"
    said = re.sub(r"\bto the (\w+)-th power\b", r"to the power \1", said)
    said = re.sub(r"\b([A-Za-z])-th\b", r"\1th", said)
    return re.sub(r"\s+", " ", said).strip()


def speak(items, style="clearspeak"):
    """[(tex, display)] -> [spoken text or None where it cannot be spoken]."""
    if not items:
        return []
    if not available():
        raise MathSpeechUnavailable("the maths speech engine is not installed: run `mdaudiobook setup`")
    mathml = to_mathml(items)
    js = resources.files("mdaudiobook").joinpath("js/sre_batch.js")
    env = dict(os.environ, NODE_PATH=str(node_dir() / "node_modules"))
    with resources.as_file(js) as script:
        res = subprocess.run(["node", str(script)], input=json.dumps({"style": style, "items": mathml}),
                             capture_output=True, text=True, env=env)
    if res.returncode != 0:
        raise RuntimeError("speech-rule-engine failed: " + res.stderr[-500:])
    return [_polish(s) if s and s.strip() else None for s in json.loads(res.stdout)]
