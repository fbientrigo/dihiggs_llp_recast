# Notas del presentador

Catorce slides. No leer las viñetas: cada slide tiene una idea que se defiende
hablando. Las cifras exactas están en el one-pager si alguien las pide.

## 1. Un escalar de larga vida puede decaer dentro del tracker

Buscamos un escalar `S` de larga vida producido en `gg -> h* -> SS`. Si vive lo
bastante, decae a milímetros o centímetros del punto de colisión, ya dentro del
tracker, y sus productos cargados pueden formar un vértice desplazado. La escala
del desplazamiento en el laboratorio es beta-gamma por c-tau: el boost y la vida
media deciden si el decaimiento cae donde lo podemos ver.

- Transición: esa dependencia es justo lo que obliga a validar la cadena antes de
  reinterpretar nada.
- Pregunta probable: ¿basta con masa y vida media?
- Respuesta: no; también entran boost, producción, canales de decaimiento, tracks
  y actividad hadrónica.

## 2. Compilar el análisis no equivale a reproducir su física

Un recast aproxima una selección publicada; no es ATLAS. Lo que mide es
aceptación por eficiencia, que es una fracción de la muestra. La sección eficaz
entra después, como normalización, y por eso un factor K no puede arreglar un
cutflow: mueve la escala global, no mueve eventos entre cortes.

- Transición: entonces conviene mirar el observable central, el vértice.
- Pregunta probable: ¿un K-factor podría cerrar Gate B?
- Respuesta: no; Gate B compara paso a paso, y ahí la geometría y las eficiencias
  no se reescalan.

## 3. El DV se reconstruye con tracks, no con jets

El análisis parte de la posición de decaimiento del LLP: exige región fiducial y
Rxy sobre 4 mm, calcula el d0 de los tracks y pide al menos uno sobre 2 mm, cinco
productos cargados seleccionados y masa de vértice sobre 10 GeV. Todo el poder de
la búsqueda está en esos tracks desplazados.

- Transición: los jets cumplen otro papel, complementario.
- Pregunta probable: ¿cómo entra el boost?
- Respuesta: la longitud de vuelo escala con beta-gamma por c-tau, y eso cambia la
  población radial de vértices, o sea cuántos caen en la región fiducial.

## 4. Los jets seleccionan el evento; los tracks forman el DV

Los jets pueden venir de ISR o del decaimiento hadrónico del LLP. Importan porque
sin ellos no hay trigger ni región de señal: hacen visible el evento. Pero un jet
no prueba desplazamiento. Conviene decirlo explícitamente porque es la confusión
más común con estas búsquedas.

- Transición: ambas piezas se juntan en la cadena completa.
- Pregunta probable: ¿un evento con muchos jets tiene DV?
- Respuesta: no necesariamente; hace falta el vértice desplazado con d0,
  multiplicidad y masa.

## 5. Gate B valida la cadena completa, no el ejecutable

MadGraph fija el proceso y el merging; Pythia hace shower, hadronización y
decaimientos; FastJet y el detector de juguete construyen jets; el análisis forma
los DV y el cutflow. Cada interfaz tiene su propia forma de fallar, y por eso
pedimos cards, seeds, versiones y checksums en un manifest.

- Transición: para poder localizar un fallo necesitamos primero una referencia.
- Pregunta probable: ¿por qué no ir directo al escalar?
- Respuesta: sin línea base, un desacuerdo no se puede atribuir; no sabríamos si
  viene de generación, shower, detector o de nuestra adaptación.

## 6. Por qué usamos primero la referencia SUSY

strong-bm1 es la muestra que distribuye upstream: pares de gluinos con 0, 1 y 2
partones, 10.000 eventos por multiplicidad, 2000/850 GeV y merging a 500 GeV. Su
LLP es un neutralino. Conviene ser claro: el neutralino no es parte de nuestro
modelo, es sólo la línea base que nos permite comprobar que la cadena funciona.
Después el escalar ocupa ese lugar.

- Transición: y hoy esa validación sigue bloqueada.
- Pregunta probable: ¿el benchmark escalar tiene neutralinos?
- Respuesta: no; sólo documenta `S`. SUSY queda aislado como línea base de
  regresión.

## 7. Qué está listo y qué sigue bloqueado

Gate A está validado: el ejecutable compila, enlaza y arranca. Pythia 8.308,
FastJet 3.4.0 y MadGraph 3.5.3 ya están instalados y funcionan; el único bloqueo
real de MadGraph para producción física es el UFO. El parche A/B aplica y compila
sobre el commit congelado, y ambos modos ejecutan. Pero la parte que sí falta es
importante: la vida del LLP no se propaga en Pythia, así que ninguna etapa DV
produce nada todavía, y sigue faltando el SLHA exacto de bm1 y sus tres LHE. Sin
eso no hay Gate B.

- Transición: y ese mismo paquete A/B ya deja ver dónde está el límite exacto.
- Pregunta probable: ¿compilar prueba la física?
- Respuesta: no; prueba headers, linking y arranque. No prueba eventos, merging ni
  eficiencia de vértices.

## 8. La bifurcación A/B funciona; el transporte LLP aún no

Con un input toy idéntico (escalar de 250 GeV, c-tau 5,1 mm), la selección
trackless original acepta 25,0% de los jets; la modificada, 51,6%. Es la prueba de
que la rama A/B está bien conectada y que ambas estrategias divergen en la
dirección esperada. Pero de ahí en adelante todos los cortes del DV dan cero:
Rxy, d0, multiplicidad de tracks, masa del vértice, todo cero, en A y en B por
igual. Y el control con neutralino, que sí trae parámetros SLHA bien formados,
muestra la misma patología: no es un problema del PDG del escalar ni del parche.

Lo que vemos en el event record es que los LLP importados por SLHA llegan con
`status = -22`, `tau = 0` y `rDec = 0`: Pythia los trata como resonancias que
decaen en el origen, no como partículas de vida larga. Probamos cinco arreglos
directos (forzar `isResonance=false` tras `init()`, declarar la partícula de forma
nativa evitando SLHA, combinar ambos con `resonanceDecays=off`, entre otros) y
los cinco fallan de la misma forma o parecida. El diagnóstico apunta a una
ejecución escalonada de Pythia, separando la asignación de vida antes del shower
completo (`forceHadronLevel()` en dos pasos); no vale la pena entrar en ese
detalle en la slide, pero puede explicarse aquí si preguntan.

- Transición: por eso el próximo número que perseguimos no es de eficiencia,
  es de vida media.
- Pregunta probable: ¿entonces el 51,6% es un resultado de física?
- Respuesta: no; es un unit test de selección de jets sobre un input de juguete.
  Confirma que el código A/B funciona, nada sobre el DV.

## 9. El objetivo numérico que Gate B tendrá que igualar

Esta figura transcribe el cutflow que distribuye upstream; no es nuestro. High-pT
termina en 26,6 % de aceptación por eficiencia. Trackless cae hasta 0,022 %, que
son unos 2 eventos ponderados: por eso la escala es logarítmica y por eso ese
punto hay que reportarlo con conteo absoluto, no sólo con porcentaje.

- Transición: estos requisitos ya nos dicen qué canales nuestros encajan.
- Pregunta probable: ¿la figura demuestra Gate B?
- Respuesta: no; es el objetivo, no el resultado.

## 10. Dónde aporta este recast a nuestro modelo

bb y gg hadronizan y dan tracks de sobra; WW/ZZ hadrónicos dan alta multiplicidad.
Zgamma sirve sólo si el Z decae hadrónicamente. Gammagamma no: dos fotones no dan
el vértice multitrack que la búsqueda exige. Importante decir que esto es utilidad
potencial, no eficiencia validada.

- Transición: y hay diferencias concretas que hay que controlar antes.
- Pregunta probable: ¿por qué no gammagamma?
- Respuesta: no hay tracks cargados naturales; esa firma pertenece a otro tipo de
  búsqueda.

## 11. Cuatro diferencias que debemos controlar

El código busca neutralinos por PDG hardcoded, así que hoy no vería a `S`. El
paper describe anti-kt R=0.4 y el código usa kt R=0.4. Los fotones entran a
FastJet sin aislamiento dedicado. Y las eficiencias son parametrizaciones
aproximadas, ajustadas a la topología SUSY que las originó, así que nuestros
canales podrían caer fuera de su dominio.

- Transición: el benchmark v0 registra estos límites sin resolverlos todavía.
- Pregunta probable: ¿cambiamos ya el algoritmo de jets?
- Respuesta: no; primero Gate B, y luego cada cambio detrás de una regresión que
  demuestre que la línea base no se movió.

## 12. scalar-recast-v0: arquitectura lista, física pendiente

Ya está la arquitectura: el proceso, la relación Gamma igual a hbar sobre tau, los
formatos, los contratos y la utilidad por canal. Falta todo lo que depende del
modelo: UFO, acoplamientos, PDG, masa, anchura, vida media y BR. Lo llamamos
reconstruido porque organiza nuestros supuestos; no afirma recuperar la card
original ni autoriza generar eventos.

- Transición: y conviene situar esto dentro del proyecto completo.
- Pregunta probable: ¿por qué RECONSTRUCTED y no una card?
- Respuesta: porque una card implicaría valores físicos aprobados, y ésos son
  justamente las decisiones que traemos hoy.

## 13. Dónde encaja este recast en el proyecto

Vale la pena aclarar el reparto: `dihiggs` y `dihiggs_boundary` producen los puntos
2HDM con masa, anchura, c-tau y BR, ya filtrados por teoría y por HiggsBounds/
HiggsSignals. `dihiggs_hep_cross` se encarga de la producción MadGraph y las
secciones eficaces, y define el contrato con el que un punto entra aquí. Este repo
toma ese punto y sus eventos y devuelve aceptación por eficiencia y cutflows. El
paper recoge los resultados. Este repo no explora el espacio 2HDM, no sustituye la
producción ni es el repositorio del artículo.

- Transición: con eso claro, las decisiones que faltan son pocas y concretas.
- Pregunta probable: ¿quién fija el punto físico que entra aquí?
- Respuesta: viene del escaneo 2HDM y de producción, bajo el contrato de punto de
  modelo; nosotros consumimos ese contrato, no lo generamos.

## 14. Tres decisiones y el próximo resultado comprobable

Necesitamos tres cosas de N. Neil: el UFO y el tratamiento de la producción; el
primer punto completo con PDG, masa, vida media o anchura y tabla de BR; y el
criterio exacto de Gate B que habilita la parametrización escalar. Con eso el
trabajo queda acotado: cerrar Gate B, parametrizar sólo PDG y modo, y exigir que
la línea base SUSY siga dando el mismo cutflow antes del primer smoke escalar.

El gate técnico inmediato es más chico que Gate B y va antes: recuperar una
distribución desplazada con `<L3D>` de unos 8,8 mm en el toy de 250 GeV y c-tau
5,1 mm, con una fracción no trivial de LLP terminales por encima de 4 mm. Sólo
con eso resuelto tiene sentido comparar el cutflow DV entre A y B; hoy comparar
ceros contra ceros no dice nada.

- Pregunta probable: ¿cuál es el siguiente resultado demostrable?
- Respuesta: un Gate B documentado sobre strong-bm1, y después una regresión que
  conserve esa línea base al habilitar `S`.

## Preguntas frecuentes: paquete A/B y MadGraph

**¿Entonces el recast funciona?**
El ejecutable y la selección A/B funcionan. La parte que todavía no funciona es
la propagación de la vida del LLP hasta un vértice desplazado, por lo que aún no
tenemos una eficiencia DV.

**¿El 25% a 51,6% es un resultado físico?**
No. Es un unit test de la selección de jets sobre un input toy idéntico.
Demuestra que A y B divergen en la dirección esperada, pero no valida la rama de
vértices.

**¿Qué falta para usar MadGraph?**
MadGraph ya está instalado. Falta el UFO físico y su mapeo validado; para
nuestro 2HDM también falta asegurar el acople de producción h-phi-phi.

**¿Por qué no empezar inmediatamente con el UFO?**
Puede prepararse en paralelo, pero primero conviene cerrar la vida del toy para
no mezclar un defecto de Pythia con uno de generación.
