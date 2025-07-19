# Optional Dependencies Guide

mdaudiobook uses a minimal core installation to keep the base package lightweight. Advanced features require optional dependencies that you can install as needed.

## 🚀 Quick Start

### Basic Installation (Minimal)
```bash
# Via ucli (recommended)
ucli build mdaudiobook

# Or via pipx directly
pipx install mdaudiobook
```

**Core features included:**
- Basic markdown processing
- Simple text-to-speech (system TTS)
- Audio file generation
- Configuration management

**Package size:** ~50MB

### Add Google Cloud TTS (Most Common)
```bash
pipx inject mdaudiobook google-cloud-texttospeech
```

### Add All API Features
```bash
pipx inject mdaudiobook google-cloud-texttospeech elevenlabs openai azure-cognitiveservices-speech requests
```

### Add Local AI Processing
```bash
pipx inject mdaudiobook torch transformers ollama
```

## 📦 Available Optional Packages

### Cloud TTS Services
| Package | Command | Features |
|---------|---------|----------|
| **Google Cloud** | `pipx inject mdaudiobook google-cloud-texttospeech` | High-quality TTS, 200+ voices |
| **ElevenLabs** | `pipx inject mdaudiobook elevenlabs` | Premium voice cloning |
| **Azure** | `pipx inject mdaudiobook azure-cognitiveservices-speech` | Microsoft TTS |
| **OpenAI** | `pipx inject mdaudiobook openai` | GPT-powered TTS |

### Audio Processing
| Package | Command | Features |
|---------|---------|----------|
| **Advanced Audio** | `pipx inject mdaudiobook librosa soundfile` | Audio analysis, effects |

### Local AI
| Package | Command | Features |
|---------|---------|----------|
| **Local Models** | `pipx inject mdaudiobook torch transformers` | Offline AI processing |
| **Ollama** | `pipx inject mdaudiobook ollama` | Local LLM integration |

## 🎯 Installation Strategies

### Strategy 1: Start Minimal (Recommended)
```bash
# 1. Install core
ucli build mdaudiobook

# 2. Try basic features
mdaudiobook document.md --mode basic

# 3. Add features as needed
pipx inject mdaudiobook google-cloud-texttospeech  # When you want Google TTS
```

### Strategy 2: Google Cloud User
```bash
# Install with Google Cloud support
ucli build mdaudiobook
pipx inject mdaudiobook google-cloud-texttospeech

# Set up credentials (see GOOGLE_SETUP.md)
# Then use API mode
mdaudiobook document.md --mode api
```

### Strategy 3: Power User
```bash
# Install everything
ucli build mdaudiobook
pipx inject mdaudiobook google-cloud-texttospeech elevenlabs openai torch transformers librosa soundfile

# Use all features
mdaudiobook document.md --mode hybrid
```

## 🔧 Setup.py Extras (Alternative)

If you prefer traditional pip installation with extras:

```bash
# Basic installation
pip install mdaudiobook

# With Google Cloud
pip install mdaudiobook[google]

# With all APIs
pip install mdaudiobook[api]

# With local AI
pip install mdaudiobook[local-ai]

# Everything
pip install mdaudiobook[all]
```

## 📊 Package Size Comparison

| Installation | Packages | Approximate Size |
|-------------|----------|------------------|
| **Core only** | 15 packages | ~50MB |
| **+ Google Cloud** | +5 packages | ~80MB |
| **+ All APIs** | +15 packages | ~150MB |
| **+ Local AI** | +25 packages | ~2GB |
| **Everything** | +40 packages | ~2.5GB |

## 🎵 Processing Modes by Dependencies

| Mode | Required Dependencies | Features |
|------|----------------------|----------|
| `basic` | Core only | System TTS, basic processing |
| `local-ai` | Core + torch + transformers | Local AI enhancement |
| `api` | Core + cloud TTS packages | Cloud TTS services |
| `hybrid` | Core + any mix | Best available features |

## 🚨 Troubleshooting

### "Module not found" errors
```bash
# Check what's installed
pipx list mdaudiobook

# Install missing dependency
pipx inject mdaudiobook [package-name]
```

### Google Cloud credentials
```bash
# Install Google dependencies first
pipx inject mdaudiobook google-cloud-texttospeech

# Then set up credentials (see main README)
```

### Performance issues
```bash
# For heavy AI processing, install local dependencies
pipx inject mdaudiobook torch transformers

# For audio analysis
pipx inject mdaudiobook librosa soundfile
```

## 💡 Why Optional Dependencies?

1. **Faster installation** - Core features install in seconds
2. **Smaller footprint** - Don't install 2GB of AI models if you don't need them
3. **Flexibility** - Add only the features you use
4. **Better UX** - Clear separation between basic and advanced features
5. **Easier maintenance** - Isolated dependency conflicts

## 🔄 Upgrading

```bash
# Upgrade core package
pipx upgrade mdaudiobook

# Upgrade specific dependencies
pipx inject mdaudiobook google-cloud-texttospeech --force

# Remove unused dependencies
pipx uninstall mdaudiobook
pipx install mdaudiobook
# Then re-add only what you need
```
