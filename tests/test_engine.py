"""Kokoro end to end on one sentence (skipped when the voice model is absent)."""
import pytest

kokoro = pytest.importorskip("kokoro")

from mdaudiobook import engines  # noqa: E402


@pytest.fixture(scope="module")
def engine():
    try:
        e = engines.get("kokoro", voice="am_michael", threads=4)
        e.synthesize("Ready.", {})
    except Exception as exc:  # noqa: BLE001  (offline, no model)
        pytest.skip(f"voice model unavailable: {exc}")
    return e


def test_sentence_becomes_audio(engine):
    audio = engine.synthesize("The circle returns into itself.", {})
    assert audio.dtype.name == "float32" and 0.8 < len(audio) / engine.sample_rate < 6


def test_pronunciation_is_applied_and_validated(engine):
    plain = engine.synthesize("Hegel.", {})
    given = engine.synthesize("Hegel.", {"Hegel": "ˈheɪɡəl"})
    assert len(plain) and len(given)
    with pytest.raises(engines.EngineError):
        engine.synthesize("Hegel.", {"Hegel": "ʘʘʘ"})


def test_unknown_words(engine):
    assert "Zqwxbrin" in engine.unknown_words(["Zqwxbrin", "circle"])
    assert "circle" not in engine.unknown_words(["circle"])
