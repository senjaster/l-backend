"""Queue model"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class QueueMessage(BaseModel):
    message_id: str
    receipt_handle: str
    body: Union[Dict[str, Any], List[Any], str]
    body_raw: str
    attributes: Dict[str, Any]
    message_attributes: Dict[str, Any]

class SendMessageRequest(BaseModel):
    message_body: Union[str, dict, list] = Field(..., description="Тело сообщения")
    delay_seconds: int = Field(0, ge=0, le=900, description="Задержка в секундах")

class ReadMessagesResponse(BaseModel):
    messages: List[QueueMessage]
    count: int

class HeadObjectResponse(BaseModel):
    content_length: Optional[int]
    content_type: Optional[str]
    last_modified: Optional[str]
    etag: Optional[str]
    metadata: Dict[str, str]

class MessageIdResponse(BaseModel):
    message_id: str
    success: bool = True

class SuccessResponse(BaseModel):
    success: bool
    message: Optional[str] = None