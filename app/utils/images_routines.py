import asyncio
import logging
import httpx

from datetime import datetime
from fastapi import HTTPException
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.config import settings
from app.database import get_db_connection
from app.models.image import Image, ImageUploadStatus
from app.services.s3_objects_service import get_s3_service

from app.repositories.image import image_repo
from app.utils.async_wrapper import AsyncWrapper


logging.getLogger('httpcore').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class ImageBackgroundFetcher:
    
    def __init__(self, base_url: str, batch_size: int = 20, s3_service=None):
        self.base_url = base_url.rstrip('/')
        self.batch_size = batch_size
        self.timeout_seconds = 30  # Таймаут ожидания следующей порции (секунд)
        self.request_timeout = httpx.Timeout(10.0, connect=5.0)  # Таймаут для HTTP запроса
        self.s3_service = s3_service
    
    def _log_section_header(self, title: str, **kwargs):
        """Логирование заголовка секции"""
        logger.debug("=" * 80)
        logger.debug(f"  {title}")
        for key, value in kwargs.items():
            logger.debug(f"   {key}: {value}")
        logger.debug("=" * 80)
    
    def _log_batch_success(self, batch_number: int, items_count: int, total_count: int, 
                          date_range: str, duration: float, cursor: Optional[str]):
        """Логирование успешной загрузки порции"""
        logger.debug(f"  [ПОРЦИЯ {batch_number}] УСПЕШНО ЗАГРУЖЕНО")
        logger.debug(f"     Изображений в порции: {items_count}")
        logger.debug(f"     Всего загружено: {total_count}")
        logger.debug(f"     Диапазон дат: {date_range}")
        logger.debug(f"      Время запроса: {duration:.2f} сек")
        logger.debug(f"     Курсор: {cursor[:30] if cursor else 'None'}")
    
    def _log_progress(self, current: int, total: int, elapsed: float):
        """Логирование прогресса"""
        progress_percent = current * 100 // total
        logger.debug(f"     Прогресс проверки: {current}/{total} изображений "
                   f"({progress_percent}%) | Время: {elapsed:.1f} сек")
    
    def _log_batch_check_results(self, batch_number: int, batch_size: int, 
                                uploaded: int, missing: int, duration: float,
                                processed: int, total: int):
        """Логирование результатов проверки порции"""
        logger.debug(f"  [ПОРЦИЯ {batch_number}] ПРОВЕРКА ЗАВЕРШЕНА")
        logger.debug(f"     Результаты порции:")
        logger.debug(f"   - Проверено изображений: {batch_size}")
        logger.debug(f"     Загружено в S3 (UPLOADED): {uploaded}")
        logger.debug(f"     Отсутствует в S3 (MISSING): {missing}")
        logger.debug(f"      Время обработки порции: {duration:.2f} сек")
        logger.debug(f"     Общий прогресс: {processed}/{total} "
                   f"({processed * 100 // total}%)")
    
    def _log_final_stats(self, total_images: int, total_batches: int, 
                        total_duration: float, batch_size: int):
        """Логирование финальной статистики загрузки"""
        logger.debug("=" * 80)
        logger.debug(f"  ЗАВЕРШЕНИЕ ЗАГРУЗКИ ИЗОБРАЖЕНИЙ")
        logger.debug(f"  ИТОГОВАЯ СТАТИСТИКА:")
        logger.debug(f"     Всего загружено: {total_images} изображений")
        logger.debug(f"     Всего порций: {total_batches}")
        logger.debug(f"      Общее время: {total_duration:.2f} сек")
        logger.debug(f"     Средняя скорость: {total_images / total_duration:.2f} изображений/сек")
        logger.debug(f"     Целевой размер порции: {batch_size}")
        logger.debug("=" * 80)
    
    def _log_check_final_stats(self, total_checked: int, total_batches: int,
                              uploaded: int, missing: int, duration: float,
                              errors: int = 0):
        """Логирование финальной статистики проверки"""
        logger.debug("=" * 80)
        logger.debug(f"  ЗАВЕРШЕНИЕ ПРОВЕРКИ СТАТУСОВ")
        logger.debug(f"  ИТОГОВАЯ СТАТИСТИКА ПРОВЕРКИ:")
        logger.debug(f"     Всего проверено: {total_checked} изображений")
        logger.debug(f"     Всего порций: {total_batches}")
        logger.debug(f"     Загружено в S3 (UPLOADED): {uploaded}")
        logger.debug(f"     Отсутствует в S3 (MISSING): {missing}")
        logger.debug(f"      Общее время проверки: {duration:.2f} сек")
        logger.debug(f"     Средняя скорость: {total_checked / duration:.2f} изображений/сек")
        
        if errors > 0:
            logger.warning(f"     Всего ошибок в процессе: {errors}")
        
        logger.debug("=" * 80)
    
    def _log_error(self, error_type: str, batch_number: int, error: Exception, 
                  loaded_count: int = None, status_code: int = None):
        """Логирование ошибок"""
        logger.error(f"  [ПОРЦИЯ {batch_number}] {error_type}")
        
        if status_code:
            logger.error(f"   Статус: {status_code}")
        
        logger.error(f"   Ошибка: {error}")
        
        if loaded_count is not None:
            logger.error(f"   Загружено только {loaded_count} изображений из {batch_number} порций")
        
        if error_type == "НЕПРЕДВИДЕННАЯ ОШИБКА":
            logger.error(f"   Ошибка: {error}", exc_info=True)

    async def fetch_images_batch(
        self,
        client: httpx.AsyncClient,
        modified_since: datetime,
        offset: int = 0,
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """Получение одной порции изображений"""
        params = {
            "modified_since": modified_since.isoformat(),
            "limit": self.batch_size,
            "offset": offset,
            "sort_by": "modified_at",
            "sort_order": sort_order
        }
        
        response = await client.get(
            f"{self.base_url}/image/all",
            params=params,
            timeout=self.request_timeout
        )
        response.raise_for_status()
        return response.json()
    
    async def fetch_all_images_streaming(
        self,
        conn,
        upload_status: Optional[ImageUploadStatus] = None,
        modified_since: Optional[datetime] = None,
        uploaded_since: Optional[datetime] = None,
        callback: Optional[callable] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Получение всех изображений порциями с контролем таймаута"""
        
        if modified_since is None:
            modified_since = datetime(2020, 1, 1)
        
        if uploaded_since is None:
            uploaded_since = datetime(2020, 1, 1)
        
        # Логируем начало загрузки
        self._log_section_header(
            "НАЧАЛО ЗАГРУЗКИ ИЗОБРАЖЕНИЙ",
            **{
                "  Дата изменения": modified_since.isoformat(),
                "  Дата загрузки": uploaded_since.isoformat(),
                "  Размер порции": self.batch_size,
                "   Таймаут ожидания": f"{self.timeout_seconds} сек",
                "  URL сервера": self.base_url
            }
        )
        
        images = []
        cursor = None
        has_more = True
        last_successful_fetch = datetime.now()
        batch_number = 0
        start_time = datetime.now()
        
        async with httpx.AsyncClient() as client:
            while has_more:
                batch_number += 1
                batch_start_time = datetime.now()
                
                try:
                    # Проверка таймаута
                    time_since_last_fetch = (datetime.now() - last_successful_fetch).total_seconds()
                    if time_since_last_fetch > self.timeout_seconds:
                        logger.warning(f"  Таймаут: за последние {self.timeout_seconds} секунд не получено изображений")
                        break
                    
                    # Формируем параметры запроса
                    params = {
                        "upload_status": upload_status.value if upload_status else None,
                        "modified_since": modified_since.isoformat(),
                        "uploaded_since": uploaded_since.isoformat(),
                    }
                    if limit:
                        limit = min(limit, self.batch_size)
                        params["limit"] = str(limit)
                    if cursor:
                        params["cursor"] = cursor
                    
                    response = await client.get(
                        f"{self.base_url}/image/all",
                        params=params,
                        timeout=self.request_timeout
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    items = data.get('items', [])
                    cursor = data.get('next_cursor')
                    has_more = cursor is not None and len(items) == self.batch_size
                    
                    batch_duration = (datetime.now() - batch_start_time).total_seconds()
                    
                    if items:
                        last_successful_fetch = datetime.now()
                        images.extend(items)
                        
                        date_range = self._get_date_range(items)
                        
                        self._log_batch_success(
                            batch_number, len(items), len(images),
                            date_range, batch_duration, cursor
                        )
                        
                        elapsed = (datetime.now() - start_time).total_seconds()
                        logger.debug(f"     Прогресс: {len(images)} изображений за {elapsed:.1f} сек")
                        
                        if callback:
                            await callback(items, len(images), cursor)
                        
                        if limit and len(images) >= limit:
                            logger.debug(f"  Достигнут лимит загрузки: {limit} изображений")
                            break
                    
                    else:
                        logger.debug(f"  [ПОРЦИЯ {batch_number}] Нет изображений в этой порции")
                        break
                    
                    await asyncio.sleep(0.5)
                    
                except httpx.TimeoutException as e:
                    self._log_error("ТАЙМАУТ HTTP ЗАПРОСА", batch_number, e, len(images))
                    break
                except httpx.HTTPStatusError as e:
                    self._log_error("HTTP ОШИБКА", batch_number, e, status_code=e.response.status_code)
                    break
                except Exception as e:
                    self._log_error("НЕПРЕДВИДЕННАЯ ОШИБКА", batch_number, e, len(images))
                    break
        
        # Финальная статистика загрузки
        total_duration = (datetime.now() - start_time).total_seconds()
        self._log_final_stats(len(images), batch_number, total_duration, self.batch_size)
        
        # Проверка статусов изображений
        if images:
            await self._check_images_statuses(conn, images, start_time)
        else:
            logger.warning("  Нет изображений для проверки статусов")
        
        return images

    async def _check_images_statuses(self, conn, images: List[Dict[str, Any]], start_time: datetime):
        """Проверка статусов изображений (вынесенная логика)"""
        
        self._log_section_header(
            "НАЧАЛО ПРОВЕРКИ СТАТУСОВ ИЗОБРАЖЕНИЙ",
            **{
                "Всего проверяемых изображений": len(images),
                "Размер порции для проверки": self.batch_size,
                "Таймаут ожидания": f"{self.timeout_seconds} сек"
            }
        )
        
        check_start_time = datetime.now()
        missing_count = 0
        uploaded_count = 0
        last_successful_check = datetime.now()
        consecutive_errors = 0
        batch_number = 0
        
        for i in range(0, len(images), self.batch_size):
            batch_number += 1
            batch_start_time = datetime.now()
            batch_images = images[i:i + self.batch_size]
            
            try:
                time_since_last_check = (datetime.now() - last_successful_check).total_seconds()
                if time_since_last_check > self.timeout_seconds:
                    break
                
                batch_missing_count = 0
                batch_uploaded_count = 0
                
                for idx, image in enumerate(batch_images, 1):
                    global_idx = i + idx
                    
                    try:
                        if global_idx % self.batch_size == 0:
                            elapsed = (datetime.now() - check_start_time).total_seconds()
                            self._log_progress(global_idx, len(images), elapsed)
                        
                        if image.get('upload_status') in (
                            ImageUploadStatus.MISSING,
                            ImageUploadStatus.UNKNOWN
                        ):
                            last_modified = None
                            exists = await self.s3_service.check_exists(image['id'])
                            metadata = await self.s3_service.get_metadata(image['id'])
                            if metadata:
                                last_modified = metadata.get('last_modified')
                            if last_modified and isinstance(last_modified, datetime):
                                server_modified_at = datetime.fromisoformat(image['server_modified_at'].replace('Z', '+00:00'))
                                if last_modified > server_modified_at:
                                    server_modified_at = last_modified
                                else:
                                    server_modified_at = datetime.fromisoformat(image['server_modified_at'].replace('Z', '+00:00'))
                            server_uploaded_at = last_modified
                            upload_status = ImageUploadStatus.UPLOADED if exists else ImageUploadStatus.MISSING
                            
                            await update_image_upload_status(
                                conn,
                                image_id=image['id'],
                                upload_status=upload_status,
                                server_uploaded_at=server_uploaded_at,
                                force=True
                            )
                            
                            if upload_status == ImageUploadStatus.UPLOADED:
                                uploaded_count += 1
                                batch_uploaded_count += 1
                            else:
                                missing_count += 1
                                batch_missing_count += 1
                            
                            consecutive_errors = 0
                            last_successful_check = datetime.now()
                            
                    except Exception as e:
                        consecutive_errors += 1
                        logger.error(f"     [ПОРЦИЯ {batch_number}] Ошибка при проверке изображения {image.get('id', 'unknown')}: {e}")
                        
                        if consecutive_errors >= 5:
                            logger.error(f"     Слишком много ошибок подряд ({consecutive_errors}), прерываем проверку")
                            break
                        
                        continue
                
                batch_duration = (datetime.now() - batch_start_time).total_seconds()
                
                self._log_batch_check_results(
                    batch_number, len(batch_images), batch_uploaded_count,
                    batch_missing_count, batch_duration, i + len(batch_images), len(images)
                )
                
            except Exception as e:
                logger.error(f"  [ПОРЦИЯ {batch_number}] КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
                break
        
        check_duration = (datetime.now() - check_start_time).total_seconds()
        
        self._log_check_final_stats(
            len(images), batch_number, uploaded_count, 
            missing_count, check_duration, consecutive_errors
        )

    def _get_date_range(self, images: List[Dict[str, Any]]) -> str:
        """Получение диапазона дат из списка изображений"""
        if not images:
            return "нет данных"
        
        dates = []
        for img in images:
            # Предполагаем, что у изображения есть поле 'created_at' или 'modified_at'
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
                    logger.info(f"  Сервер {base_url} доступен")
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
) -> List[Dict[str, Any]]:
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
                s3_service=await get_s3_service()
            )
            fetcher.timeout_seconds = timeout_seconds

            images = await fetcher.fetch_all_images_streaming(
                conn=conn,
                upload_status=upload_status,
                modified_since=modified_since,
                uploaded_since=uploaded_since,
                limit=limit
            )
        except Exception as e:
            logger.error(f"  Ошибка в фоновой задаче: {e}", exc_info=True)
    
    return images


async def update_image_upload_status(
    conn,
    image_id: UUID,
    upload_status: ImageUploadStatus,
    server_uploaded_at: Optional[datetime] = None,
    force: bool = False,
) -> Image:
    """
    Обновляет только статус загрузки изображения
    
    Args:
        conn: Соединение с БД
        image_id: ID изображения
        upload_status: Новый статус загрузки
        server_uploaded_at: Новая дата загрузки на сервер
        force: Принудительное обновление
    
    Returns:
        Обновленная запись изображения
    """
    try:
        async with conn.transaction():
            # Получаем существующее изображение
            existing_image = await image_repo.get_by_id(conn, image_id)
            if not existing_image:
                raise ValueError(f"Image with id {image_id} not found")
            
            # Создаем объект Image с обновленным статусом
            updated_image = Image(
                id=existing_image.id,
                plant_id=existing_image.plant_id,
                original_file_name=existing_image.original_file_name,
                image_type=existing_image.image_type,
                metadata=existing_image.metadata,
                is_deleted=existing_image.is_deleted,
                server_modified_at=existing_image.server_modified_at,
                upload_status=upload_status,
                server_uploaded_at=server_uploaded_at or existing_image.server_uploaded_at
            )
            
            result = await image_repo.save(conn, updated_image, force=force)
            
            return result
    
    except ValueError as e:
        logger.warning(f"Image not found: {image_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update upload status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))