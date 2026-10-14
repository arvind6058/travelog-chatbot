from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Customer chat message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation identifier")


class ChatResponse(BaseModel):
    success: bool = True
    reply: str
    message: Optional[str] = None
    intent: str
    destination: Optional[str] = None
    duration_days: Optional[int] = None
    tracking_id: Optional[str] = None
    provenance: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    mode: Optional[str] = None
    is_mock: Optional[bool] = False
    fetched_at: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    persisted: bool = False
