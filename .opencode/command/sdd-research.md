---
description: Arranca un caso de uso: investiga el contexto heredado y devuelve el informe para diseñar
agent: plan
---

Iniciá el flujo spec-driven para el caso de uso: **$ARGUMENTS**

## Pasos

1. **Leé el CU.** Buscá `$ARGUMENTS` en `docs/CASOS_DE_USO.md`. Extraé objetivo, actores,
   precondiciones, postcondiciones, flujo principal, flujos alternativos y **criterios de
   aceptación**. Los criterios de aceptación son el checklist de terminado de todo lo que sigue.

2. **Leé `AGENTS.md`.** Confirmá que el CU no contradice ninguna decisión de alcance. Si
   contradice alguna (por ejemplo, si un CU stray que pide roles), **frená y avisame**.

3. **Delegá la investigación** al subagente `spec-research`, pasándole el CU. Pedile
   explícitamente que contraste con `../donata-deco` y que devuelva el delta exacto entre lo
   heredado y lo pedido.

4. **Revisá el informe** contra estas preguntas antes de seguir:
   - ¿Están las 10 invariantes de negocio verificadas para este CU?
   - ¿Hay algún caso borde heredado que el CU no menciona pero que hay que conservar?
   - ¿La investigación tiene fuentes (archivo:línea) o está lleno de conjeturas?
   - ¿Apareció alguna pregunta abierta que necesite respuesta mía?

5. **Presentame un resumen** de máximo 15 líneas: qué hay que construir, qué se reutiliza del
   sistema anterior, qué es nuevo, y qué decisiones necesito tomar antes de diseñar.

No diseñes ni implementes todavía. El siguiente paso es `/spec-design`.
