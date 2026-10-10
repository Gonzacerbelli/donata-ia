# Spec Delta

## Purpose

Tablero de trabajo que permite a los usuarios con sesión gestionar las órdenes no canceladas como
tarjetas: cambiar su estado de trabajo, priorizarlas, asignarlas a un usuario activo y comentarlas,
con filtros y orden por fecha, prioridad y usuario asignado.

## ADDED Requirements

### Requirement: Tablero con las órdenes no canceladas

`GET /work-items` SHALL devolver todas las órdenes cuyo estado de cumplimiento no sea `cancelado`
como tarjetas del tablero, junto con el resumen de sus ítems, la fecha del pedido y sus datos de
trabajo.

#### Scenario: Listado del tablero

- **WHEN** un usuario autenticado consulta `GET /work-items`
- **THEN** recibe las órdenes no canceladas con su fecha, resumen de ítems y estado de trabajo

#### Scenario: Orden cancelada excluida

- **WHEN** una orden tiene estado de cumplimiento `cancelado`
- **THEN** no aparece en el tablero

### Requirement: Estado de trabajo por defecto con creación por upsert

Una orden sin registro de trabajo SHALL mostrarse con estado de trabajo `pendiente`, prioridad
`media` y sin usuario asignado. El primer cambio sobre su tarjeta SHALL crear el registro de
trabajo de forma idempotente.

#### Scenario: Orden sin registro de trabajo

- **WHEN** una orden no cancelada no tiene datos de trabajo
- **THEN** su tarjeta se muestra con estado `pendiente`, prioridad `media` y sin asignar

#### Scenario: Primer cambio crea el registro

- **WHEN** se modifica el estado de trabajo de una orden que aún no tenía registro
- **THEN** se crea el registro con los valores por defecto del resto de los campos

### Requirement: Cambio de estado de trabajo

`PATCH /work-items/{sale_id}` SHALL aceptar como estado de trabajo uno de `pendiente`, `en_curso`,
`bloqueado` o `terminado`, y SHALL responder `422` ante cualquier otro valor sin modificar la
tarjeta.

#### Scenario: Cambio a un estado válido

- **WHEN** se envía `status: "en_curso"` para una orden
- **THEN** responde `200` y la tarjeta muestra el estado `en_curso`

#### Scenario: Estado inválido

- **WHEN** se envía un `status` fuera de los cuatro valores permitidos
- **THEN** responde `422` y el estado de la tarjeta no cambia

### Requirement: Prioridad de la tarjeta

`PATCH /work-items/{sale_id}` SHALL aceptar una prioridad entre `alta`, `media` y `baja`, y SHALL
responder `422` ante cualquier otro valor.

#### Scenario: Cambio de prioridad

- **WHEN** se envía `priority: "alta"` para una orden
- **THEN** responde `200` y la tarjeta muestra prioridad alta

#### Scenario: Prioridad inválida

- **WHEN** se envía una `priority` fuera de los tres valores permitidos
- **THEN** responde `422` y la prioridad no cambia

### Requirement: Asignación a un usuario activo

`PATCH /work-items/{sale_id}` SHALL asignar la tarjeta a un usuario existente y activo mediante
`assigned_to`, permitir reasignarla y quitarla, y SHALL responder `422` si el usuario no existe o
está inactivo.

#### Scenario: Asignación a un usuario activo

- **WHEN** se envía `assigned_to` con el id de un usuario activo
- **THEN** responde `200` y la tarjeta muestra ese usuario como asignado

#### Scenario: Usuario inexistente o inactivo

- **WHEN** se envía `assigned_to` con un id desconocido o de un usuario inactivo
- **THEN** responde `422` y la asignación no cambia

### Requirement: Comentarios de la tarjeta

`POST /work-items/{sale_id}/comments` SHALL agregar un comentario append-only con el texto, el autor
de la sesión y la fecha, y SHALL responder `422` si el texto está vacío.

#### Scenario: Agregar un comentario

- **WHEN** un usuario envía un texto no vacío a `POST /work-items/{sale_id}/comments`
- **THEN** responde `201` y el comentario aparece en la tarjeta con su autor y fecha

#### Scenario: Comentario vacío

- **WHEN** se envía un texto vacío o sólo espacios
- **THEN** responde `422` y no se agrega ningún comentario

### Requirement: Filtros y orden del tablero

`GET /work-items` SHALL permitir filtrar de forma combinable por prioridad y usuario asignado, y
ordenar por fecha del pedido en forma ascendente o descendente.

#### Scenario: Orden por fecha

- **WHEN** se solicita el tablero con orden descendente por fecha
- **THEN** las tarjetas se devuelven de la más reciente a la más antigua

#### Scenario: Filtros combinados

- **WHEN** se filtra por prioridad `alta` y un usuario asignado
- **THEN** sólo se devuelven las tarjetas que cumplen ambos criterios

### Requirement: Autorización del tablero

Todos los endpoints del tablero SHALL exigir un JWT válido y SHALL responder `401` cuando la
solicitud no lo incluye.

#### Scenario: Sin token

- **WHEN** se consulta o modifica el tablero sin un JWT válido
- **THEN** responde `401` y no se modifica ningún dato

### Requirement: Independencia del estado de cumplimiento y la cobranza

El estado de trabajo, la prioridad, la asignación y los comentarios SHALL ser un eje independiente:
cambiarlos no SHALL modificar el estado de cumplimiento, los pagos ni el stock de la orden.

#### Scenario: Cambiar el trabajo no toca la venta

- **WHEN** se cambia el estado de trabajo de una orden
- **THEN** el estado de cumplimiento, los pagos y el stock de la orden permanecen sin cambios
