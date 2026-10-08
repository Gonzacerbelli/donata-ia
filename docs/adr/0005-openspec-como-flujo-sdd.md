# 0005. OpenSpec como flujo Spec-Driven

**Estado:** Aceptada
**Fecha:** 20261008
**Contexto:** El proyecto se declaró Spec-Driven desde F0 con un flujo propio (skill
`sdd-openspec`, comandos `/sdd-*`, subagente `spec-research`, carpeta `specs/`), pero el flujo
nunca se ejecutó: `specs/` quedó vacía desde el commit inicial y los 10 casos de uso se
implementaron directo desde `docs/CASOS_DE_USO.md`. No había validación de formato, ni ciclo
propuesta→implementación→archivado, ni evidencia trazable de spec→código. Además el flujo propio
tenía inconsistencias internas: `/sdd-tasks` declarado pero inexistente y punteros rotos a
`/spec-design` y `/spec-tasks`.

## Alternativas consideradas

1. **Flujo propio sin herramienta** — coste cero, pero sin validación, sin archive y con las
   inconsistencias ya detectadas.
2. **OpenSpec (`@fission-ai/openspec`)** — herramienta con CLI (`validate`, `list`, `archive`),
   specs vivas + propuestas versionadas e integración nativa con opencode (skills `openspec-*`
   y comandos `/opsx-*`).
3. **Convivencia de ambos** — dos fuentes de verdad sobre el proceso, riesgo de que diverjan.

## Decisión

Adoptar OpenSpec como único flujo Spec-Driven:

- `openspec init --tools opencode` con profile `custom` (workflows: propose, explore, apply,
  update, sync, archive, verify, onboard).
- `openspec/config.yaml` concentra `context` (idioma, fuentes de verdad, comandos de
  verificación, invariantes de negocio), `rules` por artefacto y `operations` para apply/archive.
- Backfill as-built: `openspec/specs/<capability>/spec.md` documenta los 10 CU construidos,
  con los endpoints reales; los desvíos respecto de `docs/CASOS_DE_USO.md` se anotan como
  pendientes (ej. el catálogo de tools del CU07), nunca como requisitos falsos.
- Se deprecian el skill `sdd-openspec`, los comandos `/sdd-*`, el subagente `spec-research` y
  la carpeta `specs/`. `docs/CASOS_DE_USO.md` sigue siendo el entregable validado y no se toca.

## Consecuencias

**A favor:** specs con validación de formato; ciclo propose→apply→verify→archive como evidencia
de proceso para la rúbrica; una sola casa para el flujo; las invariantes viajan en el contexto de
cada propuesta.

**En contra:** otro formato que aprender; los artefactos de proceso viven en `openspec/` además
de los documentos de siempre (`docs/`), y hay que mantenerlos al día en cada archive.

**Impacto en el código:** `.opencode/skills/openspec-*`, `.opencode/commands/opsx-*`,
`openspec/config.yaml`, `AGENTS.md` §7-§8, `opencode.json` (agentes `spec-*` eliminados),
`README.md` §5, `docs/adr/README.md`.
