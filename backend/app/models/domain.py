from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field

from .base import BaseDocument, ObjIdStr, utcnow


class User(BaseDocument):
    google_sub: str
    email: str
    name: str | None = None
    picture: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    last_login_at: datetime | None = None


class Provider(BaseDocument):
    name: str
    contact: str | None = None
    phone: str | None = None
    email: str | None = None
    cuit: str | None = None
    notes: str | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Product(BaseDocument):
    name: str
    category: str | None = None
    description: str | None = None
    price: int | None = Field(default=None, ge=0)
    price_mayorista: int | None = Field(default=None, ge=0)
    cost: int | None = Field(default=None, ge=0)
    stock: int = Field(default=0, ge=0)
    min_stock: int = Field(default=0, ge=0)
    unit: str = "unidad"
    provider_id: ObjIdStr
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Client(BaseDocument):
    name: str
    phone: str | None = None
    email: str | None = None
    instagram: str | None = None
    address: str | None = None
    type: Literal["minorista", "mayorista", "ambos"] = "minorista"
    notes: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class SaleItem(BaseModel):
    product_id: ObjIdStr | None = None
    description: str
    qty: int = Field(gt=0)
    unit_price: int = Field(ge=0)


class Payment(BaseModel):
    amount: int = Field(gt=0)
    date: datetime = Field(default_factory=utcnow)
    type: Literal["adelanto", "pago"] = "pago"
    method: str | None = None
    notes: str | None = None


class Sale(BaseDocument):
    client_id: ObjIdStr
    client_type: Literal["minorista", "mayorista"] = "minorista"
    date: datetime = Field(default_factory=utcnow)
    items: list[SaleItem]
    subtotal: int = 0
    shipping_cost: int = Field(default=0, ge=0)
    discount: int = Field(default=0, ge=0)
    discount_pct: float | None = Field(default=None, ge=0, le=100)
    total: int = 0
    status: Literal["pendiente", "en_proceso", "entregado", "cancelado"] = "pendiente"
    payments: list[Payment] = Field(default_factory=list)
    notes: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @computed_field
    @property
    def paid(self) -> int:
        return sum(p.amount for p in self.payments)

    @computed_field
    @property
    def balance(self) -> int:
        return self.total - self.paid


class StockMove(BaseDocument):
    product_id: ObjIdStr
    product_name: str
    quantity: int
    stock_after: int
    reason: str | None = None
    ref_type: Literal["venta", "cancelacion", "compra", "ajuste"] | None = None
    ref_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class ChatThread(BaseDocument):
    thread_id: str
    user_id: ObjIdStr
    title: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class ToolCall(BaseModel):
    name: str
    arguments: dict = Field(default_factory=dict)
    result: Any = None
    ok: bool = True
    created_at: datetime = Field(default_factory=utcnow)


class ChatMessage(BaseDocument):
    thread_id: str
    role: Literal["user", "assistant"]
    content: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
