from fastapi import APIRouter, Depends

from ..dependencies import Database, get_current_user
from ..models import Sale
from ..schemas.entities import PaymentCreate, SaleCreate, SaleUpdate
from ..services import sales as sales_service

router = APIRouter(prefix="/sales", tags=["sales"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[Sale])
async def list_sales(
    db: Database,
    status: str | None = None,
    client_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = None,
) -> list[Sale]:
    return await sales_service.list_sales(
        db,
        status=status,
        client_id=client_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )


@router.post("", response_model=Sale, status_code=201)
async def create_sale(body: SaleCreate, db: Database) -> Sale:
    return await sales_service.create_sale(db, body)


@router.get("/{sale_id}", response_model=Sale)
async def get_sale(sale_id: str, db: Database) -> Sale:
    return await sales_service.get_sale_or_404(db, sale_id)


@router.patch("/{sale_id}", response_model=Sale)
async def update_sale(sale_id: str, body: SaleUpdate, db: Database) -> Sale:
    return await sales_service.update_sale(db, sale_id, body)


@router.delete("/{sale_id}", status_code=204)
async def delete_sale(sale_id: str, db: Database) -> None:
    await sales_service.delete_sale(db, sale_id)


@router.post("/{sale_id}/payments", response_model=Sale)
async def add_payment(sale_id: str, body: PaymentCreate, db: Database) -> Sale:
    return await sales_service.add_payment(db, sale_id, body)
