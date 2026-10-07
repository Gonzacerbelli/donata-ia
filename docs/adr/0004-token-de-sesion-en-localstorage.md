# 0004. Token de sesión en localStorage con validación de expiración en cliente

**Estado:** Aceptada
**Fecha:** 20261007
**Contexto:** El frontend recibe un JWT en el login (local u OAuth) y tiene que mantener la
sesión entre recargas de página, proteger las rutas y saber cuándo el token ya no sirve.

## Alternativas consideradas

1. **Cookie `httpOnly` con `SameSite`** — el servidor setea la cookie y el JS no puede leerla.
   - A favor: inmune al robo por XSS; es la opción más segura contra ese vector.
   - En contra: exige cambiar la autenticación de header `Authorization` a cookie, revisar CSRF
     (el token de cabecera no protege por sí solo), y volver a tocar backend, CORS y tests.
2. **Token en memoria** (estado de React, sin persistencia).
   - A favor: desaparece al cerrar la pestaña.
   - En contra: se pierde la sesión en cada recarga, lo que rompe la experiencia esperada.
3. **`localStorage` + validación de `exp` en cliente** (elegida).
   - A favor: simple, persistente, sin cambiar el contrato de la API.
   - En contra: accesible por JS; si hay XSS, el token es robable.

## Decisión

El JWT vive en `localStorage` (`donata.token`) y viaja **sólo** en el header `Authorization`,
nunca en la URL. `tokenStore.get()` decodifica el payload y, si `exp` venció o el payload es
ilegible, **borra el token y devuelve `null`**; `ProtectedRoute` redirige al login sin siquiera
intentar la petición. El servidor sigue siendo la única autoridad: cualquier token vencido o
alterado devuelve `401` y el interceptor limpia la sesión.

La mitigación elegida contra XSS es la otra cara de la moneda: **no se usa
`dangerouslySetInnerHTML` en ninguna parte de la app** y toda salida de la API y del asistente
se renderiza como texto (React escapa). No hay cookies, por lo que CSRF no aplica.

## Consecuencias

**A favor:** contrato de API intacto; recarga de página conserva la sesión; doble validación
(cliente para UX, servidor para seguridad).

**En contra:** un XSS robaría el token. Si el producto crece, migrar a cookie `httpOnly` +
`SameSite=Strict` con CSRF token (ver alternativa 1).

**Impacto en el código:** `frontend/src/lib/token.ts`, `frontend/src/features/auth/AuthProvider.tsx`,
`frontend/src/features/auth/components/ProtectedRoute.tsx`, `frontend/src/lib/http.ts`.
