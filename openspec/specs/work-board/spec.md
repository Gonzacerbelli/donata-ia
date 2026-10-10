# work-board Specification

## Purpose
Tablero de trabajo que permite a los usuarios con sesión gestionar las órdenes no canceladas como
tarjetas: cambiar su estado de trabajo, priorizarlas, asignarlas a un usuario activo y comentarlas,
con filtros y orden por fecha, prioridad y usuario asignado.

## Requirements

### Requirement: Tablero con las órdenes no canceladas

`GET /work-items` SHALL devolver todas las órdenes cuyo estado de cumplimiento no sea `entregado` ni
`cancelado` como tarjetas del tablero, junto con el resumen de sus ítems, la fecha del pedido y sus
datos de trabajo.

#### Scenario: Listado del tablero

- **WHEN** un usuario autenticado consulta `GET /work-items`
- **THEN** recibe las órdenes no entregadas ni canceladas con su fecha, resumen de ítems y estado de trabajo

#### Scenario: Orden cancelada excluida

- **WHEN** una orden tiene estado de cumplimiento `cancelado`
- **THEN** no aparece en el tablero

#### Scenario: Orden entregada excluida

- **WHEN** una orden tiene estado de cumplimiento `entregado`, aunque tenga registro de trabajo
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
cambiarlos no SHALL modificar el estado de cumplimiento, los pagos ni el stock de la orden. La
sincronización es unidireccional: marcar una tarjeta como `terminado` SHALL NOT entregar la orden.

#### Scenario: Cambiar el trabajo no toca la venta

- **WHEN** se cambia el estado de trabajo de una orden
- **THEN** el estado de cumplimiento, los pagos y el stock de la orden permanecen sin cambios

#### Scenario: Tarjeta terminada no entrega la orden

- **WHEN** se marca la tarjeta de una orden no entregada como `terminado`
- **THEN** el estado de cumplimiento de la orden se mantiene (no pasa a `entregado`)

### Requirement: Cierre y reapertura automáticos al cambiar el estado de cumplimiento

El estado de la tarjeta de trabajo SHALL sincronizarse con el estado de cumplimiento de la orden:
al pasar la orden a `entregado` la tarjeta queda `terminado` automáticamente (creando el registro
por upsert si no existía), y al volver de `entregado` a otro estado la tarjeta vuelve a `pendiente`
conservando prioridad, asignación y comentarios. Transiciones entre estados no entregados SHALL NOT
modificar la tarjeta.

#### Scenario: Entrega cierra la tarjeta existente

- **WHEN** una orden con tarjeta en `en_curso` pasa a estado de cumplimiento `entregado`
- **THEN** la tarjeta queda en estado de trabajo `terminado`

#### Scenario: Entrega crea la tarjeta si no existía

- **WHEN** una orden sin registro de trabajo pasa a estado de cumplimiento `entregado`
- **THEN** se crea su registro de trabajo con estado `terminado`

#### Scenario: Reapertura devuelve la tarjeta a pendiente

- **WHEN** una orden entregada vuelve a un estado de cumplimiento no entregado
- **THEN** la tarjeta vuelve a `pendiente` y conserva su prioridad, asignación y comentarios

#### Scenario: Cambio de cumplimiento no relacionado no toca la tarjeta

- **WHEN** una orden no entregada cambia entre estados no entregados (`pendiente` a `en_proceso`)
- **THEN** el estado, la prioridad, la asignación y los comentarios de su tarjeta no cambian

### Requirement: Tarjetas de órdenes entregadas congeladas

`PATCH /work-items/{sale_id}` y `POST /work-items/{sale_id}/comments` SHALL responder `404` cuando
la orden tiene estado de cumplimiento `entregado` o `cancelado`.

#### Scenario: Modificación rechazada

- **WHEN** se envía `PATCH /work-items/{sale_id}` para una orden entregada
- **THEN** responde `404` y la tarjeta no se modifica

#### Scenario: Comentario rechazado

- **WHEN** se envía `POST /work-items/{sale_id}/comments` para una orden entregada
- **THEN** responde `404` y no se agrega ningún comentario
