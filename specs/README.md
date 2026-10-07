# specs/ — Especificaciones por caso de uso

Carpeta del flujo **Spec-Driven Development**. Cada caso de uso tiene su propia carpeta, y
dentro los cuatro documentos del ciclo de vida.

> El documento fuente de verdad de los CU es [`../docs/CASOS_DE_USO.md`](../docs/CASOS_DE_USO.md).
> Esta carpeta es el **detalle de implementación** que se escribe al diseñar cada CU.

## Estructura

```
specs/
└── 001-<slug-del-cu>/
    ├── spec.md        Qué y por qué: alcance, criterios de aceptación, fuera de alcance
    ├── research.md    Salida del agente spec-research: contexto heredado + delta + fuentes
    ├── design.md      Salida de /sdd-design: datos, API, servicios, UI, seguridad, riesgos
    └── tasks.md       Salida de /sdd-tasks: tareas atómicas con criterio de terminado
```

## Nomenclatura

`001-cu01-auth-google`, `002-cu02-dashboard`, `003-cu03-productos`,
`004-cu04-clientes`, `005-cu05-ordenes`, `006-cu06-proveedores`,
`007-cu07-chat-ia`, `008-cu08-stock`, `009-cu09-notificaciones`,
`010-cu10-exportacion`.

## Reglas

- **Una carpeta por CU.** No mezcles casos de uso.
- `spec.md` **copia o referencia** los criterios de aceptación de `docs/CASOS_DE_USO.md`. No
  los reescribas con otro contenido: esos criterios son un entregable validado por el docente.
- `research.md` sin `archivo:línea` es conjetura, no investigación.
- `design.md` sin casos borde del CU no está terminado.
- `tasks.md` sólo con tareas que se puedan verificar de forma independiente.
- Cuando un CU cambie, actualizá también `docs/CASOS_DE_USO.md` y regenerá el PDF:
  ```bash
  python scripts/md2pdf.py docs/CASOS_DE_USO.md docs/CASOS_DE_USO.pdf
  ```
