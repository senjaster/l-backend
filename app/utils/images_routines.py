import asyncio
import logging
import httpx

from datetime import datetime
from fastapi import HTTPException
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.models.image import Image, ImageUploadStatus
from app.services.s3_service import s3_service
from app.repositories.image import ImageRepository


logger = logging.getLogger(__name__)
image_repo = ImageRepository()


class ImageBackgroundFetcher:
    def __init__(self, base_url: str, batch_size: int = 20):
        self.base_url = base_url.rstrip('/')
        self.batch_size = batch_size
        self.timeout_seconds = 30  # Таймаут ожидания следующей порции (секунд)
        self.request_timeout = httpx.Timeout(10.0, connect=5.0)  # Таймаут для HTTP запроса
    
    async def fetch_images_batch(
        self,
        client: httpx.AsyncClient,
        modified_since: datetime,
        offset: int = 0,
        sort_order: str = "asc"  # asc - по возрастанию даты, desc - по убыванию
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
        modified_since: Optional[datetime] = None,
        callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение всех изображений порциями с контролем таймаута
        
        Args:
            modified_since: Начальная дата для фильтрации
            callback: Функция обратного вызова для каждой порции
            
        Returns:
            Список всех полученных изображений
        """
        if modified_since is None:
            modified_since = datetime(2020, 1, 1)

        # Логируем начало загрузки
        logger.info("=" * 80)
        logger.info(f"🚀 НАЧАЛО ЗАГРУЗКИ ИЗОБРАЖЕНИЙ")
        logger.info(f"📅 Дата фильтрации: {modified_since.isoformat()}")
        logger.info(f"📦 Размер порции: {self.batch_size}")
        logger.info(f"⏱️  Таймаут ожидания: {self.timeout_seconds} сек")
        logger.info(f"🌐 URL сервера: {self.base_url}")
        logger.info("=" * 80)
        
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
                        logger.warning(f"⏰ Таймаут: за последние {self.timeout_seconds} секунд не получено изображений")
                        break
                    
                    # Формируем параметры запроса
                    params = {
                        "modified_since": modified_since.isoformat(),
                        "limit": self.batch_size
                    }
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
                    cursor = data.get('next_cursor')  # Получаем курсор для следующей страницы
                    has_more = cursor is not None and len(items) == self.batch_size

                    # Время выполнения запроса
                    batch_duration = (datetime.now() - batch_start_time).total_seconds()
                    
                    if items:
                        last_successful_fetch = datetime.now()
                        images.extend(items)
                        
                        date_range = self._get_date_range(items)
                        
                        # Логируем успешную загрузку порции
                        logger.info(f"✅ [ПОРЦИЯ {batch_number}] УСПЕШНО ЗАГРУЖЕНО")
                        logger.info(f"   📸 Изображений в порции: {len(items)}")
                        logger.info(f"   📊 Всего загружено: {len(images)}")
                        logger.info(f"   📅 Диапазон дат: {date_range}")
                        logger.info(f"   ⏱️  Время запроса: {batch_duration:.2f} сек")
                        logger.info(f"   🔄 Курсор: {cursor[:30] if cursor else 'None'}")
                        logger.info(f"   📈 Прогресс: {len(images)} изображений за "
                                f"{(datetime.now() - start_time).total_seconds():.1f} сек")
                            
                        if callback:
                            await callback(items, len(images), cursor)
                    else:
                        logger.info(f"📭 [ПОРЦИЯ {batch_number}] Нет изображений в этой порции")
                        break
                    
                    await asyncio.sleep(0.5)
                    
                except httpx.TimeoutException as e:
                    logger.error(f"❌ [ПОРЦИЯ {batch_number}] ТАЙМАУТ HTTP ЗАПРОСА")
                    logger.error(f"   Ошибка: {e}")
                    logger.error(f"   Загружено только {len(images)} изображений из {batch_number} порций")
                    break
                except httpx.HTTPStatusError as e:
                    logger.error(f"❌ [ПОРЦИЯ {batch_number}] HTTP ОШИБКА")
                    logger.error(f"   Статус: {e.response.status_code}")
                    logger.error(f"   Ошибка: {e}")
                    break
                except Exception as e:
                    logger.error(f"❌ [ПОРЦИЯ {batch_number}] НЕПРЕДВИДЕННАЯ ОШИБКА")
                    logger.error(f"   Ошибка: {e}", exc_info=True)
                    break
        
        # Общая статистика загрузки
        total_duration = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 80)
        logger.info(f"🏁 ЗАВЕРШЕНИЕ ЗАГРУЗКИ ИЗОБРАЖЕНИЙ")
        logger.info(f"📊 ИТОГОВАЯ СТАТИСТИКА:")
        logger.info(f"   ✅ Всего загружено: {len(images)} изображений")
        logger.info(f"   📦 Всего порций: {batch_number}")
        logger.info(f"   ⏱️  Общее время: {total_duration:.2f} сек")
        logger.info(f"   📈 Средняя скорость: {len(images) / total_duration:.2f} изображений/сек")
        logger.info(f"   🎯 Целевой размер порции: {self.batch_size}")
        logger.info("=" * 80)
        
        # Начинаем проверку статусов изображений
        if images:
            logger.info("=" * 80)
            logger.info(f"🔍 НАЧАЛО ПРОВЕРКИ СТАТУСОВ ИЗОБРАЖЕНИЙ")
            logger.info(f"   Всего проверяемых изображений: {len(images)}")
            logger.info(f"   Размер порции для проверки: {self.batch_size}")
            logger.info(f"   Таймаут ожидания: {self.timeout_seconds} сек")
            logger.info("=" * 80)
            
            check_start_time = datetime.now()
            missing_count = 0
            uploaded_count = 0
            processed_count = 0
            last_successful_check = datetime.now()
            consecutive_errors = 0
            batch_number = 0
            
            # Разбиваем изображения на порции для проверки
            for i in range(0, len(images), self.batch_size):
                batch_number += 1
                batch_start_time = datetime.now()
                batch_images = images[i:i + self.batch_size]
                
                try:
                    # Проверяем таймаут - если долго не было успешных проверок
                    time_since_last_check = (datetime.now() - last_successful_check).total_seconds()
                    if time_since_last_check > self.timeout_seconds:
                        break
                    
                    batch_missing_count = 0
                    batch_uploaded_count = 0
                    
                    # Проверяем каждое изображение в порции
                    for idx, image in enumerate(batch_images, 1):
                        global_idx = i + idx
                        
                        try:
                            # Логируем прогресс проверки каждые self.batch_size изображений
                            if global_idx % self.batch_size == 0:
                                progress_percent = global_idx * self.batch_size // len(images)
                                elapsed = (datetime.now() - check_start_time).total_seconds()
                                logger.info(f"   🔄 Прогресс проверки: {global_idx}/{len(images)} изображений "
                                        f"({progress_percent}%) | Время: {elapsed:.1f} сек")
                            
                            if image.get('upload_status') == ImageUploadStatus.UNKNOWN:
                                # Проверяем существование в S3
                                check_item_start = datetime.now()
                                exists = s3_service.check_exists(image['id'])
                                check_item_duration = (datetime.now() - check_item_start).total_seconds()
                                
                                upload_status = ImageUploadStatus.UPLOADED if exists else ImageUploadStatus.MISSING
                                
                                # Обновляем статус в БД
                                update_start = datetime.now()
                                await update_image_upload_status(
                                    conn,
                                    image_id=image['id'],
                                    upload_status=upload_status,
                                    force=True
                                )
                                update_duration = (datetime.now() - update_start).total_seconds()
                                
                                if upload_status == ImageUploadStatus.UPLOADED:
                                    uploaded_count += 1
                                    batch_uploaded_count += 1
                                    logger.debug(f"   📸 Изображение {image['id']}: статус обновлен на UPLOADED "
                                            f"(S3 check: {check_item_duration:.2f}с, DB update: {update_duration:.2f}с)")
                                else:
                                    missing_count += 1
                                    batch_missing_count += 1
                                    logger.debug(f"   ⚠️ Изображение {image['id']}: не найдено в S3 "
                                            f"(проверка заняла {check_item_duration:.2f}с)")
                                
                                # Сбрасываем счетчик ошибок при успешной операции
                                consecutive_errors = 0
                                last_successful_check = datetime.now()
                                
                        except Exception as e:
                            consecutive_errors += 1
                            logger.error(f"   ❌ [ПОРЦИЯ {batch_number}] Ошибка при проверке изображения {image.get('id', 'unknown')}: {e}")
                            
                            # Если слишком много ошибок подряд, прерываем проверку
                            if consecutive_errors >= 5:
                                logger.error(f"   🛑 Слишком много ошибок подряд ({consecutive_errors}), прерываем проверку")
                                break
                            
                            continue
                    
                    # Время выполнения порции
                    batch_duration = (datetime.now() - batch_start_time).total_seconds()
                    
                    # Логируем результаты порции
                    logger.info(f"✅ [ПОРЦИЯ {batch_number}] ПРОВЕРКА ЗАВЕРШЕНА")
                    logger.info(f"   📊 Результаты порции:")
                    logger.info(f"   - Проверено изображений: {len(batch_images)}")
                    logger.info(f"   💾 Загружено в S3 (UPLOADED): {batch_uploaded_count}")
                    logger.info(f"   ❌ Отсутствует в S3 (MISSING): {batch_missing_count}")
                    logger.info(f"   ⏱️  Время обработки порции: {batch_duration:.2f} сек")
                    logger.info(f"   📈 Общий прогресс: {i + len(batch_images)}/{len(images)} "
                            f"({(i + len(batch_images)) * 100 // len(images)}%)")
                    
                except Exception as e:
                    logger.error(f"❌ [ПОРЦИЯ {batch_number}] КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
                    break
            
            # Финальная статистика проверки
            check_duration = (datetime.now() - check_start_time).total_seconds()
            
            logger.info("=" * 80)
            logger.info(f"🏁 ЗАВЕРШЕНИЕ ПРОВЕРКИ СТАТУСОВ")
            logger.info(f"📊 ИТОГОВАЯ СТАТИСТИКА ПРОВЕРКИ:")
            logger.info(f"   ✅ Всего проверено: {processed_count if processed_count else len(images)} изображений")
            logger.info(f"   📦 Всего порций: {batch_number}")
            logger.info(f"   💾 Загружено в S3 (UPLOADED): {uploaded_count}")
            logger.info(f"   ❌ Отсутствует в S3 (MISSING): {missing_count}")
            logger.info(f"   ⏱️  Общее время проверки: {check_duration:.2f} сек")
            logger.info(f"   📈 Средняя скорость: {len(images) / check_duration:.2f} изображений/сек")
            
            # Проверка на наличие ошибок
            if consecutive_errors > 0:
                logger.warning(f"   ⚠️ Всего ошибок в процессе: {consecutive_errors}")
            
            logger.info("=" * 80)
            
        else:
            logger.warning("⚠️ Нет изображений для проверки статусов")
    
        return images

    
    def _get_date_range(self, images: List[Dict[str, Any]]) -> str:
        """Получение диапазона дат из списка изображений"""
        if not images:
            return "нет данных"
        
        dates = []
        for img in images:
            # Предполагаем, что у изображения есть поле 'created_at' или 'modified_at'
            date_str = img.get('modified_at') or img.get('created_at') or img.get('date')
            if date_str:
                try:
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    dates.append(date)
                except Exception as e:
                    logger.error(f"❌ Ошибка при преобразовании метки времени: {e}")
        
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
                    params={"limit": 1},  # Запрашиваем только 1 изображение
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Сервер {base_url} доступен")
                    return True
        
        except httpx.ConnectError:
            logger.warning(f"⚠️ Сервер {base_url} недоступен (попытка {attempt + 1}/{max_retries})")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при проверке сервера: {e} (попытка {attempt + 1}/{max_retries})")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
    
    logger.error(f"❌ Сервер {base_url} недоступен после {max_retries} попыток")
    return False


async def fetch_images_background(
    conn,
    base_url: str,
    modified_since: Optional[datetime] = None,
    batch_size: int = 20,
    timeout_seconds: int = 30
) -> List[Dict[str, Any]]:
    """
    Фоновая задача для получения изображений порциями
    
    Args:
        base_url: Базовый URL API
        modified_since: Начальная дата фильтрации
        batch_size: Размер порции
        timeout_seconds: Таймаут ожидания следующей порции в секундах
    """
    is_available = await check_server_availability(base_url)
    if not is_available:
        logger.error(f"🛑 Невозможно запустить загрузку: сервер {base_url} недоступен")
        return []
    
    fetcher = ImageBackgroundFetcher(base_url, batch_size)
    fetcher.timeout_seconds = timeout_seconds
    
    # Можно добавить callback для дополнительной обработки
    async def on_batch(images, offset, total_so_far):
        # Здесь можно добавить дополнительную логику для каждой порции
        # Например, сохранение в БД или отправку уведомлений
        logger.debug(f"Callback: обработано {len(images)} изображений, всего: {total_so_far}")
    
    # Запускаем загрузку
    result = await fetcher.fetch_all_images_streaming(conn, modified_since, on_batch)
    return result


async def update_image_upload_status(
    conn,
    image_id: UUID,
    upload_status: ImageUploadStatus,
    force: bool = False,
) -> Image:
    """
    Обновляет только статус загрузки изображения
    
    Args:
        conn: Соединение с БД
        image_id: ID изображения
        upload_status: Новый статус загрузки
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
            )
            
            result = await image_repo.save(conn, updated_image, force=force)
            
            return result
    
    except ValueError as e:
        logger.warning(f"Image not found: {image_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update upload status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))