"""S3 service for setting connection"""

import asyncio
import logging

from aiobotocore.session import get_session
from botocore.client import Config
from botocore.exceptions import NoCredentialsError

from app.config import settings


logging.getLogger('aiobotocore').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class S3ConnectionManager:
    """Менеджер подключения к S3"""
    
    def __init__(self):
        self._session = None
        self._client = None
        self._sqs_client = None
        self._lock = asyncio.Lock()
        self._initialized = False
        
        # Настройки подключения
        self.region_name = settings.s3_region
        self.access_key_id = settings.s3_access_key_id
        self.secret_access_key = settings.s3_secret_access_key
        self.bucket_name = settings.s3_bucket_name
        self.endpoint_host = settings.s3_endpoint_host
        self.use_virtual_hosted_style = settings.s3_use_virtual_hosted_style
        
        # Настройки пула соединений
        self.max_pool_connections = 100
        self.connection_timeout = 30
        self.read_timeout = 30

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
                
                if self.endpoint_host:
                    endpoint_url = f"https://{self.endpoint_host}"
                    client_kwargs["endpoint_url"] = endpoint_url
                
                # Создаем клиент
                self._client = await self._session.create_client(
                    "s3",
                    **client_kwargs
                ).__aenter__()

                # Создаем SQS клиент для Yandex Message Queue
                sqs_client_kwargs = {
                    "config": boto_config,
                    "aws_access_key_id": self.access_key_id,
                    "aws_secret_access_key": self.secret_access_key,
                    "endpoint_url": "https://message-queue.api.cloud.yandex.net"
                }
                
                # Создаем SQS клиент
                self._sqs_client = await self._session.create_client(
                    "sqs",
                    **sqs_client_kwargs
                ).__aenter__()
                
                self._initialized = True
                logger.info("  Async S3/SQS connection manager initialized successfully")
                
            except NoCredentialsError as e:
                logger.error(f"AWS credentials not found: {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Async S3 service: {e}")
                raise
    
    async def get_client(self):
        """Получение или создание клиента (ленивая инициализация)"""
        if not self._initialized:
            await self.initialize()
        return self._client

    async def get_sqs_client(self):
        """Получение SQS клиента (ленивая инициализация)"""
        if not self._initialized:
            await self.initialize()
        return self._sqs_client
    
    async def close(self):
        """Закрытие сессии и клиента"""
        async with self._lock:
            if self._client:
                await self._client.close()
                self._client = None
            if self._sqs_client:
                await self._sqs_client.close()
                self._sqs_client = None
            if self._session:
                self._session = None
            self._initialized = False
            logger.info("  Async S3 service closed")

    async def __aenter__(self):
        """Поддержка async context manager"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекста"""
        await self.close()

    @property
    def bucket_name(self) -> str:
        return self._bucket_name
    
    @bucket_name.setter
    def bucket_name(self, value: str):
        self._bucket_name = value
    
    @property
    def expiration(self) -> int:
        return settings.s3_presigned_url_expiration
