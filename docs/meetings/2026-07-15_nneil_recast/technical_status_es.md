# Estado técnico del recast DV+jets

## Resultado actual

- Gate A: `VALIDATED`. El ejecutable upstream congelado compila, arranca y
  resuelve Pythia 8.308/FastJet 3.4.0. Esto prueba el entorno de compilación,
  no la reproducción física.
- MadGraph: `READY`. Se recuperó exactamente la versión 3.5.3 desde los
  encabezados de las tarjetas y se instaló el tag oficial `v3.5.3`, commit
  `59b4b9c1238978f39a32b8bc83244328187704b6`.
- El import no generativo de `MSSM_SLHA2` funciona. MG5 advierte que Python
  3.12 es experimental y que reweighting no funciona; una campaña futura
  deberá usar un Python soportado.
- Contrato strong-bm1: `INCOMPLETE`. No se encontró el SLHA exacto 2000/850,
  los seeds asignados, los anchos exactos ni las tablas completas de BR.
- Gate B: `BLOCKED`. Los tres LHE siguen ausentes y no se generó una muestra
  smoke.

## Evidencia exacta recuperada

Procesos 0/1/2 jets, modelo `MSSM_SLHA2`, masas 2000/850 GeV, PDG 1000022,
13 TeV, PDF 230000, cortes, 10.000 eventos por multiplicidad, CKKW-L a
500 GeV, Pythia 8.308 y el cutflow `gluino_run01.txt`.

La interpretación 0.01 ns es sólo `INFERRED`: combina el rótulo bm1 con la
convención independiente de la tarjeta `p01ns`. No basta para declarar un
SLHA exacto. La tarjeta 2800/10 nunca se usa como sustituto.

## Por qué el escalar sigue bloqueado

Sin Gate B no se puede separar una discrepancia del generador, del merging o
del análisis. Cambiar PDG, producción o eficiencias ahora invalidaría la línea
base que debe proteger la adaptación escalar.
