"""Utility functions for database operations"""

from datetime import datetime
from typing import TypeVar, Generic, List, Set, Optional, Callable, Any
from dataclasses import dataclass

from app.exceptions import ConcurrentModificationError
from app.models import ConflictError, ConflictDetail

T = TypeVar('T')


@dataclass
class CollectionConfig(Generic[T]):
    """Configuration for nested collection validation"""
    server_collection: List[T]
    client_collection: List[T]
    collection_name: str = "items"
    id_getter: Callable[[T], Any] = lambda x: getattr(x, 'id', None)
    is_deleted_checker: Callable[[T], bool] = lambda x: getattr(x, 'is_deleted', False)


class OptimisticLockingValidator:
    """Universal validator for optimistic locking"""
    
    @staticmethod
    def validate_timestamps(
        server_modified_at: datetime,
        client_modified_at: datetime,
        truncate_func: Optional[Callable[[datetime], datetime]] = None,
        object_name: str = "object"
    ) -> None:
        """Validate timestamps"""
        if server_modified_at != client_modified_at:
            raise ConcurrentModificationError(
                conflict_error=ConflictError(
                    message=f"{object_name} was modified by another client",
                    server_modified_at=server_modified_at,
                    client_modified_at=client_modified_at
                )
            )
        
        if truncate_func:
            if truncate_func(client_modified_at) != truncate_func(server_modified_at):
                raise ConcurrentModificationError(
                    ConflictError(
                        message=f"{object_name} was modified by another client",
                        server_modified_at=server_modified_at,
                        client_modified_at=client_modified_at,
                        conflicts=[
                            ConflictDetail(
                                field="server_modified_at",
                                message="Timestamp mismatch",
                                server_value=server_modified_at.isoformat(),
                                client_value=client_modified_at.isoformat(),
                            )
                        ],
                    )
                )
    
    @staticmethod
    def validate_extra_ids(
        server_ids: Set[Any],
        client_ids: Set[Any],
        collection_name: str = "items"
    ) -> None:
        """Validate that server doesn't have extra items"""
        extra_ids = server_ids - client_ids
        if extra_ids:
            raise ConcurrentModificationError(
                ConflictError(
                    message=f"Extra child {collection_name} exist on server",
                    server_modified_at=datetime.now(),  # Placeholder, should be actual server_modified_at
                    extra_child_ids=list(extra_ids),
                    conflicts=[
                        ConflictDetail(
                            field=collection_name,
                            message=f"Server has {len(extra_ids)} extra {collection_name} not in client request",
                        )
                    ],
                )
            )
    
    @classmethod
    def validate_collections(cls, configs: List[CollectionConfig]) -> None:
        """Validate multiple collections"""
        for config in configs:
            server_ids = {
                config.id_getter(item)
                for item in config.server_collection
                if not config.is_deleted_checker(item)
            }
            client_ids = {config.id_getter(item) for item in config.client_collection}
            cls.validate_extra_ids(server_ids, client_ids, config.collection_name)
    
    @classmethod
    def validate_object(
        cls,
        server_obj: Any,
        client_obj: Any,
        truncate_func: Optional[Callable] = None,
        collection_configs: Optional[List[CollectionConfig]] = None
    ) -> None:
        """Universal object validation"""
        if hasattr(server_obj, 'server_modified_at') and hasattr(client_obj, 'server_modified_at'):
            cls.validate_timestamps(
                server_modified_at=server_obj.server_modified_at,
                client_modified_at=client_obj.server_modified_at,
                truncate_func=truncate_func,
                object_name=server_obj.__class__.__name__
            )
        
        if collection_configs:
            cls.validate_collections(collection_configs)