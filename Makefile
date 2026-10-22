PYTHON ?= python3
ROM ?=

.PHONY: help extract build test emulator
help:
	@echo 'make extract|build|test|emulator ROM="/path/to/legally-supplied-USA-ROM.gba"'

extract:
	$(PYTHON) tools/text_extractor.py "$(ROM)"

build:
	$(PYTHON) tools/text_inserter.py "$(ROM)"

test:
	FOMT_ROM="$(ROM)" $(PYTHON) -m pytest -q

emulator:
	$(PYTHON) tools/emulator_smoke.py build/fomt-vi-demo.gba --base-rom "$(ROM)"
