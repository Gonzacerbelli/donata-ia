# AI Engineering — Bitácora del proceso

> **Este documento es un entregable evaluado (1 pt documentación + 3 pts esquema de trabajo).**
> No es un informe de resultados: es el registro de **cómo** se construyó el sistema con IA.
>
> **Regla de escritura:** se completa *mientras* se trabaja, no al final. Si recién estás
> escribiendo la entrada de hace dos semanas, no la estás escribiendo bien.

---

## Cómo usar este documento

Por cada tarea relevante, agregar una entrada con esta estructura:

```markdown
### [AAAAMMDD] Tarea <nombre> — <estado>

**Objetivo.** Qué se pidió.

**Contexto dado a la IA.** Qué archivos, reglas y criterios se le dieron al agente
(cuanto más preciso, mejor el resultado).

**Prompt (esencial).** El fragmento del prompt que define el problema.

**Iteración.** Qué devolvió la IA → qué se corrigió → cuántas vueltas.

**Resultado.** Qué quedó hecho, y qué verificación lo prueba.

**Lección.** Qué se aprende para la próxima.
```

---

## 1. Entorno de trabajo

| Aspecto | Configuración | Por qué |
|---|---|---|
| Herramienta principal | **opencode** como CLI de desarrollo asistido | Agentes, comandos, skills y MCP configurables por proyecto |
| Archivo de contexto | `AGENTS.md` en la raíz | Se carga automáticamente en cada sesión: las decisiones del proyecto persisten |
| Framing del trabajo | **Spec-Driven Development** | La especificación precede al código; reduce la deriva entre lo pedido y lo construido |
| Orquestación | Subagentes especializados por dominio | Un agente que hace una sola cosa pega más que uno que hace todo |
| Protocolo | **MCP** para contexto externo | Ver `docs/MCP.md` |
| Revisión | Ciclo de **revisión adversarial** antes de dar por terminado | "Implementá X" seguido de "¿qué se rompe en X?" encuentra errores que la implementación inicial no ve |
| Verificación | Tests como criterio de terminado | Sin test verde, la tarea no está terminada |
| Eficiencia de tokens | Contexto mínimo viable por tarea | Mandar el archivo entero "por las dudas" degrada la calidad de la respuesta |

### 1.1 Reglas del contexto escritas para este proyecto

En `AGENTS.md` se consolidaron las reglas que gobiernan todo el desarrollo:

| Regla | Origen | Por qué importa |
|---|---|---|
| Sin roles de usuario | Decisión del cliente | Evita construir un módulo de autorización que nadie va a usar |
| Producto siempre con proveedor | Decisión del cliente | Sin proveedor no hay reposición posible |
| IA local, nunca cloud | Decisión del cliente | Los datos del negocio no salen de la máquina |
| El LLM sólo usa tools tipadas | Diseño propio | Un modelo con acceso libre a datos puede romper invariantes |
| Montos en ARS enteros | Dominio | Un `float` de pesos introduce errores de redondeo reales |
| Saldo siempre derivado | Dominio | Persistir un campo calculado garantiza que algún día esté desactualizado |
| Stock atómico y auditado | Dominio | El control de concurrencia mal hecho genera stock fantasma |
| Comment-free code | Preferencia | Legibilidad por estructura, no por comentarios |

> **Por qué importa para la nota:** la rúbrica pide "uso correcto de reglas de contexto para
> guiar el desarrollo de la lógica y patrones de diseño". Escribir esas reglas en un archivo
> que la IA carga en cada sesión **es** el mecanismo. La tabla de arriba documenta que hubo
> criterio, no que se copiaron convenciones.

---

## 2. Configuración de agentes (AI Engineering en la práctica)

| Agente | Rol | Por qué existe como agente separado |
|---|---|---|
| `spec-research` | Investiga el código heredado y el contexto antes de implementar | El agente que implementa no debería spendiar su contexto explorando |
| `spec-design` | Diseña la solución técnica de un CU | Diseño e implementación requieren modos de razonamiento distintos |
| `spec-tasks` | Descompone el diseño en tareas atómicas y verificables | Evita tareas de 8 horas que no se pueden verificar |
| `backend-engineer` | Implementa en FastAPI con las convenciones del proyecto | Contexto acotado al dominio backend |
| `frontend-engineer` | Implementa en React con las convenciones del proyecto | Contexto acotado al dominio frontend |
| `ai-engineer` | Agente de LangChain, tools y prompts del chat | El chat es un subsistema particular: necesita un prompt y una evaluación propios |
| `reviewer` | Revisión adversarial: "¿qué se rompe acá?" | Un revisor sin contexto de implementación encuentra más que el autor |
| `security-auditor` | Verifica la lista de `docs/SEGURIDAD.md` | La seguridad se audita contra una lista, no de memoria |

**El patrón:** el agente principal **delega**, no hace todo. El agente especializado entra con
contexto mínimo y devuelve un resultado acotado. Esto es orquestación, que es lo que evalúa la
rúbrica.

---

## 3. Técnicas de prompting aplicadas

| Técnica | Dónde se aplica | Por qué funciona |
|---|---|---|
| **Contexto explícito** | Cada tarea declara CU, reglas aplicables y criterios de aceptación | La IA no adivina el dominio: se lo decís |
| **Restricciones negativas** | *"No agregar roles"*, *"no usar API cloud"*, *"no comentar el código"* | Previene las decisiones por defecto que la IA haría mal |
| **Ejemplos** | System prompt del chat, schemas | El modelo de 7B aprende la forma por imitación, no por descripción |
| **Estructuración** | System prompt en secciones (rol / contexto / reglas / formato / ejemplos) | Un prompt difuso produce comportamiento errático en modelos chicos |
| **Temperatura baja para datos** | `OLLAMA_TEMPERATURE = 0.1` | Los datos de negocio no admiten creativity |
| **TDD como prompt** | "Escribí primero el test que falla" | Ancla el comportamiento esperado antes de la implementación |
| **División en subtareas** | Un CU → varias tareas atómicas | Reduce la probabilidad de que una respuesta larga se desvíe |
| **Reformulación tras el fallo** | Iteración | Si dos intentos fallan, cambiar el prompt es más barato que insistir |

---

## 4. Loops de autocorrección

### 4.1 Loop de implementación (el principal)

```
1. Se escribe el test que falla          → la IA lo hace
2. Se corre pytest                       → el fallo es la evidencia
3. Se implementa hasta que pase          → la IA itera
4. Se corre la suite completa            → no romper lo que ya andaba
5. Commit sólo con la suite verde        → el estado del repo es siempre coherente
```

**Por qué importa:** un agente de IA con tests no verificados escribe plausible pero incorrecto.
El test es el judge.

### 4.2 Loop de revisión adversarial

```
1. La IA implementa
2. Se la pregunta a otro agente: "¿qué se rompe acá?"
3. Se corrigen los problemas encontrados
4. Se repite hasta que la revisión no encuentra nada relevante
```

Este loop encuentra clases de errores que la implementación inicial no va a ver sola:
condiciones de carrera, casos borde, validaciones faltantes, estados inconsistentes.

### 4.3 Loop de evaluación del chat IA

El chat es lo más difícil de verificar, porque la salida es texto libre. El loop:

```
1. Definir un conjunto de casos (set de preguntas de prueba)
2. Correrlos contra el modelo real y anotar el resultado
3. Analizar los fallos: ¿eligió mal la tool? ¿pidió los datos de más?
   ¿se inventó un ID? ¿se saltó la confirmación?
4. Ajustar el prompt o la descripción de la tool
5. Repetir hasta que la tasa de acierto sea aceptable
```

**Este loop es el más importante del TP.** Un modelo de 7B en CPU no va a acertar el 100% de
las veces; lo que se busca es que acierte en los flujos frecuentes y **que no haga nada
peligroso cuando se equivoca**. El set de casos de prueba queda como evidencia.

---

## 5. Registro de iteraciones

<!-- Agregar las entradas acá, de la más reciente a la más antigua. -->

### [20260926] Especificación de los 10 casos de uso — completado

**Objetivo.** Definir los 10 casos de uso funcionales del sistema para presentarlos a
validación docente antes de desarrollar (requisito de la rúbrica).

**Contexto dado a la IA.** Rúbrica del TP, consignas del curso, y el sistema ya existente en
`donata-deco` (Streamlit + FastAPI + MongoDB) como fuente de las reglas de negocio reales.

**Prompt (esencial).** Definir 10 casos de uso cubriendo autenticación con Google, dashboard
con métricas y filtros de fechas, ABMs de productos/clientes/órdenes/proveedores, chat IA,
stock, notificaciones y exportación; cada uno con alcance frontend **y** backend.

**Iteración.** 1a versión → se agrega restricción de seguridad explícita y se eliminan los
roles de usuario (decisión del cliente). 2a versión → se incorpora que el producto siempre
tiene proveedor. 3a versión → el chat pasa a modelo local 7B. Cuarta → revisión de coherencia
interna (los criterios de aceptación de cada CU deben ser verificables con lo implementado).

**Resultado.** `docs/CASOS_DE_USO.md` + `docs/CASOS_DE_USO.pdf` (21 páginas, generado con
`scripts/md2pdf.py`, verificado).

**Lección.** Los casos de uso que se escriben **antes** de la implementación son un contrato
mucho más fuerte que los que se escriben después. Obligan a decidir antes de tener la tentación
de "después lo hago".

---

## 6. Estructura del README final

El `README.md` de la raíz tiene que ser la bitácora que pide la rúbrica. Estructura
propuesta:

```markdown
# Donata IA
1. Qué es el sistema (con captura de pantalla)
2. Arquitectura (diagrama + stack + por qué)
3. Los 10 casos de uso (enlace a docs/CASOS_DE_USO.md) + estado de cada uno
4. Puesta en marcha (docker compose up, variables de entorno, modelo de Ollama)
5. AI Engineering
   5.1 Herramientas y configuración del entorno
   5.2 Cómo se estructuró el contexto (AGENTS.md, agentes, skills)
   5.3 Prompts clave que hicieron que la implementación funcionara
   5.4 Iteraciones: qué falló y cómo se resolvió
   5.5 Loops de autocorrección
6. MCP: servidores, configuración y su rol
7. Seguridad
8. Estructura del repositorio
9. Tests
```

Las secciones 5 y 6 se alimentan de este documento y de `docs/MCP.md`. **No duplicar
contenido**: acá va el detalle, en el README se resume y se enlaza.

---

## 7. Anti-patrones evitados

| Anti-patrón | Por qué se evitó |
|---|---|
| Aceptar la primera respuesta sin verificar | Escribir plausible ≠ funcionar. El test es el judge |
| Un solo agente haciendo todo | El contexto mezclado degrada la calidad de cada parte |
| Contexto de 50 archivos "por las dudas" | Ruido: el agente pierde el hilo entre lo relevante y el ruido |
| Prompt sin restricciones explícitas | La IA aplica sus defaults, que no son los del dominio |
| Documentar al final | Una bitácora escrita de memoria no es una bitácora |
| Ignorar los fallos | Un fallo documentado vale más para la nota que un éxito silencioso |
| Meter la lógica de negocio en los componentes de React | Se pierde en el refactor y no se testea |
