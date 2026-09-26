"""The engine interface."""


class EngineError(RuntimeError):
    pass


class Engine:
    name = "base"
    sample_rate = 24000

    def __init__(self, voice, speed=1.0, **options):
        self.voice = voice
        self.speed = speed
        self.options = options

    @property
    def identity(self):
        """Everything that changes the sound, for the sentence cache key."""
        return f"{self.name}:{self.voice}:{self.speed}"

    def synthesize(self, sentence, pronunciations):
        """One sentence -> mono float32 numpy array at self.sample_rate.

        `pronunciations` is {word: IPA} for the words in this sentence that
        need a given pronunciation. Must raise EngineError rather than
        return partial or empty audio.
        """
        raise NotImplementedError

    def unknown_words(self, words):
        """Which of `words` the engine would have to guess. Default: none."""
        return set()

    def voices(self):
        return []
