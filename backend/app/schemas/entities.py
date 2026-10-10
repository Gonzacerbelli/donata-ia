from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ..models.base import ObjIdStr


class ProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    contact: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=200, pattern=r"[^@\s]+@[^@\s]+\.[^@\s]+")
    cuit: str | None = Field(default=None, max_length=20)
    notes: str | None = None


class ProviderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    contact: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=200, pattern=r"[^@\s]+@[^@\s]+\.[^@\s]+")
    cuit: str | None = Field(default=None, max_length=20)
    notes: str | None = None
    active: bool | None = None


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    description: str | None = None
    price: int | None = Field(default=None, ge=0)
    price_mayorista: int | None = Field(default=None, ge=0)
    cost: int | None = Field(default=None, ge=0)
    stock: int = Field(default=0, ge=0)
    min_stock: int = Field(default=0, ge=0)
    unit: str = "unidad"
    provider_id: ObjIdStr


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=120)
    description: str | None = None
    price: int | None = Field(default=None, ge=0)
    price_mayorista: int | None = Field(default=None, ge=0)
    cost: int | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    min_stock: int | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=40)
    provider_id: ObjIdStr | None = None
    active: bool | None = None


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=200, pattern=r"[^@\s]+@[^@\s]+\.[^@\s]+")
    instagram: str | None = Field(default=None, max_length=120)
    address: str | None = None
    type: Literal["minorista", "mayorista", "ambos"] = "minorista"
    notes: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=200, pattern=r"[^@\s]+@[^@\s]+\.[^@\s]+")
    instagram: str | None = Field(default=None, max_length=120)
    address: str | None = None
    type: Literal["minorista", "mayorista", "ambos"] | None = None
    notes: str | None = None


class SaleItemIn(BaseModel):
    product_id: ObjIdStr | None = None
    description: str | None = None
    qty: int = Field(gt=0)
    unit_price: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _requires_product_or_description(self):
        if not self.product_id and not (self.description and self.description.strip()):
            raise ValueError("Un ítem necesita product_id o description")
        return self


class SaleCreate(BaseModel):
    client_id: ObjIdStr
    client_type: Literal["minorista", "mayorista"] | None = None
    date: datetime | None = None
    items: list[SaleItemIn] = Field(min_length=1)
    shipping_cost: int = Field(default=0, ge=0)
    discount: int = Field(default=0, ge=0)
    discount_pct: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    ship_by: datetime | None = None
    payment_due: datetime | None = None


class SaleUpdate(BaseModel):
    status: Literal["pendiente", "en_proceso", "entregado", "cancelado"] | None = None
    shipping_cost: int | None = Field(default=None, ge=0)
    discount: int | None = Field(default=None, ge=0)
    discount_pct: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    ship_by: datetime | None = None
    payment_due: datetime | None = None


class PaymentCreate(BaseModel):
    amount: int = Field(gt=0)
    date: datetime | None = None
    type: Literal["adelanto", "pago"] = "pago"
    method: str | None = Field(default=None, max_length=60)
    notes: str | None = None


class StockAdjust(BaseModel):
    product_id: ObjIdStr
    quantity: int
    reason: str = Field(min_length=1, max_length=200)


class WorkItemUpdate(BaseModel):
    status: Literal["pendiente", "en_curso", "bloqueado", "terminado"] | None = None
    priority: Literal["alta", "media", "baja"] | None = None
    assigned_to: ObjIdStr | None = None


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)

    @field_validator("text")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("El comentario no puede estar vacío")
        return stripped
