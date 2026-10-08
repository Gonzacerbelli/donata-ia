# data-export Spec

<!-- Fuente: docs/CASOS_DE_USO.md CU10; as-built -->

## Purpose

Cubre la descarga de CSV y Excel desde las grillas de órdenes, clientes y productos, con exactamente los mismos filtros activos en pantalla y el formato que espera Excel en Windows.

## Requirements

### Requirement: GET /exports/{entidad}.{csv|xlsx} exporta las tres entidades

El endpoint autenticado SHALL aceptar las entidades `sales`/`clients`/`products` (y sus alias en español: `ordenes`, `ventas`, `clientes`, `productos`) en formatos `csv` y `xlsx`, y SHALL responder con `Content-Disposition: attachment`.

#### Scenario: Exportar órdenes en CSV

- **WHEN** un usuario autenticado pide `GET /exports/ordenes.csv`
- **THEN** el servidor responde `200` con `text/csv`, cuerpo en bytes y `Content-Disposition: attachment`

#### Scenario: Exportar productos en Excel

- **WHEN** se pide `GET /exports/products.xlsx`
- **THEN** el servidor responde `200` con el content type de XLSX y el archivo descargable

#### Scenario: Formato no soportado

- **WHEN** se pide `GET /exports/sales.pdf`
- **THEN** el servidor responde `422` con "Formato no soportado (usá csv o xlsx)"

#### Scenario: Entidad desconocida

- **WHEN** se pide exportar una entidad que no es `sales`, `clients` ni `products`
- **THEN** el servidor responde `422` con "Entidad no exportable"

#### Scenario: Sin sesión

- **WHEN** la petición llega sin token válido
- **THEN** el servidor responde `401` y no se genera ningún archivo

### Requirement: La exportación respeta exactamente los filtros activos

El export SHALL ejecutar la misma consulta que el listado correspondiente con los parámetros de la query string, con el mismo orden y sin límite de paginación; sólo SHALL exportarse el snapshot de los filtros enviados en ese request.

#### Scenario: Filtros de estado y rango

- **GIVEN** la grilla de órdenes filtra estado `pendiente` del `01/09/2026` al `30/09/2026`
- **WHEN** el usuario exporta a CSV
- **THEN** el archivo contiene únicamente las órdenes pendientes de ese rango, en el mismo orden que el listado

#### Scenario: Búsqueda de texto

- **WHEN** se exporta con el parámetro `search=Juan`
- **THEN** el archivo sólo incluye registros que coinciden con "Juan"

#### Scenario: Filtros que cambian durante la descarga

- **WHEN** el usuario modifica los filtros en pantalla mientras se genera el archivo
- **THEN** el archivo refleja los parámetros enviados en ese request, no el estado posterior

### Requirement: El export de órdenes incluye los campos derivados del negocio

Las órdenes SHALL exportar número, fecha, cliente, tipo de cliente, estado, estado de cobro (`sin_pago`/`parcial`/`pagada`), ítems en texto legible, cantidad de ítems, subtotal, descuento, costo de envío, total, pagado, saldo y notas.

#### Scenario: Ítems en texto legible

- **WHEN** una orden tiene dos unidades de un producto y un envío
- **THEN** la columna "Ítems" muestra "2 x Taza; 1 x Envío" y la columna "Cant. de ítems" muestra 3

#### Scenario: Estado de cobro derivado

- **GIVEN** una orden con pagos parciales
- **WHEN** se exporta
- **THEN** el estado de cobro es "parcial" y el saldo es total menos pagado

#### Scenario: Cliente de la orden

- **WHEN** se exporta una orden
- **THEN** la columna "Cliente" muestra el nombre del cliente asociado

### Requirement: El export de clientes incluye contacto y métricas derivadas

Los clientes SHALL exportar nombre, teléfono, email, Instagram, dirección, tipo, conteo de órdenes, total facturado, saldo pendiente, notas y fecha de alta; las órdenes canceladas no SHALL contarse.

#### Scenario: Métricas del cliente

- **GIVEN** un cliente con dos órdenes, una de ellas cancelada
- **WHEN** se exporta
- **THEN** el conteo de órdenes es 1 y total facturado y saldo corresponden sólo a las no canceladas

#### Scenario: Cliente sin órdenes

- **WHEN** se exporta un cliente que nunca compró
- **THEN** las columnas de órdenes, total facturado y saldo pendiente valen 0

### Requirement: El export de productos incluye catálogo, proveedor y stock

Los productos SHALL exportar nombre, categoría, proveedor, unidad, precios minorista y mayorista, costo, stock, stock mínimo y estado (`activo`/`inactivo`), respetando el filtro de activos recibido en la query.

#### Scenario: Proveedor asignado

- **WHEN** se exporta un producto con proveedor
- **THEN** la columna "Proveedor" muestra el nombre de ese proveedor

#### Scenario: Incluir inactivos

- **GIVEN** el filtro `active_only=false`
- **WHEN** se exporta productos
- **THEN** también aparecen filas con estado "inactivo"

### Requirement: Los montos se exportan como números y las fechas en DD/MM/AAAA

Las columnas monetarias SHALL exportarse numéricas y utilizables para cálculo: en XLSX con formato de moneda con separador de miles y en CSV como número plano (45000). Las fechas SHALL escribirse en formato DD/MM/AAAA.

#### Scenario: XLSX con formato monetario

- **WHEN** se abre el archivo de órdenes en Excel
- **THEN** las celdas de subtotal, total, pagado y saldo son numéricas con formato de moneda y separador de miles

#### Scenario: CSV con montos planos

- **WHEN** se importa el CSV en Excel
- **THEN** los montos se cargan como números sin separador de miles

#### Scenario: Fechas

- **WHEN** el archivo contiene una orden del 3 de septiembre de 2026
- **THEN** la celda muestra 03/09/2026

### Requirement: El CSV se genera en UTF-8 con BOM para Excel en Windows

El CSV SHALL generarse en UTF-8 con BOM y las celdas de texto del XLSX SHALL guardarse como texto, de modo que acentos y ñ se visualicen correctamente al abrirlos con Excel en Windows.

#### Scenario: Nombres con acentos y ñ

- **WHEN** se exporta un cliente llamado "Nuñez, Asunción"
- **THEN** el archivo se abre en Excel de Windows mostrando acentos y ñ correctamente

#### Scenario: Celdas con texto tipo fórmula

- **WHEN** una nota contiene "=HYPERLINK(1)"
- **THEN** la celda del XLSX se guarda como texto y no se ejecuta como fórmula

### Requirement: El nombre del archivo describe entidad, rango y filtros

El nombre SHALL viajar en `Content-Disposition` e incluir la entidad, el rango de fechas y los filtros aplicados, por ejemplo `ordenes_2026-09-01_a_2026-09-30_pendientes.xlsx`.

#### Scenario: Rango y estado

- **GIVEN** filtros de fecha del 01/09/2026 al 30/09/2026 y estado `pendiente`
- **WHEN** se exportan órdenes a XLSX
- **THEN** el archivo descargado se llama `ordenes_2026-09-01_a_2026-09-30_pendientes.xlsx`

#### Scenario: Sin filtros

- **WHEN** se exportan clientes sin ningún filtro
- **THEN** el nombre es la entidad con la extensión, por ejemplo `clientes.csv`

#### Scenario: Texto de búsqueda

- **WHEN** el filtro de texto es "Juan Pérez"
- **THEN** el nombre lo normaliza en minúsculas separadas por guiones

### Requirement: La descarga se hace con una petición autenticada sin navegar

El frontend SHALL llamar a `GET /exports/...` con la cabecera `Authorization`, SHALL recibir un blob y SHALL disparar la descarga con un enlace temporal; el token no SHALL viajar en la URL y la vista no SHALL recargarse ni perder la sesión.

#### Scenario: Descarga desde la grilla

- **WHEN** el usuario pulsa "Exportar CSV"
- **THEN** el navegador descarga el archivo y la pantalla sigue en el mismo estado, con la sesión activa

#### Scenario: Error durante la exportación

- **WHEN** el servidor responde un error
- **THEN** la interfaz muestra el mensaje debajo de los botones y no cambia de pantalla

### Requirement: El volumen máximo de una exportación es de 10 000 filas

Si el resultado supera los 10 000 registros, el servidor SHALL responder `422` pidiendo acotar el rango o los filtros, en lugar de generar un archivo gigante.

#### Scenario: Volumen excedido

- **WHEN** los filtros seleccionan más de 10 000 registros
- **THEN** el servidor responde `422` con "Demasiados registros (N). Acotá el rango o los filtros."

#### Scenario: Volumen exacto en el límite

- **WHEN** los filtros seleccionan 10 000 registros
- **THEN** el servidor responde `200` con el archivo completo

### Requirement: La exportación respeta un rate limit propio

La exportación SHALL admitir como máximo 10 pedidos por usuario y minuto; al excederlo el servidor SHALL responder `429` con `Retry-After` y la interfaz SHALL bloquear los botones durante esa espera.

#### Scenario: Límite excedido

- **WHEN** un usuario supera los 10 pedidos de exportación en un minuto
- **THEN** el servidor responde `429` con `Retry-After`

#### Scenario: Espera en la interfaz

- **WHEN** la interfaz recibe un `429`
- **THEN** los botones quedan deshabilitados con el tiempo de espera y se reactivan al terminar

### Requirement: Los botones de exportación están deshabilitados sin datos

Los botones "Exportar CSV" y "Exportar Excel" SHALL deshabilitarse cuando el listado activo esté vacío, y también mientras dure la descarga o la espera de rate limit.

<!-- Pendiente: tooltip "No hay datos para exportar con los filtros actuales" del CU10 -->

#### Scenario: Listado vacío

- **GIVEN** los filtros activos no devuelven registros
- **WHEN** se renderiza la grilla
- **THEN** los botones de exportación están deshabilitados

#### Scenario: Descarga en curso

- **WHEN** el usuario dispara una exportación
- **THEN** ese botón muestra el indicador de carga hasta terminar

#### Scenario: Exportación vía API sin registros

- **WHEN** se pide directamente un export con filtros que no matchean ningún registro
- **THEN** el servidor responde `200` con un archivo que contiene sólo el encabezado

### Requirement: El contenido peligroso se escapa en CSV y XLSX

El CSV SHALL escapar comillas y saltos de línea con comillas dobles y SHALL neutralizar las celdas que empiezan con `=`, `+`, `-` o `@`; el XLSX SHALL guardar esas celdas como texto para que Excel no las ejecute como fórmulas.

#### Scenario: Celda que empieza con signo de igual

- **WHEN** una nota contiene "=1+1"
- **THEN** en el CSV la celda aparece como "'=1+1" y en el XLSX como texto

#### Scenario: Texto con comas y saltos de línea

- **WHEN** un campo contiene comas, comillas o saltos de línea
- **THEN** el CSV lo envuelve en comillas dobles con los saltos escapados y el XLSX lo guarda en una celda multilínea
