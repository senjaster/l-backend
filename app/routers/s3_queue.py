import asyncio
import logging

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from typing import Optional, Any, Dict

from app.dependencies.permissions import get_permission_service
from app.models.queue import (
    SendMessageRequest, 
    ReadMessagesResponse, 
    MessageIdResponse, 
    SuccessResponse
)
from app.services.s3_queue_service import S3QueueService, get_s3_queue_service
from app.services.s3_objects_service import get_s3_objects_service
from app.utils.images_routines import update_image_upload_status_in_db
from app.utils.s3_queue_routines import (
    process_messages_background
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/s3_queue", tags=["s3_queue"])


@router.get("/{folder_id}/{queue_name}/messages", response_model=ReadMessagesResponse)
async def read_messages(
    folder_id: str = Path(..., description="ID папки в Yandex Cloud"),
    queue_name: str = Path(..., description="Имя очереди"),
    max_messages: int = Query(10, ge=1, le=10, description="Максимальное количество сообщений (1-10)"),
    wait_time: int = Query(20, ge=0, le=20, description="Время ожидания в секундах (0-20)"),
    service: S3QueueService = Depends(get_s3_queue_service)
) -> ReadMessagesResponse:
    """
    Чтение сообщений из очереди Yandex Message Queue.
    
    - **folder_id**: ID папки в Yandex Cloud
    - **queue_name**: Имя очереди
    - **max_messages**: от 1 до 10 сообщений за раз
    - **wait_time**: время ожидания (long polling)
    
    Пример:
    GET /s3_queue/b1gqe8fc51c3onjshekj/dj60000000q167rj06qd/file-info-queue/messages?max_messages=10&wait_time=20
    """
    queue_url = service.build_queue_url(folder_id, queue_name)
    logger.info(f"📤 Reading from queue: {queue_url}")
    
    try:
        messages = await service.read_queue_messages(
            queue_url=queue_url,
            max_messages=max_messages,
            wait_time=wait_time
        )
        return ReadMessagesResponse(
            messages=messages,
            count=len(messages)
        )
    except Exception as e:
        logger.error(f"Error reading messages: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading messages: {str(e)}")


@router.delete("/{folder_id}/{queue_name}/messages", response_model=SuccessResponse)
async def delete_message(
    folder_id: str = Path(..., description="ID папки в Yandex Cloud"),
    queue_name: str = Path(..., description="Имя очереди"),
    receipt_handle: str = Query(..., description="Receipt handle сообщения"),
    service: S3QueueService = Depends(get_s3_queue_service)
) -> SuccessResponse:
    """
    Удаление сообщения из очереди после обработки.
    
    - **folder_id**: ID папки в Yandex Cloud
    - **queue_name**: Имя очереди
    - **receipt_handle**: Handle сообщения, полученный при чтении
    
    Пример:
    DELETE /s3_queue/b1gqe8fc51c3onjshekj/dj60000000q167rj06qd/file-info-queue/messages?receipt_handle=abc123
    """
    queue_url = service.build_queue_url(folder_id, queue_name)
    
    try:
        success = await service.delete_queue_message(
            queue_url=queue_url,
            receipt_handle=receipt_handle
        )
        if not success:
            raise HTTPException(status_code=404, detail="Message not found or already deleted")
        return SuccessResponse(success=True, message="Message deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting message: {str(e)}")


@router.post("/{folder_id}/{queue_name}/purge", response_model=SuccessResponse)
async def purge_queue(
    folder_id: str = Path(..., description="ID папки в Yandex Cloud"),
    queue_name: str = Path(..., description="Имя очереди"),
    confirm: bool = Query(False, description="Подтверждение очистки очереди"),
    service: S3QueueService = Depends(get_s3_queue_service)
) -> SuccessResponse:
    """
    Очистка всех сообщений из очереди.
    
    ⚠️ **Внимание**: Необратимая операция! Используйте с осторожностью.
    
    - **folder_id**: ID папки в Yandex Cloud
    - **queue_name**: Имя очереди
    - **confirm**: Должен быть True для подтверждения операции
    
    Пример:
    POST /s3_queue/b1gqe8fc51c3onjshekj/dj60000000q167rj06qd/file-info-queue/purge?confirm=true
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required: set confirm=true to purge the queue"
        )
    
    queue_url = service.build_queue_url(folder_id, queue_name)
    
    try:
        success = await service.purge_queue(queue_url=queue_url)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to purge queue")
        return SuccessResponse(success=True, message="Queue purged successfully")
    except Exception as e:
        logger.error(f"Error purging queue: {e}")
        raise HTTPException(status_code=500, detail=f"Error purging queue: {str(e)}")


@router.post("/{folder_id}/{queue_name}/messages", response_model=MessageIdResponse)
async def send_message(
    folder_id: str = Path(..., description="ID папки в Yandex Cloud"),
    queue_name: str = Path(..., description="Имя очереди"),
    request: SendMessageRequest = Body(...),
    service: S3QueueService = Depends(get_s3_queue_service)
) -> MessageIdResponse:
    """
    Отправка сообщения в очередь Yandex Message Queue.
    
    - **folder_id**: ID папки в Yandex Cloud
    - **queue_name**: Имя очереди
    - **request**: Тело сообщения (строка, JSON объект или массив)
    
    Пример:
    POST /s3_queue/b1gqe8fc51c3onjshekj/dj60000000q167rj06qd/file-info-queue/messages
    {
        "message_body": {"image_id": "123", "status": "processed"},
        "delay_seconds": 0
    }
    """
    queue_url = service.build_queue_url(folder_id, queue_name)
    
    try:
        message_id = await service.send_queue_message(
            queue_url=queue_url,
            message_body=request.message_body,
            delay_seconds=request.delay_seconds
        )
        
        if message_id is None:
            raise HTTPException(status_code=500, detail="Failed to send message")
        
        return MessageIdResponse(message_id=message_id)
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")


async def log_processing_result(task) -> None:
    """Callback для логирования результата фоновой задачи"""
    try:
        result = await task
        logger.info(f"  Background processing completed: {result}")
        if result.get('error'):
            logger.error(f"   Error: {result.get('error')}")
        else:
            logger.info(f"   Processed: {result.get('processed', 0)}")
            logger.info(f"   Failed: {result.get('failed', 0)}")
            logger.info(f"   Skipped: {result.get('skipped', 0)}")
    except Exception as e:
        logger.error(f"  Background task failed: {e}", exc_info=True)


@router.post("/process_messages_from_date/{folder_id}/{queue_name}")
async def process_messages_from_date(
    folder_id: str = Path(..., description="ID папки в Yandex Cloud"),
    queue_name: str = Path(..., description="Имя очереди"),
    uploaded_since: Optional[datetime] = Query(
        datetime.now() - timedelta(days=2), 
        description="Начальная дата для фильтрации сообщений (ISO format)"
    ),
    max_messages: int = Query(10, ge=1, le=10, description="Максимальное количество сообщений (1-10)"),
    wait_time: int = Query(20, ge=0, le=20, description="Время ожидания в секундах (0-20)"),
    sqs_service: S3QueueService = Depends(get_s3_queue_service)
)   -> Dict[str, Any]:
    """ 
    Обработка сообщений из очереди начиная с указанной даты.
    
    - **folder_id**: ID папки в Yandex Cloud
    - **queue_name**: Имя очереди
    - **uploaded_since**: Начальная дата для фильтрации (ISO format, например: 2024-01-01T00:00:00)
    - **max_messages**: от 1 до 10 сообщений за раз
    - **wait_time**: время ожидания (long polling)
    """
    queue_url = sqs_service.build_queue_url(folder_id, queue_name)
    
    task = asyncio.create_task(
        process_messages_background(
            folder_id=folder_id,
            queue_name=queue_name,
            uploaded_since=uploaded_since,
            batch_size=max_messages,
            timeout_seconds=wait_time,
            sqs_service=sqs_service
        )
    )
    
    task.add_done_callback(
        lambda t: asyncio.create_task(log_processing_result(t))
    )
    
    return {
        "status": "Messages processing has started in background",
        "base_url": queue_url,
        "message": f"Messages will be processed in batches with size of {max_messages}"
    }