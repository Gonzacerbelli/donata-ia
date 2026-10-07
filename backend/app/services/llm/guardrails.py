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
    "reponer",
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


def validate_answer(answer: str) -> list[str]:
    issues: list[str] = []
    if _HEX_ID.search(answer):
        issues.append("La respuesta menciona un ObjectId de 24 caracteres; verificar.")
    if _MONEY_DECIMAL.search(answer):
        issues.append("La respuesta usa montos decimales; Donata trabaja con pesos enteros.")
    return issues
