# mdaudiobook

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](https://opensource.org/licenses/Apache-2.0)
[![ucli-tools](https://img.shields.io/badge/ucli--tools-ecosystem-green.svg)](https://github.com/ucli-tools)

**Professional Markdown to Audiobook Pipeline for Academic and Technical Content**

`mdaudiobook` converts Markdown documents into high-quality audiobooks with intelligent handling of mathematical expressions, citations, and academic syntax. Features a minimal core installation with optional dependencies for advanced features.

---

## ✨ Key Features

- **🚀 Fast Installation:** Minimal 50MB core install, add features as needed
- **🎯 Interactive Setup:** Guided configuration for Google Cloud TTS and other services
- **🧠 Smart Processing:** Converts LaTeX math to natural speech, handles academic syntax
- **🔧 Flexible Modes:** Basic, local AI, cloud API, and hybrid processing options
- **📚 Academic Focus:** Designed for technical documents, research papers, and educational content
- **🎵 Professional Output:** Chapterized `.m4b` audiobooks with metadata and navigation

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- [ucli](https://github.com/ucli-tools/ucli) (recommended) or pipx

### Installation Options

#### Option 1: Via ucli (Recommended)
```bash
# Install mdaudiobook with minimal dependencies (~50MB)
ucli build mdaudiobook

# Start using immediately with basic TTS
mdaudiobook document.md --mode basic
```

#### Option 2: Manual Installation
```bash
# Clone and install locally
git clone https://github.com/ucli-tools/mdaudiobook.git
cd mdaudiobook
pipx install .

# Test basic functionality
mdaudiobook document.md --mode basic
```

### Adding Optional Features

mdaudiobook uses a minimal core installation. Add features as needed:

#### Google Cloud TTS (Most Popular)
```bash
# One-command setup: installs dependencies + configures credentials
mdaudiobook --setup-google

# Use premium TTS (works automatically with hybrid mode)
mdaudiobook document.md
```

**Advanced users:**
```bash
# Skip automatic dependency installation
mdaudiobook --setup-google --no-install-deps
```

#### Other Cloud TTS Services
```bash
# ElevenLabs, Azure, OpenAI
pipx inject mdaudiobook elevenlabs azure-cognitiveservices-speech openai
```

#### Local AI Processing
```bash
# For offline AI enhancement (large download ~2GB)
pipx inject mdaudiobook torch transformers
```

#### Everything (Power Users)
```bash
# Install all optional features
pipx inject mdaudiobook google-cloud-texttospeech elevenlabs torch transformers librosa
```

### Verify Installation
```bash
# Check help and available modes
mdaudiobook --help

# Test with a sample document
mdaudiobook example.md --verbose --dry-run
```

## 🔧 Usage

### Basic Commands

```bash
# Basic audiobook generation (works immediately after install)
mdaudiobook document.md

# Use specific processing mode
mdaudiobook document.md --mode basic      # Offline TTS
mdaudiobook document.md --mode api        # Cloud TTS (requires setup)
mdaudiobook document.md --mode hybrid     # Best available (default)

# Verbose output and dry-run for testing
mdaudiobook document.md --verbose --dry-run

# Custom output directory
mdaudiobook document.md --output-dir ./audiobooks
```

### Interactive Setup

```bash
# Step-by-step Google Cloud TTS setup
mdaudiobook --setup-google

# Get help and see all options
mdaudiobook --help
```

### Processing Modes

| Mode | Dependencies | Features | Use Case |
|------|-------------|----------|----------|
| `basic` | Core only | System TTS, fast | Quick conversion, testing |
| `local-ai` | + torch, transformers | Local AI enhancement | Offline, privacy-focused |
| `api` | + cloud TTS packages | Premium voices, quality | Production audiobooks |
| `hybrid` | Any available | Best of all modes | Recommended default |

## ⚙️ Configuration

### Document Configuration (Optional)

Add YAML frontmatter to your Markdown files for custom settings:

```yaml
---
title: "Real and Complex Mathematical Analysis"
author: "Dr. Jane Smith"
processing_mode: "hybrid"  # basic, local-ai, api, hybrid
output_format: "m4b"       # m4b, mp3, wav
voices:
  main_narrator: "google_en-us-neural2-d"
  math_voice: "google_en-us-wavenet-c"
---

# Your content here...
```

### Google Cloud TTS Setup

Use the one-command setup for easy configuration:

```bash
# Complete setup: installs dependencies + configures credentials
mdaudiobook --setup-google
```

The setup will:
1. **Automatically install Google Cloud dependencies** (pipx inject)
2. Guide you through Google Cloud project creation
3. Help you download and configure service account credentials
4. Test the connection to ensure everything works
5. Save credentials to `~/.config/mdaudiobook/google-credentials.json`

**Advanced users who want manual dependency control:**
```bash
# Skip automatic dependency installation
mdaudiobook --setup-google --no-install-deps
```

### Manual Configuration (Advanced)

For advanced users, credentials can be placed in:
- `~/.config/mdaudiobook/google-credentials.json`
- `~/.config/mdaudiobook/credentials.json`
- Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Default Google Cloud location: `~/.config/gcloud/application_default_credentials.json`

## 📦 Optional Dependencies

mdaudiobook uses a minimal core installation (~50MB) with optional features:

### Installation Sizes
| Package Set | Size | Command |
|-------------|------|----------|
| **Core** | ~50MB | `ucli build mdaudiobook` |
| **+ Google Cloud** | ~80MB | `pipx inject mdaudiobook google-cloud-texttospeech` |
| **+ All APIs** | ~150MB | `pipx inject mdaudiobook elevenlabs openai azure-cognitiveservices-speech` |
| **+ Local AI** | ~2GB | `pipx inject mdaudiobook torch transformers` |
| **Everything** | ~2.5GB | `pipx inject mdaudiobook google-cloud-texttospeech elevenlabs torch transformers librosa` |

### Feature Categories
- **`google`**: Google Cloud TTS only (most popular)
- **`cloud-tts`**: All cloud TTS APIs (ElevenLabs, Azure, OpenAI)
- **`local-ai`**: Offline AI processing with torch/transformers
- **`audio`**: Advanced audio processing with librosa
- **`api`**: All API features combined
- **`all`**: Everything for power users

See [OPTIONAL_DEPENDENCIES.md](OPTIONAL_DEPENDENCIES.md) for detailed installation strategies.

## 📁 Project Structure

```
mdaudiobook/
├── README.md                    # This file
├── OPTIONAL_DEPENDENCIES.md     # Detailed dependency guide
├── LICENSE                     # Apache 2.0 license
├── setup.py                    # Python package configuration
├── requirements.txt            # Minimal core dependencies
├── Makefile                    # ucli integration
├── src/
│   └── mdaudiobook/            # Main package
│       ├── cli.py              # Command-line interface
│       ├── markdown_processor.py
│       ├── text_enhancer.py
│       ├── audiobook_generator.py
│       └── config_manager.py
├── documents/                  # Example markdown files
└── tests/                      # Automated tests
```

## 🎯 User Experience Highlights

### For Beginners
```bash
# Install and start using immediately
ucli build mdaudiobook
mdaudiobook document.md  # Works right away with basic TTS
```

### For Google Cloud Users
```bash
# One-command setup (installs dependencies + configures credentials)
mdaudiobook --setup-google
mdaudiobook document.md  # Premium quality automatically
```

### For Power Users
```bash
# Install everything for maximum features
pipx inject mdaudiobook google-cloud-texttospeech elevenlabs torch transformers
mdaudiobook document.md --mode hybrid  # Best of all worlds
```

### Key Benefits
- ⚡ **Fast**: 50MB core install vs 2GB+ traditional approach
- 🎯 **Guided**: Interactive setup eliminates configuration confusion
- 🔧 **Flexible**: Add only the features you need
- 🚀 **Modern**: Uses pipx for clean, isolated installations
- 📚 **Academic**: Designed for technical documents and research

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

---

*Part of the `ucli-tools` ecosystem - Professional tools for academic and technical content creation.*
