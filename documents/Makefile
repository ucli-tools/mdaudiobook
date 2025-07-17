# Example Makefile for mdaudiobook
#
# This Makefile demonstrates how to use the `mdaudiobook` tool
# to generate an audiobook from the `example.md` source file.
#
# Assumes `mdaudiobook` has been installed system-wide.
# See the main project README for installation instructions.

.PHONY: all build build-audiobook clean help

# Default target
all: build-audiobook

# Build the audiobook for example.md
build: build-audiobook
build-audiobook:
	@echo "Building audiobook: example.md"
	@mdaudiobook example.md
	@echo "Audiobook 'example.m4b' created successfully."

# Clean the generated audiobook file
clean:
	@rm -f example.m4b
	@echo "Cleaned generated file: example.m4b"

# Display help information
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build-audiobook  - Generate the audiobook from example.md (default)"
	@echo "  build            - Alias for build-audiobook"
	@echo "  clean            - Remove the generated audiobook file"
	@echo "  help             - Show this help message"
