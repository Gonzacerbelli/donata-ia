# MCP — Model Context Protocol

> **Requisito del TP (1 punto):** integrar al menos 2 servidores MCP en el flujo de desarrollo
> o en la arquitectura, con **al menos uno externo**.
>
> Este documento es el entregable que demuestra *qué* servidores se usan, *cómo* se configuran
> y *qué rol real* con un rol claro cada uno en el desarrollo.

---

## 1. Qué es MCP en este proyecto

**Model Context Protocol** es el estándar por el que un agente de IA se conecta a herramientas
y fuentes de contexto externas de forma estandarizada. En vez de que cada agente se invente sus
integraciones, usa un protocolo común.

En este proyecto el MCP se usa como **capa de contexto del proceso de desarrollo**: los
agentes acceden a documentación, al sistema de archivos y a las fuentes de referencia a través
de servidores MCP, en lugar de adivinar o de pedir que se le pegue el contenido.

> **Distinción importante para la nota — hay DOS planos de MCP en este proyecto:**
>
> 1. **MCP dentro del producto:** el asistente del sistema (CU07) consume sus herramientas de
>    negocio a través de un servidor MCP **propio** llamado `donata-mcp` (§2.0). Esta es la
>    integración de MCP en la **arquitectura de la aplicación**.
> 2. **MCP en el entorno de desarrollo:** los agentes que *construyen* el sistema usan servidores
>    MCP externos (context7, filesystem, playwright, sequential-thinking, github) para obtener
>    contexto y verificar el trabajo (§2.1–§2.5).
>
> Son complementarios: uno se evalúa como arquitectura, el otro como esquema de trabajo. En la
> entrega conviene mostrarlos como dos planos separados.

---

## 2. Servidores MCP del proyecto

### 2.0 `donata-mcp` — interno · el asistente de la aplicación

| | |
|---|---|
| **Tipo** | **Interno** (código propio, servidor MCP propio) |
| **Implementación** | `backend/app/mcp_server.py` con **FastMCP** |
| **Transporte** | `stdio` (el backend lo lanza como subproceso vía `langchain-mcp-adapters`) |
| **Endpoint HTTP** | Ninguno: no se expone a la red, sólo al proceso del agente |
| **Qué expone** | 16 herramientas de negocio en español que envuelven los **services** ya validados |

**Rol en el producto.** Es la forma en que el agente CU07 obtiene sus *tools*: en vez de
declarar funciones sueltas en el código del agente, el negocio se expone como un servidor MCP y
el agente lo consume con `MultiServerMCPClient`. Ventaja concreta: las herramientas se pueden
probar de forma aislada (hablando MCP por stdio) y el agente queda desacoplado de la
implementación.

**Herramientas expuestas** (`donata-mcp`):

| Tool | Qué hace | Envuelve |
|---|---|---|
| `buscar_productos` | Lista/filtra el catálogo | `services/products` + `repositories/products` |
| `listar_productos_a_reponer` | Productos en el stock mínimo o por debajo | `repositories/products` |
| `buscar_productos_semantico` | Búsqueda semántica de productos | `services/llm/vector_store` (Chroma) |
| `consultar_producto` | Ficha de un producto | `services/products` |
| `consultar_precios` | Precio minorista/mayorista resuelto | `services/products` |
| `listar_clientes` | Lista/filtra clientes | `services/clients` |
| `crear_cliente` | Alta de cliente | `services/clients` |
| `listar_ventas` | Lista/filtra ventas | `services/sales` |
| `consultar_saldo_cliente` | Saldo derivado de un cliente (deuda, facturado, cobrado) | `repositories/sales` + `repositories/clients` |
| `listar_clientes_pendientes` | Clientes con órdenes sin entregar y saldo pendiente | `repositories/sales` + `repositories/clients` |
| `crear_venta` | Crea una venta (ítems mixtos, precio dual) | `services/sales` |
| `registrar_pago` | Registra un pago | `services/sales` |
| `cancelar_venta` | Cancela y restaura stock | `services/sales` + `services/stock` |
| `reponer_stock` | Suma stock y/o actualiza el precio de venta | `services/stock` + `services/products` |
| `resumen_negocio` | Agregados del dashboard | `services/reports` |
| `consultar_documentacion` | Responde desde el manual (RAG) | `services/llm/rag` |

> **Seguridad:** el agente **no** toca Mongo. Cada tool pasa por el service, que aplica las
> mismas validaciones y reglas de negocio que la API (stock atómico, montos enteros, saldo
> derivado). Es la materialización de la regla 3.4 de `AGENTS.md`.

**Cómo se consume** (`backend/app/services/llm/agent.py`):

```python
client = MultiServerMCPClient({
    "donata": {
        "command": "python",
        "args": ["-m", "app.mcp_server"],
        "transport": "stdio",
        "env": server_env,           # MONGO_URI, CHROMA_DIR, OLLAMA_BASE_URL, ...
    }
})
tools = await client.get_tools()
```

### 2.1 `context7` — externo · Documentación de librerías actualizado

| | |
|---|---|
| **Tipo** | **Externo** (servicio público, no se ejecuta localmente) |
| **Paquete** | `@upstash/context7-mcp` |
| **Transporte** | local (npx) |
| **Qué expone** | Documentación real y versionada de librerías: FastAPI, Pydantic, LangChain, Motor, React, TanStack Query, Vite |

**Rol en el desarrollo.** Es el que evita el error más caro de trabajar con IA: **inventar APIs**.
Un modelo entrenado conoce la API de FastAPI de hace tiempo, no la actual. `context7` entrega el
código y la documentación de la **versión instalada**, así que la implementación usa APIs que
existen de verdad.

Ejemplo concreto de uso:

- *"¿Cuál es la forma actual de definir dependency overrides en FastAPI 0.115?"*
- *"¿Cómo se configura `ChatOllama` de `langchain-ollama` para tool calling?"*
- *"¿Cuál es la sintaxis vigente de `defineConfig` en Vite 6?"*

Sin este servidor, la respuesta habría salido del conocimiento del modelo: plausible, y a
veces desactualizada.

---

### 2.2 `filesystem` — externo · Acceso al proyecto y a documentación

| | |
|---|---|
| **Tipo** | **Externo** (paquete oficial de Anthropic, ejecutado localmente vía npx) |
| **Paquete** | `@modelcontextprotocol/server-filesystem` |
| **Transporte** | local (npx) |
| **Qué expone** | Lectura y escritura de archivos dentro de los directorios autorizados |

**Rol en el desarrollo.** Da a los agentes especializados acceso al repositorio y a los
documentos de referencia **fuera del directorio de trabajo principal** (por ejemplo, el
`AGENTS.md` de la carpeta hermana que se va a migrar), sin copiar el contenido a mano.

Directorios que se le autorizan:

- `C:\Users\Gonzalo\Documents\Repositorios\donata-deco` — el sistema heredado a portar.
- `C:\Users\Gonzalo\Documents\Repositorios\donata-ia` — el proyecto en sí.

**Por qué importa para la nota:** es la demostración práctica de que el agente opera sobre su
entorno con un protocolo estándar, y no sólo sobre el chat.

---

### 2.3 `playwright` — externo · Verificación de la interfaz en un navegador real

| | |
|---|---|
| **Tipo** | **Externo** (paquete de Microsoft, ejecutado localmente vía npx) |
| **Paquete** | `@playwright/mcp` |
| **Transporte** | local (npx) |
| **Qué expone** | Navegación, capturas, inspección del DOM y de la consola del navegador |

**Rol en el desarrollo.** Es el que **verifica la funcionalidad entregada**. Como la rúbrica
evalúa que el sistema *resuelva los casos de uso de forma interactiva y sin errores críticos*,
necesitamos poder *usar* la aplicación, no sólo compilarla.

Ejemplos de uso:

- Recorrer el flujo de login y confirmar que el guard de rutas funciona.
- Crear una orden desde la UI y comprobar que el stock se descuenta.
- Verificar que la tabla de exportación tiene los datos filtrados esperados.
- Capturar la consola del navegador para detectar errores silenciosos que ningún test detecta.
- Verificar el layout responsivo en distintos anchos.

---

### 2.4 `sequential-thinking` — externo · Razonamiento estructurado para decisiones difíciles

| | |
|---|---|
| **Tipo** | **Externo** (paquete oficial de Anthropic, ejecutado localmente vía npx) |
| **Paquete** | `@modelcontextprotocol/server-sequential-thinking` |
| **Transporte** | local (npx) |
| **Qué expone** | Un bucle de razonamiento paso a paso, editable entre pasos |

**Rol en el desarrollo.** Se usa para los puntos donde **no hay una respuesta correcta
obvia** y hace falta desarmar el problema antes de decidir:

- ¿Cómo garantizar atomicidad de stock sinÍ Introducir una transacción que Mongo standalone no da?
- ¿Cómo diseñar las tools del agente para que un 7B elija bien la correcta?
- ¿Cuál es el modelo 7B que mejor sigue instrucciones en español en CPU?
- ¿Cómo hacer que la exportación reutilice exactamente la query del listado?

**No** se usa para escribir código rutinario: ahí es ruido y costo sin beneficio.

---

### 2.5 `github` — **externo remoto** · Gestión del repositorio y de los PR

| | |
|---|---|
| **Tipo** | **Externo remoto** (`type: remote`, servicio hospedado) |
| **URL** | `https://api.githubcopilot.com/mcp/` |
| **Autenticación** | header `Authorization: Bearer {env:GITHUB_PAT}` (PAT por variable de entorno) |
| **Qué expone** | Operaciones del repositorio: ramas, commits, issues, pull requests, revisiones |

**Rol en el desarrollo.** Es el que cierra el ciclo del flujo spec-driven por ramas: el agente
crea la rama de una tarea, commitea, abre el pull request y lo consulta sin salir del editor. En
este proyecto, cada hito se integró por PR con merge squash (ver `docs/AI-ENGINEERING.md`).

> **Este es el único servidor MCP puramente remoto** del proyecto. Los demás son paquetes de
> terceros ejecutados localmente vía `npx`.

**Autenticación con un PAT.** El header usa `{env:GITHUB_PAT}`: opencode sustituye la variable
desde el **entorno del proceso**, no desde el `.env` del proyecto. Hay que definir `GITHUB_PAT`
como variable de usuario/sistema **antes** de arrancar opencode (si el valor queda vacío, el
header sale como `Bearer ` y GitHub responde `401`).

```powershell
# Windows (una sola vez; después reiniciar opencode)
[Environment]::SetEnvironmentVariable("GITHUB_PAT","<token>","User")
```

```bash
# Linux / macOS
export GITHUB_PAT=<token>   # en el shell que lanza opencode
```

Scopes: un token **fine-grained** limitado a `Gonzacerbelli/donata-ia` (Contents + Pull requests)
alcanza; un token clásico necesita el scope `repo`. No se necesitan permisos de más.

> **Estado: Probado.** El servidor se usó de punta a punta en el hito de documentación MCP: creó
> la rama, el commit y el pull request #17 sin salir del editor. Deja de ser "configuración
> muerta" en el sentido de §6.

---

## 3. Configuración

La configuración vive en `opencode.json`, en el bloque `mcp`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "context7": {
      "type": "local",
      "command": ["npx", "-y", "@upstash/context7-mcp"],
      "enabled": true
    },
    "filesystem": {
      "type": "local",
      "command": [
        "npx", "-y", "@modelcontextprotocol/server-filesystem",
        "C:\\Users\\Gonzalo\\Documents\\Repositorios\\donata-deco",
        "C:\\Users\\Gonzalo\\Documents\\Repositorios\\donata-ia"
      ],
      "enabled": true
    },
    "playwright": {
      "type": "local",
      "command": ["npx", "-y", "@playwright/mcp"],
      "enabled": true,
      "environment": { "BROWSER": "chromium" }
    },
    "sequential-thinking": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"],
      "enabled": true
    },
    "github": {
      "type": "remote",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer {env:GITHUB_PAT}" },
      "enabled": true
    }
  }
}
```

**Notas de la configuración:**

- `command` **siempre** es un array de strings, nunca un string suelto.
- `type` es obligatorio.
- Los headers de servidores remotos soportan interpolación `{env:VAR}`, resuelta contra el
  **entorno del proceso** de opencode (no contra el `.env` del proyecto). Si la variable no
  existe, se sustituye por cadena vacía.
- **Después de modificar `opencode.json` hay que reiniciar opencode**: la configuración se lee
  una vez al arrancar y no se recarga en caliente.

### 3.1 Requisitos

```bash
node --version     # v18 o superior
npx --version
```

Para el servidor remoto `github`, además:

```bash
# debe devolver un valor no vacío al arrancar opencode
echo $GITHUB_PAT        # Linux/macOS
echo $env:GITHUB_PAT    # Windows PowerShell
```

La primera invocación de cada servidor descarga el paquete. Conviene ejecutar cada uno una vez
**antes** de documentarlo como funcionando, para no documentar algo que nunca se probó.

### 3.2 Arranque en frío (troubleshooting)

`opencode` lanza cada servidor `local` como subproceso **al iniciar** y espera su handshake MCP con
un timeout. Si un servidor **nunca se ejecutó antes**, el primer `npx -y` descarga el paquete y
puede tardar más que ese timeout: `opencode` lo marca como caído y lo deja fuera de la sesión, sin
reintentar en caliente. Los servidores ya cacheados levantan en ~1 s y no se ven afectados.

Síntoma en el log de `opencode` (`~/.local/share/opencode/log/opencode.log`):

```
level=WARN message="server unavailable" key=context7 type=local status=failed
```

**Solución:** precalentar la caché de `npx` una vez y **reiniciar `opencode`** (la configuración se
lee solo al arrancar):

```bash
npx -y @upstash/context7-mcp    # primera descarga; Ctrl+C al ver "running on stdio"
```

Con la caché tibia, `context7` vuelve a conectarse en el siguiente arranque. Es un artefacto del
primer `npx`, no un fallo de la configuración.

---

## 4. Cobertura del requisito

**Plano A — MCP en el producto:**

| Servidor | Tipo | Rol | Estado |
|---|---|---|---|
| `donata-mcp` | **Interno** (implementación propia) | Tools del asistente CU07 | Probado (tests por stdio + E2E real) |

**Plano B — MCP en el entorno de desarrollo:**

| Requisito | Servidor | Tipo | Estado |
|---|---|---|---|
| Servidor MCP #1 | `context7` | Externo (local) | Configurado |
| Servidor MCP #2 | `filesystem` | Externo (local) | Configurado |
| Servidor MCP #3 | `playwright` | Externo (local) | Configurado |
| Servidor MCP #4 | `sequential-thinking` | Externo (local) | Configurado |
| Servidor MCP #5 | `github` | **Externo remoto** | **Probado** (rama + commit + PR #17) |

**Cobertura:** 1 servidor MCP propio en la arquitectura del producto + 5 servidores MCP en el
entorno de desarrollo, **uno de ellos remoto**. El requisito (≥ 2 servidores, ≥ 1 externo) queda
cubierto con holgura, y además hay integración de MCP *dentro del producto* (no sólo en el
tooling de desarrollo).

---

## 5. Cómo se demuestra el uso en la entrega

**Plano A — `donata-mcp` (producto).** Se demuestra con el chequeo E2E real:

```bash
docker compose run --rm --no-deps api python -m scripts.e2e_check
```

El script pide *"¿Cuántos productos tengo en el catálogo y cuánto stock hay?"* contra Ollama
real; el agente elige la herramienta `buscar_productos`, la ejecuta por MCP y redacta la
respuesta con datos reales de Mongo. La salida imprime las herramientas usadas:

```
Respuesta: En tu catálogo actualmente hay ... con stock ...
Herramientas usadas: ['buscar_productos']
```

Además hay pruebas unitarias que hablan MCP por **stdio real** (`backend/tests/test_mcp_server.py`)
y del orquestador del agente (`backend/tests/test_assistant.py`).

**Plano B — servidores de desarrollo.** Un ejemplo concreto por servidor:

| Servidor | Ejemplo de uso | Qué aporta |
|---|---|---|
| `context7` | Consulta de la API de `ChatOllama` y de `MultiServerMCPClient` | Versión correcta de la API, no la memorizada |
| `filesystem` | Lectura del backend de `donata-deco` | Lógica heredada sin copiar a mano |
| `playwright` | Recorrido del flujo de creación de orden (frontend) | Evidencia de que la UI funciona de verdad |
| `sequential-thinking` | Diseño del stock atómico y de las tools del agente | Decisión argumentada, no arbitraria |
| `github` | Creación de rama + PR + merge squash de cada hito | Trazabilidad del proceso de desarrollo |

---

## 6. Honestidad técnica

Vale más reconocer los límites que inventar capacidades:

- Los servidores `local` de MCP **se ejecutan en la máquina del usuario** vía `npx`. Son
  externos en el sentido de que son paquetes de terceros mantenidos fuera de este proyecto, no
  código escrito por nosotros. El único puramente remoto es el que se configure con `type: remote`.
- `npx -y` descarga el paquete la primera vez: hace falta conexión en ese momento, aunque el
  resto del desarrollo sea offline.
- Un servidor MCP que no se usó es configuración muerta. Por eso la columna "Estado" debe
  decir "probado" y no "configurado" cuando se termine el proyecto. Hoy el servidor del
  producto (`donata-mcp`) está **probado** (tests por stdio + E2E con Ollama real); los
  servidores de desarrollo quedan como "configurados" hasta que se registre su uso concreto.
- `donata-mcp` usa **stdio**, no HTTP: no abre puertos ni expone el negocio a la red. Es
  deliberado — el único cliente es el propio agente del backend.
