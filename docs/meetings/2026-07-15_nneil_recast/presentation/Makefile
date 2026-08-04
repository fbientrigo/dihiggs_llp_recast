# Python must provide matplotlib; the repo .venv does not.
# Override, e.g.: make PYTHON="conda run -n base python"
PYTHON ?= python3

# First available engine wins: tectonic, latexmk, then plain pdflatex.
TECTONIC := $(shell command -v tectonic 2>/dev/null)
LATEXMK  := $(shell command -v latexmk 2>/dev/null)

.PHONY: all clean copies

all: reference_cutflow_upstream.pdf nneil_recast_es.pdf one_page_status_es.pdf copies

reference_cutflow_upstream.pdf: reference_cutflow_upstream.csv make_reference_cutflow_plot.py
	$(PYTHON) make_reference_cutflow_plot.py

%.pdf: %.tex reference_cutflow_upstream.pdf
	@if [ -n "$(TECTONIC)" ]; then tectonic --keep-logs --chatter minimal $<; \
	elif [ -n "$(LATEXMK)" ]; then latexmk -pdf -interaction=nonstopmode -halt-on-error $<; \
	else pdflatex -interaction=nonstopmode -halt-on-error $< && pdflatex -interaction=nonstopmode -halt-on-error $<; fi

copies: nneil_recast_es.pdf one_page_status_es.pdf reference_cutflow_upstream.pdf
	cp $^ ..

clean:
	rm -f *.aux *.fdb_latexmk *.fls *.log *.nav *.out *.snm *.toc
