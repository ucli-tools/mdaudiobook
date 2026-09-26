# mdaudiobook - Markdown books to audiobooks
# Part of the ucli-tools ecosystem
#
# Install with:   make build        (CPU; the usual case)
#                 make build-gpu    (CUDA machine: the same code, faster voices)
# Then once:      mdaudiobook setup
# Reinstall with: make rebuild
# Uninstall with: make delete

.PHONY: build build-gpu rebuild delete test help

CPU_TORCH := --index https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match

build: ## Install mdaudiobook with CPU PyTorch (uv tool install → ~/.local/bin)
	uv tool install --python 3.12 --from . mdaudiobook --force --reinstall $(CPU_TORCH)
	@echo "Installed. Run 'mdaudiobook setup' once to fetch the maths speech engine and the voice model."

build-gpu: ## Install mdaudiobook with CUDA PyTorch
	uv tool install --python 3.12 --from . mdaudiobook --force --reinstall
	@echo "Installed. Run 'mdaudiobook setup', then build with --device cuda."

rebuild: delete build ## Reinstall mdaudiobook

delete: ## Uninstall mdaudiobook
	uv tool uninstall mdaudiobook || true

test: ## Run the test suite in a throwaway environment
	uv run --python 3.12 $(CPU_TORCH) --with pytest --with-editable . pytest -q

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'
