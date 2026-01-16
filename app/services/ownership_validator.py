"""Ownership validation service for plant, equipment, and inspection aggregates"""

from uuid import UUID
import logging
from app.models.plant import Plant
from app.models.equipment import Equipment
from app.models.inspection import Inspection
from app.models.inspector import Inspector
from app.models import ConflictError, ConflictDetail
from app.repositories.plant import PlantRepository, queries as plant_queries
from app.repositories.equipment import EquipmentRepository, queries as equipment_queries
from app.repositories.inspection import (
    InspectionRepository,
    queries as inspection_queries,
)
from app.exceptions import ConcurrentModificationError
from app.utils.claim_utils import is_claim_expired

logger = logging.getLogger(__name__)


class OwnershipValidator:
    """
    Service to validate ownership of plant, equipment, and inspection aggregates.
    Checks if a user has the right to modify an aggregate based on claim ownership or creator ownership.
    """

    def __init__(self, conn, current_user: Inspector):
        """
        Initialize the ownership validator with a database connection and current user.

        Args:
            conn: Database connection to use for validation queries
            current_user: Current authenticated user
        """
        self.conn = conn
        self.current_user = current_user
        self.plant_repo = PlantRepository()
        self.equipment_repo = EquipmentRepository()
        self.inspection_repo = InspectionRepository()

    async def validate_plant_ownership(self, plant: Plant) -> None:
        """
        Validate that the plant is claimed by the current user.
        Pessimistic locks are never bypassed, only by anonymous user (when auth is disabled).

        Args:
            plant: Plant to validate

        Raises:
            ConcurrentModificationError: If plant is not claimed by current user
        """
        # Skip validation only for anonymous user (when auth is disabled)
        if self.current_user.id == -1:
            return

        current = await self.plant_repo.get_by_id(self.conn, plant.id)
        if not current:
            return  # New plant, no validation needed

        # Check if claim expired, release it first
        if current.claimed_by_device_id is not None and is_claim_expired(
            current.claimed_at
        ):
            await self.plant_repo.release(self.conn, plant.id)
            # Refresh current state
            current = await self.plant_repo.get_by_id(self.conn, plant.id)
            if not current:
                return  # Should not happen, but handle gracefully

        # Check claim ownership
        if current.claimed_by_user_id is None:
            raise ConcurrentModificationError(
                ConflictError(
                    message="Plant must be claimed before modification",
                    server_modified_at=current.server_modified_at,
                    conflicts=[
                        ConflictDetail(
                            field="claimed_by_user_id",
                            message="Plant is not claimed by any user",
                        )
                    ],
                )
            )

        if current.claimed_by_user_id != self.current_user.id:
            # Get username for better error message
            plant_with_username = await plant_queries.get_by_id_with_username(
                self.conn, id=plant.id
            )
            claimed_by_username = (
                plant_with_username["claimed_by_username"]
                if plant_with_username
                else f"user ID {current.claimed_by_user_id}"
            )

            raise ConcurrentModificationError(
                ConflictError(
                    message="Plant is claimed by another user",
                    server_modified_at=current.server_modified_at,
                    conflicts=[
                        ConflictDetail(
                            field="claimed_by_user_id",
                            message=f"Plant is claimed by {claimed_by_username}, not by {self.current_user.username}",
                        )
                    ],
                )
            )

    async def validate_equipment_ownership(self, equipment: Equipment) -> None:
        """
        Validate that the plant (parent of equipment) is claimed by the current user.
        Pessimistic locks are never bypassed, only by anonymous user (when auth is disabled).

        Args:
            equipment: Equipment to validate

        Raises:
            ConcurrentModificationError: If plant is not claimed by current user
        """
        # Skip validation only for anonymous user (when auth is disabled)
        if self.current_user.id == -1:
            return

        current = await self.equipment_repo.get_by_id(self.conn, equipment.id)
        if not current:
            return  # New equipment, no validation needed

        # Get plant claim info for this equipment
        plant_claim_info_row = (
            await equipment_queries.get_plant_claim_info_for_equipment(
                self.conn, equipment_id=equipment.id
            )
        )
        if not plant_claim_info_row:
            return  # No plant found (shouldn't happen in normal flow)

        # Check if claim expired, release it first
        if plant_claim_info_row[
            "claimed_by_device_id"
        ] is not None and is_claim_expired(plant_claim_info_row["claimed_at"]):
            await self.plant_repo.release(self.conn, plant_claim_info_row["plant_id"])
            # Refresh plant claim info
            plant_claim_info_row = (
                await equipment_queries.get_plant_claim_info_for_equipment(
                    self.conn, equipment_id=equipment.id
                )
            )
            if not plant_claim_info_row:
                return  # Should not happen, but handle gracefully

        # Check claim ownership
        if plant_claim_info_row["claimed_by_user_id"] is None:
            raise ConcurrentModificationError(
                ConflictError(
                    message="Plant must be claimed before modifying equipment",
                    server_modified_at=current.server_modified_at,
                    conflicts=[
                        ConflictDetail(
                            field="plant_claim",
                            message=f"Plant {plant_claim_info_row['plant_id']} is not claimed by any user",
                        )
                    ],
                )
            )

        if plant_claim_info_row["claimed_by_user_id"] != self.current_user.id:
            claimed_by_username = (
                plant_claim_info_row.get("claimed_by_username")
                or f"user ID {plant_claim_info_row['claimed_by_user_id']}"
            )

            raise ConcurrentModificationError(
                ConflictError(
                    message="Plant is claimed by another user",
                    server_modified_at=current.server_modified_at,
                    conflicts=[
                        ConflictDetail(
                            field="plant_claim",
                            message=f"Plant {plant_claim_info_row['plant_id']} is claimed by {claimed_by_username}, not by {self.current_user.username}",
                        )
                    ],
                )
            )

    async def validate_inspection_ownership(self, inspection: Inspection) -> None:
        """
        Validate that the inspection was created by the current user.
        Pessimistic locks are never bypassed, only by anonymous user (when auth is disabled).

        Args:
            inspection: Inspection to validate

        Raises:
            ConcurrentModificationError: If inspection was not created by current user or has extra steps
        """
        # Skip validation only for anonymous user (when auth is disabled)
        if self.current_user.id == -1:
            return

        current = await self.inspection_repo.get_by_id(self.conn, inspection.id)
        if not current:
            return  # New inspection, no validation needed

        # Check if user is the creator of this inspection
        if current.inspector_id != self.current_user.id:
            # Get username for better error message
            inspection_with_username = await inspection_queries.get_by_id_with_username(
                self.conn, id=inspection.id
            )
            inspector_username = (
                inspection_with_username["inspector_username"]
                if inspection_with_username
                else f"inspector ID {current.inspector_id}"
            )

            raise ConcurrentModificationError(
                ConflictError(
                    message="Only the creator can modify this inspection",
                    server_modified_at=current.server_modified_at,
                    conflicts=[
                        ConflictDetail(
                            field="inspector_id",
                            message=f"Inspection was created by {inspector_username}, not by {self.current_user.username}",
                        )
                    ],
                )
            )

        # Check for extra steps on server
        current_step_ids = {step.id for step in current.steps if not step.is_deleted}
        incoming_step_ids = {step.id for step in inspection.steps}
        extra_step_ids = current_step_ids - incoming_step_ids

        if extra_step_ids:
            raise ConcurrentModificationError(
                ConflictError(
                    message="Extra child entities exist on server",
                    server_modified_at=current.server_modified_at,
                    extra_child_ids=list(extra_step_ids),
                    conflicts=[
                        ConflictDetail(
                            field="steps",
                            message=f"Server has {len(extra_step_ids)} extra steps not in client request",
                        )
                    ],
                )
            )
