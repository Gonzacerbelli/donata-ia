# openspec/specs/dashboard-reports Spec

<!-- Fuente: docs/CASOS_DE_USO.md CU02; as-built -->

## Purpose

La capability describe el comportamiento del dashboard y los reportes implementados, incluyendo filtros por fecha y las métricas/endpoint reales expuestos por el backend.

## Requirements

### Requirement: Filtros por rango de fechas

El sistema SHALL permitir filtrar las métricas del dashboard por un rango de fechas aplicable a las órdenes/pagos.

#### Scenario: Rango por defecto aplicado
- **WHEN** el dashboard se carga sin parámetros de fecha
- **THEN** el frontend muestra el período preseleccionado según UI (rango definido en frontend) y las consultas incluyen rango si seleccionado

#### Scenario: Filtros desde/hasta aplicados
- **WHEN** el usuario selecciona fechas desde y hasta
- **THEN** las consultas de reportes incluyen date_from y date_to y reflejan el rango seleccionado

#### Scenario: Limpieza de filtros
- **WHEN** el usuario limpia el rango de fechas
- **THEN** las consultas de reportes se realizan sin parámetros de fecha

### Requirement: Reportes implementados en backend

El sistema SHALL exponer los reportes vía GET /reports/summary, GET /reports/top-products, GET /reports/low-stock y GET /reports/inventory-value.

#### Scenario: Resumen de ventas
- **WHEN** se solicita GET /reports/summary con opcionales date_from/date_to
- **THEN** el sistema devuelve las métricas de ventas para el rango

#### Scenario: Top de productos
- **WHEN** se solicita GET /reports/top-products con opcionales date_from/date_to y limit
- **THEN** el sistema devuelve el ranking de productos más vendidos para el rango

#### Scenario: Stock bajo
- **WHEN** se solicita GET /reports/low-stock
- **THEN** el sistema devuelve la lista de productos con stock bajo

#### Scenario: Valor de inventario
- **WHEN** se solicita GET /reports/inventory-value
- **THEN** el sistema devuelve el valor total de inventario calculado

<!-- Pendiente: CU02 describe GET /reports/dashboard consolidado; el código real expone /reports/summary, /reports/top-products, /reports/low-stock, /reports/inventory-value y el frontend compone el dashboard con esos endpoints. -->

### Requirement: Métricas mostradas en dashboard

El dashboard frontend SHALL mostrar métricas basadas en los reportes consumidos.

#### Scenario: KPI de ventas
- **WHEN** el dashboard carga datos de /reports/summary
- **THEN** se muestra "Ventas" (revenue) y "Órdenes" (sales_count) formateados en ARS

#### Scenario: KPI de cobranza
- **WHEN** el dashboard carga datos de /reports/summary
- **THEN** se muestra "Cobrado" (collected) y "Por cobrar" (receivable)

#### Scenario: Top productos en dashboard
- **WHEN** el dashboard carga datos de /reports/top-products
- **THEN** se muestra la tabla de productos más vendidos con cantidad y facturado para el rango

#### Scenario: Stock bajo y valor inventario
- **WHEN** el dashboard carga /reports/low-stock y /reports/inventory-value
- **THEN** se muestran valor de inventario, unidades y lista de productos con stock bajo

### Requirement: Navegabilidad desde KPIs

Los KPIs del dashboard SHALL permitir navegar a otros módulos con contexto de filtros.

#### Scenario: Navegación a órdenes desde KPIs
- **WHEN** el usuario hace click en un KPI relacionado a órdenes/ventas/cobranza
- **THEN** el sistema navega a /ordenes preservando los filtros de fecha (from/to) en la URL

#### Scenario: Navegación a productos desde stock bajo
- **WHEN** el usuario hace click en "Ver productos"
- **THEN** el sistema navega a /productos

### Requirement: Formato de moneda y fechas

El sistema SHALL formatear importes en pesos argentinos y trabajar con rangos de fecha.

#### Scenario: Formato ARS en KPIs y tablas
- **WHEN** se muestran importes monetarios en dashboard
- **THEN** los valores se formatean en pesos argentinos (ARS)

#### Scenario: Rangos válidos
- **WHEN** el usuario selecciona un rango inválido (date_from > date_to)
- **THEN** el frontend valida y no envía consulta al backend

#### Scenario: Fechas sin datos
- **WHEN** no existen datos para el rango seleccionado
- **THEN** las métricas muestran 0 y los listados muestran estado vacío

### Requirement: Acceso protegido a reportes

Todos los endpoints de /reports SHALL requerir autenticación.

#### Scenario: Reporte sin token
- **WHEN** se solicita cualquier endpoint de /reports sin autenticación
- **THEN** el sistema rechaza la solicitud con error no autenticado
