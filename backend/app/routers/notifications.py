from fastapi import APIRouter, Depends

from ..dependencies import CurrentUser, Database, get_current_user
from ..schemas.notifications import NotificationList, NotificationUpdate
from ..services import notifications as notifications_service

router = APIRouter(
    prefix="/notifications", tags=["notifications"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=NotificationList)
async def list_notifications(user: CurrentUser, db: Database) -> NotificationList:
    result = await notifications_service.list_notifications(db, str(user.id))
    return NotificationList(**result)


@router.patch("/{notification_id}", response_model=NotificationList)
async def update_notification(
    notification_id: str, body: NotificationUpdate, user: CurrentUser, db: Database
) -> NotificationList:
    result = await notifications_service.update_notification(
        db, str(user.id), notification_id, read=body.read, dismissed=body.dismissed
    )
    return NotificationList(**result)


@router.post("/read-all", response_model=NotificationList)
async def mark_all_read(user: CurrentUser, db: Database) -> NotificationList:
    result = await notifications_service.mark_all_read(db, str(user.id))
    return NotificationList(**result)


@router.post("/dismiss-all", response_model=NotificationList)
async def dismiss_all(user: CurrentUser, db: Database) -> NotificationList:
    result = await notifications_service.dismiss_all(db, str(user.id))
    return NotificationList(**result)
