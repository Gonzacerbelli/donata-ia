# openspec/specs/auth-google Spec

<!-- Fuente: docs/CASOS_DE_USO.md CU01; as-built -->

## Purpose

La capability describe el flujo de autenticación OAuth 2.0 con Google implementado en el sistema (login, callback, intercambio de código a token y sesión actual).

## Requirements

### Requirement: Inicio de flujo OAuth con Google

El sistema SHALL exponer el inicio del flujo OAuth 2.0 con Google para redirigir al usuario al diálogo de consentimiento.

#### Scenario: Obtener URL de autorización de Google
- **WHEN** el usuario solicita iniciar sesión con Google
- **THEN** el sistema responde con la URL de autorización generada por el proveedor para el flujo OAuth 2.0

#### Scenario: Redirección al proveedor de Google
- **WHEN** el frontend recibe la URL de autorización
- **THEN** el navegador es redirigido a esa URL con los parámetros correspondientes para el diálogo de consentimiento

### Requirement: Callback de Google y creación/actualización de usuario

El sistema SHALL procesar el callback de Google, validar el código recibido y crear o actualizar el usuario autenticado.

#### Scenario: Callback exitoso crea o actualiza usuario
- **WHEN** Google redirige con código y estado válidos
- **THEN** el sistema autentica con Google, crea el usuario si no existe, actualiza sus datos si existe y marca último acceso

#### Scenario: Usuario inactivo rechaza login
- **WHEN** el usuario existe pero está marcado como inactivo
- **THEN** el sistema redirige al login con mensaje de error y no emite sesión

#### Scenario: Error o parámetros faltantes en callback
- **WHEN** Google retorna error o faltan code/state en el callback
- **THEN** el sistema redirige al login con mensaje de error apropiado

#### Scenario: Validación de estado CSRF
- **WHEN** el parámetro state no coincide con el esperado
- **THEN** el sistema rechaza el callback y redirige al login con error

### Requirement: Intercambio de código a token JWT

El sistema SHALL permitir intercambiar un código temporal por un token de acceso JWT válido.

#### Scenario: Intercambio exitoso
- **WHEN** se envía un código válido y no expirado
- **THEN** el sistema devuelve un token JWT de acceso y los datos del usuario

#### Scenario: Código inválido o expirado
- **WHEN** el código no existe o ya fue utilizado/expirado
- **THEN** el sistema rechaza la solicitud con error de credenciales inválidas

#### Scenario: Usuario inactivo al intercambiar código
- **WHEN** el usuario asociado al código está inactivo
- **THEN** el sistema rechaza la solicitud con error de usuario desactivado

### Requirement: Consulta de sesión actual

El sistema SHALL permitir consultar los datos del usuario autenticado con un token válido.

#### Scenario: Sesión válida
- **WHEN** la solicitud incluye un JWT válido
- **THEN** el sistema devuelve la información del usuario autenticado

#### Scenario: Token ausente o inválido
- **WHEN** la solicitud no incluye token válido
- **THEN** el sistema rechaza la solicitud con error de no autenticado

### Requirement: Autenticación local de emergencia

El sistema SHALL soportar autenticación local con usuario y contraseña para casos de emergencia.

#### Scenario: Login local exitoso
- **WHEN** se envían credenciales locales válidas
- **THEN** el sistema emite un token JWT y devuelve los datos del usuario

#### Scenario: Credenciales locales inválidas
- **WHEN** usuario o contraseña son incorrectos
- **THEN** el sistema rechaza la solicitud con error de credenciales inválidas

### Requirement: Logout gestionado en cliente

El sistema SHALL NO exponer un endpoint de logout; la invalidación de sesión es responsabilidad del cliente.

#### Scenario: Logout del cliente
- **WHEN** el usuario solicita cerrar sesión desde el frontend
- **THEN** el cliente elimina el token almacenado y redirige a la pantalla de login

### Requirement: Endpoints OAuth implementados

El sistema SHALL implementar el flujo OAuth con los endpoints concretos GET /auth/google, GET /auth/google/callback y POST /auth/exchange.

#### Scenario: Inicio OAuth
- **WHEN** se consulta el inicio de Google
- **THEN** el sistema responde en GET /auth/google con la URL de autorización

#### Scenario: Callback OAuth
- **WHEN** Google redirige al backend
- **THEN** el backend recibe la respuesta en GET /auth/google/callback

#### Scenario: Intercambio de código
- **WHEN** el frontend intercambia el código recibido
- **THEN** el sistema procesa la solicitud en POST /auth/exchange

<!-- Pendiente: La documentación de CU01 menciona GET /auth/google/login y endpoint de logout; el código real usa GET /auth/google, POST /auth/exchange y no tiene endpoint de logout (logout es cliente-side). -->