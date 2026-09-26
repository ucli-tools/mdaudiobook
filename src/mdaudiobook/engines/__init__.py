"""Voice engines. An engine turns one sentence, with the pronunciations it
needs, into audio. Everything else (script, cache, mastering, checks) is
shared, so moving a finished book to another engine is a setting.

To add an engine: subclass Engine in a module here and register it in
ENGINES. Its `identity` must change whenever its output would, because the
sentence cache is keyed on it.
"""
from .base import Engine, EngineError

ENGINES = {}


def get(name, **kw):
    if not ENGINES:
        from .kokoro import KokoroEngine
        ENGINES["kokoro"] = KokoroEngine
    if name not in ENGINES:
        raise EngineError(f"unknown engine {name!r}; available: {', '.join(sorted(ENGINES))}")
    return ENGINES[name](**kw)


__all__ = ["Engine", "EngineError", "get", "ENGINES"]
