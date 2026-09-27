"""Kokoro-82M: an open neural voice (Apache-2.0) that runs on a CPU.

Voices are named <language><gender>_<name>: "am_michael" is American English,
male; "bf_emma" British English, female. Pronunciations are passed inline as
Kokoro's [word](/phonemes/) markup after converting IPA to its phoneme set.
Words its dictionary lacks fall back to espeak-ng; `unknown_words` lists
them so a book can put the ones that matter in its lexicon.
"""
import os
import re

import numpy as np

from .base import L_CLOSE, L_OPEN, LETTER_IPA, Engine, EngineError

VOICES = ["am_michael", "am_fenrir", "am_puck", "am_echo", "am_eric", "am_liam", "am_onyx", "am_adam",
          "af_heart", "af_bella", "af_nicole", "af_aoede", "af_kore", "af_sarah", "af_nova", "af_sky",
          "af_alloy", "af_jessica", "af_river", "bm_george", "bm_fable", "bm_lewis", "bm_daniel",
          "bf_emma", "bf_isabella", "bf_alice", "bf_lily"]

# IPA -> Kokoro (misaki) phonemes: diphthongs are single letters there
_IPA = [("eɪ", "A"), ("aɪ", "I"), ("oʊ", "O"), ("əʊ", "Q"), ("aʊ", "W"), ("ɔɪ", "Y"), ("dʒ", "ʤ"), ("tʃ", "ʧ"),
        ("ɝ", "ɜɹ"), ("ɚ", "əɹ"), ("r", "ɹ"), ("g", "ɡ"), ("ɫ", "l"), ("ʍ", "w"), ("ɐ", "ə"), ("ˑ", ""),
        ("ː", ""), (".", ""), ("‿", "")]


def ipa_to_kokoro(ipa):
    out = ipa.replace("'", "ˈ").replace(",", "ˌ")
    for a, b in _IPA:
        out = out.replace(a, b)
    return out


class KokoroEngine(Engine):
    name = "kokoro"
    sample_rate = 24000

    def __init__(self, voice="am_michael", speed=1.0, device="cpu", threads=None, **options):
        super().__init__(voice, speed, **options)
        if voice not in VOICES and not os.path.exists(voice):
            raise EngineError(f"unknown Kokoro voice {voice!r}; try one of: {', '.join(VOICES)}")
        self.device = device
        self.threads = threads
        self._pipe = None
        self._g2p = None

    @property
    def identity(self):
        return f"kokoro-82m:{self.voice}:{self.speed}"

    def _pipeline(self):
        if self._pipe is None:
            import torch
            if self.threads:
                torch.set_num_threads(int(self.threads))
            from kokoro import KPipeline
            self._pipe = KPipeline(lang_code=os.path.basename(self.voice)[0], repo_id="hexgrad/Kokoro-82M",
                                   device=self.device)
            self._vocab = set(self._pipe.model.vocab) if getattr(self._pipe, "model", None) else set()
        return self._pipe

    def phonemes(self, ipa):
        ph = ipa_to_kokoro(ipa)
        self._pipeline()
        bad = sorted({c for c in ph if self._vocab and c not in self._vocab and not c.isspace()})
        if bad:
            raise EngineError(f"IPA {ipa!r} has sounds Kokoro cannot make: {' '.join(bad)}")
        return ph

    def synthesize(self, sentence, pronunciations):
        pipe = self._pipeline()
        text = re.sub(f"{L_OPEN}([A-Za-z]){L_CLOSE}",
                      lambda m: f"[{m.group(1)}](/{self.phonemes(LETTER_IPA[m.group(1).lower()])}/)", sentence)
        # Longest words first, so "Leibnizian" is not cut by "Leibniz"
        for word in sorted(pronunciations, key=len, reverse=True):
            ph = self.phonemes(pronunciations[word])
            text = re.sub(r"(?<![\w\[])%s(?![\w\]])" % re.escape(word), f"[{word}](/{ph}/)", text)
        chunks = []
        for result in pipe(text, voice=self.voice, speed=self.speed, split_pattern=None):
            if result.audio is not None:
                chunks.append(result.audio.numpy() if hasattr(result.audio, "numpy") else np.asarray(result.audio))
        if not chunks:
            raise EngineError(f"no audio for: {sentence[:80]!r}")
        return np.concatenate(chunks).astype(np.float32)

    def unknown_words(self, words):
        if self._g2p is None:
            from misaki import en
            self._g2p = en.G2P(trf=False, british=os.path.basename(self.voice)[0] == "b", fallback=None)
        unknown = set()
        words = list(words)
        for i in range(0, len(words), 400):
            _, tokens = self._g2p(" , ".join(words[i:i + 400]))
            for tk in tokens:
                if tk.phonemes in (None, "", "❓") and re.search(r"[A-Za-z]", tk.text):
                    unknown.add(tk.text)
        return unknown

    def voices(self):
        return VOICES
