# stock-management Spec

<!-- Fuente: docs/CASOS_DE_USO.md CU08; as-built -->

## Purpose

Cubre el ajuste manual de stock de productos, el historial auditable de movimientos (por producto y global), los movimientos generados por órdenes, la atomicidad de las actualizaciones y el resaltado visual del stock en la grilla.

## Requirements

### Requirement: Ajuste manual de stock

`POST /products/stock/adjust` SHALL recibir `product_id`, `quantity` y `reason`, actualizar el stock del producto y responder `200` con el producto actualizado. El motivo es obligatorio y un producto inexistente responde `404`.

<!-- Pendiente: el CU08 describe `POST /products/{id}/stock`; el endpoint real es `POST /products/stock/adjust` con el `product_id` en el cuerpo. -->

#### Scenario: Ajuste positivo

- **WHEN** se envía `POST /products/stock/adjust` con `quantity: 5` y un motivo
- **THEN** responde `200` con el stock del producto incrementado en 5

#### Scenario: Ajuste negativo

- **WHEN** se envía `quantity: -3` con stock suficiente
- **THEN** responde `200` con el stock del producto decrementado en 3

#### Scenario: Sin motivo

- **WHEN** `reason` llega vacío
- **THEN** responde `422` y el stock no cambia

#### Scenario: Producto inexistente

- **WHEN** `product_id` no corresponde a un producto
- **THEN** responde `404` y no se registra ningún movimiento

#### Scenario: Sin autenticación

- **WHEN** se llama el endpoint sin token de sesión
- **THEN** responde `401`

<!-- Pendiente: el CU08 A1 espera `422` para `quantity = 0`; el backend acepta el cero y registra un movimiento sin efecto. El CU08 A2 espera `400` cuando el ajuste dejaría el stock negativo; esa guarda no está en el backend (sólo en el formulario). -->

### Requirement: Registro del movimiento de ajuste

Cada ajuste manual SHALL registrar un movimiento con el producto, la cantidad con signo, el stock resultante, el motivo, el tipo `ajuste` y la fecha, sin referencia a otra entidad.

#### Scenario: Movimiento tras un ajuste

- **WHEN** se aplica un ajuste de `+5` a un producto con stock 10
- **THEN** el movimiento más reciente tiene `quantity` 5, `stock_after` 15, `ref_type` `ajuste`, `ref_id` nulo y el motivo enviado

#### Scenario: Motivo del movimiento

- **WHEN** se envía el motivo "Merma"
- **THEN** el movimiento registrado muestra "Merma" como motivo

<!-- Pendiente: el CU08 pide clasificar los ajustes positivos como `compra` y los negativos como `ajuste`; el código registra siempre `ajuste`, por lo que el tipo `compra` no se genera en ningún flujo. -->

### Requirement: Validación del ajuste en el formulario

El formulario de ajuste de stock SHALL rechazar en el cliente cantidades que no sean enteras distintas de cero, motivos vacíos y ajustes negativos que dejarían el stock por debajo de cero, mostrando el error en español antes de enviar la petición.

#### Scenario: Cantidad cero

- **WHEN** el usuario envía cantidad 0
- **THEN** se muestra "Ingresá un entero distinto de cero" y no se envía la petición

#### Scenario: Ajuste negativo mayor al stock

- **WHEN** el usuario pide descontar más unidades de las disponibles
- **THEN** se muestra "El ajuste no puede dejar el stock en negativo" y no se envía la petición

#### Scenario: Motivo vacío en el formulario

- **WHEN** el usuario deja el motivo sin completar
- **THEN** se muestra "Indicá el motivo del ajuste" y no se envía la petición

### Requirement: Historial de movimientos consultable

`GET /products/{id}/moves` SHALL devolver los movimientos de un producto y `GET /stock/moves` SHALL devolver el historial global con `product_id` opcional, ambos ordenados por fecha descendente y acotados por `limit` entre 1 y 500 (por defecto 50 en el historial del producto y 100 en el global).

#### Scenario: Historial de un producto

- **WHEN** se consulta `GET /products/{id}/moves`
- **THEN** responde `200` con los movimientos de ese producto, el más reciente primero

#### Scenario: Historial global filtrado

- **WHEN** se consulta `GET /stock/moves?product_id=<id>`
- **THEN** responde `200` sólo con los movimientos de ese producto

#### Scenario: Historial global sin filtro

- **WHEN** se consulta `GET /stock/moves` sin `product_id`
- **THEN** responde `200` con los movimientos de todos los productos

#### Scenario: Límite fuera de rango

- **WHEN** se envía `limit` menor que 1 o mayor que 500
- **THEN** responde `422`

#### Scenario: Sin movimientos

- **WHEN** un producto nunca tuvo movimientos
- **THEN** responde `200` con una lista vacía

<!-- Pendiente: el CU08 prevé un toast de "deshacer" que genera un ajuste inverso y un enlace a la orden dentro del historial; hoy el historial sólo muestra cantidad, stock resultante, motivo, tipo y fecha. -->

### Requirement: Trazabilidad completa de cada movimiento

Todo movimiento SHALL registrar la cantidad con signo, el stock resultante luego de aplicarlo, el motivo, el tipo y la fecha; los movimientos originados en órdenes SHALL incluir además la referencia a la orden.

#### Scenario: Campos del movimiento

- **WHEN** se produce cualquier movimiento de stock
- **THEN** el registro expone cantidad, stock resultante, motivo, tipo, referencia y fecha

#### Scenario: Orden en el historial del producto

- **WHEN** se consulta el historial de un producto vendido por una orden
- **THEN** los movimientos de esa venta muestran el tipo `venta` con la referencia a la orden

### Requirement: Movimientos generados por órdenes

Crear o reactivar una orden SHALL descontar stock con movimientos de tipo `venta` referidos a la orden; cancelar o eliminar una orden SHALL restituir stock con movimientos de tipo `cancelacion` referidos a la orden.

#### Scenario: Crear orden

- **WHEN** se crea una orden con un producto de catálogo
- **THEN** se registra un movimiento `venta` con `ref_id` igual al id de la orden y cantidad negativa

#### Scenario: Cancelar orden

- **WHEN** una orden pasa a `cancelado`
- **THEN** se registra un movimiento `cancelacion` con `ref_id` igual al id de la orden y cantidad positiva

#### Scenario: Reactivar orden

- **WHEN** una orden cancelada vuelve a un estado activo
- **THEN** se registra un movimiento `venta` con `ref_id` igual al id de la orden y cantidad negativa

#### Scenario: Eliminar orden

- **WHEN** se elimina una orden activa sin pagos
- **THEN** se registran movimientos `cancelacion` referidos a la orden y el stock vuelve al valor previo

### Requirement: Stock insuficiente en descuentos por venta

Los descuentos de stock originados en ventas SHALL exigir stock suficiente de forma atómica: si no hay stock, la operación SHALL responder `400` nombrando el producto y el descuento no se aplica.

#### Scenario: Venta sin stock

- **WHEN** una orden intenta descontar más unidades de las disponibles
- **THEN** responde `400` con "Stock insuficiente para '<producto>'" y el stock no cambia

### Requirement: Actualizaciones atómicas bajo concurrencia

Las actualizaciones de stock SHALL aplicarse con una única operación condicional sobre el producto, de modo que dos solicitudes simultáneas no se pisen y cada movimiento registre el stock resultante real de ese instante.

#### Scenario: Dos ajustes simultáneos

- **WHEN** se procesan dos ajustes concurrentes sobre el mismo producto
- **THEN** ambos quedan aplicados y cada movimiento refleja el stock resultante de su propia operación

#### Scenario: Ajuste simultáneo con venta

- **WHEN** un ajuste y una venta se procesan a la vez sobre el mismo producto
- **THEN** el stock final es coherente con ambas operaciones y ninguna quedó a medias

### Requirement: Resaltado visual del stock en la grilla

El listado de productos SHALL mostrar el stock con color semántico: "Agotado" en rojo cuando el stock es 0, tono ámbar cuando el stock no supera el stock mínimo y color normal cuando lo supera.

#### Scenario: Producto agotado

- **WHEN** un producto tiene stock 0
- **THEN** la columna de stock muestra "Agotado" en rojo

#### Scenario: Producto en stock mínimo

- **WHEN** un producto tiene stock menor o igual a su stock mínimo y distinto de cero
- **THEN** la columna de stock muestra la cantidad en ámbar

#### Scenario: Stock saludable

- **WHEN** un producto tiene stock mayor que su stock mínimo
- **THEN** la columna de stock muestra la cantidad con el color normal
