---
description: Diseña la solución técnica de un caso de uso (modelo de datos, endpoints, componentes, flujos)
agent: plan
---

Diseñá la solución técnica para: **$ARGUMENTS**

## Entrada

El informe de investigación de `/sdd-research` y la sección del CU en `docs/CASOS_DE_USO.md`.
Si no hay informe, decilo y pedí correr `/sdd-research` primero.

## Qué producir

### 1. Modelo de datos
- Colecciones y documentos afectados, campo por campo, con tipo.
- Índices nuevos y su justificación.
- Qué campos son **derivados** (no se persisten) y su fórmula.
- Cómo se garantiza la integridad referencial (incluido el Product.provider_id obligatorio).

### 2. API
Para cada endpoint: método, path, query params, body, respuesta, y **todos** los códigos de
error con su mensaje en español. Si el endpoint es nuevo, va en `/exports` o en el router que
corresponda.

### 3. Servicios
Qué lógica de negocio va en `services/`, con sus invariantes y sus casos borde.
**La lógica no va en el router.** Si algo no se puede testear sin levantar la app, va al service.

### 4. Frontend
- Componentes y su árbol.
- Qué estado es del servidor, qué estado va en la URL, qué estado es local.
- Los **cuatro estados** de cada pantalla: cargando, vacío, error, datos.
- Cómo se manejan los errores del backend en la UI.

### 5. Seguridad
Qué endpoint queda público (sólo debería ser `health` y el flujo de OAuth), rate limit
aplicado, y validaciones de schema.

### 6. IA (sólo si el CU lo necesita)
Para CU07: qué tools hacen falta, qué argumentos tienen, cómo se evita la confirmación bypass.
Descripción textual del system prompt y por qué está estructurado así.

### 7. Estrategia de testing
Qué tests, en qué archivo, qué caso borde cubre cada uno.

### 8. Riesgos
Lo que puede salir mal y cómo se mitiga.

## Reglas

- Un endpoint por caso, no un endpoint que haga de todo.
- Si el diseño necesita un campo que no está justificado por el CU o por una invariante, **no
  lo agregues**. Decilo como pregunta.
- Si encontrás que el modelo de datos heredado no alcanza para un criterio de aceptación del CU,
  señalalo explícitamente y propón el cambio mínimo.
- No escribas código de implementación. Escribí la **estructura**: firmas, schemas, contratos.

Al terminar, el siguiente paso es `/spec-tasks`.
