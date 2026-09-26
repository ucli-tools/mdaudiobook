"""mdaudiobook: Markdown books to audiobooks.

The pipeline is script -> check -> synthesize -> master -> verify. The script
is the exact text the listener will hear, built from pandoc's reading of the
book; every later step works from it and can be checked against it.
"""

__version__ = "2.0.0"
