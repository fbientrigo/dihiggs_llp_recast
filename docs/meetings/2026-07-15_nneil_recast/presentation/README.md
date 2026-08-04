# Paquete para reunión con N. Neil

Presentación, resumen técnico y cutflow de referencia en español. La figura y
el CSV transcriben el resultado upstream distribuido; no representan una
reproducción local ni cierran Gate B.

El paquete acompaña `benchmarks/scalar/scalar-recast-v0`, clasificado
`RECONSTRUCTED`, con generación y validación física `NOT_RUN`.

## Construcción

La `.venv` del repo no trae matplotlib y no debe traerlo sólo por esta reunión:
hay que pasar un intérprete que sí lo tenga. Motor TeX y Python usados en la
última compilación:

```bash
# tectonic vive en un entorno conda aparte (creado sólo para este paquete)
export PATH="$HOME/anaconda3/envs/texmini/bin:$PATH"
make PYTHON="conda run -n base python"
make clean   # conserva los PDF
```

Alternativas equivalentes: `PYTHON=/home/fabi/higgs_env_py312/bin/python`, y
`latexmk` o `pdflatex` si están instalados. El `Makefile` elige el primer motor
disponible entre `tectonic`, `latexmk` y `pdflatex`.

`make` genera la figura con matplotlib, compila los dos documentos y copia los
tres PDF al directorio superior.

## Contenido

- `nneil_recast_es.tex` — 14 slides;
- `one_page_status_es.tex` — resumen de una página;
- `speaker_notes_es.md` — notas por slide;
- `reference_cutflow_upstream.csv` — transcripción del cutflow upstream; los
  valores no se editan, sólo las etiquetas de la figura.

## Deferred after meeting

- generación MadGraph y reconstrucción final de SLHA;
- instalación de otro Python;
- modificación del C++ y adaptación del PDG;
- cambio de algoritmo de jets y aislamiento de fotones;
- eventos del paper, exclusiones y Deep Research;
- refactor general.
