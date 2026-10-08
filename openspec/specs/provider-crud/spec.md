# provider-crud Spec

<!-- Fuente: docs/CASOS_DE_USO.md CU06; as-built -->

## Purpose

Cubre el alta, la lectura, la edición y la baja de proveedores, su búsqueda en el listado, la guarda de integridad al eliminar y el vínculo obligatorio entre productos y proveedor.

## Requirements

### Requirement: Alta de proveedor

`POST /providers` SHALL crear un proveedor con `name` obligatorio de 1 a 120 caracteres y los campos opcionales `contact`, `phone`, `email`, `cuit` y `notes`, respondiendo `201` con el proveedor creado y `active` en `true`.

#### Scenario: Alta válida

- **WHEN** se envía `POST /providers` con `name` y los campos opcionales
- **THEN** responde `201` con el proveedor creado, `active: true` y sus fechas de alta

#### Scenario: Sin nombre

- **WHEN** se envía `POST /providers` sin `name` o con `name` vacío
- **THEN** responde `422` y el proveedor no se crea

#### Scenario: Email con formato inválido

- **WHEN** se envía `email` que no tiene formato de correo
- **THEN** responde `422` con el detalle del campo

#### Scenario: Sin autenticación

- **WHEN** se llama `POST /providers` sin token de sesión
- **THEN** responde `401`

<!-- Pendiente: el CU06 paso 4 y A2 exigen validar el CUIT (11 dígitos con guiones opcionales) con `422`; el backend sólo limita el CUIT a 20 caracteres y no valida su formato. -->

### Requirement: Listado con búsqueda por nombre

`GET /providers` SHALL devolver los proveedores ordenados por nombre ascendente. El parámetro `search` SHALL filtrar por nombre de forma parcial e insensible a mayúsculas, y `active_only=true` SHALL devolver sólo los proveedores activos.

#### Scenario: Búsqueda parcial por nombre

- **WHEN** se envía `search` con un fragmento del nombre
- **THEN** se devuelven los proveedores cuyo nombre contiene ese fragmento, sin distinguir mayúsculas

#### Scenario: Búsqueda sin coincidencias

- **WHEN** `search` no coincide con ningún nombre
- **THEN** responde `200` con una lista vacía

#### Scenario: Sólo activos

- **WHEN** se envía `active_only=true`
- **THEN** se devuelven únicamente los proveedores con `active` en `true`

<!-- Pendiente: el CU06 exige búsqueda por nombre, contacto y CUIT; el backend sólo busca por nombre. El CU06 también pide que la grilla muestre la cantidad de productos asociados por proveedor y el conteo no se expone en la respuesta ni se muestra en la grilla (sólo se usa internamente para la guarda de borrado). -->

### Requirement: Edición de proveedor

`PATCH /providers/{id}` SHALL actualizar sólo los campos enviados y devolver el proveedor actualizado. Si el proveedor no existe SHALL responder `404`.

#### Scenario: Actualización parcial

- **WHEN** se envía `PATCH /providers/{id}` con `contact`
- **THEN** responde `200` con el contacto actualizado y el resto de los campos sin cambios

#### Scenario: Cambio de estado activo

- **WHEN** se envía `PATCH /providers/{id}` con `active: false`
- **THEN** el proveedor queda inactivo y sigue siendo listable sin `active_only`

#### Scenario: Proveedor inexistente

- **WHEN** se envía un `provider_id` que no existe
- **THEN** responde `404`

### Requirement: Baja protegida por productos asociados

`DELETE /providers/{id}` SHALL responder `204` y eliminar el proveedor cuando no tiene productos. Si tiene al menos un producto asociado SHALL responder `409` con un mensaje que indica que el proveedor tiene productos, sin eliminarlo.

#### Scenario: Proveedor sin productos

- **WHEN** se elimina un proveedor que no tiene productos
- **THEN** responde `204` y `GET /providers/{id}` posterior responde `404`

#### Scenario: Proveedor con productos

- **GIVEN** un proveedor con al menos un producto asignado
- **WHEN** se envía `DELETE /providers/{id}`
- **THEN** responde `409` con el mensaje "No se puede eliminar: el proveedor tiene productos asociados" y el proveedor sigue existiendo

#### Scenario: Proveedor inexistente

- **WHEN** se elimina un `provider_id` que no existe
- **THEN** responde `404`

<!-- Pendiente: el CU06 A1 pide que el mensaje indique la cantidad ("tiene N producto(s) asociado(s)"); el mensaje actual no incluye el número. -->

### Requirement: Proveedor obligatorio en los productos

`POST /products` SHALL exigir `provider_id` y SHALL verificar que el proveedor exista, respondiendo `422` cuando falta o no corresponde a un proveedor registrado.

#### Scenario: Producto sin proveedor

- **WHEN** se envía `POST /products` sin `provider_id`
- **THEN** responde `422` y el producto no se crea

#### Scenario: Proveedor inexistente

- **WHEN** `provider_id` no corresponde a ningún proveedor
- **THEN** responde `422` con el mensaje "El proveedor indicado no existe"

#### Scenario: Producto con proveedor válido

- **WHEN** se envía `POST /products` con un `provider_id` existente
- **THEN** responde `201` con el producto asociado a ese proveedor

### Requirement: Proveedor visible en el ABM de productos

La grilla y el formulario de productos SHALL mostrar y permitir seleccionar el proveedor, y el listado de productos SHALL poder filtrarse por `provider_id`.

#### Scenario: Filtro por proveedor

- **WHEN** se lista `GET /products?provider_id=<id>`
- **THEN** se devuelven sólo los productos de ese proveedor

#### Scenario: Proveedor sin productos en la grilla

- **WHEN** la grilla de productos se carga con un proveedor que aún no tiene productos
- **THEN** el producto no aparece en el filtrado y la lista queda vacía
