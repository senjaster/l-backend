import asyncio
from typing import Optional, List, Dict, Tuple
from uuid import UUID
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError
import logging

from .s3_connection import S3ConnectionManager
from .s3_key_generator import S3KeyGenerator


logger = logging.getLogger(__name__)


class S3ObjectService:
    """Сервис для работы с объектами в S3"""
    
    def __init__(self, connection_manager: S3ConnectionManager):
        """
        Инициализация сервиса.
        
        Args:
            connection_manager: Менеджер подключения к S3
        """
        self._connection = connection_manager
        self._key_generator = S3KeyGenerator()
    
    def _get_object_key(self, image_id: UUID) -> str:
        """Генерация ключа объекта"""
        return self._key_generator.generate_image_key(image_id)
    
    async def generate_presigned_url(
        self, 
        image_id: UUID, 
        operation: str = "get_object"
    ) -> Optional[Tuple[str, datetime]]:
        """
        Генерация presigned URL для доступа к объекту.
        
        Args:
            image_id: UUID изображения
            operation: S3 операция ('get_object', 'put_object')
        
        Returns:
            Tuple (presigned URL, время истечения) или None при ошибке
        """
        try:
            client = await self._connection.get_s3_client()
            object_key = self._get_object_key(image_id)
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=self._connection.expiration
            )
            
            presigned_url = await client.generate_presigned_url(
                operation,
                Params={
                    "Bucket": self._connection.bucket_name,
                    "Key": object_key
                },
                ExpiresIn=self._connection.expiration,
            )
            
            return presigned_url, expires_at
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL for {image_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {e}")
            return None
    
    async def generate_upload_presigned_url(self, image_id: UUID) -> Optional[Tuple[str, datetime]]:
        """
        Генерация presigned URL для загрузки.
        
        Args:
            image_id: UUID изображения
        
        Returns:
            Tuple (presigned URL, время истечения) или None при ошибке
        """
        return await self.generate_presigned_url(image_id, operation="put_object")
    
    async def check_exists(self, image_id: UUID) -> bool:
        """Проверка существования объекта"""
        try:
            client = await self._connection.get_s3_client()
            object_key = self._get_object_key(image_id)
            
            await client.head_object(
                Bucket=self._connection.bucket_name,
                Key=object_key
            )
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                return False
            logger.error(f"Error checking existence for {image_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking existence: {e}")
            return False
    
    async def check_exists_batch(
        self, 
        image_ids: List[UUID]
    ) -> Dict[UUID, bool]:
        """Пакетная проверка существования объектов"""
        if not image_ids:
            return {}
        
        tasks = [self.check_exists(image_id) for image_id in image_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        result_dict = {}
        for image_id, result in zip(image_ids, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to check {image_id}: {result}")
                result_dict[image_id] = False
            else:
                result_dict[image_id] = result
        
        found_count = sum(result_dict.values())
        logger.debug(f"Batch check: {found_count}/{len(image_ids)} found")
        return result_dict
    
    async def get_metadata(self, image_id: UUID) -> Optional[Dict]:
        """Получение метаданных объекта"""
        try:
            client = await self._connection.get_s3_client()
            object_key = self._get_object_key(image_id)
            
            response = await client.head_object(
                Bucket=self._connection.bucket_name,
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
                logger.error(f"Error getting metadata for {image_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting metadata: {e}")
            return None
    
    async def upload_file(
        self, 
        image_id: UUID, 
        file_data: bytes,
        content_type: str = "image/jpeg",
        metadata: Optional[Dict] = None
    ) -> bool:
        """Загрузка файла в S3"""
        try:
            client = await self._connection.get_s3_client()
            object_key = self._get_object_key(image_id)
            
            default_metadata = {
                'uploaded_at': datetime.now(timezone.utc).isoformat(),
                'image_id': str(image_id)
            }
            
            if metadata:
                default_metadata.update(metadata)
            
            await client.put_object(
                Bucket=self._connection.bucket_name,
                Key=object_key,
                Body=file_data,
                ContentType=content_type,
                Metadata=default_metadata
            )
            
            logger.info(f"Successfully uploaded {image_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Error uploading {image_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading {image_id}: {e}")
            return False
    
    async def delete_object(self, image_id: UUID) -> bool:
        """Удаление объекта из S3"""
        try:
            client = await self._connection.get_s3_client()
            object_key = self._get_object_key(image_id)
            
            await client.delete_object(
                Bucket=self._connection.bucket_name,
                Key=object_key
            )
            
            logger.info(f"Successfully deleted {image_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting {image_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting {image_id}: {e}")
            return False
    
    async def delete_batch(self, image_ids: List[UUID]) -> Dict[UUID, bool]:
        """Пакетное удаление объектов"""
        tasks = [self.delete_object(image_id) for image_id in image_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        result_dict = {}
        for image_id, result in zip(image_ids, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to delete {image_id}: {result}")
                result_dict[image_id] = False
            else:
                result_dict[image_id] = result
        
        success_count = sum(result_dict.values())
        logger.info(f"Batch delete: {success_count}/{len(image_ids)} succeeded")
        return result_dict
    
    async def get_object_size(self, image_id: UUID) -> Optional[int]:
        """Получение размера объекта в байтах"""
        metadata = await self.get_metadata(image_id)
        return metadata.get('content_length') if metadata else None


# Функция для использования в FastAPI приложении
async def get_s3_objects_service() -> S3ObjectService:
    """Dependency для получения S3 сервиса"""
    connection_manager = S3ConnectionManager()
    await connection_manager.initialize()
    s3_objects_service = S3ObjectService(connection_manager)
    return s3_objects_service


# Функция для инициализации и закрытия при старте/остановке приложения
async def init_s3_objects_service():
    """Инициализация S3 сервиса при старте приложения"""
    s3_objects_service = await get_s3_objects_service()
    await s3_objects_service._connection.initialize()


async def close_s3_objects_service():
    """Закрытие S3 сервиса при остановке приложения"""
    s3_objects_service = await get_s3_objects_service()
    await s3_objects_service._connection.close()