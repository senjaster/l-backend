import asyncio
import json
import logging
from typing import List, Dict, Optional, Union, Any
from uuid import UUID

from botocore.exceptions import ClientError

from .s3_connection import S3ConnectionManager


logger = logging.getLogger(__name__)


class S3QueueService:
    """Сервис для работы с S3 объектами и очередями YMQ"""
    
    def __init__(self, connection_manager: S3ConnectionManager):
        """
        Инициализация сервиса.
        
        Args:
            connection_manager: Менеджер подключения к S3
        """
        self._connection = connection_manager
    
    def build_queue_url(self, folder_id: str, queue_name: str) -> str:
        """
        Формирует полный URL очереди Yandex Message Queue.
        
        Args:
            folder_id: ID папки в Yandex Cloud
            queue_name: Имя очереди
        
        Returns:
            Полный URL очереди
        """
        self._connection.queue_host
        return f"https://{self._connection.queue_host}/{folder_id}/{queue_name}/file-info-queue"
    
    async def read_queue_messages(self, queue_url: str, max_messages: int = 10, wait_time: int = 20) -> List[Dict]:
        """
        Асинхронное чтение сообщений из очереди YMQ (SQS).
        
        Args:
            queue_url: URL очереди в Yandex Message Queue
            max_messages: Максимальное количество сообщений для получения (1-10)
            wait_time: Время ожидания появления сообщений в секундах (long polling, 0-20)
        
        Returns:
            Список словарей с сообщениями, каждый содержит:
            - message_id: ID сообщения
            - receipt_handle: Handle для удаления сообщения
            - body: Тело сообщения (строка JSON)
            - attributes: Атрибуты сообщения
        """
        logger.info(f"Starting read_queue_messages: queue_url={queue_url}, max_messages={max_messages}, wait_time={wait_time}")
        
        try:
            client = await self._connection.get_sqs_client()
            
            request_params = {
                'QueueUrl': queue_url,
                'MaxNumberOfMessages': min(max_messages, 10),
                'WaitTimeSeconds': wait_time,
                'VisibilityTimeout': 60,
                'AttributeNames': ['All'],
                'MessageAttributeNames': ['All']
            }
            
            import time
            start_time = time.time()
            response = await client.receive_message(**request_params)
            elapsed_time = time.time() - start_time
            
            logger.debug(f"receive_message completed in {elapsed_time:.2f}s")
            
            if 'Error' in response:
                logger.error(f"AWS error in response: {response['Error']}")
                return []
            
            messages = response.get('Messages', [])
            logger.info(f"Found {len(messages)} messages in queue")
            
            if messages:
                result = []
                for msg in messages:
                    body = msg.get('Body', '')
                    try:
                        parsed_body = json.loads(body) if body else {}
                    except json.JSONDecodeError:
                        parsed_body = body
                    
                    result.append({
                        'message_id': msg.get('MessageId'),
                        'receipt_handle': msg.get('ReceiptHandle'),
                        'body': parsed_body,
                        'body_raw': body,
                        'attributes': msg.get('Attributes', {}),
                        'message_attributes': msg.get('MessageAttributes', {})
                    })
                
                logger.info(f"Successfully processed {len(result)} messages")
                return result
            else:
                logger.debug("No messages in queue")
                
                # Check queue attributes for debugging
                try:
                    queue_attrs = await client.get_queue_attributes(
                        QueueUrl=queue_url,
                        AttributeNames=[
                            'ApproximateNumberOfMessages',
                            'ApproximateNumberOfMessagesDelayed',
                            'ApproximateNumberOfMessagesNotVisible'
                        ]
                    )
                    attr = queue_attrs.get('Attributes', {})
                    logger.debug(f"Queue attributes: {attr}")
                except Exception as e:
                    logger.debug(f"Failed to get queue attributes: {e}")
                
                return []
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"ClientError reading messages: {error_code} - {error_msg}")
            logger.error(f"Queue URL: {queue_url}")
            return []
            
        except Exception as e:
            logger.error(f"Unexpected error reading messages: {type(e).__name__} - {e}")
            logger.error(f"Queue URL: {queue_url}")
            return []
        
    async def delete_queue_message(self, queue_url: str, receipt_handle: str) -> bool:
        """
        Асинхронное удаление сообщения из очереди после обработки.
        
        Args:
            queue_url: URL очереди в Yandex Message Queue
            receipt_handle: Handle сообщения (полученный при чтении)
        
        Returns:
            True если сообщение удалено успешно, иначе False
        """
        try:
            client = await self._connection.get_sqs_client()
            
            await client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            
            logger.debug(f"  Message deleted from queue: {receipt_handle[:20]}...")
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"Error deleting message from queue: {error_code}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting message: {e}")
            return False
    
    async def purge_queue(self, queue_url: str) -> bool:
        """
        Асинхронная очистка всех сообщений из очереди.
        
        Args:
            queue_url: URL очереди в Yandex Message Queue
        
        Returns:
            True если очередь очищена успешно, иначе False
        """
        try:
            client = await self._connection.get_sqs_client()
            
            await client.purge_queue(QueueUrl=queue_url)
            
            logger.info(f"  Queue purged successfully: {queue_url}")
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"Error purging queue: {error_code}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error purging queue: {e}")
            return False
    
    async def send_queue_message(self, queue_url: str, message_body: Union[str, dict, list], 
                                delay_seconds: int = 0) -> Optional[str]:
        """
        Асинхронная отправка сообщения в очередь.
        
        Args:
            queue_url: URL очереди в Yandex Message Queue
            message_body: Тело сообщения (строка, словарь или список)
            delay_seconds: Задержка перед отправкой (0-900 секунд)
        
        Returns:
            ID отправленного сообщения или None при ошибке
        """
        try:
            client = await self._connection.get_sqs_client()
            
            if isinstance(message_body, (dict, list)):
                body = json.dumps(message_body, ensure_ascii=False, default=str)
            else:
                body = str(message_body)
            
            response = await client.send_message(
                QueueUrl=queue_url,
                MessageBody=body,
                DelaySeconds=delay_seconds
            )
            
            message_id = response.get('MessageId')
            logger.info(f"✅ Message sent to queue. MessageId: {message_id}")
            return message_id
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"Error sending message to queue: {error_code}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return None


# Функция для использования в FastAPI приложении
async def get_s3_queue_service() -> S3QueueService:
    """Dependency для получения S3 сервиса"""
    connection_manager = S3ConnectionManager()
    await connection_manager.initialize()
    s3_queue_service = S3QueueService(connection_manager)
    return s3_queue_service