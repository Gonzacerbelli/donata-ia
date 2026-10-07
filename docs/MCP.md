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

> **Distinción importante para la nota:** el chatbot de la aplicación (CU07) **no** usa MCP.
> Usa LangChain con tools propias contra la API interna. MCP se usa en el **entorno de
> desarrollo con IA**. Son dos cosas distintas y conviene no mezclarlas al explicarlas.

---

## 2. Servidores MCP del proyecto

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
    }
  }
}
```

**Notas de la configuración:**

- `command` **siempre** es un array de strings, nunca un string suelto.
- `type` es obligatorio.
- Los headers de servidores remotos soportan interpolación `{env:VAR}`.
- **Después de modificar `opencode.json` hay que reiniciar opencode**: la configuración se lee
  una vez al arrancar y no se recarga en caliente.

### 3.1 Requisitos

```bash
node --version     # v18 o superior
npx --version
```

La primera invocación de cada servidor descarga el paquete. Conviene ejecutar cada uno una vez
**antes** de documentarlo como funcionando, para no documentar algo que nunca se probó.

---

## 4. Cobertura del requisito

| Requisito | Servidor | Tipo | Estado |
|---|---|---|---|
| Servidor MCP #1 | `context7` | **Externo** | Configurado |
| Servidor MCP #2 | `filesystem` | **Externo** | Configurado |
| Servidor MCP #3 | `playwright` | **Externo** | Configurado |
| Servidor MCP #4 | `sequential-thinking` | **Externo** | Configurado |

**4 servidores, todos externos,, muy por encima del mínimo de 2.** El requisito de "al menos 1 externo"
queda cubierto con holgura.

---

## 5. Cómo se demuestra el uso en la entrega

Para que la demostración sea convincente, el README final debe incluir **un ejemplo concreto
por servidor**, con la pregunta o la acción y lo que el servidor aportó:

| Servidor | Ejemplo de uso a documentar | Qué aporta |
|---|---|---|
| `context7` | Consulta de la API de `ChatOllama` para tool calling | Versión correcta de la API, no la memorizada |
| `filesystem` | Lectura de `donata-deco/backend/app/routers/sales.py` | Lógica heredada sin copiar a mano |
| `playwright` | Recorrido del flujo de creación de orden | Evidencia de que la UI funciona de verdad |
| `sequential-thinking` | Diseño del mecanismo de stock atómico | Decisión argumentada, no arbitraria |

**Pendiente:** completar la sección 5 con los ejemplos reales a medida que se usen. Acá está la
estructura; el contenido se llena durante el desarrollo.

---

## 6. Honestidad técnica

Vale más reconocer los límites que inventar capacidades:

- Los servidores `local` de MCP **se ejecutan en la máquina del usuario** vía `npx`. Son
  externos en el sentido de que son paquetes de terceros mantenidos fuera de este proyecto, no
  código escrito por nosotros. El único puramente remoto es el que se configure con `type: remote`.
- `npx -y` descarga el paquete la primera vez: hace falta conexión en ese momento, aunque el
  resto del desarrollo sea offline.
- Un servidor MCP que no se usó es configuración muerta. Por eso la columna "Estado" debe
  decir "probado" y no "configurado" cuando se termine el proyecto.
