from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    issue_id: Optional[int] = None
    title: str
    message: str
    is_read: bool
    created_at: datetime
