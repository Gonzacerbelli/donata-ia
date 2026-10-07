# AGENTS.md — Frontend Donata IA

> Reglas específicas del frontend. **Leé también `AGENTS.md` de la raíz**: eso no se repite acá.

---

## Stack

React 19 · TypeScript (estricto) · Vite · Tailwind CSS · TanStack Query · React Router ·
Zod · axios o fetch · Vitest · Playwright

## Estructura

```
frontend/src/
├── app/                  router, layout, providers globales
├── features/
│   └── <feature>/
│       ├── components/   presentacionales
│       ├── hooks/        hooks de datos y de UI
│       ├── api.ts        llamadas al backend
│       └── types.ts      tipos del dominio
├── components/
│   ├── ui/               base (shadcn o propio)
│   ├── layout/           chrome: sidebar, header, contenedor
│   ├── common/           botón, tabla, modal, empty state, skeleton
│   └── ai/               ChatWidget
├── lib/                  cliente HTTP, auth, utils, schemas Zod
├── hooks/                hooks compartidos
├── types/                tipos globales
└── routes/               definición de rutas
```

**Por qué por feature y no por tipo:** una pantalla de órdenes se lee junta. Separar todos
los componentes y todos los hooks en carpetas distintas obliga a saltar constantly entre
archivos para entender una pantalla.

## Estado — la regla que más se rompe

| Tipo de estado | Herramienta | Ejemplo |
|---|---|---|
| Del servidor | **TanStack Query** | La lista de órdenes, el dashboard |
| De la URL | **search params** | Filtros, búsqueda, pestaña, orden, página |
| Local efímero | `useState` | Si un modal está abierto, un campo en curso |

**Nunca copies datos del servidor a `useState`.** Es la causa número uno de estados
desincronizados: la copia queda vieja y la UI miente.

**Si un filtro no está en la URL, se pierde al recargar** y no se puede compartir por link.
Los KPIs navegables del dashboard (que llevan filtros aplicados) dependen de esto.

## Tipos

- TypeScript **estricto**. `strict: true`, sin `any`.
- Los tipos del dominio se generan del OpenAPI de FastAPI o se definen a mano y se mantienen
  sincronizados. No reescribas el mismo tipo en tres archivos.
- Los importes de tipos usan `import type`.

## Seguridad — checklist

- [ ] Guard de rutas: sin token válido no se renderiza el contenido protegido.
- [ ] Interceptor `401` → limpiar sesión, redirigir al login, avisar.
- [ ] `403` → mensaje explicativo, **sin** logout.
- [ ] `429` → leer `Retry-After`, deshabilitar la acción, mostrar cuenta regresiva.
- [ ] `5xx` → mensaje genérico + reintentar. **Nunca** el cuerpo crudo de la respuesta.
- [ ] **Nunca** `dangerouslySetInnerHTML` con contenido del usuario.
- [ ] La respuesta del chat IA se renderiza como **texto** o markdown **sanitizado**. El modelo
      puede devolver HTML/JS si se lo pide: la UI no lo ejecuta.
- [ ] Zod valida antes de enviar. **Es UX, no seguridad**: el backend sigue decidiendo.
- [ ] Acción destructiva → confirmación explícita.
- [ ] Nada de secretos en el bundle. El token no viaja en la URL.
- [ ] CSP en producción.

## Los cuatro estados de cada pantalla

1. **Cargando** — skeleton o spinner. Una pantalla sin estado de carga parece rota.
2. **Vacío** — explicación + acción para resolverlo. *"No hay órdenes este mes. Creá la primera."*
3. **Error** — mensaje + reintentar. El error no borra el resto de la pantalla.
4. **Datos** — el caso normal.

Una pantalla con sólo el cuarto está incompleta. Es el defecto más común al maquetar.

## Convenciones

- **Sin comentarios en el código**, salvo pedido explícito.
- Identificadores en **inglés**; textos de UI en **español**.
- Montos: `Intl.NumberFormat("es-AR", { maximumFractionDigits: 0 })`.
- Fechas: `America/Argentina/Buenos_Aires`, formato `DD/MM/AAAA`.
- Un componente, un motivo para re-renderizar. Si tiene varios, dividilo.
- Accesibilidad: `<button>` para acciones (no `div` con `onClick`), `<label>` ligado al input,
  foco visible, `aria-label` en botones sólo con ícono.
- Los filtros de los listados van en la URL y el botón de exportar **reusa esos mismos
  parámetros** (CU10: lo que se ve es lo que se descarga).

## Comandos

```bash
npm run dev        # servidor de desarrollo
npm run build      # build de producción (verifica tipos)
npm run lint
npm test
npx playwright test
```

## Orden de implementación

1. Cliente HTTP con interceptores → auth (login, guard, sesión) → layout y router.
2. Un módulo simple (proveedores) para validar el patrón de grilla + filtros + modal.
3. Productos (agrega proveedor obligatorio, ajuste de stock, historial).
4. Órdenes (el núcleo: ítems mixtos, totales en vivo, pagos, estados).
5. Dashboard (agrega las agregaciones y los KPIs navegables).
6. Notificaciones y exportación.
7. Chat IA — **al final**: es lo único que depende de un servicio externo que puede no
   estar disponible, y no debe bloquear el resto de la app.
