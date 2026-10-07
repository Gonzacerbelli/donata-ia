---
description: Implementa un caso de uso guiando la IA con TDD y registra la bitácora de AI Engineering
agent: build
---

Implementá: **$ARGUMENTS**

## Contexto obligatorio

Leé antes de escribir código:
1. `AGENTS.md` (raíz) — reglas de negocio y decisiones de alcance.
2. `backend/AGENTS.md` y/o `frontend/AGENTS.md` según lo que toque.
3. La sección del CU en `docs/CASOS_DE_USO.md` — **criterios de aceptación**.
4. El diseño de `/spec-design` y las tareas de `/spec-tasks`, si existen.

## Método: TDD, en este orden

```
1. Test que falla        → corré pytest, confirmá que falla por la razón correcta
2. Implementación mínima  → lo justo para que pase
3. pytest verde          → el test nuevo pasa
4. Suite completa        → no rompiste nada
5. Revisión adversarial  → otro agente busca qué se rompe
6. Corregir, repetir
7. Registrar en AI-ENGINEERING.md
8. Recién acá: terminado
```

## Restricciones

- **Una tarea por vez.** No mezcles dos casos de uso.
- Portá la lógica de `../donata-deco` cuando exista. No la reescribas desde cero.
- **TDD real**: si el test pasa antes de implementar, el test está mal.
- No agregues campos, endpoints ni features que no estén en el diseño.
- Nada de roles. Nada de API de IA cloud. Nada de comentarios en el código.

## Verificación antes de decir "terminado"

```bash
docker compose run --rm api pytest        # suite del backend verde
cd frontend && npm run build && npm run lint
```

Si no podés correr alguno, decilo explícitamente. **No declares terminado algo que no
verificaste.**

## Al terminar

1. Actualizá la tabla de fases en `docs/PLAN-IMPLEMENTACION.md`.
2. Agregá la entrada de bitácora en `docs/AI-ENGINEERING.md` con esta estructura:
   **Objetivo** · **Contexto dado a la IA** · **Prompt esencial** · **Iteración** (qué falló y
   qué se corrigió) · **Resultado** · **Lección**.
3. Si tomaste una decisión técnica no obvia, escribí un ADR en `docs/adr/`.
4. Reportá los criterios de aceptación del CU, uno por uno, con cómo se cumple.
