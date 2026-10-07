# 3. Búsqueda vectorial local con colecciones separadas

**Estado:** Aceptada
**Fecha:** 20261005
**Contexto:** El asistente necesita dos cosas distintas: (a) responder consultas sobre las reglas
del negocio a partir de documentación, y (b) encontrar productos por descripción difusa. La
restricción dura es que **ningún dato del negocio sale de la máquina**.

## Alternativas consideradas

1. **Vector store cloud** (p. ej. un servicio de embeddings administrado) — descartada por la
   restricción de IA 100 % local.
2. **Una sola colección** para manual + catálogo — simple, pero mezcla conocimiento estable con
   datos que cambian: cada reindexado del catálogo arriesga la base de conocimiento.
3. **Dos colecciones locales** (elegida): `donata_kb` (manual) y `donata_products` (catálogo).

## Decisión

Se usa **Chroma** embebido con **embeddings HuggingFace** (`all-MiniLM-L6-v2`, 384 dims),
ejecutados en `to_thread` para no bloquear el event loop. El manual se indexa en `donata_kb` con
una ingesta idempotente (`scripts/ingest_kb.py`, flag `--force`); el catálogo se sincroniza en
`donata_products`. La sintaxis de Chroma exige nombres de colección de al menos 3 caracteres.

## Consecuencias

**A favor:** todo local y reproducible; el reindexado del catálogo no toca el manual; el
resultado es verificable (`¿Cómo se calculan los precios mayoristas?` se responde desde el manual).
**En contra:** los embeddings se descargan la primera vez (se cachean en `data/hf_cache`) y en
CPU son más lentos que un servicio dedicado.
**Impacto en el código:** `services/llm/vector_store.py`, `services/llm/rag.py`,
`scripts/ingest_kb.py`, montaje `data/hf_cache` en `docker-compose.yml`.