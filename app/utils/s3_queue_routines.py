import logging

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any
from uuid import UUID

from app.config import settings
from app.database import get_db_connection
from app.models.image import ImageUploadStatus
from app.repositories.image import image_repo
from app.services.s3_queue_service import S3QueueService, get_s3_queue_service
from app.utils.images_routines import update_image_upload_status

logger = logging.getLogger(__name__)


class QueueBackgroundProcessor:
    """Класс для фоновой обработки сообщений из очереди"""
    
    def __init__(
        self,
        queue_url: str,
        sqs_service: S3QueueService,
        batch_size: int = 10,
        timeout_seconds: int = 20
    ) -> None:
        self.queue_url = queue_url
        self.sqs_service = sqs_service
        self.batch_size = batch_size
        self.timeout_seconds = timeout_seconds
        
    async def _check_queue_available(self) -> bool:
        """Проверяет доступность очереди"""
        try:
            return bool(self.queue_url)
        except Exception:
            return False
    
    async def process_messages_loop(
        self,
        conn,
        uploaded_since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Циклическая обработка сообщений из очереди
        
        Args:
            conn: Соединение с базой данных
            uploaded_since: Начальная дата для фильтрации (опционально)
            limit: Максимальное количество сообщений для обработки
            
        Returns:
            Dict со статистикой обработки
        """
        processed = 0
        failed = 0
        skipped = 0
        total_processed = 0
        
        skipped_reasons = {
            'missing_required_fields': 0,
            'wrong_bucket': 0,
            'date_filter': 0
        }
        failed_reasons = {
            'invalid_uuid': 0,
            'image_not_found': 0
        }
        
        if not await self._check_queue_available():
            logger.error(f"Queue {self.queue_url} is not available")
            return {
                "processed": 0, 
                "failed": 0, 
                "skipped": 0,
                "details": {
                    "skipped_reasons": skipped_reasons,
                    "failed_reasons": failed_reasons
                }
            }
        
        while True:
            if limit is not None and total_processed >= limit:
                logger.info(f"Reached limit of {limit} messages")
                break
            
            remaining = limit - total_processed if limit is not None else self.batch_size
            batch_size = min(self.batch_size, remaining)
            
            messages = await self.sqs_service.read_queue_messages(
                queue_url=self.queue_url,
                max_messages=batch_size,
                wait_time=self.timeout_seconds
            )
            
            if not messages:
                logger.info("No more messages in queue")
                break
            
            for message in messages:
                if limit is not None and total_processed >= limit:
                    break
                
                status, detail = await self.process_single_message(
                    message=message,
                    conn=conn,
                    queue_url=self.queue_url,
                    sqs_service=self.sqs_service,
                    uploaded_since=uploaded_since
                )
                
                if status == 'processed':
                    processed += 1
                elif status == 'failed':
                    failed += 1
                    if detail in failed_reasons:
                        failed_reasons[detail] += 1
                elif status == 'skipped':
                    skipped += 1
                    if detail in skipped_reasons:
                        skipped_reasons[detail] += 1
                
                total_processed += 1
            
            if len(messages) < batch_size:
                break
        
        return {
            "processed": processed,
            "failed": failed,
            "skipped": skipped,
            "total_processed": total_processed,
            "details": {
                "skipped_reasons": skipped_reasons,
                "failed_reasons": failed_reasons
            }
        }
    
    async def process_single_message(
        self,
        message: Dict[str, Any],
        conn,
        queue_url: str,
        sqs_service: S3QueueService,
        uploaded_since: Optional[datetime] = None
    ) -> tuple[str, str]:
        """
        Обрабатывает одно сообщение из очереди
        
        Args:
            message: Сообщение из очереди
            conn: Соединение с базой данных
            queue_url: URL очереди
            sqs_service: Сервис SQS
            uploaded_since: Начальная дата для фильтрации (опционально)
        
        Returns:
            Tuple (status, details) где status: 'processed', 'failed', 'skipped'
        """
        receipt_handle = message.get('receipt_handle', "")
        
        try:
            body = message.get('body', {})
            if isinstance(body, str):
                import json
                body = json.loads(body)
            
            bucket = body.get('bucket')
            key = body.get('key')
            last_modified = body.get('last_modified')
            last_modified_dt = None
            
            if not all([bucket, key, last_modified]):
                logger.warning(f"Skipping message: missing required fields. Body: {body}")
                await sqs_service.delete_queue_message(
                    queue_url=queue_url,
                    receipt_handle=receipt_handle
                )
                return ('skipped', 'missing_required_fields')
            
            if uploaded_since is not None:
                try:
                    if isinstance(last_modified, str):
                        last_modified_dt = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                        uploaded_since_dt = uploaded_since.replace(tzinfo=timezone.utc)
                        if last_modified_dt < uploaded_since_dt:
                            logger.info(f"Skipping message: last_modified {last_modified} < uploaded_since {uploaded_since}")
                            await sqs_service.delete_queue_message(
                                queue_url=queue_url,
                                receipt_handle=receipt_handle
                            )
                            return ('skipped', 'date_filter')
                except (ValueError, AttributeError):
                    logger.warning(f"Invalid date format or unable to parse: {last_modified}")
                    # Продолжаем обработку, если дата не распарсилась
            
            if bucket != settings.s3_bucket_name:
                logger.info(f"Skipping message: bucket {bucket} is not {settings.s3_bucket_name}")
                await sqs_service.delete_queue_message(
                    queue_url=queue_url,
                    receipt_handle=receipt_handle
                )
                return ('skipped', 'wrong_bucket')
            
            new_key = key.rsplit('.', 1)[0] if '.' in key else key
            
            try:
                image_uuid = UUID(new_key)
            except ValueError:
                logger.error(f"Invalid UUID format: {new_key}")
                await sqs_service.delete_queue_message(
                    queue_url=queue_url,
                    receipt_handle=receipt_handle
                )
                return ('failed', 'invalid_uuid')
            
            image = await image_repo.get_by_id(conn=conn, image_id=image_uuid)
            
            if not image:
                logger.error(f"Image not found with id: {new_key}")
                await sqs_service.delete_queue_message(
                    queue_url=queue_url,
                    receipt_handle=receipt_handle
                )
                return ('failed', 'image_not_found')
            
            await update_image_upload_status(
                conn=conn,
                image_id=image.id,
                upload_status=ImageUploadStatus.UPLOADED,
                server_uploaded_at=last_modified_dt,
                force=True
            )
            
            logger.info(f"  Successfully processed image: {new_key}, last_modified: {last_modified}")
            
            await sqs_service.delete_queue_message(
                queue_url=queue_url,
                receipt_handle=receipt_handle
            )
            
            return ('processed', 'success')
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            try:
                await sqs_service.delete_queue_message(
                    queue_url=queue_url,
                    receipt_handle=receipt_handle
                )
            except Exception as delete_error:
                logger.error(f"Error deleting message: {delete_error}")
            return ('failed', str(e))


async def process_messages_background(
    folder_id: str,
    queue_name: str,
    uploaded_since: Optional[datetime] = datetime.now() - timedelta(days=2),
    batch_size: int = 10,
    timeout_seconds: int = 20,
    limit: Optional[int] = None,
    sqs_service: Optional[S3QueueService] = None
) -> Dict[str, Any]:
    """
    Фоновая задача для обработки сообщений из очереди порциями
    
    Args:
        folder_id: ID папки в Yandex Cloud
        queue_name: Имя очереди
        uploaded_since: Начальная дата для фильтрации сообщений
        batch_size: Размер порции (максимум сообщений за раз)
        timeout_seconds: Таймаут ожидания сообщений в секундах
        limit: Максимальное количество сообщений для обработки (None - без лимита)
        sqs_service: Сервис SQS очередей
    
    Returns:
        Dict с количеством обработанных, неудачных и пропущенных сообщений
    """
    if sqs_service is None:
        sqs_service = await get_s3_queue_service()
    
    queue_url = sqs_service.build_queue_url(folder_id, queue_name)
    logger.info(f"  Starting background processing from queue: {queue_url} from date: {uploaded_since}")
    
    total_processed = 0
    total_failed = 0
    total_skipped = 0
    
    async for conn in get_db_connection():
        try:
            processor = QueueBackgroundProcessor(
                queue_url=queue_url,
                sqs_service=sqs_service,
                batch_size=batch_size,
                timeout_seconds=timeout_seconds
            )
            
            stats = await processor.process_messages_loop(
                conn=conn,
                uploaded_since=uploaded_since,
                limit=limit
            )
            
            total_processed = stats.get('processed', 0)
            total_failed = stats.get('failed', 0)
            total_skipped = stats.get('skipped', 0)
            
            logger.info(f"  Background processing completed: processed={total_processed}, "
                       f"failed={total_failed}, skipped={total_skipped}")
            
        except Exception as e:
            logger.error(f"  Error in background task: {e}", exc_info=True)
            return {
                "processed": 0,
                "failed": 0,
                "skipped": 0,
                "error": str(e)
            }
    
    return {
        "processed": total_processed,
        "failed": total_failed,
        "skipped": total_skipped
    }

