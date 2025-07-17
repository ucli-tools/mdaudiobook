# mdaudiobook

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](https://opensource.org/licenses/Apache-2.0)
[![ucli-tools](https://img.shields.io/badge/ucli--tools-ecosystem-green.svg)](https://github.com/ucli-tools)

**A professional, Makefile-driven pipeline to convert Markdown documents into high-quality audiobooks.**

`mdaudiobook` is a powerful command-line tool designed for academic and technical content. It intelligently handles complex elements like mathematical expressions, citations, and footnotes, producing clean, navigable audiobooks. As a core component of the `ucli-tools` ecosystem, it works in tandem with `mdtexpdf` to provide a unified document creation workflow.

---

## ✨ Features

- **System-Wide Command:** Install once with `make install-system` and use `mdaudiobook` from any directory.
- **Makefile-Driven Workflow:** Simple `make` commands handle setup, building, installation, and processing.
- **Unified Metadata:** Shares a 3-section YAML frontmatter with `mdtexpdf` for consistent configuration across PDF and audio outputs.
- **Intelligent Text Handling:** Converts LaTeX math to natural speech and correctly processes academic syntax.
- **Multiple Processing Modes:** Choose between free, local AI, premium API, and reliable hybrid modes.
- **Standardized Output:** Generates chapterized `.m4b` audiobooks in the current working directory for a clean, predictable workflow.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- FFmpeg
- Git

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ucli-tools/mdaudiobook.git
    cd mdaudiobook
    ```

2.  **Setup the environment:**
    ```bash
    make setup
    ```

3.  **Build and install the tool system-wide:**
    ```bash
    make install-system
    ```
    *You may be prompted for your password as this installs the tool to `/usr/local/bin`.*

4.  **Verify the installation:**
    ```bash
    mdaudiobook --version
    ```

## 🔧 Usage

Once installed, `mdaudiobook` can be run directly on any Markdown file. The output `.m4b` file will be created in the same directory.

```bash
# Navigate to your document's directory
cd /path/to/my/documents/

# Generate an audiobook from a Markdown file
mdaudiobook my_document.md

# Use a specific processing mode (e.g., premium API)
mdaudiobook my_document.md --mode api
```

For development and batch processing, you can also use the `Makefile` targets from within the project directory:

```bash
# Process a single file using the Makefile
make audiobook SOURCE=path/to/document.md

# Process all documents in the `documents/` directory
make process-all
```

## ⚙️ Configuration

`mdaudiobook` uses a 3-section YAML frontmatter at the top of your Markdown file, shared with `mdtexpdf`.

```yaml
---
# 1. Common Metadata (Used by both tools)
title: "The God Equation"
author: "Dr. Michio Kaku"
---
# 2. PDF-Specific Metadata (Ignored by mdaudiobook)
no_numbers: true
---
# 3. Audio-Specific Metadata (Used by mdaudiobook)
processing_mode: "hybrid" # basic, local_ai, api, hybrid
output_format: "m4b"      # m4b, mp3, wav
voices:
  main_narrator: "google_en-us-neural2-d"
  math_voice: "google_en-us-wavenet-c"
```

API keys and other sensitive data are managed in a `.env` file. Copy the example and add your credentials:

```bash
cp .env.example .env
nano .env
```

## 📁 Project Structure

```
mdaudiobook/
├── README.md                    # This file
├── LICENSE                     # Apache 2.0 license
├── Makefile                    # Build and processing commands
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── config/
│   └── default.yaml.example   # Configuration template
├── src/
│   └── ...                     # Source code
├── scripts/
│   └── process_audiobook.py   # Main processing script
├── documents/                 # Example input markdown files
├── output/                    # Default output directory
└── tests/
    └── ...                     # Automated tests
```

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

---

*Part of the `ucli-tools` ecosystem - Professional tools for academic and technical content creation.*
