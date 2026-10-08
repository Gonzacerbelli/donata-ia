# order-management Spec

<!-- Fuente: docs/CASOS_DE_USO.md CU05; as-built -->

## Purpose

Cubre el ciclo de vida de las órdenes de venta: alta con ítems mixtos, precios minorista/mayorista, descuentos, stock atómico, estados de cumplimiento, pagos y saldo derivado, cancelación, eliminación y listado con filtros.

## Requirements

### Requirement: Creación de orden con ítems mixtos

`POST /sales` SHALL crear una orden con ítems de catálogo (con `product_id`), ítems libres (con `description` y `unit_price`) o una combinación de ambos. La orden nace en estado `pendiente` y la respuesta es `201`. `items` no puede ser vacío.

#### Scenario: Ítems de catálogo y libres en la misma orden

- **WHEN** se envía `POST /sales` con un ítem que tiene `product_id` y otro con `description` y `unit_price`
- **THEN** responde `201` con los dos ítems persistidos, `subtotal` igual a la suma de `qty × unit_price` y `status` igual a `pendiente`

#### Scenario: Orden sin ítems

- **WHEN** se envía `POST /sales` con `items` vacío
- **THEN** responde `422` y no se crea ninguna orden

#### Scenario: Ítem libre sin precio

- **WHEN** un ítem tiene `description` pero no `unit_price`
- **THEN** responde `422` informando que falta el precio de un ítem

### Requirement: Determinación del precio unitario

`POST /sales` SHALL persistir el `unit_price` enviado cuando está presente; si un ítem de catálogo no envía precio, SHALL resolverlo por tipo de cliente: `mayorista` usa el precio mayorista del producto cuando existe y si no el minorista. Sin `client_type` se usa el tipo del cliente, tratando `ambos` como `minorista`.

#### Scenario: Precio explícito enviado

- **WHEN** un ítem de catálogo envía `unit_price` distinto del catálogo
- **THEN** se persiste el precio enviado

#### Scenario: Cliente mayorista con precio mayorista

- **WHEN** se crea una orden sin `unit_price` para un cliente `mayorista` cuyo producto tiene `price_mayorista`
- **THEN** el ítem se persiste con el precio mayorista

#### Scenario: Cliente mayorista sin precio mayorista

- **WHEN** se crea una orden sin `unit_price` para un cliente `mayorista` y el producto no tiene `price_mayorista`
- **THEN** el ítem se persiste con el precio minorista

#### Scenario: Cliente de tipo ambos sin listado elegido

- **WHEN** se crea una orden para un cliente `ambos` sin enviar `client_type`
- **THEN** se aplica la lista de precios minorista

<!-- Pendiente: el CU05 indica que el precio mayorista tiene prioridad sobre cualquier precio enviado; el código acepta el `unit_price` enviado y sólo resuelve el precio cuando no llega. -->

### Requirement: Producto de catálogo inexistente

`POST /sales` SHALL rechazar con `422` cualquier ítem cuyo `product_id` no corresponda a un producto existente, sin crear la orden.

#### Scenario: Product_id desconocido

- **WHEN** un ítem referencia un `product_id` inexistente
- **THEN** responde `422` indicando que el producto no existe y no se crea la orden

### Requirement: Total, descuento y envío

`POST /sales` y `PATCH /sales/{id}` SHALL calcular `total = subtotal − descuento + envío`. El descuento se expresa como monto o porcentaje, se convierte a entero redondeado y se acota entre 0 y el subtotal; `discount_pct` fuera de 0–100 responde `422`.

#### Scenario: Descuento por porcentaje con envío

- **WHEN** se envía `discount_pct: 10` con `shipping_cost: 500` sobre un subtotal de 1000
- **THEN** `discount` es 100 y `total` es 1400

#### Scenario: Descuento por monto

- **WHEN** se envía `discount: 300` sobre un subtotal de 1000 sin envío
- **THEN** `discount` es 300 y `total` es 700

#### Scenario: Descuento mayor al subtotal

- **WHEN** se envía `discount` mayor que el subtotal
- **THEN** el descuento se acota al subtotal y el `total` resulta igual al subtotal más el envío

<!-- Pendiente: el CU05 A2 espera `422 "El descuento no puede superar el subtotal"`; el código lo acota en silencio. -->

#### Scenario: Porcentaje fuera de rango

- **WHEN** se envía `discount_pct` mayor a 100
- **THEN** responde `422` y no se crea la orden

### Requirement: Descuento atómico de stock al crear

`POST /sales` SHALL descontar el stock de cada ítem de catálogo de forma atómica. Si algún ítem no tiene stock suficiente SHALL responder `400` nombrando el producto y no dejar ningún efecto: se revierten los descuentos ya aplicados y la orden no queda registrada.

#### Scenario: Stock insuficiente en un ítem posterior

- **GIVEN** una orden con dos ítems de catálogo y el segundo sin stock suficiente
- **WHEN** se envía `POST /sales`
- **THEN** responde `400` con el nombre del producto sin stock, el stock de todos los productos queda como al inicio y `GET /sales` sigue vacío

#### Scenario: Creación exitosa descuenta stock

- **WHEN** se crea una orden con dos ítems de catálogo con stock disponible
- **THEN** el stock de ambos productos baja en la cantidad vendida

### Requirement: Auditoría de los movimientos de stock

Cada descuento o restitución de stock originado en una orden SHALL registrar un movimiento con cantidad con signo, motivo, stock resultante, tipo y referencia a la orden; una creación fallida deja además los movimientos de reversión.

#### Scenario: Movimientos al crear la orden

- **WHEN** se crea una orden con dos productos de catálogo
- **THEN** existen dos movimientos con cantidad negativa, tipo `venta` y `ref_id` igual al id de la orden

#### Scenario: Reversión ante fallo parcial

- **WHEN** la creación falla por stock insuficiente en un ítem después de descontar otros
- **THEN** se registran movimientos de reversión que dejan el stock como estaba y la orden no existe

### Requirement: Saldo derivado de los pagos

Las respuestas de orden SHALL calcular `paid` como la suma de sus pagos y `balance` como `total − paid`. Estos valores se derivan en cada respuesta y no se persisten como campos propios de la orden.

#### Scenario: Orden con seña parcial

- **GIVEN** una orden con total 2000
- **WHEN** se registra un pago de 1500
- **THEN** la respuesta tiene `paid` 1500 y `balance` 500

#### Scenario: Orden sin pagos

- **WHEN** se consulta una orden recién creada sin pagos
- **THEN** `paid` es 0 y `balance` es igual al `total`

### Requirement: Registro de pagos y señas

`POST /sales/{id}/payments` SHALL agregar un pago con `amount` mayor a cero, tipo `adelanto` o `pago`, fecha y método opcionales, y devolver la orden actualizada. En una orden cancelada SHALL responder `400`.

#### Scenario: Seña parcial

- **WHEN** se registra un pago de 1500 con tipo `adelanto` sobre una orden de 2000
- **THEN** responde `200` con el pago en la lista, `paid` 1500 y `balance` 500

#### Scenario: Pago en orden cancelada

- **WHEN** se envía un pago a una orden con estado `cancelado`
- **THEN** responde `400` con el mensaje "No se pueden registrar pagos de una venta cancelada" y el pago no se registra

#### Scenario: Monto no positivo

- **WHEN** se envía un pago con `amount` igual a 0 o negativo
- **THEN** responde `422` y el pago no se registra

#### Scenario: Pago que supera el saldo

- **WHEN** se registra un pago mayor que el saldo pendiente
- **THEN** el pago se acepta y `balance` queda negativo

<!-- Pendiente: el CU05.1 espera `201` al registrar un pago; el endpoint responde `200`. El CU05 paso 6 prevé una seña inicial junto al alta de orden, que hoy no existe: el primer pago se registra desde el detalle. -->

### Requirement: Estados de cobro independientes del cumplimiento

La interfaz SHALL mostrar un estado de cobro derivado del saldo: `sin_pago` cuando no hay pagos, `parcial` cuando los pagos no cubren el total y `pagada` cuando el saldo es cero o negativo. Este estado es independiente del estado de cumplimiento.

#### Scenario: Orden entregada sin pagos

- **WHEN** una orden en estado `entregado` no tiene pagos
- **THEN** el badge de cumplimiento muestra "Entregado" y el de cobro muestra "Sin pago"

#### Scenario: Orden pagada a medias

- **WHEN** los pagos cubren menos del total y hay al menos un pago
- **THEN** el estado de cobro muestra "Parcial"

#### Scenario: Cobertura total

- **WHEN** la suma de pagos cubre o supera el total
- **THEN** el estado de cobro muestra "Pagada"

### Requirement: Cambio de estado de cumplimiento

`PATCH /sales/{id}` SHALL cambiar el estado entre `pendiente`, `en_proceso`, `entregado` y `cancelado`, y SHALL aceptar además la actualización de notas, envío, descuento, costo de envío y fechas. Cualquier otro estado responde `422`.

#### Scenario: Avance a entregado

- **WHEN** se envía `PATCH /sales/{id}` con `status: entregado`
- **THEN** responde `200` con el estado actualizado

#### Scenario: Estado inválido

- **WHEN** se envía `status` fuera de los valores permitidos
- **THEN** responde `422` y la orden no cambia

#### Scenario: Recálculo al modificar descuento o envío

- **WHEN** se envía un `PATCH` con `discount` o `shipping_cost`
- **THEN** el `total` se recalcula como `subtotal − descuento + envío`

### Requirement: Cancelación restituye el stock

Al pasar una orden a `cancelado`, `PATCH /sales/{id}` SHALL devolver el stock de cada ítem de catálogo y SHALL registrar movimientos de restitución con tipo `cancelacion` y referencia a la orden.

#### Scenario: Cancelar una orden con stock vendido

- **GIVEN** una orden activa que descontó 3 unidades
- **WHEN** se envía `PATCH /sales/{id}` con `status: cancelado`
- **THEN** responde `200` y el stock del producto vuelve a su valor previo con un movimiento `cancelacion` referido a la orden

#### Scenario: Re-cancelación sin efecto

- **WHEN** se envía `status: cancelado` sobre una orden ya cancelada
- **THEN** responde `200` sin generar movimientos adicionales

### Requirement: Revertir una cancelación vuelve a descontar

Al salir de `cancelado` hacia otro estado, `PATCH /sales/{id}` SHALL volver a descontar el stock. Si falta stock SHALL responder `400` y la orden permanece `cancelado`.

#### Scenario: Revertir con stock disponible

- **WHEN** una orden cancelada se cambia a `en_proceso` con stock suficiente
- **THEN** responde `200`, el estado cambia y el stock se vuelve a descontar

#### Scenario: Revertir sin stock suficiente

- **WHEN** una orden cancelada se cambia a otro estado y algún producto ya no tiene stock
- **THEN** responde `400` y la orden sigue `cancelado`

<!-- Pendiente: el CU05 A7 asume rollback total; hoy los ítems descontados antes de detectar el fallo no se revierten, por lo que el stock puede quedar descontado con la orden todavía cancelada. -->

### Requirement: Eliminación de orden

`DELETE /sales/{id}` SHALL restituir el stock y eliminar la orden. Si la orden tiene pagos registrados SHALL responder `409` sin modificar nada.

#### Scenario: Orden sin pagos

- **WHEN** se elimina una orden activa sin pagos
- **THEN** responde `204` y el stock queda como antes de la venta

#### Scenario: Orden con pagos registrados

- **WHEN** se elimina una orden que tiene al menos un pago
- **THEN** responde `409` informando que no se puede eliminar una venta con pagos, y la orden y sus pagos siguen existiendo

#### Scenario: Orden ya cancelada sin pagos

- **WHEN** se elimina una orden cancelada sin pagos
- **THEN** responde `204` sin registrar nuevos movimientos de stock

### Requirement: Listado con filtros y búsqueda

`GET /sales` SHALL listar las órdenes ordenadas por fecha descendente y SHALL filtrar de forma combinable por `status`, `client_id`, `date_from`/`date_to` y `search`, donde `search` coincide con el nombre de un cliente o con el texto de la descripción de un ítem.

#### Scenario: Búsqueda por nombre de cliente

- **WHEN** se envía `search` con parte del nombre de un cliente
- **THEN** se devuelven sólo las órdenes de ese cliente

#### Scenario: Búsqueda por texto de ítem

- **WHEN** se envía `search` con un texto que aparece en la descripción de un ítem libre
- **THEN** se devuelve esa orden

#### Scenario: Filtros combinados

- **WHEN** se combinan `status`, `client_id` y rango de fechas
- **THEN** se devuelven sólo las órdenes que cumplen todos los criterios

#### Scenario: Sin resultados

- **WHEN** ningún filtro coincide
- **THEN** responde `200` con una lista vacía

<!-- Pendiente: el CU05 paso 11 pide listado paginado; `GET /sales` no acepta parámetros de paginación y devuelve todas las órdenes que cumplen el filtro. -->

### Requirement: Cliente inexistente rechazado en el alta

`POST /sales` SHALL responder `404` cuando `client_id` no corresponde a un cliente existente, sin crear la orden ni tocar stock.

#### Scenario: Client_id desconocido

- **WHEN** se envía un `client_id` inexistente
- **THEN** responde `404` y `GET /sales` no muestra órdenes nuevas

<!-- Pendiente: el CU05 A8 prevé `422`/`409` y un control de cliente inactivo; el código responde `404` y los clientes no tienen estado inactivo. -->

### Requirement: Protección contra doble envío del formulario

El formulario de nueva orden SHALL deshabilitar el botón de envío mientras `POST /sales` está en curso, de modo que un doble clic no genere dos órdenes.

#### Scenario: Doble clic en Crear orden

- **GIVEN** el usuario hizo clic en "Crear orden" y la petición está en curso
- **WHEN** vuelve a hacer clic
- **THEN** el botón está deshabilitado y sólo se crea una orden

<!-- Pendiente: el CU05 A9 pide idempotencia también del lado del servidor por clave de cliente; el backend no la implementa. -->

### Requirement: Detalle de orden

`GET /sales/{id}` SHALL devolver la cabecera con totales, el desglose de ítems con cantidad y precio, la lista de pagos, las notas y las fechas de envío y de cobro.

#### Scenario: Consulta del detalle

- **WHEN** se solicita `GET /sales/{id}` de una orden existente
- **THEN** responde `200` con items, subtotal, descuento, envío, total, pagos y notas

#### Scenario: Orden inexistente

- **WHEN** se solicita un id que no existe
- **THEN** responde `404`

<!-- Pendiente: el CU05 paso 12 incluye el historial de movimientos de stock de la orden dentro del detalle; hoy esa historia sólo se consulta por producto. -->
