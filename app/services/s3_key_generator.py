from uuid import UUID
from typing import Optional


class S3KeyGenerator:
    """Генератор ключей для объектов в S3"""
    
    def __init__(self, prefix: str = "", extension: str = "jpg"):
        """
        Args:
            prefix: Префикс для всех ключей (например, 'images/')
            extension: Расширение файла (без точки)
        """
        self.prefix = prefix
        self.extension = extension
    
    def generate_image_key(self, image_id: UUID, custom_extension: Optional[str] = None) -> str:
        """
        Генерация ключа для изображения.
        
        Args:
            image_id: UUID изображения
            custom_extension: Своё расширение (если не указано, используется default)
        """
        ext = custom_extension or self.extension
        key = f"{image_id}.{ext}"
        
        if self.prefix:
            key = f"{self.prefix.rstrip('/')}/{key}"
        
        return key
    
    def parse_key(self, key: str) -> Optional[UUID]:
        """
        Извлечение UUID из ключа объекта.
        
        Args:
            key: Ключ объекта в S3
        
        Returns:
            UUID или None если не удалось распарсить
        """
        # Убираем префикс если он есть
        if self.prefix:
            if key.startswith(self.prefix):
                key = key[len(self.prefix):]
            else:
                return None
        
        # Убираем расширение
        if '.' in key:
            key = key.split('.')[0]
        
        try:
            return UUID(key)
        except ValueError:
            return None