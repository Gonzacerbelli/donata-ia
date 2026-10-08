# openspec/specs/client-crud Spec

<!-- Fuente: docs/CASOS_DE_USO.md CU04; as-built -->

## Purpose

La capability describe el ABM de clientes implementado, incluyendo búsqueda multi-campo, tipos de cliente, vista de actividad, validaciones y la regla de no eliminar clientes con historial.

## Requirements

### Requirement: Listado de clientes

El sistema SHALL permitir listar clientes con búsqueda y filtros.

#### Scenario: Listado básico
- **WHEN** se solicita GET /clients (requerido autenticado)
- **THEN** el sistema devuelve la lista de clientes ordenada por nombre

#### Scenario: Búsqueda multi-campo
- **WHEN** se incluye search en la consulta
- **THEN** el sistema busca coincidencias parciales por nombre, teléfono e Instagram (según repositorio)

#### Scenario: Filtro por tipo de cliente
- **WHEN** se incluye client_type (minorista/mayorista/ambos)
- **THEN** el sistema filtra clientes por ese tipo

### Requirement: Creación de cliente

El sistema SHALL permitir crear un nuevo cliente con validaciones.

#### Scenario: Creación exitosa
- **WHEN** se envían datos válidos para POST /clients
- **THEN** el sistema crea el cliente y responde 201

#### Scenario: Campos obligatorios
- **WHEN** falta nombre (obligatorio)
- **THEN** el sistema rechaza la creación con error de validación (422)

#### Scenario: Validación de formato de email
- **WHEN** se envía email con formato inválido
- **THEN** el sistema rechaza con error de validación por campo (422)

### Requirement: Consulta de cliente individual

El sistema SHALL permitir obtener un cliente por identificador.

#### Scenario: Consulta exitosa
- **WHEN** se solicita GET /clients/{id}
- **THEN** el sistema devuelve el cliente solicitado

#### Scenario: Cliente inexistente
- **WHEN** se solicita un id que no existe
- **THEN** el sistema responde not found (404)

### Requirement: Edición de cliente

El sistema SHALL permitir actualizar un cliente existente.

#### Scenario: Actualización parcial exitosa
- **WHEN** se envía PATCH /clients/{id} con campos parciales
- **THEN** el sistema actualiza solo los campos enviados y devuelve el cliente actualizado

#### Scenario: Validaciones en edición
- **WHEN** se actualiza email con formato inválido
- **THEN** el sistema rechaza con error de validación (422)

#### Scenario: Cliente inexistente al editar
- **WHEN** se intenta editar un cliente inexistente
- **THEN** el sistema responde not found (404)

### Requirement: Resumen de actividad del cliente

El frontend SHALL mostrar el resumen de actividad del cliente (órdenes, facturado, saldo).

#### Scenario: Resumen visible en frontend
- **WHEN** el usuario abre el resumen del cliente
- **THEN** el frontend muestra información de actividad del cliente (órdenes, facturado, saldo) según UI

### Requirement: Baja de cliente con validación de historial

El sistema SHALL rechazar la eliminación de clientes con ventas asociadas.

#### Scenario: Eliminación rechazada por ventas asociadas
- **WHEN** el cliente tiene ventas asociadas
- **THEN** el sistema rechaza la eliminación con conflicto (409) y mensaje explicativo indicando que tiene ventas registradas

#### Scenario: Mensaje explicativo en caso de conflicto
- **WHEN** se rechaza la eliminación por historial
- **THEN** el sistema devuelve error con mensaje "No se puede eliminar: el cliente tiene ventas registradas" (409)

#### Scenario: Cliente inexistente al eliminar
- **WHEN** se intenta eliminar un cliente inexistente
- **THEN** el sistema responde not found (404)

### Requirement: Detección de duplicados sugerida

El sistema SHALL gestionar posibles duplicados en creación con mensaje explicativo cuando corresponda.

#### Scenario: Detección de duplicados (comportamiento documentado)
- **WHEN** se intenta crear cliente con nombre y teléfono similares a uno existente
- **THEN** el backend puede responder con conflicto (409) sugiriendo cliente existente según CU04; en implementación actual el servicio crea directamente (sin chequeo de duplicados explícito) <!-- Pendiente: CU04 menciona detección de duplicados (mismo nombre y teléfono) con 409 y sugerencia; el código actual de create_client no implementa este chequeo explícito. -->

### Requirement: Acceso protegido a clientes

Todos los endpoints de /clients SHALL requerir autenticación.

#### Scenario: Acceso sin token
- **WHEN** se solicita cualquier endpoint de /clients sin autenticación
- **THEN** el sistema rechaza con error no autenticado
