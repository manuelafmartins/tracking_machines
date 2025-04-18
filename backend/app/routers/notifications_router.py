from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from .. import database, models
from ..dependencies import get_current_user
from ..notifications import notify_specific_user, send_sms_notification

# Configure router
router = APIRouter(tags=["notifications"], prefix="/notifications")


class TestNotificationRequest(BaseModel):
    """
    Schema for test notification requests.
    
    Attributes:
        message: The notification text to send
        user_id: Optional target user ID (admin only, defaults to current user)
    """
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
    
    This endpoint allows testing the notification system without triggering actual
    system events. Users can send notifications to themselves, while administrators 
    can send test notifications to any user.
    
    Args:
        request: Test notification request containing message and optional user_id
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 
            - 403 if non-admin tries to send to another user
            - 400 if current user has no phone number or notifications disabled
            - 500 if notification fails to send
    """
    if request.user_id and request.user_id != current_user.id:
        # Only admins can send to other users
        if current_user.role != models.UserRoleEnum.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can send test notifications to other users"
            )
        # Send to specific user
        success = notify_specific_user(db, request.user_id, request.message)
    else:
        # Send to current user
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

    # Handle result
    if success:
        return {"success": True, "message": "Test notification sent successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification"
        )