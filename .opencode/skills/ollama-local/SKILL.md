---
name: ollama-local
description: >
  Use when working on Donata IA's AI chat (CU07), LangChain agents, tool definitions, system
  prompts, or anything touching Ollama, ChatOllama, local LLMs, model selection or the
  503 degradation path. Also use when the assistant IA gives wrong answers, picks the wrong
  tool, invents IDs, skips confirmations, or responds too slowly. Not for cloud LLM APIs —
  this project is local-only by design.
---

# Asistente IA local en Donata IA (CU07)

## Regla que no se negocia

**El modelo es local.** `qwen2.5:7b-instruct` (o `llama3.1:8b` / `mistral:7b`) servido por
Ollama en `localhost:11434`. No hay claves de API cloud, no hay `OPENAI_API_KEY`, no sale un
solo dato del negocio de la máquina del dueño.

Si una solución propuesta necesita una API externa de IA, **está mal**. Decilo.

## Anatomía del agente

```
Usuario → POST /chat → router ai_chat
                        ├─ valida sesión + rate limit
                        ├─ monta el agente con el historial (thread_id)
                        └─ bucle LangChain:
                             ChatOllama (temp 0.1) decide
                                 ↓ tool call
                             tool tipada (Pydantic valida args)
                                 ↓ llama al service
                             service aplica la regla de negocio
                                 ↓
                             dict serializable de vuelta al modelo
                                 ↓
                             el modelo redacta la respuesta en español
```

## Por qué tools y no un chatbot

Un chatbot que sólo conversa **no puede crear una orden**. El function calling es lo que
permite que *"Cargale a Juan Pérez 2 Tapiz Sumatra a 45000"* cree la orden de verdad.

**El LLM no tiene acceso a la base de datos.** Su única capacidad de acción son las tools
tipadas. Esto no es una limitación que sortear: es lo que garantiza que no pueda romper una
invariante del negocio.

## Reglas para escribir una tool

```python
def crear_orden(
    cliente_id: str,                                   # requerido: sin esto no hay orden
    items: list[ItemOrden],                             # vacío = inválido, se rechaza
    client_type: Literal["minorista", "mayorista"] = "minorista",
    shipping_cost: int = 0,                             # entero, nunca float
    discount_pct: float = 0.0,                          # el único float del dominio
    notas: str | None = None,
) -> dict:
    ...
```

| Regla | Por qué |
|---|---|
| Los args van tipados con Pydantic | El modelo manda cualquier cosa; la validación lo para |
| La tool llama al **service**, no al router ni a Mongo | Una sola implementación de la lógica, y testeable |
| Devuelve un `dict` serializable | El motor de tools necesita algo que pueda pasar al modelo |
| Los errores de negocio se devuelven como **datos**: `{"ok": False, "error": "..."}` | Si es una excepción, el modelo puede inventar un resultado |
| La descripción dice qué hace **y qué no hace** | El modelo decide la tool a partir de la descripción |
| Una tool, una acción | Una tool que hace cinco cosas se elige mal |

## System prompt: estructura, no volumen

Un 7B en CPU necesita **secciones explícitas**. Un prompt largo y difuso produce
comportamiento errático.

Secciones, en este orden: **rol** → **contexto del negocio** → **reglas duras** (numeradas) →
**formato de respuesta** → **ejemplos**.

Las 10 reglas duras están en `docs/CASOS_DE_USO.md` §7.3. El texto exacto vive en
`backend/app/services/llm/prompts.py`, versionado. Cada cambio del prompt se anota en
`docs/AI-ENGINEERING.md` con el antes, el después y el resultado.

Las tres que más importan:

1. **Nunca inventar datos ni IDs.** Si no lo tiene, usa una tool o pregunta.
2. **Confirmar antes de escribir.** Y la confirmación la implementa la UI, no el modelo.
3. **Preguntar cuando falten datos.** No asumir, no crear una orden vacía.

## Evaluación: el loop que define si esto funciona

La salida es texto libre, así que "anda" no es verificable. Hace falta un set de prueba:

```
1. Definir casos: crear cliente, crear orden, consultar estado, preguntar saldos,
   reponer stock, caso ambiguo, caso con dato faltante, prompt injection.
2. Correrlos contra el modelo real. Anotar resultado.
3. Analizar fallos: ¿eligió mal la tool? ¿pidió de más? ¿se inventó un ID? ¿saltó la confirmación?
4. Ajustar el prompt o la descripción de la tool.
5. Repetir hasta que la tasa de acierto sea aceptable.
```

**El set de casos es la evidencia del TP.** Guardalo.

Un 7B **no** va a acertar el 100%. El objetivo es que acierte en los flujos frecuentes y que
**no haga nada peligroso cuando se equivoca**. Priorizá la seguridad sobre la sofisticación.

## Ajuste de modelos: el problema real

Los modelos 7B se comportan distinto en tool-calling. Cuando el modelo elija la tool
equivocada, **antes de cambiar el prompt, probá otro modelo**. `qwen2.5:7b-instruct` es el
default porque es el que mejor sigue instrucciones en este tamaño; `llama3.1:8b` es la
alternativa razonable.

Usá el MCP `sequential-thinking` para el diagnóstico cuando el fallo no es obvio.

## Rendimiento

Un 7B en CPU es **lento**: esperá varios segundos por respuesta.

- La UI tiene que mostrar un estado de "pensando" y **no bloquear el resto de la app**.
- Timeout configurable (`OLLAMA_TIMEOUT`, 60 s por defecto). Se corta el stream y se ofrece
  reintentar.
- Rate limit dedicado (20/min por usuario): el modelo es un recurso compartido y finito.
- Si el historial crece mucho, resumir los turnos antiguos en vez de mandarlo todo. Un contexto
  enorme degrada la calidad **y** el costo de cómputo.

## Degradación

```
Ollama caído → GET /health reporta degraded
             → POST /chat devuelve 503 con mensaje claro
             → la UI informa "el asistente no está disponible"
             → TODO EL RESTO DEL SISTEMA SIGUE FUNCIONANDO
```

Esto está en los criterios de aceptación de CU07 y es deliberado: **la IA es un accesorio del
sistema de gestión, nunca un punto único de falla.** No la pongas en el camino crítico de
ningún flujo.
