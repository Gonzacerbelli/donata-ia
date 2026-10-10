# user-directory Specification

## Purpose
Directorio de s�lo lectura de los usuarios activos del sistema, para asignar tarjetas de trabajo y
filtrar el tablero por usuario asignado, sin roles ni permisos.

## Requirements

### Requirement: Listado de usuarios activos

`GET /users` SHALL devolver los usuarios activos con su id, nombre y email, y SHALL exigir un JWT
v�lido.

#### Scenario: Listado de activos

- **WHEN** un usuario autenticado consulta `GET /users`
- **THEN** recibe la lista de usuarios activos con id, nombre y email

#### Scenario: Usuario inactivo excluido

- **WHEN** un usuario tiene `active` en falso
- **THEN** no aparece en el listado

#### Scenario: Sin token

- **WHEN** se consulta `GET /users` sin un JWT v�lido
- **THEN** responde `401`
