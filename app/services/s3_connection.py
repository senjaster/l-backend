"""S3 service for setting connection"""

import asyncio
import logging

from aiobotocore.session import ClientCreatorContext, get_session
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
        self._client_cm = None
        self._sqs_client_cm = None
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
            
            self._client_cm = self._session.create_client("s3", **s3_client_kwargs)
            self._client = await self._client_cm.__aenter__()

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
            
            sqs_client_kwargs["endpoint_url"] = "https://message-queue.api.cloud.yandex.net"
            
            self._sqs_client_cm = self._session.create_client("sqs", **sqs_client_kwargs)
            self._sqs_client = await self._sqs_client_cm.__aenter__()
            
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

    async def get_sqs_client_cm(self) -> ClientCreatorContext:
        """
        Возвращает контекстный менеджер SQS клиента.
        
        Использование:
            async with await connection.get_sqs_client_cm() as client:
                response = await client.receive_message(...)
        
        Клиент автоматически закрывается при выходе из блока async with.
        """
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
        
        session = get_session()
        return session.create_client("sqs", **sqs_client_kwargs)

    async def get_s3_client_cm(self) -> ClientCreatorContext:
        """
        Возвращает контекстный менеджер S3 клиента.
        
        Использование:
            async with await connection.get_s3_client_cm() as client:
                response = await client.head_object(...)
        
        Клиент автоматически закрывается при выходе из блока async with.
        """
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
        
        session = get_session()
        return session.create_client("s3", **s3_client_kwargs)

    async def close(self):
        """Закрытие сессии и клиента"""
        async with self._lock:
            if self._client_cm:
                try:
                    # Получаем доступ к внутренней aiohttp сессии
                    if hasattr(self._client, '_http_session'):
                        try:
                            await self._client._http_session.close()
                            logger.debug("S3 aiohttp session closed")
                        except Exception as e:
                            logger.debug(f"Error closing S3 aiohttp session: {e}")
                    
                    await self._client_cm.__aexit__(None, None, None)
                    logger.debug("S3 client context manager exited")
                except Exception as e:
                    logger.warning(f"Error closing S3 client: {e}")
                finally:
                    self._client = None
                    self._client_cm = None
                    self._s3_initialized = False
            
            if self._sqs_client_cm:
                try:
                    # Получаем доступ к внутренней aiohttp сессии
                    if hasattr(self._sqs_client, '_http_session'):
                        try:
                            await self._sqs_client._http_session.close()
                            logger.debug("SQS aiohttp session closed")
                        except Exception as e:
                            logger.debug(f"Error closing SQS aiohttp session: {e}")
                    
                    await self._sqs_client_cm.__aexit__(None, None, None)
                    logger.debug("SQS client context manager exited")
                except Exception as e:
                    logger.warning(f"Error closing SQS client: {e}")
                finally:
                    self._sqs_client = None
                    self._sqs_client_cm = None
                    self._sqs_initialized = False
            
            if self._session:
                try:
                    # Закрываем внутреннюю сессию aiobotocore
                    if hasattr(self._session, '_session') and hasattr(self._session._session, 'close'):
                        await self._session._session.close()
                        logger.debug("aiobotocore session closed")
                except Exception as e:
                    logger.debug(f"Error closing aiobotocore session: {e}")
                finally:
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