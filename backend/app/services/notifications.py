from datetime import UTC

from ..core.errors import NotFoundError
from ..models import utcnow
from ..repositories import notifications as notifications_repo
from ..repositories import products as products_repo
from ..repositories import sales as sales_repo

SEVERITY_ORDER = {"alta": 0, "media": 1, "baja": 2}
ENVIO_WINDOW_HOURS = 72


def _aware(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _alert(
    *,
    type_: str,
    severity: str,
    title: str,
    description: str,
    entity: str,
    entity_id: str,
    action: str,
    when,
) -> dict:
    return {
        "id": f"{type_}:{entity_id}",
        "type": type_,
        "severity": severity,
        "title": title,
        "description": description,
        "entity": entity,
        "entity_id": entity_id,
        "action": action,
        "created_at": when,
    }


async def compute_alerts(db) -> list[dict]:
    alerts: list[dict] = []
    now = _aware(utcnow())

    products = await products_repo.list_products(db, active_only=True)
    for product in products:
        if product.stock == 0:
            alerts.append(
                _alert(
                    type_="STOCK_AGOTADO",
                    severity="alta",
                    title=f"Sin stock: {product.name}",
                    description=f"El producto «{product.name}» está agotado.",
                    entity="product",
                    entity_id=str(product.id),
                    action="Reponer urgente",
                    when=_aware(product.updated_at),
                )
            )
        elif product.stock <= product.min_stock:
            alerts.append(
                _alert(
                    type_="STOCK_MINIMO",
                    severity="media",
                    title=f"Stock mínimo: {product.name}",
                    description=(
                        f"Quedan {product.stock} {product.unit} (mínimo {product.min_stock})."
                    ),
                    entity="product",
                    entity_id=str(product.id),
                    action="Programar reposición",
                    when=_aware(product.updated_at),
                )
            )

    window_end = now.timestamp() + ENVIO_WINDOW_HOURS * 3600
    for sale in await sales_repo.list_sales(db):
        if sale.status == "cancelado":
            continue
        ship_by = _aware(sale.ship_by)
        payment_due = _aware(sale.payment_due)

        if ship_by is not None and sale.status != "entregado":
            if ship_by < now:
                alerts.append(
                    _alert(
                        type_="ENVIO_VENCIDO",
                        severity="alta",
                        title=f"Envío vencido (orden {sale.id})",
                        description="La fecha límite de envío ya pasó.",
                        entity="sale",
                        entity_id=str(sale.id),
                        action="Priorizar envío",
                        when=ship_by,
                    )
                )
            elif ship_by.timestamp() <= window_end and sale.status in ("pendiente", "en_proceso"):
                alerts.append(
                    _alert(
                        type_="ENVIO_PENDIENTE",
                        severity="media",
                        title=f"Envío próximo (orden {sale.id})",
                        description="La orden debe despacharse en las próximas 72 h.",
                        entity="sale",
                        entity_id=str(sale.id),
                        action="Preparar envío",
                        when=ship_by,
                    )
                )

        if sale.balance > 0 and sale.status not in ("entregado", "cancelado"):
            if payment_due is not None and payment_due < now:
                alerts.append(
                    _alert(
                        type_="PAGO_VENCIDO",
                        severity="alta",
                        title=f"Cobro vencido (orden {sale.id})",
                        description="El saldo pendiente superó su fecha de vencimiento.",
                        entity="sale",
                        entity_id=str(sale.id),
                        action="Cobro prioritario",
                        when=payment_due,
                    )
                )
            else:
                alerts.append(
                    _alert(
                        type_="PAGO_PENDIENTE",
                        severity="media",
                        title=f"Pago pendiente (orden {sale.id})",
                        description=f"Saldo pendiente de ${sale.balance}.",
                        entity="sale",
                        entity_id=str(sale.id),
                        action="Registrar cobro",
                        when=_aware(sale.updated_at),
                    )
                )

        if not sale.items or not sale.total:
            alerts.append(
                _alert(
                    type_="ORDEN_SIN_ITEMS",
                    severity="baja",
                    title=f"Orden incompleta ({sale.id})",
                    description="La orden no tiene ítems o total.",
                    entity="sale",
                    entity_id=str(sale.id),
                    action="Completar orden",
                    when=_aware(sale.created_at),
                )
            )

    return alerts


async def list_notifications(db, user_id: str) -> dict:
    alerts = await compute_alerts(db)
    states = await notifications_repo.get_states(db, user_id)
    items: list[dict] = []
    for alert in alerts:
        state = states.get(alert["id"], {})
        alert["read"] = bool(state.get("read"))
        alert["dismissed"] = bool(state.get("dismissed"))
        if alert["dismissed"]:
            continue
        items.append(alert)
    items.sort(key=lambda a: (SEVERITY_ORDER[a["severity"]], a["type"], a["id"]))
    unread = sum(1 for item in items if not item["read"])
    return {"items": items, "unread_count": unread}


async def _current_ids(db) -> set[str]:
    return {alert["id"] for alert in await compute_alerts(db)}


async def update_notification(
    db, user_id: str, notification_id: str, *, read=None, dismissed=None
) -> dict:
    if notification_id not in await _current_ids(db):
        raise NotFoundError("La notificación no existe o ya no está vigente")
    fields: dict = {}
    if read is not None:
        fields["read"] = read
    if dismissed is not None:
        fields["dismissed"] = dismissed
    if fields:
        await notifications_repo.set_state(db, user_id, notification_id, **fields)
    return await list_notifications(db, user_id)


async def mark_all_read(db, user_id: str) -> dict:
    for notification_id in await _current_ids(db):
        await notifications_repo.set_state(db, user_id, notification_id, read=True)
    return await list_notifications(db, user_id)


async def dismiss_all(db, user_id: str) -> dict:
    for notification_id in await _current_ids(db):
        await notifications_repo.set_state(db, user_id, notification_id, dismissed=True)
    return await list_notifications(db, user_id)
