# Python REST Service Architecture Design

## Overview
This document describes the architecture for a Python REST service that serves as a transparent data repository for a mobile application, providing CRUD operations over a PostgreSQL database.

## Technology Stack
- **Framework**: FastAPI (async support, automatic OpenAPI docs)
- **Database**: PostgreSQL with `lesiv` schema
- **Query Layer**: PugSQL (SQL-first approach)
- **Models**: Pydantic (validation and serialization)
- **Database Driver**: asyncpg (async PostgreSQL driver with connection pooling)
- **Python Version**: 3.11+

## Architectural Principles
1. **Transparency**: No business logic - pure data repository
2. **Simplicity**: Single Pydantic model for both API and repository layers
3. **Async-first**: All operations are asynchronous
4. **Transactional**: Aggregate updates are atomic
5. **Flat API**: All aggregates exposed at root level, no nesting

---

## Identified Aggregates

Based on [`ddl.sql`](../ddl.sql:1), the following aggregates are identified:

### 1. Inspector Aggregate (Read-Only)
- **Root**: [`lesiv.inspector`](../ddl.sql:11)
- **Children**: None
- **Operations**: GET only (read-only reference data)

### 2. StickerType Aggregate
- **Root**: [`lesiv.sticker_type`](../ddl.sql:25)
- **Children**: [`lesiv.sticker_temp_range`](../ddl.sql:32)
- **Operations**: GET, PUT, DELETE

### 3. EquipmentType Aggregate
- **Root**: [`lesiv.equipment_type`](../ddl.sql:48)
- **Children**: [`lesiv.equipment_control_point_template`](../ddl.sql:54)
- **Operations**: GET, PUT, DELETE

### 4. Plant Aggregate
- **Root**: [`lesiv.plant`](../ddl.sql:98)
- **Children**: [`lesiv.facility`](../ddl.sql:113)
- **Operations**: GET, PUT, DELETE
- **Custom Operations**: POST /plant/{id}/grab, POST /plant/{id}/release

### 5. Equipment Aggregate
- **Root**: [`lesiv.equipment`](../ddl.sql:130)
- **Children**: 
  - [`lesiv.equipment_control_point`](../ddl.sql:148)
  - [`lesiv.equipment_defect`](../ddl.sql:168)
- **Operations**: GET, PUT, DELETE

### 6. Inspection Aggregate
- **Root**: [`lesiv.inspection`](../ddl.sql:193)
- **Children**: 
  - [`lesiv.inspection_step`](../ddl.sql:211)
  - [`lesiv.inspection_image_link`](../ddl.sql:243)
- **Operations**: GET, PUT, DELETE

### 7. Image (Standalone)
- **Table**: [`lesiv.image`](../ddl.sql:259)
- **Operations**: GET, PUT, DELETE

### 8. Log (Append-only)
- **Table**: [`lesiv.log`](../ddl.sql:75)
- **Operations**: POST only (batch insert)

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration (database URL, etc.)
│   ├── database.py             # Database connection pool setup
│   │
│   ├── models/                 # Pydantic models
│   │   ├── __init__.py
│   │   ├── inspector.py
│   │   ├── sticker_type.py
│   │   ├── equipment_type.py
│   │   ├── plant.py
│   │   ├── equipment.py
│   │   ├── inspection.py
│   │   ├── image.py
│   │   └── log.py
│   │
│   ├── repositories/           # PugSQL repositories
│   │   ├── __init__.py
│   │   ├── base.py            # Base repository class
│   │   ├── inspector.py
│   │   ├── sticker_type.py
│   │   ├── equipment_type.py
│   │   ├── plant.py
│   │   ├── equipment.py
│   │   ├── inspection.py
│   │   ├── image.py
│   │   └── log.py
│   │
│   ├── queries/                # SQL queries for PugSQL
│   │   ├── inspector/
│   │   │   ├── get_by_id.sql
│   │   │   ├── insert.sql
│   │   │   ├── update.sql
│   │   │   └── delete.sql
│   │   ├── sticker_type/
│   │   │   ├── get_by_id.sql
│   │   │   ├── get_temp_ranges.sql
│   │   │   ├── insert_sticker_type.sql
│   │   │   ├── insert_temp_range.sql
│   │   │   ├── update_sticker_type.sql
│   │   │   ├── update_temp_range.sql
│   │   │   ├── delete_sticker_type.sql
│   │   │   └── delete_temp_ranges.sql
│   │   ├── equipment_type/
│   │   ├── plant/
│   │   ├── equipment/
│   │   ├── inspection/
│   │   ├── image/
│   │   └── log/
│   │
│   └── routers/                # FastAPI routers
│       ├── __init__.py
│       ├── inspector.py
│       ├── sticker_type.py
│       ├── equipment_type.py
│       ├── plant.py
│       ├── equipment.py
│       ├── inspection.py
│       ├── image.py
│       └── log.py
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## API Endpoint Design

### Standard CRUD Pattern

All aggregates follow this pattern:

```
GET    /aggregate/{id}          # Get aggregate by ID
PUT    /aggregate/{id}          # Create or update entire aggregate
DELETE /aggregate/{id}          # Logical delete (set is_deleted=true)
```

### Complete API Specification

#### Inspector (Read-Only)
```
GET    /inspector/{id}          # Get inspector by ID
```

#### StickerType
```
GET    /sticker-type/{id}       # Get sticker type with temp ranges
PUT    /sticker-type/{id}       # Create or update sticker type
DELETE /sticker-type/{id}       # Logical delete
```

#### EquipmentType
```
GET    /equipment-type/{id}     # Get equipment type with control point templates
PUT    /equipment-type/{id}     # Create or update equipment type
DELETE /equipment-type/{id}     # Logical delete
```

#### Plant
```
GET    /plants                  # List all plants (id, name only)
GET    /plant/{id}              # Get plant with facilities and equipment IDs
PUT    /plant/{id}              # Create or update plant
DELETE /plant/{id}              # Logical delete
POST   /plant/{id}/grab         # Custom: grab plant for editing
POST   /plant/{id}/release       # Custom: release plant
```

#### Equipment
```
GET    /equipment/{id}          # Get equipment with control points, defects, and inspection IDs
PUT    /equipment/{id}          # Create or update equipment
DELETE /equipment/{id}          # Logical delete
```

#### Inspection
```
GET    /inspection/{id}         # Get inspection with steps and image IDs
PUT    /inspection/{id}         # Create or update inspection
DELETE /inspection/{id}         # Logical delete
```

#### Image
```
GET    /image/{id}              # Get image metadata
PUT    /image/{id}              # Create or update image
DELETE /image/{id}              # Actual delete (no is_deleted flag)
```

#### Log
```
POST   /log                     # Batch insert log entries
```

### Navigation Pattern

Each aggregate includes IDs of related child aggregates for navigation:

- **Plant** → includes `equipment_ids` for each facility
- **Equipment** → includes `inspection_ids`
- **Inspection** → includes `image_ids` for each step

This allows the mobile app to navigate the aggregate hierarchy without complex queries.

---

## Pydantic Model Design

### Key Principles
1. Use same models for API requests/responses and repository layer
2. Use `Optional` for nullable fields
3. Use Python `datetime` for timestamps (FastAPI handles conversion)
4. Use `UUID` type for UUID fields
5. Use `Enum` for PostgreSQL enum types
6. Nested models for child entities

### Example: Plant Aggregate Model

```python
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class Facility(BaseModel):
    id: UUID
    plant_id: UUID
    name: str
    is_deleted: bool = False
    equipment_ids: list[UUID] = Field(default_factory=list)  # Navigation


class Plant(BaseModel):
    id: UUID
    name: str
    grabbed_by_device_id: Optional[UUID] = None
    grabbed_by_user_id: Optional[int] = None
    grabbed_at: Optional[datetime] = None
    is_deleted: bool = False
    server_modified_at: datetime
    facilities: list[Facility] = Field(default_factory=list)


class PlantListItem(BaseModel):
    """Lightweight model for plant list endpoint"""
    id: UUID
    name: str


class PlantListResponse(BaseModel):
    items: list[PlantListItem]
    total: int
```

### Example: Equipment Aggregate Model

```python
from enum import Enum
from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class DefectStatus(str, Enum):
    DETECTED = "DETECTED"
    RESOLVED = "RESOLVED"


class EquipmentControlPoint(BaseModel):
    id: UUID
    equipment_id: UUID
    control_point_type: str
    point_count: int
    sticker_count: int
    sticker_type_id: Optional[int] = None
    t_max: int
    t_excess: int
    is_deleted: bool = False


class EquipmentDefect(BaseModel):
    id: UUID
    equipment_id: UUID
    unit_name: str
    t_max: Optional[int] = None
    t_excess: Optional[int] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    status: DefectStatus = DefectStatus.DETECTED
    is_deleted: bool = False


class Equipment(BaseModel):
    id: UUID
    plant_id: UUID
    parent_id: Optional[UUID] = None
    name: str
    is_container: bool = False
    equipment_type_id: Optional[int] = None
    estimated_point_count: Optional[int] = None
    is_deleted: bool = False
    server_modified_at: datetime
    control_points: list[EquipmentControlPoint] = Field(default_factory=list)
    defects: list[EquipmentDefect] = Field(default_factory=list)
    inspection_ids: list[UUID] = Field(default_factory=list)  # Navigation
```

### Example: Inspection Aggregate Model

```python
from enum import Enum
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field


class InspectionStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class InspectionStepType(str, Enum):
    GENERAL_INSPECTION = "GENERAL_INSPECTION"
    DEFECT_REPORT = "DEFECT_REPORT"
    DEFECT_FOLLOW_UP = "DEFECT_FOLLOW_UP"


class DefectSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"
    DEVELOPING = "DEVELOPING"


class InspectionStep(BaseModel):
    id: UUID
    timestamp: datetime
    inspection_id: UUID
    step_number: int
    step_type: InspectionStepType
    defect_id: Optional[UUID] = None
    description: Optional[str] = None
    is_resolved: Optional[bool] = None
    sticker_type_id: Optional[int] = None
    sticker_temp_range_id: Optional[int] = None
    t_observed: Optional[float] = None
    measured_current: Optional[int] = None
    nominal_current: Optional[int] = None
    severity: Optional[DefectSeverity] = None
    is_under_load: Optional[bool] = None
    is_deleted: bool = False
    image_ids: list[UUID] = Field(default_factory=list)  # Navigation


class Inspection(BaseModel):
    id: UUID
    equipment_id: UUID
    inspector_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: InspectionStatus = InspectionStatus.PLANNED
    is_deleted: bool = False
    server_modified_at: datetime
    steps: list[InspectionStep] = Field(default_factory=list)
```

---

## Repository Layer Design

### Base Repository Pattern

```python
from typing import Generic, TypeVar, Optional
import pugsql

T = TypeVar('T')


class BaseRepository(Generic[T]):
    def __init__(self, queries_path: str):
        self.queries = pugsql.module(queries_path)
        
    async def get_by_id(self, conn, id) -> Optional[T]:
        raise NotImplementedError
        
    async def save(self, conn, entity: T) -> T:
        raise NotImplementedError
        
    async def delete(self, conn, id) -> bool:
        raise NotImplementedError
```

### Transaction Management

All aggregate updates must be transactional:

```python
async def update_plant(plant_id: UUID, plant: Plant):
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            # Update plant
            await plant_repo.update_plant(conn, plant)
            
            # Update facilities
            await plant_repo.sync_facilities(conn, plant_id, plant.facilities)
```

### Child Entity Synchronization Strategy

For PUT operations on aggregates with children:

1. **Match by ID**: Update existing children that match by ID
2. **Add new**: Insert children with IDs not in database
3. **Mark deleted**: Set `is_deleted=true` for children in DB but not in request

```python
async def sync_facilities(self, conn, plant_id: UUID, facilities: list[Facility]):
    # Get existing facility IDs
    existing = await self.queries.get_facility_ids(conn, plant_id=plant_id)
    existing_ids = {f['id'] for f in existing}
    
    incoming_ids = {f.id for f in facilities}
    
    # Update or insert
    for facility in facilities:
        if facility.id in existing_ids:
            await self.queries.update_facility(conn, **facility.dict())
        else:
            await self.queries.insert_facility(conn, **facility.dict())
    
    # Mark deleted
    to_delete = existing_ids - incoming_ids
    for facility_id in to_delete:
        await self.queries.mark_facility_deleted(conn, id=facility_id)


async def get_by_id(self, conn, plant_id: UUID) -> Optional[Plant]:
    # Get plant
    plant_row = await self.queries.get_by_id(conn, id=plant_id)
    if not plant_row:
        return None
    
    # Get facilities with equipment IDs
    facilities = []
    facility_rows = await self.queries.get_facilities(conn, plant_id=plant_id)
    for fac_row in facility_rows:
        # Get equipment IDs for this facility
        equipment_ids = await self.queries.get_equipment_ids_by_facility(
            conn,
            facility_id=fac_row['id']
        )
        facilities.append(Facility(
            **fac_row,
            equipment_ids=[eq['id'] for eq in equipment_ids]
        ))
    
    return Plant(**plant_row, facilities=facilities)
```

---

## PugSQL Query Design

### Query Organization

Each aggregate has its own directory with SQL files:

```
queries/
├── plant/
│   ├── get_by_id.sql
│   ├── update_plant.sql
│   ├── get_facility_ids.sql
│   ├── insert_facility.sql
│   ├── update_facility.sql
│   └── mark_facility_deleted.sql
```

### Example Queries

**get_by_id.sql**
```sql
-- :name get_by_id :one
SELECT * FROM lesiv.plant
WHERE id = :id;
```

**get_facilities.sql**
```sql
-- :name get_facilities :many
SELECT * FROM lesiv.facility
WHERE plant_id = :plant_id
ORDER BY name;
```

**get_equipment_ids_by_facility.sql**
```sql
-- :name get_equipment_ids_by_facility :many
SELECT id FROM lesiv.equipment
WHERE parent_id = :facility_id
  AND is_deleted = false
ORDER BY name;
```

**get_all_plants.sql**
```sql
-- :name get_all_plants :many
SELECT id, name FROM lesiv.plant
WHERE is_deleted = false
ORDER BY name;
```

**update_plant.sql**
```sql
-- :name update_plant :affected
UPDATE lesiv.plant
SET 
    name = :name,
    grabbed_by_device_id = :grabbed_by_device_id,
    grabbed_by_user_id = :grabbed_by_user_id,
    grabbed_at = :grabbed_at,
    is_deleted = :is_deleted,
    server_modified_at = CURRENT_TIMESTAMP
WHERE id = :id;
```

**insert_facility.sql**
```sql
-- :name insert_facility :insert
INSERT INTO lesiv.facility (id, plant_id, name, is_deleted)
VALUES (:id, :plant_id, :name, :is_deleted);
```

**mark_facility_deleted.sql**
```sql
-- :name mark_facility_deleted :affected
UPDATE lesiv.facility
SET is_deleted = true
WHERE id = :id;
```

---

## FastAPI Router Design

### Standard Router Pattern

```python
from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID
from app.models.plant import Plant
from app.repositories.plant import PlantRepository
from app.database import get_db_connection

router = APIRouter(prefix="/plant", tags=["plant"])
plant_repo = PlantRepository()


@router.get("/plants", response_model=PlantListResponse)
async def list_plants(conn=Depends(get_db_connection)):
    """List all plants (id and name only)"""
    plants = await plant_repo.get_all(conn)
    return PlantListResponse(
        items=[PlantListItem(id=p['id'], name=p['name']) for p in plants],
        total=len(plants)
    )


@router.get("/{plant_id}", response_model=Plant)
async def get_plant(plant_id: UUID, conn=Depends(get_db_connection)):
    """Get plant with facilities and equipment IDs"""
    plant = await plant_repo.get_by_id(conn, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.put("/{plant_id}", response_model=Plant)
async def update_plant(plant_id: UUID, plant: Plant, conn=Depends(get_db_connection)):
    if plant.id != plant_id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    
    async with conn.transaction():
        result = await plant_repo.save(conn, plant)
    return result


@router.delete("/{plant_id}", status_code=204)
async def delete_plant(plant_id: UUID, conn=Depends(get_db_connection)):
    async with conn.transaction():
        success = await plant_repo.delete(conn, plant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plant not found")
```

### Custom Grab/Release Endpoints

```python
from pydantic import BaseModel


class GrabRequest(BaseModel):
    device_id: UUID
    user_id: int


class ReleaseRequest(BaseModel):
    device_id: UUID


@router.post("/{plant_id}/grab", response_model=Plant)
async def grab_plant(
    plant_id: UUID,
    request: GrabRequest,
    conn=Depends(get_db_connection)
):
    async with conn.transaction():
        plant = await plant_repo.grab(
            conn,
            plant_id,
            request.device_id,
            request.user_id
        )
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.post("/{plant_id}/release", response_model=Plant)
async def release_plant(
    plant_id: UUID,
    request: ReleaseRequest,
    conn=Depends(get_db_connection)
):
    async with conn.transaction():
        plant = await plant_repo.release(
            conn,
            plant_id,
            request.device_id
        )
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant
```

### Log Batch Insert Endpoint

```python
from app.models.log import LogEntry


@router.post("/log", status_code=201)
async def create_logs(
    logs: list[LogEntry], 
    conn=Depends(get_db_connection)
):
    async with conn.transaction():
        await log_repo.insert_batch(conn, logs)
    return {"inserted": len(logs)}
```

---

## Database Connection Management

### Connection Pool Setup

```python
# app/database.py
import asyncpg
from contextlib import asynccontextmanager
from app.config import settings

db_pool: asyncpg.Pool = None


async def init_db_pool():
    global db_pool
    db_pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=5,
        max_size=20,
        command_timeout=60
    )


async def close_db_pool():
    global db_pool
    if db_pool:
        await db_pool.close()


async def get_db_connection():
    async with db_pool.acquire() as connection:
        yield connection
```

### Application Lifecycle

```python
# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_db_pool, close_db_pool
from app.routers import (
    inspector, sticker_type, equipment_type, 
    plant, equipment, inspection, image, log
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db_pool()
    yield
    # Shutdown
    await close_db_pool()


app = FastAPI(
    title="L-Inspector Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(inspector.router)
app.include_router(sticker_type.router)
app.include_router(equipment_type.router)
app.include_router(plant.router)
app.include_router(equipment.router)
app.include_router(inspection.router)
app.include_router(image.router)
app.include_router(log.router)
```

---

## Configuration Management

```python
# app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    
    class Config:
        env_file = ".env"


settings = Settings()
```

**.env.example**
```
DATABASE_URL=postgresql://user:password@localhost:5432/lesiv
```

---

## Error Handling Strategy

### Standard HTTP Status Codes

- `200 OK`: Successful GET
- `201 Created`: Successful POST (logs)
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Validation error or ID mismatch
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Database or server error

### Global Exception Handler

```python
from fastapi import Request
from fastapi.responses import JSONResponse


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

---

## Testing Strategy

### Unit Tests
- Test Pydantic model validation
- Test repository methods with mock database

### Integration Tests
- Test API endpoints with test database
- Test transaction rollback on errors
- Test child entity synchronization logic

### Test Database Setup
```python
import pytest
import asyncpg
from app.database import init_db_pool, close_db_pool


@pytest.fixture(scope="session")
async def db_pool():
    await init_db_pool()
    yield
    await close_db_pool()
```

---

## Performance Considerations

1. **Connection Pooling**: Use asyncpg pool (5-20 connections)
2. **Batch Operations**: Log endpoint accepts multiple entries
3. **Indexes**: Rely on indexes defined in [`ddl.sql`](../ddl.sql:1)
4. **Lazy Loading**: Load child entities only when needed
5. **Transaction Scope**: Keep transactions as short as possible

---

## Deployment Considerations

### Dependencies
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
asyncpg==0.29.0
pugsql==0.2.4
python-dotenv==1.0.0
```

### Running the Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Support
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## API Documentation

FastAPI automatically generates:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Summary

This architecture provides:
- ✅ Clean separation of concerns (models, repositories, routers)
- ✅ Transparent data access without business logic
- ✅ Transactional aggregate updates
- ✅ Async-first design for performance
- ✅ Simple, maintainable codebase
- ✅ Automatic API documentation
- ✅ Type safety with Pydantic
- ✅ SQL-first approach with PugSQL

The design follows the requirements exactly:
- 3 layers: Repository (PugSQL) → Models (Pydantic) → API (FastAPI)
- Same models for all layers
- Flat API structure
- Standard CRUD operations
- Custom grab/release for Plant
- Batch log insertion