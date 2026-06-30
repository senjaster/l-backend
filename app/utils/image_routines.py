import asyncio
import logging
import httpx

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.config import settings
from app.database import get_db_connection
from app.models.image import Image, ImageUploadStatus
from app.repositories.image import ImageRepository
from app.services.s3_objects_service import get_s3_objects_service


logging.getLogger('httpcore').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
image_repo = ImageRepository()


class ImageBackgroundFetcher:
    
    def __init__(self, base_url: str, batch_size: int = 20, s3_service=None) -> None:
        self.base_url = base_url.rstrip('/')
        self.batch_size = batch_size
        self.timeout_seconds = 30  # Таймаут ожидания следующей порции (секунд)
        self.request_timeout = httpx.Timeout(10.0, connect=5.0)  # Таймаут для HTTP запроса
        self.s3_service = s3_service
    
    async def fetch_all_images(
            self,
            conn,
            upload_status: Optional[ImageUploadStatus] = None,
            modified_since: Optional[datetime] = None,
            uploaded_since: Optional[datetime] = None,
            limit: Optional[int] = None
        ) -> List[Image]:
            """Получение всех изображений"""
            
            if modified_since is None:
                modified_since = datetime(2020, 1, 1)
            
            if uploaded_since is None:
                uploaded_since = datetime(2020, 1, 1)
            
            try:
                images = await image_repo.get_all(
                    conn,
                    upload_status=upload_status.value if upload_status else None,
                    modified_since=modified_since,
                    uploaded_since=uploaded_since,
                    limit=limit
                )
                
                self._log_final_download_stats(
                    modified_since=modified_since,
                    uploaded_since=uploaded_since, 
                    upload_status=upload_status.value if upload_status else "unknown",
                    total_images=len(images),
                    start_time=datetime.now(),
                    limit=limit
                )
                
                return images
                
            except Exception as e:
                logger.error(f"\n    Ошибка при получении изображений: {e}")
                raise
    
    def _log_section_header(self, title: str, **kwargs) -> None:
        """Логирование заголовка секции"""
        logger.debug("=" * 80)
        logger.debug(f"  {title}")
        for key, value in kwargs.items():
            logger.debug(f"   {key}: {value}")
        logger.debug("=" * 80)
    
    def _log_progress(self, current: int, total: int, elapsed: float) -> None:
        """Логирование прогресса"""
        progress_percent = current * 100 // total
        logger.debug(f"     Прогресс проверки: {current}/{total} изображений в хранилище S3"
                   f"({progress_percent}%) | Время: {elapsed:.1f} сек")
    
    def _log_final_download_stats(
        self,
        modified_since: datetime,
        uploaded_since: datetime,
        upload_status: Optional[str],
        total_images: int,
        start_time: datetime,
        limit: Optional[int] = None
    ) -> None:
        """Логирование финальной статистики загрузки"""
        total_duration = (datetime.now() - start_time).total_seconds()
        
        logger.debug(f"{'='*60}")
        self._log_section_header(
            "СТАТИСТИКА ЗАГРУЗКИ ИЗОБРАЖЕНИЙ",
            **{
                "  Дата изменения": modified_since.isoformat(),
                "  Дата загрузки": uploaded_since.isoformat(),
                "  URL сервера": self.base_url,
                "  Статус загрузки": upload_status if upload_status else "Все"
            }
        )
        logger.debug(f"{'='*60}")
        logger.debug(f"    Всего загружено: {total_images}")
        logger.debug(f"      Общее время: {total_duration:.2f} сек")
        
        if total_duration > 0:
            logger.debug(f"    Средняя скорость: {total_images/total_duration:.1f} изоб/сек")
        else:
            logger.debug(f"    Средняя скорость: N/A")
        
        if limit:
            logger.debug(f"    Установленный лимит: {limit}")
        
        logger.debug(f"{'='*60}\n")

    def _get_call_stack(self) -> str:
        """Получение стека вызовов для отладки"""
        import traceback
        stack = traceback.extract_stack()
        # Берем только релевантные вызовы
        relevant_calls = [
            f"{frame.filename}:{frame.lineno} in {frame.name}"
            for frame in stack[-8:-1]  # Последние 8 вызовов, исключая текущий
            if 'site-packages' not in frame.filename  # Исключаем библиотеки
        ]
        return " -> ".join(relevant_calls)

    async def _determine_image_status(
        self,
        image: Image,
    ) -> tuple[ImageUploadStatus, Optional[datetime]]:
        """
        Определяет текущий статус изображения на S3 и дату последнего изменения
        
        Args:
            image: Объект изображения
            
        Returns:
            tuple: (upload_status, server_uploaded_at)
        """
        metadata = await self.s3_service.get_metadata(image.id)
        
        last_modified = None
        server_uploaded_at = None
        upload_status = ImageUploadStatus.MISSING
        
        if metadata:
            upload_status = ImageUploadStatus.UPLOADED
            last_modified = metadata.get('last_modified')
            
            # Обновляем server_modified_at если есть более свежая дата
            if last_modified and isinstance(last_modified, datetime):
                server_modified_at = datetime.fromisoformat(
                    str(image.server_modified_at).replace('Z', '+00:00')
                )
                if last_modified > server_modified_at:
                    server_uploaded_at = last_modified
                else:
                    server_uploaded_at = image.server_modified_at
            else:
                server_uploaded_at = image.server_modified_at
        else:
            server_uploaded_at = image.server_modified_at
        
        return upload_status, server_uploaded_at

    async def get_images_statuses_from_s3(
        self,
        images: List[Image],
        batch_size: int = 100,
    ) -> List[Image]:
        """
        Проверка статусов всех изображений с обработкой ошибок
        
        Args:
            conn: Соединение с БД
            images: Список изображений
            batch_size: Размер порции для прогресс-логирования
            max_consecutive_errors: Максимальное количество ошибок подряд до прерывания
        
        Returns:
            Dict со статистикой проверки
        """
        total_images = len(images)
        check_start_time = datetime.now()
        
        updated_images = []
        for idx, image in enumerate(images, 1):
            
            if idx % batch_size == 0:
                elapsed = (datetime.now() - check_start_time).total_seconds()
                self._log_progress(idx, total_images, elapsed)
            
            updated_image = image.model_copy()
            updated_image.upload_status, updated_image.server_uploaded_at = \
                await self._determine_image_status(image)
        
            updated_images.append(updated_image)
        elapsed = (datetime.now() - check_start_time).total_seconds()
        logger.info(
            f"Проверка статусов завершена: "
            f"всего={total_images}, "
            f"время={elapsed:.2f}с"
        )
        
        return updated_images

    def _get_date_range(self, images: List[Dict[str, Any]]) -> str:
        """Получение диапазона дат из списка изображений"""
        if not images:
            return "нет данных"
        
        dates = []
        for img in images:
            date_str = img.get('server_modified_at')
            if date_str:
                try:
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    dates.append(date)
                except Exception as e:
                    logger.error(f"  Ошибка при преобразовании метки времени: {e}")
        
        if not dates:
            return "нет дат"
        
        min_date = min(dates).strftime('%Y-%m-%d %H:%M:%S')
        max_date = max(dates).strftime('%Y-%m-%d %H:%M:%S')
        
        if min_date == max_date:
            return min_date
        return f"{min_date} - {max_date}"


async def check_server_availability(
    base_url: str,
    max_retries: int = 3,
    retry_delay: int = 2
) -> bool:
    """Проверка доступности сервера перед началом загрузки"""
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{base_url}/image/all",
                    params={"limit": 1},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    logger.debug(f"  Сервер {base_url} доступен")
                    return True
        
        except httpx.ConnectError:
            logger.warning(f"  Сервер {base_url} недоступен (попытка {attempt + 1}/{max_retries})")
        except Exception as e:
            logger.warning(f"  Ошибка при проверке сервера: {e} (попытка {attempt + 1}/{max_retries})")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
    
    logger.error(f"  Сервер {base_url} недоступен после {max_retries} попыток")
    return False


async def fetch_images_background(
    base_url: str,
    upload_status: Optional[ImageUploadStatus] = None,
    modified_since: Optional[datetime] = None,
    uploaded_since: Optional[datetime] = None,
    batch_size: int = 100,
    timeout_seconds: int = 30,
    limit: Optional[int] = None
) -> List[Image]:
    """
    Фоновая задача для получения изображений порциями
    
    Args:
        base_url: Базовый URL API
        upload_status: Фильтр по статусу загрузки (MISSING, UPLOADED, UNKNOWN)
        modified_since: Изменены, начиная с этой даты
        uploaded_since: Загружены, начиная с этой даты
        batch_size: Размер порции
        timeout_seconds: Таймаут ожидания следующей порции в секундах
        limit: Максимальное количество изображений для загрузки (None - без лимита)
    """
    is_available = await check_server_availability(base_url)
    if not is_available:
        logger.error(f"  Невозможно запустить загрузку: сервер {base_url} недоступен")
        return []
    
    async for conn in get_db_connection():
        try:
            fetcher = ImageBackgroundFetcher(
                base_url=base_url, 
                batch_size=batch_size,
                s3_service=await get_s3_objects_service()
            )
            fetcher.timeout_seconds = timeout_seconds

            images = await fetcher.fetch_all_images(
                conn=conn,
                upload_status=upload_status,
                modified_since=modified_since,
                uploaded_since=uploaded_since,
                limit=limit
            )

            updated_images = []
            if images:
                updated_images = await fetcher.get_images_statuses_from_s3(images)
            else:
                logger.warning("    Для заданного фильтра не найдено изображений в базе данных")
            
            for image in updated_images:
                await image_repo.update_upload_status(
                    conn,
                    image_id=image.id,
                    upload_status=image.upload_status,
                    server_uploaded_at=image.server_uploaded_at,
                )
        
        except Exception as e:
            logger.error(f"  Ошибка в фоновой задаче: {e}", exc_info=True)
    
    return images

