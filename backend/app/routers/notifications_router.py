from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from .. import database, models
from ..dependencies import get_current_user
from ..notifications import notify_specific_user, send_sms_notification

router = APIRouter(tags=["notifications"], prefix="/notifications")

class TestNotificationRequest(BaseModel):
    """Schema for test notification requests."""
    message: str
    user_id: Optional[int] = None

@router.post("/test", response_model=dict)
def test_notification(
    request: TestNotificationRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Sends a test notification to the current user or a specific user (admin only).
    """
    if request.user_id and request.user_id != current_user.id:
        # Only admins can send to other users
        if current_user.role != models.UserRoleEnum.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can send test notifications to other users"
            )
        success = notify_specific_user(db, request.user_id, request.message)
    else:
        if not current_user.phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You don't have a registered phone number"
            )
        if not current_user.notifications_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Notifications are disabled for your account"
            )
        success = send_sms_notification(current_user.phone_number, request.message)

    if success:
        return {"success": True, "message": "Test notification sent successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification"
        )
