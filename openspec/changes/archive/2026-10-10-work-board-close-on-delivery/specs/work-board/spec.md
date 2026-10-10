# Spec Delta

## Purpose

<!-- Existing capability: work-board. Delete this section for an existing capability. -->

## ADDED Requirements

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

## MODIFIED Requirements

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