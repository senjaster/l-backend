"""S3 service for generating presigned URLs"""

import logging
from typing import Optional, Tuple, List, Dict
from uuid import UUID
from datetime import datetime, timedelta, timezone

from botocore.client import Config
from botocore.exceptions import ClientError, NoCredentialsError

import asyncio
from aiobotocore.session import get_session

from app.config import settings


logging.getLogger('aiobotocore').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class AsyncS3Service:
    """Асинхронный сервис для работы с S3"""
    
    def __init__(self):
        """Инициализация асинхронного S3 клиента"""
        self._session = None
        self._client = None
        self._lock = asyncio.Lock()
        self._initialized = False
        
        self.region_name = settings.s3_region
        self.access_key_id = settings.s3_access_key_id
        self.secret_access_key = settings.s3_secret_access_key
        self.bucket_name = settings.s3_bucket_name
        self.expiration = settings.s3_presigned_url_expiration
        self.endpoint_host = settings.s3_endpoint_host
        self.use_virtual_hosted_style = settings.s3_use_virtual_hosted_style
        
        # Настройки для пула соединений
        self.max_pool_connections = 100  # Максимум соединений в пуле
        self.connection_timeout = 30
        self.read_timeout = 30
        
    async def _get_client(self):
        """Получение или создание клиента (ленивая инициализация)"""
        if not self._initialized:
            await self.initialize()
        return self._client
    
    async def initialize(self):
        """Инициализация сессии и клиента"""
        async with self._lock:
            if self._initialized:
                return
            
            try:
                # Проверка наличия учетных данных
                if not self.access_key_id or not self.secret_access_key:
                    raise NoCredentialsError("AWS credentials not found")
                
                # Создаем сессию
                self._session = get_session()
                
                # Настройка конфигурации
                config_kwargs = {
                    "signature_version": 's3v4',
                    "s3": {
                        'addressing_style': 'virtual' if self.use_virtual_hosted_style else 'path'
                    },
                    "max_pool_connections": self.max_pool_connections,
                    "connect_timeout": self.connection_timeout,
                    "read_timeout": self.read_timeout,
                    "retries": {
                        'max_attempts': 3,
                        'mode': 'adaptive'
                    }
                }
                
                # Добавляем регион
                if self.region_name:
                    config_kwargs["region_name"] = self.region_name
                
                boto_config = Config(**config_kwargs)
                
                # Параметры для создания клиента
                client_kwargs = {
                    "config": boto_config,
                    "aws_access_key_id": self.access_key_id,
                    "aws_secret_access_key": self.secret_access_key,
                }
                
                # Добавляем custom endpoint URL если указан
                if self.endpoint_host:
                    endpoint_url = f"https://{self.endpoint_host}"
                    client_kwargs["endpoint_url"] = endpoint_url
                
                # Создаем клиент
                self._client = await self._session.create_client(
                    "s3",
                    **client_kwargs
                ).__aenter__()
                
                self._initialized = True
                logger.info("✅ Async S3 service initialized successfully")
                
            except NoCredentialsError as e:
                logger.error(f"AWS credentials not found: {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Async S3 service: {e}")
                raise
    
    async def close(self):
        """Закрытие сессии и клиента"""
        async with self._lock:
            if self._client:
                await self._client.close()
                self._client = None
            if self._session:
                self._session = None
            self._initialized = False
            logger.info("✅ Async S3 service closed")
    
    async def __aenter__(self):
        """Поддержка async context manager"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекста"""
        await self.close()
    
    async def generate_presigned_url(
        self, 
        image_id: UUID, 
        operation: str = "get_object"
    ) -> Optional[Tuple[str, datetime]]:
        """
        Асинхронная генерация presigned URL для доступа к объекту в S3.
        
        Args:
            image_id: UUID изображения (используется как ключ в S3)
            operation: S3 операция (по умолчанию: 'get_object' для скачивания)
        
        Returns:
            Tuple (presigned URL, время истечения) или None при ошибке
        """
        try:
            client = await self._get_client()
            
            # Используем image_id как ключ
            object_key = f"{image_id}.jpg"
            
            # Вычисляем время истечения
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.expiration)
            
            # Генерируем presigned URL
            presigned_url = await client.generate_presigned_url(
                operation,
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=self.expiration,
            )
            
            return presigned_url, expires_at
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL for image {image_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL for image {image_id}: {e}")
            return None
    
    async def generate_upload_presigned_url(
        self, 
        image_id: UUID
    ) -> Optional[Tuple[str, datetime]]:
        """
        Асинхронная генерация presigned URL для загрузки изображения в S3.
        
        Args:
            image_id: UUID изображения (используется как ключ в S3)
        
        Returns:
            Tuple (presigned URL, время истечения) для PUT операции или None при ошибке
        """
        return await self.generate_presigned_url(image_id, operation="put_object")
    
    async def check_exists(self, image_id: UUID) -> bool:
        """
        Асинхронная проверка существования изображения в S3.
        
        Args:
            image_id: UUID изображения
        
        Returns:
            True если объект существует, False в противном случае
        """
        try:
            client = await self._get_client()
            object_key = f"{image_id}.jpg"
            
            # Используем head_object для проверки
            await client.head_object(
                Bucket=self.bucket_name, 
                Key=object_key
            )
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                return False
            # Логируем только реальные ошибки (не 404)
            logger.error(f"Error checking existence for image {image_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking existence for image {image_id}: {e}")
            return False
    
    async def check_exists_batch(
        self, 
        image_ids: List[UUID]
    ) -> Dict[UUID, bool]:
        """
        Асинхронная пакетная проверка существования нескольких изображений.
        
        Args:
            image_ids: Список UUID изображений
        
        Returns:
            Словарь {image_id: exists_flag}
        """
        if not image_ids:
            return {}
        
        # Создаем задачи для параллельной проверки
        tasks = [self.check_exists(image_id) for image_id in image_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Формируем результат
        result_dict = {}
        for image_id, result in zip(image_ids, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to check image {image_id}: {result}")
                result_dict[image_id] = False
            else:
                result_dict[image_id] = result
        
        logger.debug(f"Batch check completed: {sum(result_dict.values())}/{len(image_ids)} found")
        return result_dict
    
    async def head_object(self, image_id: UUID) -> Optional[Dict]:
        """
        Асинхронное получение метаданных объекта.
        
        Args:
            image_id: UUID изображения
        
        Returns:
            Словарь с метаданными или None при ошибке
        """
        try:
            client = await self._get_client()
            object_key = f"{image_id}.jpg"
            
            response = await client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            return {
                'content_length': response.get('ContentLength'),
                'content_type': response.get('ContentType'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') != '404':
                logger.error(f"Error getting head object for {image_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting head object for {image_id}: {e}")
            return None
    
    async def upload_file(
        self, 
        image_id: UUID, 
        file_data: bytes,
        content_type: str = "image/jpeg"
    ) -> bool:
        """
        Асинхронная загрузка файла в S3.
        
        Args:
            image_id: UUID изображения
            file_data: Бинарные данные файла
            content_type: MIME тип файла
        
        Returns:
            True при успешной загрузке, False при ошибке
        """
        try:
            client = await self._get_client()
            object_key = f"{image_id}.jpg"
            
            await client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_data,
                ContentType=content_type,
                Metadata={
                    'uploaded_at': datetime.now(timezone.utc).isoformat(),
                    'image_id': str(image_id)
                }
            )
            
            logger.info(f"Successfully uploaded image {image_id} to S3")
            return True
            
        except ClientError as e:
            logger.error(f"Error uploading image {image_id} to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading image {image_id}: {e}")
            return False
    
    async def delete_object(self, image_id: UUID) -> bool:
        """
        Асинхронное удаление объекта из S3.
        
        Args:
            image_id: UUID изображения
        
        Returns:
            True при успешном удалении, False при ошибке
        """
        try:
            client = await self._get_client()
            object_key = f"{image_id}.jpg"
            
            await client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            logger.info(f"Successfully deleted image {image_id} from S3")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting image {image_id} from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting image {image_id}: {e}")
            return False


# Создаем глобальный экземпляр сервиса
async_s3_service = AsyncS3Service()


# Функция для использования в FastAPI приложении
async def get_s3_service() -> AsyncS3Service:
    """Dependency для получения S3 сервиса"""
    return async_s3_service


# Функция для инициализации и закрытия при старте/остановке приложения
async def init_s3_service():
    """Инициализация S3 сервиса при старте приложения"""
    await async_s3_service.initialize()


async def close_s3_service():
    """Закрытие S3 сервиса при остановке приложения"""
    await async_s3_service.close()