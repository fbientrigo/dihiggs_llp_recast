> **Audited entry point:** read `START_HERE_AUDITED.md` before executing this package.

# Recast DV+jets — paquete A/B ejecutable

Este paquete permite avanzar en dos niveles sin presentar un proxy como una
exclusión experimental.

## Qué es A/B

- **A — original:** selección trackless del recast público de ATLAS
  `2301.13866`, incluyendo las eficiencias parametrizadas de evento y vértice.
- **B — modified:** umbrales de jets más bajos usados como escenario
  prospectivo en arXiv:`2606.01681`; conserva la eficiencia de vértice y omite
  la eficiencia parametrizada de evento, siguiendo la definición del paper.

Ambas versiones usan exactamente el mismo punto escalar cuando se comparan.
Así, la diferencia A/B corresponde a la estrategia de análisis, no a un cambio
simultáneo de masa, vida o branching ratios.

## Tres niveles de ejecución

### 1. Proxy del paper — funciona ahora

No necesita MadGraph, Pythia ni FastJet. Usa directamente las eficiencias de la
Table II del paper escalar y calcula

```text
Nsig = luminosidad * sigma * eficiencia.
```

```bash
python3 scripts/run_proxy_ab.py
```

Produce `results/ab_proxy.csv` y `results/ab_summary.md`.

También puede consumir directamente un CSV con la estructura exportada por
`PhysScanWithFixings.cpp`:

```bash
python3 scripts/run_proxy_ab.py \
  --scan-csv examples/scan_points_example.csv \
  --out-csv results/ab_proxy_from_scan.csv \
  --out-md results/ab_proxy_from_scan.md
```

El CSV de ejemplo contiene valores sintéticos consistentes en anchura/vida; no
son puntos físicamente aceptados de un scan real.

### 2. Toy de plumbing — genera un LHE sintético

Este nivel crea eventos `gg -> S S` de dos cuerpos con cinemática determinista.
No es MadGraph y no representa la distribución física del Higgs off-shell. Su
único objetivo es comprobar que SLHA -> Pythia -> PDG del LLP -> recast están
conectados correctamente.

```bash
python3 scripts/generate_toy_lhe.py \
  --pdg 9900035 --mass-gev 250 --events 500 \
  --output events/scalar_pair_toy.lhe
```

### 3. Cadena C++ — requiere el stack HEP

Se incluye un parche contra el commit upstream congelado
`d4047c744062094c9f88e507bb1ccf69e9fe88d6`. El parche:

- permite configurar el PDG del LLP;
- añade los modos `original` y `modified`;
- mantiene el comportamiento upstream por defecto.

```bash
export UPSTREAM_ROOT=/ruta/a/recastingCodes
git -C "$UPSTREAM_ROOT" checkout d4047c744062094c9f88e507bb1ccf69e9fe88d6
git -C "$UPSTREAM_ROOT" apply "$PWD/patches/recast_scalar_ab.patch"

# Compilar según el README upstream y después:
scripts/run_cpp_ab.sh "$UPSTREAM_ROOT"
```

Los logs se escriben en `results/cpp_A_original.log` y
`results/cpp_B_modified.log`.

## Inputs incluidos

```text
configs/ab_scenarios.json       puntos y secciones eficaces del proxy
cards/A_original/               SLHA y Pythia para la selección A
cards/B_modified/               SLHA y Pythia para la selección B
cards/control_neutralino/       control de PDG compatible con upstream
cards/madgraph/                 contrato de generación; requiere un UFO real
model/scalar_portal_contract.json
patches/recast_scalar_ab.patch
```

El benchmark escalar incluido es:

```text
mS = 250 GeV
ctau = 5.1 mm
Gamma = 3.87e-14 GeV
BR(bb, WW, ZZ, gg) = (0.25, 0.50, 0.20, 0.05)
```

Los BR son un ejemplo ejecutable, no los valores exactos del paper ni de un
punto 2HDM. Para usar un punto del scan deben reemplazarse por las anchuras y BR
exportadas por 2HDMC.

## Lo que todavía falta para una reproducción

- UFO escalar validado y su mapeo al modelo 2HDM;
- sección eficaz real de `gg -> h* -> S S`;
- muestras MadGraph de 0/1/2 partones y merging validado;
- distribución real de `beta*gamma`;
- comparación del cutflow local con Table II;
- evaluación estadística completa.

Los resultados de este paquete deben llevar una de estas etiquetas:

```text
PAPER_TABLE_PROXY
TOY_LHE_PLUMBING_TEST
LOCAL_RECAST_RESULT
```

Sólo la última, después de la validación correspondiente, puede considerarse
un resultado de simulación local.
