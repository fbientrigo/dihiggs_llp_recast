# Notas del presentador

## Mensaje central

Tenemos una implementación pública de una búsqueda DV+jets. Ya validamos su instalación, entendemos cómo forma el vértice y cómo usa los jets, y estructuramos la referencia upstream. Todavía no hemos producido el benchmark con eventos propios. Sí podemos construir una reproducción estadística documentada y, después, adaptar el análisis al escalar usando los eventos y parámetros de los demás repositorios.

## Guion por slide

### 1. Pregunta científica

Abrir con la física: queremos saber si un escalar `S` producido por `gg → h* → SS` y que decae dentro del tracker puede quedar restringido por una selección DV+jets. No abrir con “Gate A”, commits ni el estado del código.

- Fuente: arXiv:2606.01681, resumen y Secs. II–III.
- No afirmar: “ya reinterpretamos el 2HDM”.
- Transición: para responder necesitamos saber qué mide un recast.

### 2. Qué es un recast

Un recast aproxima la selección pública y devuelve `A×ε`. La tasa esperada se obtiene luego con sección eficaz, luminosidad y BR. Compilar no prueba la física y un factor K no mueve eventos entre cortes.

- Fuente: `docs/validation_contract.md`; arXiv:2606.01681, Eq. (28).
- Pregunta: “¿Un K-factor podría cerrar la comparación?” Respuesta: no; solo cambia la normalización.

### 3. Cómo se forma el DV

Pythia transporta/decide la posición de decaimiento del LLP. El análisis usa esa posición y sus productos cargados para exigir volumen fiducial, `Rxy > 4 mm`, al menos un track con `|d0| > 2 mm`, multiplicidad y masa del DV. Después aplica eficiencias parametrizadas.

- Fuente: arXiv:2606.01681, Sec. III; arXiv:2301.13866.
- Matiz: la escala radial depende de `βγcτ`; masa y vida media no bastan sin el boost y los BR.

### 4. Qué hacen los jets

Los jets sirven para trigger y regiones de señal, y pueden provenir de ISR o del decaimiento hadrónico. El desplazamiento no lo prueba el jet: lo prueban los tracks y la posición del decaimiento.

- Frase a repetir: “Los jets permiten registrar y seleccionar; los tracks forman el DV”.

### 5. Qué hicimos

Cuatro logros: upstream congelado, stack HEP verificado, ejecutable compilado/smoke técnico, resultado upstream convertido en una referencia comparable. La consecuencia correcta es que la infraestructura está lista para producir una reproducción; no que el benchmark ya esté reproducido.

- Fuente local: `technical_status_es.md` y reportes M1/M2 citados por el paquete.
- GitHub: el último commit remoto consultado (`220f719`, 11-07-2026) es anterior al paquete local del 15-07-2026. No mostrarlo salvo pregunta de provenance.
- Pregunta: “¿Ya corrió strong-bm1?” Respuesta: no con nuestras tres muestras; todavía falta el cutflow local.

### 6. Por qué strong-bm1

Definir el nombre: `bm1` es benchmark 1; `strong` es producción fuerte de pares de gluinos; el neutralino es el LLP de la referencia SUSY. Ninguno pertenece al modelo escalar. Sirven para proteger la cadena antes de cambiar el PDG y la topología.

- Valores upstream recuperados: 0/1/2 partones; 10.000 eventos por multiplicidad; masas 2000/850 GeV; CKKW-L 500 GeV.
- No afirmar que 0,01 ns fue recuperado exactamente: el paquete lo clasifica como inferido.

### 7. Tres objetivos

No mezclar: (1) validar el recast público con strong-bm1; (2) reproducir un benchmark de arXiv:2606.01681; (3) reinterpretar nuestros puntos 2HDM. Son dependientes, pero producen evidencia distinta.

### 8. Niveles de reproducción

Lo localmente validado es técnico. El cutflow es una referencia extraída. Podemos reconstruir una producción estadística completa con SLHA, cards y seeds propios. No podemos prometer identidad bit a bit sin activos históricos.

- Pregunta: “¿Una configuración reconstruida sigue siendo útil?” Respuesta: sí, si queda declarada y se compara estadísticamente sin llamarla recuperación exacta.

### 9. Resultado upstream

Las barras son acumulativas. High-pT y trackless llegan a aproximadamente 30% de aceptación. Tras las eficiencias, high-pT queda en 26,6%, mientras trackless cae a 0,022%, equivalente a 2,052 eventos ponderados. Esa última cifra requiere cautela estadística. El próximo gráfico debe añadir un segundo conjunto de barras local.

- Valores completos: high-pT `A=29.71822%`, `Aε=26.60133%`, 2520.908 ponderados. Trackless `A=29.74913%`, `Aε=0.02165427%`, 2.052094 ponderados. Total inicial 9476.625.
- No inventar incertidumbres.
- Pregunta: “¿Este gráfico es resultado nuestro?” Respuesta: no; es la referencia upstream que debemos reproducir.

### 10. Paper escalar

El paper especifica topología, modelo fenomenológico, rango 65–250 GeV, benchmarks, cadena de simulación, selección DV, cutflows y límites. Dice que construye un UFO con FeynRules/NLOCT, genera LO con MG5, aplica `K=1.6`, shower/hadronización con Pythia8 y reconstruye jets anti-kT `R=0.4`. Widths y BR provienen de 2HDMC modificado.

No identificamos entre los activos públicos consultados el UFO exacto, sources FeynRules/NLOCT, cards, versiones completas, seeds o LHE. Los BR aparecen gráficamente y no como tabla numérica completa. La formulación defendible es “podemos reconstruir”, no “el paper entrega”.

- Fuente primaria: arXiv:2606.01681v1, Eqs. (1), (27)–(28), Figs. 1–5, Tables 1–2.
- Nota práctica: el HTML de arXiv pierde algunos símbolos matemáticos; extraer valores exactos del PDF/TeX antes de generar.

### 11. Paquete A/B ejecutable

La comparación usa el mismo punto físico en ambos lados. A conserva los umbrales trackless originales y las eficiencias parametrizadas de evento y vértice. B usa los umbrales 90/65/55 GeV de la estrategia modificada, elimina el requisito adicional de jet desplazado y aplica solo la eficiencia de vértice.

El paquete contiene SLHA, cards Pythia, un LHE toy determinista, un control neutralino, un parche contra el commit upstream congelado y un proxy que funciona sin el stack HEP. El LHE toy prueba conexiones y formatos; no es una muestra MadGraph ni representa la distribución de `gg→h*→SS`.

- Punto toy común: `mS=250 GeV`, `ctau=5.1 mm`, `PDG=9900035`.
- Anchura consistente: `Gamma=3.869×10^-14 GeV`.
- No presentar los BR ilustrativos como valores del paper o del scan 2HDM.

### 12. Resultado A/B de orden de magnitud

Las eficiencias visibles son valores directos de Table II. Para 139 fb^-1 y tres eventos, `sigma3=0.0216/epsilon fb`. La mejora B es prospectiva; solo A corresponde a la selección Run 2 existente.

- 100 GeV, 290 mm: A `2.1e-3`, B `1.5e-2`; sigma A para tres eventos `10.3 fb`.
- 170 GeV, 55 mm: A `1.2e-2`, B `5.5e-2`; sigma A `1.80 fb`.
- 250 GeV, 5.1 mm: A `2.9e-2`, B `1.1e-1`; sigma A `0.74 fb`.
- No multiplicar nuevamente por BR: las eficiencias de Table II ya incluyen la mezcla de decaimientos del paper.

### 13. Canales

`bb`, `gg` y `WW/ZZ` hadrónicos son compatibles. `Zγ` solo podría servir cuando el `Z` decae hadrónicamente; eso no está validado. `γγ` no forma por sí solo un DV multitrack y exige una búsqueda distinta de fotones no prompt.

- No afirmar eficiencia demostrada para ningún canal propio.

### 14. Mapa y cierre

`dihiggs`/`dihiggs_boundary` producen y filtran puntos físicos; `dihiggs_hep_cross` debe producir UFO/eventos/sección eficaz; `dihiggs_llp_recast` consume el punto y los eventos y devuelve cutflows y `A×ε`; el paper combina tasa y respuesta. El recast no hace el scan ni reemplaza MadGraph.

El próximo resultado verificable es un cutflow local de strong-bm1 comparado con upstream. Pedir solo tres decisiones: reconstrucción documentada, tolerancia y primer benchmark escalar.

## Matriz focalizada del paper escalar

| Elemento | Publicado explícitamente | Inferible | Reconstruible | No disponible entre activos consultados |
|---|---:|---:|---:|---:|
| Proceso `gg→h*→SS` | sí |  | sí |  |
| Definición fenomenológica del modelo | sí, Eq. (1) |  | sí |  |
| Masas benchmark | sí, Table 2 |  | sí |  |
| Mixing angle | sí como parámetro/benchmarks |  | sí | outputs exactos de scan |
| Widths y proper lifetime | relación y benchmarks | valores intermedios | sí con implementación declarada | outputs exactos de 2HDMC modificado |
| Branching ratios | curvas en Fig. 1 | valores aproximados de la figura | sí | tabla numérica completa |
| UFO | se declara su construcción | estructura desde Eq. (1) | sí, equivalente | archivo exacto |
| FeynRules/NLOCT | paquetes declarados | implementación | sí | source exacto |
| Cards MG5/run/Pythia | cadena descrita | configuración parcial | sí, propias | cards exactas |
| Versiones de software | nombres de paquetes |  | fijables | conjunto completo de versiones |
| Seeds |  |  | nuevas seeds | seeds originales |
| LHE | se declara su uso |  | muestras nuevas | muestras originales |
| Algoritmo de jets | anti-kT, R=0,4 |  | sí |  |
| Selección DV | sí, Sec. III |  | sí |  |
| Mapas de eficiencia | funciones ATLAS citadas |  | congelables desde fuente oficial | modificaciones privadas, si existen |
| Cutflows | sí, Table 2 |  | sí | evento-a-evento original |
| Límites finales | sí, Figs. 4–5 | digitalización | sí con hipótesis declaradas | arrays numéricos completos |

## Preguntas más probables y respuestas breves

1. **¿Ya reprodujimos el benchmark?**
   No. Validamos compilación/entorno y estructuramos la referencia upstream; faltan eventos propios y un segundo cutflow.

2. **¿Por qué usar una referencia SUSY si buscamos un escalar?**
   Porque prueba la implementación pública sin cambiar su física. El neutralino no entra al modelo final; es una línea base de regresión.

3. **¿Qué obtendremos después de la reunión?**
   Primero, un cutflow local de strong-bm1 comparado con upstream. Solo después, un benchmark escalar completo y, finalmente, `A×ε` para puntos 2HDM.

## Frases que no deben usarse

- “Ya reproducimos el cutflow/paper/2HDM.”
- “El gráfico es nuestro resultado.”
- “El paper publica las cards/UFO exactos.”
- “`Zγ` ya tiene eficiencia demostrada.”
- “Los jets contienen el desplazamiento.”
- “Un K-factor arregla la validación.”
