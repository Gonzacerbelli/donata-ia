# openspec/specs/product-crud Spec

<!-- Fuente: docs/CASOS_DE_USO.md CU03; as-built -->

## Purpose

La capability describe el ABM de productos implementado, incluyendo validaciones, proveedor obligatorio, filtros, baja lógica/física, y el hecho de que el stock no se edita desde el ABM.

## Requirements

### Requirement: Listado de productos con filtros

El sistema SHALL permitir listar productos con filtros y búsqueda.

#### Scenario: Listado básico
- **WHEN** se solicita GET /products (requerido autenticado)
- **THEN** el sistema devuelve la lista de productos

#### Scenario: Filtro por búsqueda
- **WHEN** se incluye search en la consulta
- **THEN** el sistema filtra productos por nombre/categoría según implementación

#### Scenario: Filtro por categoría y proveedor
- **WHEN** se incluyen category y provider_id
- **THEN** el sistema aplica ambos filtros a la consulta

#### Scenario: Filtro por activos
- **WHEN** se incluye active_only (por defecto True según router)
- **THEN** el sistema retorna solo productos activos cuando corresponde

### Requirement: Creación de producto

El sistema SHALL permitir crear un nuevo producto con validaciones obligatorias.

#### Scenario: Creación exitosa con proveedor válido
- **WHEN** se envían datos válidos y provider_id existe
- **THEN** el sistema crea el producto y responde 201 con el producto creado

#### Scenario: Proveedor obligatorio
- **WHEN** no se indica provider_id o es vacío
- **THEN** el sistema rechaza la creación con error de validación (422)

#### Scenario: Proveedor inexistente
- **WHEN** se indica provider_id que no existe
- **THEN** el sistema rechaza la creación con error indicando que el proveedor no existe (422)

#### Scenario: Creación con stock inicial
- **WHEN** se envía stock inicial en alta
- **THEN** el sistema persiste el stock inicial del producto

### Requirement: Consulta de producto individual

El sistema SHALL permitir obtener un producto por su identificador.

#### Scenario: Consulta exitosa
- **WHEN** se solicita GET /products/{id} con id válido
- **THEN** el sistema devuelve el producto solicitado

#### Scenario: Producto inexistente
- **WHEN** se solicita un id que no existe
- **THEN** el sistema responde con error not found (404)

### Requirement: Edición de producto

El sistema SHALL permitir actualizar un producto existente.

#### Scenario: Actualización exitosa
- **WHEN** se envía PATCH /products/{id} con datos válidos
- **THEN** el sistema actualiza el producto y devuelve el producto actualizado

#### Scenario: Validación de proveedor en edición
- **WHEN** se actualiza provider_id a un valor inexistente
- **THEN** el sistema rechaza la actualización con error (422) indicando que el proveedor no existe

#### Scenario: Stock no editable desde ABM
- **WHEN** se intenta modificar el campo stock desde el formulario de edición
- **THEN** el frontend no permite editar stock en el ABM (se gestiona por ajuste de stock) y el stock no se actualiza desde esta vía

<!-- Pendiente: CU03 indica "El stock no es editable desde aquí"; código/frontend reflejan ajuste separado (POST /products/stock/adjust, CU08). -->

### Requirement: Baja lógica de producto

El sistema SHALL permitir desactivar un producto manteniéndolo en el histórico.

#### Scenario: Desactivación exitosa
- **WHEN** se actualiza el producto con active: false vía PATCH /products/{id}
- **THEN** el producto queda inactivo y disponible para consulta histórica

#### Scenario: Producto inactivo excluido de catálogo operativo
- **WHEN** active_only es true en listado
- **THEN** los productos inactivos no aparecen en el listado operativo

#### Scenario: Producto inactivo excluido de selector de nuevas órdenes
- **WHEN** se listan productos para crear nueva orden (catálogo operativo)
- **THEN** los productos inactivos no aparecen disponibles para selección

### Requirement: Baja física de producto

El sistema SHALL permitir eliminar físicamente un producto previa validación de referencias.

#### Scenario: Eliminación exitosa sin referencias
- **WHEN** el producto no tiene ventas asociadas
- **THEN** el sistema elimina el producto y responde 204

#### Scenario: Eliminación rechazada por ventas asociadas
- **WHEN** el producto figura en al menos una venta/orden
- **THEN** el sistema rechaza la eliminación con conflicto (409) y mensaje explicativo

#### Scenario: Producto inexistente al eliminar
- **WHEN** se intenta eliminar un producto que no existe
- **THEN** el sistema responde not found (404)

### Requirement: Ajuste de stock separado

El sistema SHALL gestionar variaciones de stock mediante POST /products/stock/adjust, independiente del CRUD.

#### Scenario: Ajuste de stock vía endpoint dedicado
- **WHEN** se envía POST /products/stock/adjust con product_id, quantity, reason
- **THEN** el sistema registra el movimiento y actualiza el stock del producto

#### Scenario: Historial de movimientos
- **WHEN** se consulta GET /products/{product_id}/moves
- **THEN** el sistema devuelve el historial de movimientos de stock del producto

### Requirement: Validaciones de negocio en productos

El sistema SHALL aplicar validaciones de precios, stock, stock mínimo y proveedor.

#### Scenario: Precios y costos no negativos
- **WHEN** se envían valores negativos para precio/costo/stock/min_stock en creación o actualización
- **THEN** el sistema rechaza con error de validación según esquema

#### Scenario: Proveedor referencial válido
- **WHEN** se guarda producto con provider_id
- **THEN** el sistema valida que el proveedor exista en la colección providers

#### Scenario: Campos obligatorios en alta
- **WHEN** faltan campos obligatorios (nombre, provider_id, precio minorista según esquema/UI)
- **THEN** el sistema rechaza la solicitud con error de validación

### Requirement: Acceso protegido a productos

Todos los endpoints de /products SHALL requerir autenticación.

#### Scenario: Acceso sin token
- **WHEN** se solicita cualquier endpoint de /products sin autenticación
- **THEN** el sistema rechaza con error no autenticado
