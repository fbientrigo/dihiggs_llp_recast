# Demo segura para la reunión

La demo no genera eventos ni modifica el submódulo.

```bash
source .venv/bin/activate
python scripts/check_environment.py
python scripts/parse_upstream_cutflow.py \
  external/recastingCodes/DisplacedVertices/ATLAS-SUSY-2018-13_GCottin/recast_code/2_results/strong/gluino_run01.txt \
  --out results/upstream_validation/strong-bm1/reference_cutflow.json
python scripts/prepare_upstream_benchmark.py \
  --benchmark strong-bm1 --dry-run
python -m pytest tests/test_cutflow.py -q
```

Resultados esperados:

- core, build y MadGraph: `READY`;
- benchmark: `BLOCKED` por contrato `INCOMPLETE`, SLHA exacto ausente y tres LHE ausentes;
- parser: 9476.625 eventos ponderados, 26.60133% high-pT Acc×Eff,
  0.02165427% trackless Acc×Eff y 4.949932e-13 mb;
- pruebas del comparador: pass, frontera 20%, baja estadística y failure.
