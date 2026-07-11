PYTHON ?= python3
UPSTREAM_ROOT ?= external/recastingCodes
MANIFEST ?= results/manifests/environment.json

.PHONY: help bootstrap install test lint static-check upstream-check check hep-preflight manifest build-upstream clean

help:
	@printf '%s\n' \
	  'make install         Install the local package and development tools' \
	  'make bootstrap       Materialize the frozen upstream recast checkout' \
	  'make static-check    Run unit tests and linting without HEP dependencies' \
	  'make upstream-check  Validate the frozen upstream folder and revision' \
	  'make check           Run static and upstream layout checks' \
	  'make hep-preflight   Report local compiler and HEP tool availability' \
	  'make build-upstream  Compile the frozen upstream C++ recast' \
	  'make manifest        Write a reproducibility manifest' \
	  'make clean           Remove local caches and generated manifest'

install:
	$(PYTHON) -m pip install -e '.[dev]'

bootstrap:
	./scripts/bootstrap_upstream.sh

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

static-check: test lint

upstream-check:
	$(PYTHON) scripts/check_upstream_layout.py --root $(UPSTREAM_ROOT)

check: static-check upstream-check

hep-preflight:
	$(PYTHON) scripts/check_environment.py

build-upstream:
	./scripts/build_upstream.sh

manifest:
	@mkdir -p $(dir $(MANIFEST))
	$(PYTHON) scripts/write_environment_manifest.py --out $(MANIFEST)

clean:
	rm -rf .pytest_cache .ruff_cache build dist src/*.egg-info src/dvrecast/__pycache__ tests/__pycache__
	rm -f $(MANIFEST)
