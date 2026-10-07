from motor.motor_asyncio import AsyncIOMotorDatabase

from ..core.errors import (
    BusinessRuleError,
    ConflictError,
    DomainError,
    NotFoundError,
    UnprocessableError,
)
from ..models import Payment, Sale, utcnow
from ..repositories import clients as clients_repo
from ..repositories import products as products_repo
from ..repositories import sales as sales_repo
from ..repositories.base import valid_oid
from ..schemas.entities import PaymentCreate, SaleCreate, SaleUpdate
from . import stock as stock_service


def _resolve_price(product, client_type: str) -> int | None:
    if client_type == "mayorista" and product.price_mayorista is not None:
        return product.price_mayorista
    return product.price


def _compute_discount(subtotal: int, discount: int, discount_pct: float | None) -> int:
    if discount_pct is not None:
        discount = round(subtotal * discount_pct / 100)
    return max(0, min(discount, subtotal))


async def list_sales(
    db: AsyncIOMotorDatabase,
    *,
    status: str | None = None,
    client_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = None,
) -> list[Sale]:
    return await sales_repo.list_sales(
        db,
        status=status,
        client_id=client_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )


async def get_sale_or_404(db: AsyncIOMotorDatabase, sale_id: str) -> Sale:
    sale = await sales_repo.get_sale(db, sale_id)
    if sale is None:
        raise NotFoundError("La venta no existe")
    return sale


async def create_sale(db: AsyncIOMotorDatabase, body: SaleCreate) -> Sale:
    client = await clients_repo.get_client(db, body.client_id)
    if client is None:
        raise NotFoundError("El cliente no existe")
    client_type = body.client_type or (client.type if client.type != "ambos" else "minorista")

    subtotal = 0
    items: list[dict] = []
    for item in body.items:
        price = item.unit_price
        description = item.description
        if item.product_id:
            product = await products_repo.get_product(db, item.product_id)
            if product is None:
                raise UnprocessableError(f"El producto {item.product_id} no existe")
            description = description or product.name
            if price is None:
                price = _resolve_price(product, client_type)
        if price is None:
            raise UnprocessableError("Falta el precio de un ítem")
        if not description:
            raise UnprocessableError("Falta la descripción de un ítem")
        subtotal += price * item.qty
        items.append(
            {
                "product_id": valid_oid(item.product_id) if item.product_id else None,
                "description": description,
                "qty": item.qty,
                "unit_price": price,
            }
        )

    discount = _compute_discount(subtotal, body.discount, body.discount_pct)
    total = subtotal - discount + body.shipping_cost
    if total < 0:
        raise UnprocessableError("El total no puede ser negativo")

    now = utcnow()
    sale_doc = {
        "client_id": valid_oid(str(client.id)),
        "client_type": client_type,
        "date": body.date or now,
        "items": items,
        "subtotal": subtotal,
        "discount": discount,
        "discount_pct": body.discount_pct,
        "shipping_cost": body.shipping_cost,
        "total": total,
        "status": "pendiente",
        "payments": [],
        "notes": body.notes,
        "created_at": now,
        "updated_at": now,
    }
    sale = await sales_repo.create_sale(db, sale_doc)

    applied: list[tuple[str, int]] = []
    try:
        for it in sale.items:
            if it.product_id:
                await stock_service.move_stock(
                    db,
                    it.product_id,
                    -it.qty,
                    reason=f"Venta a {client.name}",
                    ref_type="venta",
                    ref_id=sale.id,
                )
                applied.append((it.product_id, it.qty))
    except DomainError:
        for product_id, qty in applied:
            await stock_service.move_stock(
                db,
                product_id,
                qty,
                reason="Reversión de venta fallida",
                ref_type="ajuste",
                ref_id=sale.id,
            )
        await sales_repo.delete_sale(db, sale.id)
        raise
    return sale


async def _cancel_sale(db: AsyncIOMotorDatabase, sale: Sale) -> None:
    for it in sale.items:
        if it.product_id:
            await stock_service.move_stock(
                db,
                it.product_id,
                it.qty,
                reason="Cancelación de venta",
                ref_type="cancelacion",
                ref_id=sale.id,
                require_stock=False,
            )


async def _reactivate_sale(db: AsyncIOMotorDatabase, sale: Sale) -> None:
    for it in sale.items:
        if it.product_id:
            await stock_service.move_stock(
                db,
                it.product_id,
                -it.qty,
                reason="Reactivación de venta",
                ref_type="venta",
                ref_id=sale.id,
            )


async def update_sale(db: AsyncIOMotorDatabase, sale_id: str, body: SaleUpdate) -> Sale:
    sale = await sales_repo.get_sale(db, sale_id)
    if sale is None:
        raise NotFoundError("La venta no existe")
    updates: dict = {}
    if body.status is not None and body.status != sale.status:
        if body.status == "cancelado" and sale.status != "cancelado":
            await _cancel_sale(db, sale)
        elif sale.status == "cancelado" and body.status != "cancelado":
            await _reactivate_sale(db, sale)
        updates["status"] = body.status

    financial = False
    if body.shipping_cost is not None:
        updates["shipping_cost"] = body.shipping_cost
        financial = True
    if body.discount_pct is not None:
        updates["discount_pct"] = body.discount_pct
        updates["discount"] = _compute_discount(sale.subtotal, sale.discount, body.discount_pct)
        financial = True
    elif body.discount is not None:
        updates["discount"] = _compute_discount(sale.subtotal, body.discount, None)
        financial = True
    if financial:
        discount = updates.get("discount", sale.discount)
        shipping = updates.get("shipping_cost", sale.shipping_cost)
        total = sale.subtotal - discount + shipping
        if total < 0:
            raise UnprocessableError("El total no puede ser negativo")
        updates["total"] = total

    updates["updated_at"] = utcnow()
    updated = await sales_repo.update_sale(db, sale_id, updates)
    assert updated is not None
    return updated


async def add_payment(db: AsyncIOMotorDatabase, sale_id: str, body: PaymentCreate) -> Sale:
    sale = await sales_repo.get_sale(db, sale_id)
    if sale is None:
        raise NotFoundError("La venta no existe")
    if sale.status == "cancelado":
        raise BusinessRuleError("No se pueden registrar pagos de una venta cancelada")
    payment = Payment(
        amount=body.amount,
        date=body.date or utcnow(),
        type=body.type,
        method=body.method,
        notes=body.notes,
    )
    updated = await sales_repo.add_payment(db, sale_id, payment.model_dump())
    assert updated is not None
    return updated


async def delete_sale(db: AsyncIOMotorDatabase, sale_id: str) -> None:
    sale = await sales_repo.get_sale(db, sale_id)
    if sale is None:
        raise NotFoundError("La venta no existe")
    if sale.payments:
        raise ConflictError("No se puede eliminar una venta con pagos registrados")
    if sale.status != "cancelado":
        await _cancel_sale(db, sale)
    await sales_repo.delete_sale(db, sale_id)
