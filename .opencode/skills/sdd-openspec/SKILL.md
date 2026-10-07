---
name: sdd-openspec
description: >
  Use when working on Donata IA and the task is to plan, design, break down or verify a
  feature, case of use (CU), endpoint, model or refactor — or when the user says "spec-driven",
  "SDD", "sdd-", "diseñá", "planificá" or "task breakdown". Enforces the project's
  spec-first workflow: no implementation before the use case and its acceptance criteria
  are clear. Not for small mechanical edits.
---

# Spec-Driven Development en Donata IA

El proyecto se construye **spec-first**: la especificación precede al código. Esto no es
formalidad — la rúbrica del TP evalúa el proceso de ingeniería, y un CU escrito antes de
implementar es lo que hace que un agente de IA no invente funcionalidad.

## El flujo

```
/sdd-research   →  contexto heredado + delta
/sdd-design     →  modelo de datos, API, servicios, UI, seguridad
/sdd-tasks      →  tareas atómicas con criterio de terminado
/sdd-implement  →  TDD + revisión adversarial + bitácora
```

## Las cinco reglas del flujo

### 1. La especificación es la fuente de verdad

`docs/CASOS_DE_USO.md` manda. Si el código y el documento discrepan, primero se corrige el
documento (con el aval del usuario: es un entregable validado por el docente).

**Cada criterio de aceptación es un checkbox.** No se da por terminado un CU mientras
algún checkbox no se pueda demostrar.

### 2. Un CU por vez

No mezcles dos casos de uso en el mismo cambio. Un commit, un CU, una verificación.
Esto no es purismo: cuando algo falla, el error queda acotado a una unidad y el diagnóstico
es inmediato.

### 3. TDD en el backend

Test que falla → implementación → suite verde. El test es el judge de la respuesta del
agente. Un agente sin tests verificados escribe código plausible pero incorrecto, y el
proyecto hereda bugs que cuestan más que los tests.

### 4. Revisión adversarial antes de terminado

Después de implementar, otro agente pregunta *"¿qué se rompe acá?"*. Encuentra clases de
errores que la implementación inicial no va a ver sola: condiciones de carrera, estados
inconsistentes, validaciones faltantes, casos borde.

Es un loop, no un paso: revisar → corregir → volver a revisar hasta que no salgan hallazgos
relevantes.

### 5. La bitácora se escribe mientras se trabaja

`docs/AI-ENGINEERING.md` se actualiza en cada tarea, no al final. Una bitácora escrita de
memoria tres semanas después no es una bitácora. Y **los fallos son evidencia de proceso**:
un error y cómo se resolvió vale más para la nota que un éxito silencioso.

## Contexto mínimo viable

El patrón que más impacta en la calidad: **decí exactamente qué archivos leer y qué reglas
aplican**, en vez de cargar el repo entero.

Buen prompt:

> Implementá el endpoint de registro de pagos. Aplicá la regla de saldo derivado de
> `AGENTS.md` §3.7 y el patrón de tests de `donata-deco/backend/tests/test_ventas.py`.
> No cambies el esquema de la colección.

Malo:

> Implementá el registro de pagos.

El segundo produce código correcto en el 60% de los casos. El primero, en el 95%. Y la
diferencia se nota más fuerte cuanto más fuerte la regla es específica del dominio.

## Antes de implementar, verificá estas invariantes

Son las que la IA rompe con más frecuencia porque van contra su default:

| Invariante | Cómo la rompe la IA por default |
|---|---|
| Montos en ARS enteros | Usa `float` y agrega `round()` |
| Saldo derivado | Persiste un campo `balance` "para no recalcular" |
| Stock atómico | Lee, valida en Python, y después escribe |
| Producto con proveedor | Lo hace `Optional[str] = None` "por flexibilidad" |
| Sin roles | Agrega `role` por costumbre de un sistema multiusuario |
| Ítems mixtos | Asume que todo ítem referencia un producto |
| Export = listado | Escribe una segunda función de query |

Si un agente propone cualquiera de estas cosas, está proposing algo incorrecto. Corregilo
explícitamente en el prompt.

## Referencias

- `AGENTS.md` — reglas del proyecto. **Leelo primero, siempre.**
- `docs/CASOS_DE_USO.md` — los 10 CU y sus criterios de aceptación.
- `docs/ARQUITECTURA.md` — capas, modelo de datos, decisiones técnicas.
- `docs/PLAN-IMPLEMENTACION.md` — fases, tareas, estado del avance.
- `docs/SEGURIDAD.md` — checklist verificable de controles.
- `docs/AI-ENGINEERING.md` — bitácora (se actualiza en cada tarea).
- `../donata-deco` — el sistema heredado con la lógica ya resuelta. **Portar, no reinventar.**
