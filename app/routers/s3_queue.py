import logging

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from typing import Optional, Any
from uuid import UUID

from app.config import settings
from app.database import get_db_connection
from app.dependencies.permissions import get_permission_service
from app.models.queue import (
    SendMessageRequest, 
    ReadMessagesResponse, 
    MessageIdResponse, 
    SuccessResponse
)
from app.routers.image import get_image_by_id
from app.services.permission_service import PermissionService
from app.services.s3_queue_service import S3QueueService, get_s3_queue_service
from app.services.s3_objects_service import S3ObjectService, get_s3_objects_service
from app.utils.images_routines import ImageUploadStatus, update_image_upload_status


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
    permission_service: PermissionService = Depends(get_permission_service),
    s3_service: S3ObjectService = Depends(get_s3_objects_service),
    sqs_service: S3QueueService = Depends(get_s3_queue_service)
)   -> dict[str, Any]:
    """ 
    Обработка сообщений из очереди начиная с указанной даты.
    
    - **folder_id**: ID папки в Yandex Cloud
    - **queue_name**: Имя очереди
    - **uploaded_since**: Начальная дата для фильтрации (ISO format, например: 2024-01-01T00:00:00)
    - **max_messages**: от 1 до 10 сообщений за раз
    - **wait_time**: время ожидания (long polling)
    """
    queue_url = sqs_service.build_queue_url(folder_id, queue_name)
    logger.info(f"📤 Processing messages from queue: {queue_url} from date: {uploaded_since}")
    
    processed_count = 0
    failed_count = 0
    skipped_count = 0
    
    try:
        messages = await sqs_service.read_queue_messages(
            queue_url=queue_url,
            max_messages=max_messages,
            wait_time=wait_time
        )
        
        if not messages:
            logger.info("No messages in queue")
            return {
                "status": "success",
                "processed": 0,
                "failed": 0,
                "skipped": 0,
                "message": "No messages in queue"
            }
        
        async for conn in get_db_connection():
            try:
                for message in messages:
                    try:
                        receipt_handle = message.get('receipt_handle', "")

                        body = message.get('body', {})
                        if isinstance(body, str):
                            import json
                            body = json.loads(body)
                        
                        bucket = body.get('bucket')
                        key = body.get('key')
                        last_modified = body.get('last_modified')
                        
                        if not all([bucket, key, last_modified]):
                            logger.warning(f"Skipping message: missing required fields. Body: {body}")
                            skipped_count += 1
                            await sqs_service.delete_queue_message(
                                queue_url=queue_url,
                                receipt_handle=receipt_handle
                            )
                            continue
                        
                        if bucket == settings.s3_bucket_name:
                            new_key = key.rsplit('.', 1)[0] if '.' in key else key
                        else:
                            logger.info(f"Skipping message: bucket {bucket} is not {settings.s3_bucket_name}")
                            skipped_count += 1
                            await sqs_service.delete_queue_message(
                                queue_url=queue_url,
                                receipt_handle=receipt_handle
                            )
                            continue
                        
                        try:
                            try:
                                image_uuid = UUID(new_key)
                            except ValueError:
                                logger.error(f"Invalid UUID format: {new_key}")
                                failed_count += 1
                                await sqs_service.delete_queue_message(
                                    queue_url=queue_url,
                                    receipt_handle=receipt_handle
                                )
                                continue
                            
                            image = await get_image_by_id(
                                image_id=image_uuid,
                                conn=conn,
                                permission_service=permission_service,
                                s3_service=s3_service
                            )
                            
                            if not image:
                                logger.error(f"Image not found with id: {new_key}")
                                failed_count += 1
                                await sqs_service.delete_queue_message(
                                    queue_url=queue_url,
                                    receipt_handle=receipt_handle
                                )
                                continue
                            
                            await update_image_upload_status(
                                conn=conn,
                                image_id=image.id,
                                upload_status=ImageUploadStatus.UPLOADED,
                                server_uploaded_at=last_modified,
                                force=True
                            )
                            
                            logger.info(f"✅ Successfully processed image: {new_key}, last_modified: {last_modified}")
                            processed_count += 1
                            
                            await sqs_service.delete_queue_message(
                                queue_url=queue_url,
                                receipt_handle=receipt_handle
                            )
                            
                        except Exception as e:
                            logger.error(f"Error processing image {new_key}: {e}")
                            failed_count += 1
                            await sqs_service.delete_queue_message(
                                queue_url=queue_url,
                                receipt_handle=receipt_handle
                            )
                            
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        failed_count += 1
                        try:
                            await sqs_service.delete_queue_message(
                                queue_url=queue_url,
                                receipt_handle=receipt_handle
                            )
                        except Exception as delete_error:
                            logger.error(f"Error deleting message: {delete_error}")
                
                break  # Выходим из async for после обработки
                
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                return {
                    "status": "error",
                    "message": f"Database connection error: {str(e)}"
                }
        
        return {
            "status": "success",
            "processed": processed_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "total_processed": len(messages),
            "message": f"Processed {processed_count} messages, failed {failed_count}, skipped {skipped_count}"
        }
        
    except Exception as e:
        logger.error(f"Error processing messages: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing messages: {str(e)}")