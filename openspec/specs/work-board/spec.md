# work-board Specification

## Purpose
Tablero de trabajo que permite a los usuarios con sesi�n gestionar las �rdenes no canceladas como
tarjetas: cambiar su estado de trabajo, priorizarlas, asignarlas a un usuario activo y comentarlas,
con filtros y orden por fecha, prioridad y usuario asignado.

## Requirements

### Requirement: Tablero con las �rdenes no canceladas

`GET /work-items` SHALL devolver todas las �rdenes cuyo estado de cumplimiento no sea `entregado` ni
`cancelado` como tarjetas del tablero, junto con el resumen de sus �tems, la fecha del pedido y sus
datos de trabajo.

#### Scenario: Listado del tablero

- **WHEN** un usuario autenticado consulta `GET /work-items`
- **THEN** recibe las �rdenes no entregadas ni canceladas con su fecha, resumen de �tems y estado de trabajo

#### Scenario: Orden cancelada excluida

- **WHEN** una orden tiene estado de cumplimiento `cancelado`
- **THEN** no aparece en el tablero

#### Scenario: Orden entregada excluida

- **WHEN** una orden tiene estado de cumplimiento `entregado`, aunque tenga registro de trabajo
- **THEN** no aparece en el tablero

### Requirement: Estado de trabajo por defecto con creaci�n por upsert

Una orden sin registro de trabajo SHALL mostrarse con estado de trabajo `pendiente`, prioridad
`media` y sin usuario asignado. El primer cambio sobre su tarjeta SHALL crear el registro de
trabajo de forma idempotente.

#### Scenario: Orden sin registro de trabajo

- **WHEN** una orden no cancelada no tiene datos de trabajo
- **THEN** su tarjeta se muestra con estado `pendiente`, prioridad `media` y sin asignar

#### Scenario: Primer cambio crea el registro

- **WHEN** se modifica el estado de trabajo de una orden que a�n no ten�a registro
- **THEN** se crea el registro con los valores por defecto del resto de los campos

### Requirement: Cambio de estado de trabajo

`PATCH /work-items/{sale_id}` SHALL aceptar como estado de trabajo uno de `pendiente`, `en_curso`,
`bloqueado` o `terminado`, y SHALL responder `422` ante cualquier otro valor sin modificar la
tarjeta.

#### Scenario: Cambio a un estado v�lido

- **WHEN** se env�a `status: "en_curso"` para una orden
- **THEN** responde `200` y la tarjeta muestra el estado `en_curso`

#### Scenario: Estado inv�lido

- **WHEN** se env�a un `status` fuera de los cuatro valores permitidos
- **THEN** responde `422` y el estado de la tarjeta no cambia

### Requirement: Prioridad de la tarjeta

`PATCH /work-items/{sale_id}` SHALL aceptar una prioridad entre `alta`, `media` y `baja`, y SHALL
responder `422` ante cualquier otro valor.

#### Scenario: Cambio de prioridad

- **WHEN** se env�a `priority: "alta"` para una orden
- **THEN** responde `200` y la tarjeta muestra prioridad alta

#### Scenario: Prioridad inv�lida

- **WHEN** se env�a una `priority` fuera de los tres valores permitidos
- **THEN** responde `422` y la prioridad no cambia

### Requirement: Asignaci�n a un usuario activo

`PATCH /work-items/{sale_id}` SHALL asignar la tarjeta a un usuario existente y activo mediante
`assigned_to`, permitir reasignarla y quitarla, y SHALL responder `422` si el usuario no existe o
est� inactivo.

#### Scenario: Asignaci�n a un usuario activo

- **WHEN** se env�a `assigned_to` con el id de un usuario activo
- **THEN** responde `200` y la tarjeta muestra ese usuario como asignado

#### Scenario: Usuario inexistente o inactivo

- **WHEN** se env�a `assigned_to` con un id desconocido o de un usuario inactivo
- **THEN** responde `422` y la asignaci�n no cambia

### Requirement: Comentarios de la tarjeta

`POST /work-items/{sale_id}/comments` SHALL agregar un comentario append-only con el texto, el autor
de la sesi�n y la fecha, y SHALL responder `422` si el texto est� vac�o.

#### Scenario: Agregar un comentario

- **WHEN** un usuario env�a un texto no vac�o a `POST /work-items/{sale_id}/comments`
- **THEN** responde `201` y el comentario aparece en la tarjeta con su autor y fecha

#### Scenario: Comentario vac�o

- **WHEN** se env�a un texto vac�o o s�lo espacios
- **THEN** responde `422` y no se agrega ning�n comentario

### Requirement: Filtros y orden del tablero

`GET /work-items` SHALL permitir filtrar de forma combinable por prioridad y usuario asignado, y
ordenar por fecha del pedido en forma ascendente o descendente.

#### Scenario: Orden por fecha

- **WHEN** se solicita el tablero con orden descendente por fecha
- **THEN** las tarjetas se devuelven de la m�s reciente a la m�s antigua

#### Scenario: Filtros combinados

- **WHEN** se filtra por prioridad `alta` y un usuario asignado
- **THEN** s�lo se devuelven las tarjetas que cumplen ambos criterios

### Requirement: Autorizaci�n del tablero

Todos los endpoints del tablero SHALL exigir un JWT v�lido y SHALL responder `401` cuando la
solicitud no lo incluye.

#### Scenario: Sin token

- **WHEN** se consulta o modifica el tablero sin un JWT v�lido
- **THEN** responde `401` y no se modifica ning�n dato

### Requirement: Independencia del estado de cumplimiento y la cobranza

El estado de trabajo, la prioridad, la asignaci�n y los comentarios SHALL ser un eje independiente:
cambiarlos no SHALL modificar el estado de cumplimiento, los pagos ni el stock de la orden. La
sincronizaci�n es unidireccional: marcar una tarjeta como `terminado` SHALL NOT entregar la orden.

#### Scenario: Cambiar el trabajo no toca la venta

- **WHEN** se cambia el estado de trabajo de una orden
- **THEN** el estado de cumplimiento, los pagos y el stock de la orden permanecen sin cambios

#### Scenario: Tarjeta terminada no entrega la orden

- **WHEN** se marca la tarjeta de una orden no entregada como `terminado`
- **THEN** el estado de cumplimiento de la orden se mantiene (no pasa a `entregado`)

### Requirement: Cierre y reapertura autom�ticos al cambiar el estado de cumplimiento

El estado de la tarjeta de trabajo SHALL sincronizarse con el estado de cumplimiento de la orden:
al pasar la orden a `entregado` la tarjeta queda `terminado` autom�ticamente (creando el registro
por upsert si no exist�a), y al volver de `entregado` a otro estado la tarjeta vuelve a `pendiente`
conservando prioridad, asignaci�n y comentarios. Transiciones entre estados no entregados SHALL NOT
modificar la tarjeta.

#### Scenario: Entrega cierra la tarjeta existente

- **WHEN** una orden con tarjeta en `en_curso` pasa a estado de cumplimiento `entregado`
- **THEN** la tarjeta queda en estado de trabajo `terminado`

#### Scenario: Entrega crea la tarjeta si no exist�a

- **WHEN** una orden sin registro de trabajo pasa a estado de cumplimiento `entregado`
- **THEN** se crea su registro de trabajo con estado `terminado`

#### Scenario: Reapertura devuelve la tarjeta a pendiente

- **WHEN** una orden entregada vuelve a un estado de cumplimiento no entregado
- **THEN** la tarjeta vuelve a `pendiente` y conserva su prioridad, asignaci�n y comentarios

#### Scenario: Cambio de cumplimiento no relacionado no toca la tarjeta

- **WHEN** una orden no entregada cambia entre estados no entregados (`pendiente` a `en_proceso`)
- **THEN** el estado, la prioridad, la asignaci�n y los comentarios de su tarjeta no cambian

### Requirement: Tarjetas de �rdenes entregadas congeladas

`PATCH /work-items/{sale_id}` y `POST /work-items/{sale_id}/comments` SHALL responder `404` cuando
la orden tiene estado de cumplimiento `entregado` o `cancelado`.

#### Scenario: Modificaci�n rechazada

- **WHEN** se env�a `PATCH /work-items/{sale_id}` para una orden entregada
- **THEN** responde `404` y la tarjeta no se modifica

#### Scenario: Comentario rechazado

- **WHEN** se env�a `POST /work-items/{sale_id}/comments` para una orden entregada
- **THEN** responde `404` y no se agrega ning�n comentario
