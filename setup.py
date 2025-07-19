#!/usr/bin/env python3
"""
mdaudiobook - Professional Markdown to Audiobook Pipeline
Part of the ucli-tools ecosystem
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mdaudiobook",
    version="0.1.0",
    author="ucli-tools",
    author_email="contact@ucli-tools.org",
    description="Professional Markdown to Audiobook Pipeline for Academic and Technical Content",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/ucli-tools/mdaudiobook",
    project_urls={
        "Bug Tracker": "https://github.com/ucli-tools/mdaudiobook/issues",
        "Documentation": "https://github.com/ucli-tools/mdaudiobook/docs",
        "Source Code": "https://github.com/ucli-tools/mdaudiobook",
        "ucli-tools": "https://github.com/ucli-tools",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Text Processing :: Markup",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        # Development tools
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.1",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
            "pre-commit>=3.3.3",
        ],
        # Documentation tools
        "docs": [
            "mkdocs>=1.5.2",
            "mkdocs-material>=9.2.3",
        ],
        # Google Cloud TTS (most common)
        "google": [
            "google-cloud-texttospeech>=2.14.1",
        ],
        # Advanced audio processing
        "audio": [
            "librosa>=0.10.1",
            "soundfile>=0.12.1",
        ],
        # Local AI models
        "local-ai": [
            "ollama>=0.1.7",
            "transformers>=4.33.2",
            "torch>=2.0.1",
        ],
        # Cloud TTS APIs
        "cloud-tts": [
            "elevenlabs>=0.2.24",
            "azure-cognitiveservices-speech>=1.31.0",
            "openai>=0.28.0",
        ],
        # HTTP clients for APIs
        "http": [
            "requests>=2.31.0",
            "httpx>=0.24.1",
            "aiohttp>=3.8.5",
        ],
        # All API features (convenience)
        "api": [
            "google-cloud-texttospeech>=2.14.1",
            "elevenlabs>=0.2.24",
            "azure-cognitiveservices-speech>=1.31.0",
            "openai>=0.28.0",
            "anthropic>=0.3.11",
            "requests>=2.31.0",
            "httpx>=0.24.1",
            "aiohttp>=3.8.5",
        ],
        # Everything (for power users)
        "all": [
            "google-cloud-texttospeech>=2.14.1",
            "elevenlabs>=0.2.24",
            "azure-cognitiveservices-speech>=1.31.0",
            "openai>=0.28.0",
            "anthropic>=0.3.11",
            "ollama>=0.1.7",
            "transformers>=4.33.2",
            "torch>=2.0.1",
            "librosa>=0.10.1",
            "soundfile>=0.12.1",
            "requests>=2.31.0",
            "httpx>=0.24.1",
            "aiohttp>=3.8.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "mdaudiobook=mdaudiobook.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "mdaudiobook": [
            "templates/*.yaml",
            "config/*.yaml",
        ],
    },
    keywords=[
        "audiobook",
        "markdown",
        "text-to-speech",
        "tts",
        "academic",
        "technical",
        "latex",
        "mathematics",
        "ucli-tools",
    ],
    zip_safe=False,
)
