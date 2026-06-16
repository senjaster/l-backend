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
        self._s3_initialized = False
        self._sqs_initialized = False
        
        # Настройки подключения
        self.region_name = settings.s3_region
        self.access_key_id = settings.s3_access_key_id
        self.secret_access_key = settings.s3_secret_access_key
        self.bucket_name = settings.s3_bucket_name
        self.endpoint_host = settings.s3_endpoint_host
        self.queue_host = settings.s3_queue_host
        self.use_virtual_hosted_style = settings.s3_use_virtual_hosted_style
        
        # Настройки пула соединений
        self.max_pool_connections = 100
        self.connection_timeout = 30
        self.read_timeout = 30

    async def initialize(self):
        """Инициализация сессии и всех клиентов"""
        async with self._lock:
            if self._initialized:
                return
            
            try:
                if not self.access_key_id or not self.secret_access_key:
                    raise NoCredentialsError("AWS credentials not found")
                
                self._session = get_session()
                
                await self._initialize_s3_client()
                await self._initialize_sqs_client()
                
                self._initialized = True
                logger.info("S3/SQS connection manager initialized successfully")
                
            except NoCredentialsError as e:
                logger.error(f"AWS credentials not found: {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize connection manager: {e}")
                raise

    async def _initialize_s3_client(self):
        """Инициализация S3 клиента"""
        if self._s3_initialized:
            return
        
        try:
            logger.info("Initializing S3 client...")
            
            s3_config_kwargs = {
                "region_name": self.region_name,
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
            
            s3_config = Config(**s3_config_kwargs)
            
            s3_client_kwargs = {
                "config": s3_config,
                "aws_access_key_id": self.access_key_id,
                "aws_secret_access_key": self.secret_access_key,
            }
            
            if self.endpoint_host:
                endpoint_url = f"https://{self.endpoint_host}"
                s3_client_kwargs["endpoint_url"] = endpoint_url
            
            self._client = await self._session.create_client(
                "s3",
                **s3_client_kwargs
            ).__aenter__()
            
            self._s3_initialized = True
            logger.info("S3 client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise

    async def _initialize_sqs_client(self):
        """Инициализация SQS клиента для Yandex Message Queue"""
        if self._sqs_initialized:
            return
        
        try:
            logger.info("Initializing SQS client...")
            
            sqs_config_kwargs = {
                "region_name": self.region_name,
                "signature_version": 's3v4',
                "max_pool_connections": self.max_pool_connections,
                "connect_timeout": self.connection_timeout,
                "read_timeout": self.read_timeout,
                "retries": {
                    'max_attempts': 3,
                    'mode': 'adaptive'
                }
            }
            
            sqs_config = Config(**sqs_config_kwargs)
            
            sqs_client_kwargs = {
                "config": sqs_config,
                "aws_access_key_id": self.access_key_id,
                "aws_secret_access_key": self.secret_access_key,
            }
            
            if self.queue_host:
                endpoint_url = f"https://{self.queue_host}"
                sqs_client_kwargs["endpoint_url"] = endpoint_url
            else:
                sqs_client_kwargs["endpoint_url"] = "https://message-queue.api.cloud.yandex.net"
            
            self._sqs_client = await self._session.create_client(
                "sqs",
                **sqs_client_kwargs
            ).__aenter__()
            
            self._sqs_initialized = True
            logger.info("SQS client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SQS client: {e}")
            raise

    async def initialize_s3_only(self):
        """Инициализация только S3 клиента (без SQS)"""
        async with self._lock:
            if not self._session:
                self._session = get_session()
            await self._initialize_s3_client()

    async def initialize_sqs_only(self):
        """Инициализация только SQS клиента (без S3)"""
        async with self._lock:
            if not self._session:
                self._session = get_session()
            await self._initialize_sqs_client()
    
    async def get_s3_client(self):
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
            logger.info("S3 service closed")

    async def __aenter__(self):
        """Поддержка async context manager"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекста"""
        await self.close()

    @property
    def expiration(self) -> int:
        return settings.s3_presigned_url_expiration