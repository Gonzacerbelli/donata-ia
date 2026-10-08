import json
import re

OUT_OF_SCOPE_REPLY = (
    "Hola, soy el asistente de Donata. Solo puedo ayudarte con la gestión de tu negocio: "
    "productos, stock, clientes, órdenes, pagos, cobranza y reportes. "
    "Esa consulta está fuera de mi alcance. ¿Sobre qué parte del negocio querés que te ayude?"
)

GUARDED_REPLY = (
    "No puedo responder eso: escapa a lo que me está permitido hacer en Donata. "
    "Si necesitás ayuda, preguntame sobre productos, stock, clientes, órdenes, pagos o reportes."
)

INJECTION_PATTERNS = [
    r"ignora",
    r"olvida",
    r"olvidate",
    r"desestima",
    r"anula (tus|las) instrucciones",
    r"system prompt",
    r"prompt del sistema",
    r"instrucciones (del sistema|anteriores)",
    r"nuevo rol",
    r"a partir de ahora (sos|eres|actua)",
    r"actua como",
    r"jailbreak",
    r"revela (el|la|tu)",
    r"muestra (el|la|tu) (prompt|instrucciones)",
    r"dame (el|la) (prompt|instrucciones)",
]

OFF_TOPIC_TERMS = [
    "mundial",
    "futbol",
    "partido",
    "boca",
    "river",
    "elecciones",
    "politic",
    "presidente",
    "gobierno",
    "receta",
    "cocina",
    "cocinar",
    "milanesa",
    "poema",
    "poesia",
    "chiste",
    "cuento",
    "novela",
    "pelicula",
    "serie de tv",
    "cancion",
    "musica",
    "banda",
    "programacion",
    "programar",
    "python",
    "javascript",
    "script",
    "algoritmo",
    "matematica",
    "clima",
    "temperatura",
    "traduce",
    "traducir",
    "ingles",
    "medicina",
    "doctor",
    "guerra",
    "religion",
    "dios",
]

DOMAIN_TERMS: dict[str, list[str]] = {
    "productos": [
        "producto",
        "articulo",
        "stock",
        "precio",
        "costo",
        "proveedor",
        "reponer",
        "reposicion",
        "minimo",
        "categoria",
        "tapiz",
        "tapices",
        "manta",
        "mantas",
        "decoracion",
        "deco",
        "catalogo",
        "insumo",
        "unidad",
        "rubro",
    ],
    "clientes": [
        "cliente",
        "comprador",
        "minorista",
        "mayorista",
        "instagram",
        "cuil",
        "direccion del cliente",
        "telefono del cliente",
        "agenda",
    ],
    "ventas": [
        "orden",
        "venta",
        "presupuesto",
        "pedido",
        "pago",
        "adelanto",
        "saldo",
        "cobranza",
        "cancelar la orden",
        "entregado",
        "envio",
        "descuento",
        "factura",
    ],
    "reportes": [
        "reporte",
        "informe",
        "resumen",
        "kpi",
        "metrica",
        "dashboard",
        "ingreso",
        "ganancia",
        "rentabilidad",
        "vendido",
        "vendidos",
        "tendencia",
        "balance",
        "facturacion",
        "facturo",
        "cobrado",
        "por cobrar",
        "estadistica",
    ],
}

IN_SCOPE_VERBS = [
    "buscame",
    "buscar",
    "busca",
    "listame",
    "listar",
    "lista",
    "dame",
    "mostrame",
    "mostrar",
    "muestra",
    "crear",
    "crea",
    "cargale",
    "cargar",
    "carga",
    "agregar",
    "agrega",
    "registrar",
    "registra",
    "actualizar",
    "modificar",
    "editar",
    "cancelar",
    "pagar",
    "eliminar",
    "borrar",
]

WRITE_VERBS = [
    "crear",
    "crea",
    "cargar",
    "carga",
    "registrar",
    "registra",
    "agregar",
    "agrega",
    "modificar",
    "actualizar",
    "editar",
    "cancelar",
    "pagar",
    "eliminar",
    "borrar",
    "reponer",
]

# Verbos que también aparecen en consultas ("qué pedido resta cancelar", "cuánto hay
# que pagar", "qué productos debo reponer"): sólo cuentan como acción si el mensaje no
# tiene señales de consulta.
AMBIGUOUS_WRITE_VERBS = ["cancelar", "pagar", "reponer"]

QUERY_OVERRIDES = [
    "cual",
    "cuales",
    "cuanto",
    "cuanta",
    "cuantos",
    "cuantas",
    "quien",
    "quienes",
    "por cancelar",
    "a cancelar",
    "por pagar",
    "a pagar",
    "resta cancelar",
    "resta pagar",
    "sin cancelar",
    "debo reponer",
    "falta reponer",
    "a reponer",
    "que reponer",
    "por reponer",
]

AYUDA_TERMS = [
    "hola",
    "buenos dias",
    "buenas tardes",
    "buenas noches",
    "quien sos",
    "que hace",
    "que haces",
    "que podes hacer",
    "como funcion",
    "como puedo",
    "ayuda",
    "ayudame",
    "gracias",
    "donata",
    "manual",
    "opciones",
    "que sabes hacer",
]

_HEX_ID = re.compile(r"\b[0-9a-fA-F]{24}\b")
_MONEY_DECIMAL = re.compile(r"(?<![\w])(\d{1,3}(?:[.,]\d{3})*|\d+)[.,]\d{1,2}(?![\w])")
_FENCED_JSON = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)
_WS = re.compile(r"\s+")
_ACCENTS = str.maketrans("áéíóúüñ", "aeiouun")


def _normalize(text: str) -> str:
    lowered = text.lower().translate(_ACCENTS)
    return _WS.sub(" ", lowered).strip()


def _contains_any(norm_text: str, terms: list[str]) -> bool:
    return any(term in norm_text for term in terms)


def has_prompt_injection(text: str) -> bool:
    norm = _normalize(text)
    return any(re.search(pattern, norm) for pattern in INJECTION_PATTERNS)


def classify_topic(text: str) -> str:
    norm = _normalize(text)
    if not norm:
        return "fuera_de_contexto"
    if any(re.search(pattern, norm) for pattern in INJECTION_PATTERNS):
        return "injection"
    if _contains_any(norm, OFF_TOPIC_TERMS):
        return "fuera_de_contexto"
    for domain, terms in DOMAIN_TERMS.items():
        if _contains_any(norm, terms):
            return domain
    if _contains_any(norm, IN_SCOPE_VERBS) or _contains_any(norm, AYUDA_TERMS):
        return "in_scope"
    return "fuera_de_contexto"


def is_off_topic(text: str) -> bool:
    return classify_topic(text) in ("fuera_de_contexto", "injection")


def mentions_write_action(text: str) -> bool:
    """True si el pedido del usuario implica crear, modificar o registrar algo.

    Los verbos ambiguos (`cancelar`, `pagar`) también se usan en consultas ("el pedido
    que resta cancelar", "cuánto hay que pagar"): sólo se cuentan como acción cuando el
    mensaje no tiene una señal clara de consulta.
    """
    norm = _normalize(text)
    hard = [verb for verb in WRITE_VERBS if verb not in AMBIGUOUS_WRITE_VERBS]
    if _contains_any(norm, hard):
        return True
    if _contains_any(norm, AMBIGUOUS_WRITE_VERBS):
        return not _contains_any(norm, QUERY_OVERRIDES)
    return False


READ_PREFIXES = [
    "cuant",
    "saldo",
    "debe",
    "deud",
    "sab",
    "decime",
    "dime",
    "busc",
    "list",
    "mostr",
    "consult",
    "revis",
    "ver",
]

# Interrogativos que marcan una consulta aunque no haya un verbo de lectura explícito
# ("¿cuál es el pedido que más resta por cobrar?", "¿quién debe más?").
INTERROGATIVES = [
    "cual",
    "cuales",
    "cuanto",
    "cuanta",
    "cuantos",
    "cuantas",
    "quien",
    "quienes",
]


def mentions_read_action(text: str) -> bool:
    """True si el pedido es de lectura: ver, buscar o informarse, sin modificar nada."""
    tokens = _WS.split(_normalize(text))
    return any(token.startswith(prefix) for token in tokens for prefix in READ_PREFIXES)


def is_read_request(text: str) -> bool:
    """True si el pedido es una consulta: no propone ni pide confirmación.

    Es consulta si hay un verbo/construcción de lectura (buscar, cuánto, saldo, "por
    cancelar") o un interrogativo, y no hay un verbo de escritura inequívoco. Así
    "el pedido que más resta por cancelar" es consulta aunque contenga "cancelar".
    """
    if mentions_write_action(text):
        return False
    norm = _normalize(text)
    return (
        mentions_read_action(text)
        or _contains_any(norm, QUERY_OVERRIDES)
        or _contains_any(norm, INTERROGATIVES)
    )


def validate_answer(answer: str) -> list[str]:
    issues: list[str] = []
    if _HEX_ID.search(answer):
        issues.append("La respuesta menciona un ObjectId de 24 caracteres; verificar.")
    if _MONEY_DECIMAL.search(answer):
        issues.append("La respuesta usa montos decimales; Donata trabaja con pesos enteros.")
    return issues


def _decimal_to_int(match: re.Match) -> str:
    raw = match.group(0)
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        return str(int(round(float(raw))))
    except ValueError:
        return match.group(0)


def _is_tool_call_payload(payload) -> bool:
    if not isinstance(payload, dict):
        return False
    return {"name", "arguments"}.issubset(payload) or {"herramienta", "argumentos"}.issubset(
        payload
    )


def strip_tool_call_blocks(answer: str) -> str:
    """Elimina bloques de código con forma de llamada a herramienta (JSON con nombre y
    argumentos) para que el usuario nunca vea JSON crudo en la respuesta."""

    def _replace(match: re.Match) -> str:
        try:
            payload = json.loads(match.group(1))
        except ValueError:
            return match.group(0)
        return "" if _is_tool_call_payload(payload) else match.group(0)

    return _FENCED_JSON.sub(_replace, answer)


def sanitize_answer(answer: str) -> str:
    """Sustituye ids internos y montos decimales por valores seguros en pesos enteros."""
    text = strip_tool_call_blocks(answer)
    text = _HEX_ID.sub("un id interno", text)
    return _MONEY_DECIMAL.sub(_decimal_to_int, text)
