# notifications Spec

<!-- Fuente: docs/CASOS_DE_USO.md CU09; as-built -->

## Purpose

Cubre las alertas en plataforma del negocio —stock, fechas de envío, cobros y órdenes incompletas—, su presentación en la campana del header y el manejo por usuario de lectura y descarte.

## Requirements

### Requirement: Los productos activos generan alertas de stock

Un producto activo con `stock == 0` SHALL generar `STOCK_AGOTADO` (severidad alta) y con `stock <= min_stock` SHALL generar `STOCK_MINIMO` (severidad media); cada producto SHALL generar como máximo una de las dos.

#### Scenario: Producto agotado

- **GIVEN** un producto activo con stock 0
- **WHEN** se consulta `GET /notifications`
- **THEN** aparece `STOCK_AGOTADO` con severidad alta y la acción "Reponer urgente" sobre ese producto

#### Scenario: Producto en stock mínimo

- **GIVEN** un producto activo cuyo stock es menor o igual al mínimo
- **WHEN** se consulta `GET /notifications`
- **THEN** aparece `STOCK_MINIMO` con severidad media y la acción "Programar reposición"

#### Scenario: Stock repuesto

- **GIVEN** un producto alertado por stock mínimo
- **WHEN** su stock sube por encima del mínimo
- **THEN** la alerta desaparece del listado

### Requirement: Las órdenes generan alertas por fecha límite de envío

Una orden no cancelada con `ship_by` vencido que no está entregada SHALL generar `ENVIO_VENCIDO` (alta); una orden `pendiente` o `en_proceso` cuyo `ship_by` vence dentro de las próximas 72 horas SHALL generar `ENVIO_PENDIENTE` (media).

#### Scenario: Envío vencido

- **GIVEN** una orden con la fecha de envío pasada y sin entregar
- **WHEN** se consulta `GET /notifications`
- **THEN** aparece `ENVIO_VENCIDO` con severidad alta y la acción "Priorizar envío"

#### Scenario: Envío por vencer

- **GIVEN** una orden pendiente que debe despacharse dentro de 48 horas
- **WHEN** se consulta `GET /notifications`
- **THEN** aparece `ENVIO_PENDIENTE` con severidad media y la acción "Preparar envío"

#### Scenario: Orden entregada o cancelada

- **GIVEN** una orden entregada o cancelada con fecha de envío pasada
- **WHEN** se consulta `GET /notifications`
- **THEN** no aparece ninguna alerta de envío para esa orden

### Requirement: Las órdenes con saldo generan alertas de cobro

Una orden con saldo mayor a cero que no está entregada SHALL generar `PAGO_PENDIENTE` (media) y, si la fecha de vencimiento del cobro ya pasó, `PAGO_VENCIDO` (alta) en su lugar.

#### Scenario: Saldo pendiente

- **GIVEN** una orden con saldo a pagar y sin fecha de cobro vencida
- **WHEN** se consulta `GET /notifications`
- **THEN** aparece `PAGO_PENDIENTE` con severidad media y la acción "Registrar cobro"

#### Scenario: Cobro vencido

- **GIVEN** una orden cuyo saldo superó la fecha de vencimiento del cobro
- **WHEN** se consulta `GET /notifications`
- **THEN** aparece `PAGO_VENCIDO` con severidad alta

#### Scenario: Orden saldada

- **GIVEN** una orden con `PAGO_PENDIENTE`
- **WHEN** se registra un pago que cubre todo el saldo
- **THEN** la alerta de cobro desaparece del listado

### Requirement: Las órdenes sin ítems o sin total generan una alerta de baja prioridad

Una orden guardada sin ítems o sin total SHALL generar `ORDEN_SIN_ITEMS` con severidad baja y la acción "Completar orden", sin importar su estado.

#### Scenario: Orden incompleta

- **GIVEN** una orden guardada con la lista de ítems vacía
- **WHEN** se consulta `GET /notifications`
- **THEN** aparece `ORDEN_SIN_ITEMS` con severidad baja

#### Scenario: Orden completa

- **GIVEN** una orden con ítems y total informados
- **WHEN** se consulta `GET /notifications`
- **THEN** no aparece `ORDEN_SIN_ITEMS` para esa orden

### Requirement: La campana muestra el total de notificaciones no leídas

El ícono de la campana del header SHALL mostrar un badge con la cantidad de alertas no leídas del usuario; el contador SHALL bajar al instante después de cada acción y el listado SHALL refrescarse cada 60 segundos.

#### Scenario: Badge con no leídas

- **WHEN** el usuario tiene 3 alertas sin leer
- **THEN** la campana muestra el badge con 3, y al superar las 99 muestra "99+"

#### Scenario: Sin no leídas

- **WHEN** no hay alertas sin leer
- **THEN** la campana no muestra badge

#### Scenario: Marcado individual

- **WHEN** el usuario marca una alerta como leída
- **THEN** el badge se actualiza de inmediato

### Requirement: GET /notifications calcula las alertas vigentes en cada consulta

`GET /notifications` SHALL devolver las alertas calculadas en el momento a partir del estado actual del negocio, combinadas con la lectura y el descarte del usuario, más el total `unread_count`; SHALL exigir sesión y afectar sólo al usuario autenticado.

#### Scenario: Respuesta con sesión

- **WHEN** un usuario autenticado consulta `GET /notifications`
- **THEN** recibe `200` con `items` (id, type, severity, title, description, entity, entity_id, action, read, dismissed) y `unread_count`

#### Scenario: Sin sesión

- **WHEN** la petición llega sin token válido
- **THEN** el servidor responde `401`

#### Scenario: Estado por usuario

- **GIVEN** dos usuarios ven la misma alerta
- **WHEN** uno la marca como leída
- **THEN** el otro sigue viéndola como no leída

### Requirement: El panel lateral lista los ítems ordenados por severidad

El panel de la campana SHALL listar los ítems con severidad alta primero y luego media y baja, ordenados dentro de cada grupo por tipo; cada ítem SHALL mostrar título, descripción y un botón para descartarlo, más las acciones masivas "Marcar leídas" y "Descartar todo".

<!-- Pendiente: agrupar por severidad/tipo con encabezados, mostrar fecha relativa ("hace 2 h") y botón de acción directa (ej. "Registrar pago") -->

#### Scenario: Severidades mixtas

- **WHEN** hay alertas de distinta severidad
- **THEN** las de severidad alta aparecen primero y dentro de cada severidad se ordenan por tipo

#### Scenario: Dos productos agotados

- **WHEN** dos productos distintos están agotados
- **THEN** aparecen dos ítems independientes, uno por producto

### Requirement: Con cero alertas el panel muestra un estado vacío

Cuando no hay alertas vigentes el panel SHALL mostrar un estado vacío claro y el contador SHALL quedar en cero.

<!-- Pendiente: texto "Todo al día. No hay alertas." del CU09 -->

#### Scenario: Panel vacío

- **GIVEN** todas las alertas fueron resueltas o descartadas
- **WHEN** el usuario abre la campana
- **THEN** se muestra "No hay notificaciones." y la campana no tiene badge

#### Scenario: Listado sin condiciones de alerta

- **WHEN** ninguna entidad del negocio cumple una condición de alerta
- **THEN** la respuesta trae `items` vacío y `unread_count` en 0

### Requirement: Marcar como leída actualiza el contador al instante

`PATCH /notifications/{id}` con `{"read": true}` SHALL marcar una alerta vigente como leída del usuario y devolver el listado actualizado con `unread_count` reducido; una alerta que ya no esté vigente SHALL responder `404`.

#### Scenario: Marcar una alerta

- **WHEN** se envía `PATCH /notifications/{id}` con `{"read": true}`
- **THEN** la alerta queda con `read: true` y `unread_count` baja en uno

#### Scenario: Marcar dos veces

- **WHEN** se marca la misma alerta como leída una segunda vez
- **THEN** sigue leída y `unread_count` no vuelve a bajar

#### Scenario: Alerta no vigente

- **WHEN** el id no corresponde a una alerta vigente
- **THEN** el servidor responde `404` con "La notificación no existe o ya no está vigente"

### Requirement: Marcar todas como leídas deja el contador en cero

`POST /notifications/read-all` SHALL marcar todas las alertas vigentes del usuario como leídas y devolver el listado con `unread_count` en 0, manteniendo los ítems visibles en el panel.

#### Scenario: Marcar todas

- **WHEN** se envía `POST /notifications/read-all`
- **THEN** el servidor responde `200` con `unread_count` en 0 y los ítems siguen en el panel

#### Scenario: Sin alertas vigentes

- **WHEN** se envía `POST /notifications/read-all` sin alertas
- **THEN** el servidor responde `200` sin errores y el listado queda vacío

### Requirement: Descartar oculta la alerta sin resolver el problema de negocio

`PATCH /notifications/{id}` con `{"dismissed": true}` y `POST /notifications/dismiss-all` SHALL ocultar alertas del panel sin modificar la orden ni el producto: el saldo, el stock y las fechas SHALL quedar intactos.

<!-- Pendiente: CU09 A6 indica que una alerta descartada vuelve a aparecer si la condición sigue vigente; hoy el descarte persiste -->

#### Scenario: Descartar todo

- **WHEN** se envía `POST /notifications/dismiss-all`
- **THEN** el panel queda vacío y el stock y los saldos del negocio no cambian

#### Scenario: Descartar una alerta

- **WHEN** se envía `PATCH /notifications/{id}` con `{"dismissed": true}`
- **THEN** la alerta desaparece del panel y no se cuenta en `unread_count`

### Requirement: Las alertas se recalculan y desaparecen al resolverse la causa

Las alertas SHALL recalcularse en cada consulta a partir del estado actual: no existe un estado persistido de "resuelta", de modo que al cambiar el dato la alerta SHALL dejar de aparecer.

#### Scenario: Pago total

- **GIVEN** una orden con `PAGO_PENDIENTE`
- **WHEN** se cubre todo el saldo
- **THEN** la alerta no aparece en la siguiente consulta

#### Scenario: Entrega de la orden

- **GIVEN** una orden con `ENVIO_VENCIDO`
- **WHEN** se la marca como entregada
- **THEN** la alerta de envío desaparece

#### Scenario: Producto eliminado

- **GIVEN** un producto alertado que fue eliminado
- **WHEN** se consulta `GET /notifications`
- **THEN** no quedan alertas de ese producto ni ítems tachados

### Requirement: El clic en una alerta navega a la entidad y la marca como leída

Al hacer clic en una alerta de orden SHALL navegarse a `/ordenes/{entity_id}` y en una de producto al listado `/productos`; en ambos casos el panel SHALL cerrarse y la alerta SHALL quedar marcada como leída.

<!-- Pendiente: navegación al producto individual con contexto expandido -->

#### Scenario: Clic en alerta de orden

- **GIVEN** una alerta `ENVIO_VENCIDO` de una orden
- **WHEN** el usuario hace clic en ella
- **THEN** se abre la pantalla de esa orden y la alerta queda `read: true`

#### Scenario: Clic en alerta de producto

- **GIVEN** una alerta `STOCK_MINIMO` de un producto
- **WHEN** el usuario hace clic en ella
- **THEN** se abre el listado de productos y la alerta queda `read: true`

### Requirement: Las acciones requieren sesión de usuario

Todas las operaciones de `GET`, `PATCH` y `POST` sobre `/notifications` SHALL exigir un usuario autenticado.

#### Scenario: Sin token

- **WHEN** se consulta o modifica una notificación sin token válido
- **THEN** el servidor responde `401` y no expone ni altera ninguna alerta
