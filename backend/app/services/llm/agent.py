import ast
import json
import os
import re
from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool, tool
from langchain_mcp_adapters.client import MultiServerMCPClient

from ...config import settings
from ...repositories import clients as clients_repo
from ...repositories import products as products_repo
from ...repositories import sales as sales_repo
from . import guardrails
from .rag import get_llm

SYSTEM_PROMPT = """Sos el asistente operativo de Donata, un negocio de alfombras y textiles.
Ayudás a gestionar productos, stock, precios, clientes, proveedores, ventas, pagos y reportes.

Reglas:
- Respondé siempre en español, breve y claro.
- Para datos concretos (stock, precios, ventas, clientes) usá las herramientas
  disponibles; nunca inventes datos.
- Si una búsqueda no da resultados, volvé a buscar con una o dos palabras del nombre,
  sin aclaraciones ni datos de más.
- Para dudas sobre el funcionamiento del negocio, usá la herramienta de documentación.
- Los ids de clientes y productos salen de las herramientas: buscalos antes de proponer
  una acción y no los incluyas en tu respuesta al usuario.
- Trabajás con pesos argentinos enteros; no uses decimales. Los porcentajes van de 0 a 100.
- Las acciones de escritura (`crear_cliente`, `crear_venta`, `registrar_pago`,
  `cancelar_venta`, `reponer_stock`) no se ejecutan: si el usuario pide crear, modificar,
  cancelar, registrar o reponer algo, llamá a esa herramienta con los parámetros EXACTOS
  de su firma (nombres, tipos y obligatoriedad) y quedará registrada una propuesta que el
  usuario confirma en la pantalla. También podés usar `proponer_accion` con `herramienta`,
  `argumentos` y `resumen`. Nada se ejecuta hasta la confirmación. Si los argumentos no
  coinciden con la firma te voy a devolver el detalle: corregilos y volvé a llamar antes
  de responderle al usuario. Si el usuario pide varias cosas (cliente, venta, seña),
  empezá por la primera y esperá la confirmación.
- Si `proponer_accion` te devuelve argumentos inválidos, corregilos con la firma que te
  muestro más abajo y volvé a proponer antes de responderle al usuario.
- Cuando propongas una acción, terminá pidiendo la confirmación explícita del usuario.
- Nunca escribas la llamada a una herramienta dentro de tu respuesta (ni en texto ni en
  bloques de código): emitila como llamada real a la herramienta.
- Si una consulta está fuera del negocio, aclaralo amablemente.

Flujo para crear una venta:
1. Buscá el cliente con `listar_clientes`. Si no existe, proponé primero `crear_cliente`
   (con `direccion` y `telefono` si los tenés) y esperá la confirmación.
2. Buscá cada producto con `buscar_productos` y anotá su `id` y `stock`.
3. Proponé `crear_venta` con `cliente_id` e `items` = [{"product_id": "<id>", "qty": n}].
   - El costo de envío va en `envio` (pesos) y el detalle ("Envío por Andreani") en `notas`.
   - Para cobrar la seña de una sola vez usá `pago_porcentaje` (p. ej. 50) o `pago_monto`;
     `pago_tipo` es "adelanto" (seña) o "pago" (cobro total).
   - `registrar_pago` sirve después, para pagos sobre una venta ya creada.

Flujo para reponer stock o cambiar un precio:
1. Buscá el producto con `buscar_productos` y anotá su `id`.
2. Proponé `reponer_stock` con `producto_id`, `cantidad` (unidades a sumar al stock) y
   `precio_venta` (nuevo precio minorista en pesos); el que no cambia va en 0.
   - Si el usuario pide reposiciones para varios productos, hacé una propuesta por vez.

Ejemplo de llamada válida (con los ids reales que obtuviste):
crear_venta(cliente_id="<id>", items=[{"product_id": "<id>", "qty": 7}], envio=0,
            notas="Envío por Andreani", pago_porcentaje=50, pago_tipo="adelanto")
"""

MAX_STEPS = 8

PROPOSE_NUDGE = (
    "Dejá la acción registrada como propuesta llamando a la herramienta correspondiente "
    "con sus parámetros, para que el usuario la confirme en la pantalla; no hace falta "
    "que me preguntes primero."
)

WRITE_TOOLS = {
    "crear_cliente",
    "crear_venta",
    "registrar_pago",
    "cancelar_venta",
    "reponer_stock",
}

_TYPE_LABELS = {
    "string": "texto",
    "integer": "número entero",
    "number": "número",
    "boolean": "true/false",
    "array": "lista",
    "object": "objeto",
}


def tool_schema(tool: BaseTool) -> dict:
    """Esquema JSON de argumentos de una herramienta (dict en MCP, modelo en LangChain)."""
    schema = getattr(tool, "args_schema", None)
    if isinstance(schema, dict):
        return schema
    if schema is not None and hasattr(schema, "model_json_schema"):
        return schema.model_json_schema()
    return {}


def _param_label(name: str, spec: dict, required: set[str]) -> str:
    if spec.get("enum") is not None:
        opciones = " | ".join(str(option) for option in spec["enum"] if option != "")
        label = f"({opciones})" if opciones else "(texto)"
    else:
        label = f"({_TYPE_LABELS.get(spec.get('type', ''), spec.get('type', 'texto'))})"
    if name in required:
        return f"{name}: {label}!"
    default = spec.get("default", "")
    rendered = f'"{default}"' if isinstance(default, str) else str(default)
    return f"{name}: {label} = {rendered}"


def signatures_text(tools: list[BaseTool]) -> str:
    """Firmas exactas de las herramientas de escritura, para el prompt del modelo."""
    if not tools:
        return ""
    lines = [
        "Firmas de las acciones (usá estos nombres de parámetros y nada más; "
        "los que terminan en ! son obligatorios):"
    ]
    for write_tool in tools:
        schema = tool_schema(write_tool)
        props = schema.get("properties", {}) or {}
        required = set(schema.get("required", []) or [])
        params = ", ".join(_param_label(name, spec, required) for name, spec in props.items())
        description = (write_tool.description or "").strip().splitlines()[0]
        lines.append(f"- {write_tool.name}({params}) → {description}")
    return "\n".join(lines)


def _type_matches(expected: str, value: Any) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return True


def validate_args(name: str, schema: dict, args: dict) -> list[str]:
    """Problemas (en español) de `args` contra la firma de la herramienta `name`."""
    problems: list[str] = []
    props = schema.get("properties", {}) or {}
    required = schema.get("required", []) or []
    if not props:
        return problems
    for key in required:
        if args.get(key) in (None, ""):
            problems.append(f"falta '{key}' (obligatorio)")
    for key, value in args.items():
        if key not in props:
            problems.append(f"'{key}' no es un parámetro de {name}")
            continue
        spec = props[key]
        expected = spec.get("type")
        if expected and not _type_matches(expected, value):
            problems.append(f"'{key}' debe ser {_TYPE_LABELS.get(expected, expected)}")
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in spec and value < spec["minimum"]:
                problems.append(f"'{key}' debe ser mayor o igual a {spec['minimum']}")
            if "maximum" in spec and value > spec["maximum"]:
                problems.append(f"'{key}' debe ser menor o igual a {spec['maximum']}")
            continue
        if spec.get("enum") is not None and value not in spec["enum"]:
            opciones = ", ".join(str(option) for option in spec["enum"] if option != "")
            problems.append(f"'{key}' debe ser uno de: {opciones}")
    return problems


def _server_env() -> dict[str, str]:
    return {
        **os.environ,
        "MONGO_URI": settings.mongo_uri,
        "MONGO_DB": settings.mongo_db,
        "CHROMA_DIR": settings.chroma_dir,
        "EMBEDDING_MODEL": settings.embedding_model,
        "OLLAMA_BASE_URL": settings.ollama_base_url,
        "OLLAMA_MODEL": settings.ollama_model,
        "RAG_TOP_K": str(settings.rag_top_k),
    }


def build_mcp_client() -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {
            "donata": {
                "command": "python",
                "args": ["-m", "app.mcp_server"],
                "transport": "stdio",
                "env": _server_env(),
            }
        }
    )


async def load_tools() -> list[BaseTool]:
    client = build_mcp_client()
    return await client.get_tools()


def _propose_tool(write_tools: list[BaseTool] | None = None) -> BaseTool:
    write_tools = write_tools or []
    schemas = {t.name: tool_schema(t) for t in write_tools}

    def proponer_accion(herramienta: str, argumentos: dict | str, resumen: str) -> str:
        """Propone una acción de escritura que el usuario debe confirmar en la pantalla.

        No ejecuta nada. `herramienta` es el nombre de la operación, `argumentos` es el
        objeto JSON con los parámetros EXACTOS de esa operación y `resumen` describe la
        acción en una frase.
        """
        if herramienta not in schemas:
            disponibles = ", ".join(sorted(schemas)) or "ninguna"
            return f"Error: '{herramienta}' no es una acción válida. Acciones: {disponibles}."
        args = argumentos if isinstance(argumentos, dict) else _parse_args(argumentos)
        if args is None:
            return "Error: `argumentos` debe ser un objeto JSON."
        problems = validate_args(herramienta, schemas[herramienta], args)
        if problems:
            return (
                f"Argumentos inválidos para {herramienta}: {'; '.join(problems)}. "
                "Volvé a proponer la acción con la firma exacta."
            )
        return PROPOSED_OK

    firmas = signatures_text(write_tools)
    proponer_accion.__doc__ = (
        f"{proponer_accion.__doc__}\n\n{firmas}" if firmas else proponer_accion.__doc__
    )
    return tool(proponer_accion)


def _parse_args(raw: Any) -> dict | None:
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError):
            return None
        return parsed if isinstance(parsed, dict) else None
    return None


async def toolsets() -> tuple[list[BaseTool], list[BaseTool]]:
    """(herramientas visibles para el agente, herramientas de escritura entre ellas)."""
    all_tools = await load_tools()
    write_tools = [t for t in all_tools if t.name in WRITE_TOOLS]
    return [*all_tools, _propose_tool(write_tools)], write_tools


def _to_lc_messages(history: list[tuple[str, str]]) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    for role, content in history:
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    return messages


async def run_agent(
    message: str,
    history: list[tuple[str, str]] | None = None,
    *,
    db=None,
) -> tuple[str, list[dict[str, Any]]]:
    tool_calls_log: list[dict[str, Any]] = []
    tools, write_tools = await toolsets()
    tool_map = {tool.name: tool for tool in tools}
    llm = get_llm(temperature=0).bind_tools(tools)
    nudged = False

    firmas = signatures_text(write_tools)
    system_prompt = f"{SYSTEM_PROMPT}\n\n{firmas}" if firmas else SYSTEM_PROMPT
    messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
    messages.extend(_to_lc_messages(history or []))
    messages.append(HumanMessage(content=message))

    for _ in range(MAX_STEPS):
        ai_message = await llm.ainvoke(messages)
        messages.append(ai_message)
        calls = getattr(ai_message, "tool_calls", None) or []
        if not calls:
            content = ai_message.content
            text = content if isinstance(content, str) else str(content)
            entry = _text_call_entry(text, write_tools)
            if entry is not None and entry.get("ok"):
                feedback = await reference_feedback(
                    db, entry["arguments"]["herramienta"], entry["arguments"]["argumentos"]
                )
                if feedback:
                    entry = {**entry, "ok": False, "result": feedback}
            if entry is not None and entry.get("ok"):
                tool_calls_log.append(entry)
                return _proposal_reply(entry), tool_calls_log
            if (
                not nudged
                and not _has_proposal(tool_calls_log)
                and guardrails.mentions_write_action(message)
            ):
                nudged = True
                nudge = PROPOSE_NUDGE
                if entry is not None:
                    nudge = f"{entry['result']} {PROPOSE_NUDGE}"
                messages.append(HumanMessage(content=nudge))
                continue
            return text, tool_calls_log
        for call in calls:
            if call["name"] in WRITE_TOOLS:
                entry = _write_proposal(write_tools, call)
                if entry.get("ok"):
                    feedback = await reference_feedback(
                        db, entry["arguments"]["herramienta"], entry["arguments"]["argumentos"]
                    )
                    if feedback:
                        entry = {**entry, "ok": False, "result": feedback}
                tool_calls_log.append(entry)
                messages.append(ToolMessage(content=entry["result"], tool_call_id=call["id"]))
                continue
            tool = tool_map.get(call["name"])
            result = await _invoke_tool(tool, call["args"])
            tool_calls_log.append(
                {
                    "name": call["name"],
                    "arguments": call["args"],
                    "result": result,
                    "ok": _result_ok(call["name"], result),
                }
            )
            messages.append(ToolMessage(content=_stringify(result), tool_call_id=call["id"]))
    return (
        "No pude completar la consulta en varios intentos. ¿Podés reformularla?",
        tool_calls_log,
    )


async def _invoke_tool(tool: BaseTool | None, arguments: dict) -> Any:
    if tool is None:
        return {"error": "Herramienta desconocida"}
    try:
        return await tool.ainvoke(arguments)
    except Exception as exc:  # pragma: no cover - depende del servidor MCP
        return {"error": str(exc)}


def _result_ok(name: str, result: Any) -> bool:
    if isinstance(result, dict):
        return not result.get("error")
    if name == "proponer_accion" and isinstance(result, str):
        return "propuesta registrada" in result.lower()
    return True


def _has_proposal(tool_calls_log: list[dict]) -> bool:
    return any(
        entry.get("name") == "proponer_accion" and entry.get("ok") for entry in tool_calls_log
    )


_CALL_START = re.compile(r"\b([a-z_][a-z0-9_]*)\s*\(")


def _balanced_call(text: str, start: int) -> str | None:
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def _extract_text_call(text: str, tool_names: set[str]) -> tuple[str, dict] | None:
    """Detecta una herramienta escrita como texto, p. ej. `crear_venta(...)`."""
    for match in _CALL_START.finditer(text):
        name = match.group(1)
        if name not in tool_names:
            continue
        expression = _balanced_call(text, match.start())
        if expression is None:
            continue
        try:
            node = ast.parse(expression, mode="eval").body
        except SyntaxError:
            continue
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.args or node.func.id not in tool_names:
            continue
        kwargs: dict[str, Any] = {}
        for keyword in node.keywords:
            if keyword.arg is None:
                break
            try:
                kwargs[keyword.arg] = ast.literal_eval(keyword.value)
            except (ValueError, SyntaxError):
                break
        else:
            return node.func.id, kwargs
    return None


def _text_call_entry(text: str, write_tools: list[BaseTool]) -> dict | None:
    """Convierte una herramienta escrita como texto en la entrada de propuesta."""
    tool_names = set(WRITE_TOOLS) | {"proponer_accion"}
    call = _extract_text_call(text, tool_names)
    if call is None:
        return None
    name, args = call
    if name in WRITE_TOOLS:
        return _write_proposal(write_tools, {"name": name, "args": args})
    herramienta = args.get("herramienta")
    argumentos = args.get("argumentos")
    resumen = args.get("resumen")
    if herramienta not in WRITE_TOOLS or not isinstance(argumentos, dict):
        return {
            "name": "proponer_accion",
            "arguments": args,
            "result": f"Error: '{herramienta}' no es una acción válida.",
            "ok": False,
        }
    schema = next((tool_schema(t) for t in write_tools if t.name == herramienta), {})
    problems = validate_args(herramienta, schema, argumentos)
    if problems:
        return {
            "name": "proponer_accion",
            "arguments": args,
            "result": f"Argumentos inválidos para {herramienta}: {'; '.join(problems)}.",
            "ok": False,
        }
    return {
        "name": "proponer_accion",
        "arguments": {
            "herramienta": herramienta,
            "argumentos": argumentos,
            "resumen": resumen or _summary_for(herramienta, argumentos),
        },
        "result": PROPOSED_OK,
        "ok": True,
    }


def _proposal_reply(entry: dict) -> str:
    arguments = entry.get("arguments") or {}
    resumen = str(
        arguments.get("resumen")
        or _summary_for(str(arguments.get("herramienta") or ""), arguments.get("argumentos") or {})
    )
    return f"Propuesta registrada: {resumen}. Confirmala en la pantalla para ejecutarla."


def _reference_values(args: dict) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for field in ("cliente_id", "producto_id", "venta_id"):
        if args.get(field):
            values.append((field, str(args[field])))
    items = args.get("items") if isinstance(args.get("items"), list) else []
    for item in items:
        if isinstance(item, dict) and item.get("product_id"):
            values.append(("product_id", str(item["product_id"])))
    return values


async def _reference_exists(db, field: str, value: str) -> bool:
    if field in ("producto_id", "product_id"):
        return await products_repo.get_product(db, value) is not None
    if field == "cliente_id":
        return await clients_repo.get_client(db, value) is not None
    return await sales_repo.get_sale(db, value) is not None


async def _reference_candidates(db, field: str, value: str) -> str:
    if field not in ("producto_id", "product_id", "cliente_id"):
        return ""
    query = value.replace("-", " ").replace("_", " ").strip()
    if not query:
        return ""
    if field == "cliente_id":
        found = await clients_repo.list_clients(db, search=query)
        return ", ".join(f"{client.name} = {client.id}" for client in found[:3])
    found_products = await products_repo.list_products(db, search=query, active_only=True)
    return ", ".join(f"{product.name} = {product.id}" for product in found_products[:3])


async def check_references(db, name: str, args: dict) -> list[str]:
    """Problemas en español si los ids referenciados no existen en la base."""
    if db is None:
        return []
    problems: list[str] = []
    labels = {
        "cliente_id": "cliente",
        "producto_id": "producto",
        "product_id": "producto",
        "venta_id": "venta",
    }
    for field, value in _reference_values(args):
        if not await _reference_exists(db, field, value):
            problems.append(f"no existe el {labels[field]} con id '{value}'")
    return problems


async def reference_feedback(db, name: str, args: dict) -> str | None:
    """Mensaje con el detalle y las coincidencias si la propuesta usa ids inexistentes."""
    if db is None:
        return None
    missing = [
        (field, value)
        for field, value in _reference_values(args)
        if not await _reference_exists(db, field, value)
    ]
    if not missing:
        return None
    labels = {
        "cliente_id": "cliente",
        "producto_id": "producto",
        "product_id": "producto",
        "venta_id": "venta",
    }
    problems = [f"no existe el {labels[field]} con id '{value}'" for field, value in missing]
    hints = []
    for field, value in missing:
        candidates = await _reference_candidates(db, field, value)
        if candidates:
            hints.append(f"Con '{value}' coincide: {candidates}.")
    message = f"Referencias inválidas: {'; '.join(problems)}."
    if hints:
        message = f"{message} {' '.join(hints)}"
    return f"{message} Volvé a proponer con el id real de esa búsqueda."


PROPOSED_OK = (
    "Propuesta registrada. Respondé al usuario resumiendo la acción en una o dos frases "
    "(sin ids) y pidiéndole que confirme en la pantalla; todavía no se ejecutó nada."
)


def _summary_for(name: str, args: dict) -> str:
    if name == "crear_cliente":
        return f"Crear cliente {args.get('nombre', '')}".strip()
    if name == "crear_venta":
        items = [i for i in args.get("items", []) if isinstance(i, dict)]
        qty = sum(int(i.get("qty", 0) or 0) for i in items)
        resumen = f"Crear venta de {qty} unidades"
        if args.get("pago_porcentaje"):
            resumen += f" con seña del {args['pago_porcentaje']}%"
        elif args.get("pago_monto"):
            resumen += f" con seña de {args['pago_monto']} pesos"
        if args.get("notas"):
            resumen += f" ({args['notas']})"
        return resumen
    if name == "registrar_pago":
        prefijo = "Seña" if args.get("tipo") == "adelanto" else "Pago"
        return f"{prefijo} de {args.get('monto', '')} pesos".replace("  ", " ")
    if name == "cancelar_venta":
        return "Cancelar la venta"
    if name == "reponer_stock":
        acciones = []
        if args.get("cantidad"):
            acciones.append(f"sumar {args['cantidad']} unidades al stock")
        if args.get("precio_venta"):
            acciones.append(f"poner el precio de venta en {args['precio_venta']} pesos")
        return "Reponer stock: " + " y ".join(acciones) if acciones else "Reponer stock"
    return name


def _write_proposal(write_tools: list[BaseTool], call: dict) -> dict:
    """Convierte una llamada directa a una herramienta de escritura en una propuesta.

    La acción nunca se ejecuta: sólo queda registrada para que el usuario la confirme.
    """
    name = call["name"]
    args = call.get("args") or {}
    schema = next((tool_schema(t) for t in write_tools if t.name == name), {})
    problems = validate_args(name, schema, args)
    if problems:
        return {
            "name": name,
            "arguments": args,
            "result": (
                f"Argumentos inválidos para {name}: {'; '.join(problems)}. Mirá la firma "
                "exacta y volvé a llamar con los argumentos corregidos."
            ),
            "ok": False,
        }
    return {
        "name": "proponer_accion",
        "arguments": {"herramienta": name, "argumentos": args, "resumen": _summary_for(name, args)},
        "result": PROPOSED_OK,
        "ok": True,
    }


def _stringify(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(value)
