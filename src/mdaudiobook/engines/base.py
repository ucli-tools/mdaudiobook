"""The engine interface."""

L_OPEN, L_CLOSE = "\ue010", "\ue011"   # a letter in mathematics, spoken by its name

# Letter names in IPA, for engines that take pronunciations
LETTER_IPA = {"a": "ˈeɪ", "b": "ˈbi", "c": "ˈsi", "d": "ˈdi", "e": "ˈi", "f": "ˈɛf", "g": "ˈdʒi", "h": "ˈeɪtʃ",
              "i": "ˈaɪ", "j": "ˈdʒeɪ", "k": "ˈkeɪ", "l": "ˈɛl", "m": "ˈɛm", "n": "ˈɛn", "o": "ˈoʊ", "p": "ˈpi",
              "q": "ˈkju", "r": "ˈɑɹ", "s": "ˈɛs", "t": "ˈti", "u": "ˈju", "v": "ˈvi", "w": "ˈdʌbəlju",
              "x": "ˈɛks", "y": "ˈwaɪ", "z": "ˈzi"}


def plain_letters(text):
    """The sentence with letter markers removed (an engine without phonemes)."""
    return text.replace(L_OPEN, "").replace(L_CLOSE, "")


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
        need a given pronunciation. A letter of mathematics arrives between
        L_OPEN and L_CLOSE and is spoken by its name (LETTER_IPA). Must raise
        EngineError rather than return partial or empty audio.
        """
        raise NotImplementedError

    def unknown_words(self, words):
        """Which of `words` the engine would have to guess. Default: none."""
        return set()

    def voices(self):
        return []
