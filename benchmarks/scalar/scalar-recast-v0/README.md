# scalar-recast-v0

Primera arquitectura reconstruida para estudiar `gg -> h* -> S S` con un LLP
escalar. No es una tarjeta física completa ni autoriza generación.

```text
classification: RECONSTRUCTED
generation_status: NOT_RUN
physics_validation: NOT_RUN
```

El neutralino pertenece sólo a la baseline SUSY usada para validar el recast.
Este benchmark lo reemplaza conceptualmente por `S`, pero el código upstream
permanece intacto y todavía selecciona LLP por PDG hardcoded. Todos los valores
que dependen del modelo (UFO, PDG, masa, width, lifetime, acoplamientos y BR)
siguen como `TODO`.

Contenido:

- `physics_contract.yaml`: campos, estados y condiciones de generación;
- `assumptions.yaml`: límites conocidos de la reinterpretación;
- `decay_channels.yaml` y `channel_applicability.csv`: utilidad por canal;
- `cards/`: formato esperado de inputs, no cards ejecutables.

No iniciar generación hasta seleccionar el UFO correcto, fijar PDG/masa,
aprobar lifetime o width coherentes, declarar BR completos, parametrizar el PDG
en una capa propia y cerrar Gate B seguido por la regresión SUSY.
