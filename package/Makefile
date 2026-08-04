PYTHON ?= python3

.PHONY: all validate toy proxy clean

all: validate toy proxy

validate:
	$(PYTHON) scripts/validate_inputs.py

toy:
	$(PYTHON) scripts/generate_toy_lhe.py --pdg 9900035 --mass-gev 250 --events 500 --output events/scalar_pair_toy.lhe
	$(PYTHON) scripts/generate_toy_lhe.py --pdg 1000022 --mass-gev 250 --events 500 --output events/neutralino_pair_toy.lhe

proxy:
	$(PYTHON) scripts/run_proxy_ab.py

clean:
	rm -f events/*.lhe results/*.csv results/*.md results/*.log
