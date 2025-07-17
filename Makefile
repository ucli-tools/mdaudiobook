# mdaudiobook - Professional Markdown to Audiobook Pipeline
# Part of the ucli-tools ecosystem

.PHONY: help setup dev-setup demo test lint clean clean-all audiobook audiobook-basic audiobook-local-ai audiobook-api audiobook-hybrid process-all set-google build rebuild install-system uninstall-system

# Default target
help:
	@echo "mdaudiobook - Professional Markdown to Audiobook Pipeline"
	@echo ""
	@echo "Available targets:"
	@echo "  setup           - Install dependencies and setup environment"
	@echo "  dev-setup       - Setup development environment"
	@echo "  set-google      - Configure for Google Cloud TTS"
	@echo "  demo            - Run demo with example document"
	@echo ""
	@echo "Processing Commands:"
	@echo "  audiobook SOURCE=file.md           - Process audiobook (hybrid mode)"
	@echo "  audiobook-basic SOURCE=file.md     - Basic local processing"
	@echo "  audiobook-local-ai SOURCE=file.md  - Local AI enhancement"
	@echo "  audiobook-api SOURCE=file.md       - Premium API processing"
	@echo "  audiobook-hybrid SOURCE=file.md    - Hybrid fallback mode"
	@echo "  process-all                        - Process all documents in documents/"
	@echo ""
	@echo "Development:"
	@echo "  build            - Build mdaudiobook executable wrapper"
	@echo "  rebuild          - Clean and rebuild"
	@echo "  install-system   - Install to /usr/local/bin (system-wide)"
	@echo "  uninstall-system - Remove from system PATH"
	@echo "  test             - Run all tests"
	@echo "  test-integration - Run integration tests"
	@echo "  lint             - Check code quality"
	@echo "  clean            - Clean generated files"
	@echo "  clean-all        - Clean everything including venv"
	@echo ""
	@echo "Example:"
	@echo "  make audiobook SOURCE=documents/bells_theorem.md"

# Environment and setup
setup:
	@echo "Setting up mdaudiobook environment..."
	@if [ ! -d "venv" ]; then python3 -m venv venv; echo "Created virtual environment"; fi
	@echo "Activating virtual environment and installing dependencies..."
	. venv/bin/activate && pip install -r requirements.txt
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file - please configure API keys if needed"; fi
	@if [ ! -f config/default.yaml ]; then cp config/default.yaml.example config/default.yaml; echo "Created default configuration"; fi
	@echo "Setup complete! Run 'make demo' to test."
	@echo "Note: Remember to activate the virtual environment with 'source venv/bin/activate'"

dev-setup: setup
	@echo "Setting up development environment..."
	. venv/bin/activate && pip install -r requirements-dev.txt
	. venv/bin/activate && pre-commit install
	@echo "Development environment ready!"

# Google Cloud TTS Configuration
set-google:
	@echo "Configuring mdaudiobook for Google Cloud TTS..."
	@if [ ! -f config/default.yaml.google ]; then echo "Error: config/default.yaml.google not found!"; exit 1; fi
	cp config/default.yaml.google config/default.yaml
	@echo "✓ Google Cloud TTS configuration activated"
	@echo ""
	@echo "Next steps:"
	@echo "1. Ensure GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_CLOUD_PROJECT are set in .env"
	@echo "2. Run: make audiobook-api SOURCE=your_document.md"
	@echo ""
	@echo "Example:"
	@echo "  make audiobook-api SOURCE=documents/example.md"

# Demo and testing
demo:
	@echo "Running mdaudiobook demo..."
	@if [ ! -f documents/example.md ]; then \
		echo "Creating example document..."; \
		mkdir -p documents; \
		echo "# Example Document\n\nThis is a test document with math: $$E = mc^2$$" > documents/example.md; \
	fi
	. venv/bin/activate && python scripts/process_audiobook.py documents/example.md --mode basic --output output/demo.m4b
	@echo "Demo complete! Check output/demo.m4b"

# Main processing commands
audiobook:
	@if [ -z "$(SOURCE)" ]; then echo "Usage: make audiobook SOURCE=file.md"; exit 1; fi
	@echo "Processing audiobook: $(SOURCE) (hybrid mode)"
	. venv/bin/activate && python scripts/process_audiobook.py $(SOURCE) --mode hybrid --output output/

audiobook-basic:
	@if [ -z "$(SOURCE)" ]; then echo "Usage: make audiobook-basic SOURCE=file.md"; exit 1; fi
	@echo "Processing audiobook: $(SOURCE) (basic mode)"
	. venv/bin/activate && python scripts/process_audiobook.py $(SOURCE) --mode basic --output output/

audiobook-local-ai:
	@if [ -z "$(SOURCE)" ]; then echo "Usage: make audiobook-local-ai SOURCE=file.md"; exit 1; fi
	@echo "Processing audiobook: $(SOURCE) (local AI mode)"
	. venv/bin/activate && python scripts/process_audiobook.py $(SOURCE) --mode local_ai --output output/

audiobook-api:
	@if [ -z "$(SOURCE)" ]; then echo "Usage: make audiobook-api SOURCE=file.md"; exit 1; fi
	@echo "Processing audiobook: $(SOURCE) (API mode)"
	. venv/bin/activate && python scripts/process_audiobook.py $(SOURCE) --mode api --output output/

audiobook-hybrid:
	@if [ -z "$(SOURCE)" ]; then echo "Usage: make audiobook-hybrid SOURCE=file.md"; exit 1; fi
	@echo "Processing audiobook: $(SOURCE) (hybrid mode)"
	. venv/bin/activate && python scripts/process_audiobook.py $(SOURCE) --mode hybrid --output output/

# Batch processing
process-all:
	@echo "Processing all documents in documents/ directory..."
	@for file in documents/*.md; do \
		if [ -f "$$file" ]; then \
			echo "Processing $$file..."; \
			. venv/bin/activate && python scripts/process_audiobook.py "$$file" --mode hybrid --output output/; \
		fi; \
	done
	@echo "Batch processing complete!"

# Testing and quality assurance
test:
	@echo "Running tests..."
	. venv/bin/activate && python -m pytest tests/ -v

test-integration:
	@echo "Running integration tests..."
	. venv/bin/activate && python -m pytest tests/test_integration.py -v

lint:
	@echo "Checking code quality..."
	. venv/bin/activate && flake8 src/ scripts/ tests/
	. venv/bin/activate && black --check src/ scripts/ tests/
	. venv/bin/activate && isort --check-only src/ scripts/ tests/

format:
	@echo "Formatting code..."
	. venv/bin/activate && black src/ scripts/ tests/
	. venv/bin/activate && isort src/ scripts/ tests/

# Cleanup
clean:
	@echo "Cleaning generated files..."
	rm -rf output/audiobooks/*
	rm -rf output/enhanced_text/*
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	rm -rf tests/__pycache__/
	rm -rf .pytest_cache/
	rm -rf *.egg-info/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	@echo "Cleanup complete!"

# Clean everything including virtual environment
clean-all: clean
	@echo "Cleaning everything including virtual environment..."
	rm -rf venv/
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	rm -rf tests/__pycache__/
	rm -rf scripts/__pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	@echo "Complete cleanup finished!"

# Installation and packaging
install:
	. venv/bin/activate && pip install -e .

build:
	@echo "Building mdaudiobook..."
	@echo "Validating Python dependencies..."
	@if [ ! -d "venv" ]; then echo "Virtual environment not found. Run 'make setup' first."; exit 1; fi
	. venv/bin/activate && python -c "import sys; print(f'Python {sys.version}')"
	@echo "Creating executable wrapper script..."
	@MDAUDIOBOOK_DIR="$$(pwd)"; \
	if [ ! -f "mdaudiobook" ]; then \
		echo '#!/bin/bash' > mdaudiobook; \
		echo '# mdaudiobook - System wrapper for mdaudiobook.py' >> mdaudiobook; \
		echo '' >> mdaudiobook; \
		echo '# Set mdaudiobook directory (absolute path)' >> mdaudiobook; \
		echo "MDAUDIOBOOK_DIR=\"$$MDAUDIOBOOK_DIR\"" >> mdaudiobook; \
		echo '' >> mdaudiobook; \
		echo '# Store current working directory' >> mdaudiobook; \
		echo 'ORIGINAL_CWD="$$(pwd)"' >> mdaudiobook; \
		echo '' >> mdaudiobook; \
		echo '# Convert relative paths to absolute paths' >> mdaudiobook; \
		echo 'args=()' >> mdaudiobook; \
		echo 'for arg in "$$@"; do' >> mdaudiobook; \
		echo '    # Check if argument looks like a file path (contains . or / and doesnt start with -)' >> mdaudiobook; \
		echo '    if [[ "$$arg" == *.* || "$$arg" == */* ]] && [[ "$$arg" != -* ]]; then' >> mdaudiobook; \
		echo '        # Convert to absolute path if its relative' >> mdaudiobook; \
		echo '        if [[ "$$arg" != /* ]]; then' >> mdaudiobook; \
		echo '            args+=("$$ORIGINAL_CWD/$$arg")' >> mdaudiobook; \
		echo '        else' >> mdaudiobook; \
		echo '            args+=("$$arg")' >> mdaudiobook; \
		echo '        fi' >> mdaudiobook; \
		echo '    else' >> mdaudiobook; \
		echo '        args+=("$$arg")' >> mdaudiobook; \
		echo '    fi' >> mdaudiobook; \
		echo 'done' >> mdaudiobook; \
		echo '' >> mdaudiobook; \
		echo '# Activate virtual environment and execute Python script with absolute paths' >> mdaudiobook; \
		echo 'cd "$$MDAUDIOBOOK_DIR"' >> mdaudiobook; \
		echo '. venv/bin/activate && python scripts/process_audiobook.py "$${args[@]}"' >> mdaudiobook; \
		chmod +x mdaudiobook; \
		echo "Created executable wrapper: mdaudiobook"; \
	fi
	@echo "mdaudiobook build complete!"

# Clean and rebuild
rebuild: clean build

# Install to system PATH (like mdtexpdf)
install-system: build
	@echo "Installing mdaudiobook to /usr/local/bin..."
	@if [ ! -f "mdaudiobook" ]; then echo "Build first with 'make build'"; exit 1; fi
	sudo cp mdaudiobook /usr/local/bin/mdaudiobook
	sudo chmod +x /usr/local/bin/mdaudiobook
	@echo "mdaudiobook installed successfully to /usr/local/bin/mdaudiobook"
	@echo "You can now use 'mdaudiobook' from anywhere in the system"

# Remove from system PATH
uninstall-system:
	@echo "Uninstalling mdaudiobook from system..."
	sudo rm -f /usr/local/bin/mdaudiobook
	@echo "mdaudiobook uninstalled from system"

# Package build
package:
	. venv/bin/activate && python setup.py sdist bdist_wheel

# Validation
validate-config:
	@echo "Validating configuration..."
	. venv/bin/activate && python scripts/validate_config.py config/default.yaml

validate-output:
	@if [ -z "$(FILE)" ]; then echo "Usage: make validate-output FILE=output.m4b"; exit 1; fi
	@echo "Validating audiobook output: $(FILE)"
	. venv/bin/activate && python scripts/validate_output.py $(FILE)

# Documentation
docs:
	@echo "Generating documentation..."
	@echo "Documentation available in docs/ directory"

# Development utilities
check-deps:
	@echo "Checking dependencies..."
	. venv/bin/activate && pip check

update-deps:
	@echo "Updating dependencies..."
	. venv/bin/activate && pip install --upgrade -r requirements.txt

# Environment info
info:
	@echo "mdaudiobook Environment Information:"
	@echo "Python version: $$( . venv/bin/activate && python --version)"
	@echo "Pip version: $$( . venv/bin/activate && pip --version)"
	@echo "FFmpeg: $$(which ffmpeg || echo 'Not installed')"
	@echo "Git: $$(git --version)"
	@echo "Current directory: $$(pwd)"
	@echo "Configuration: $$(ls -la config/ 2>/dev/null || echo 'No config directory')"
