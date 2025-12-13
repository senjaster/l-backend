# Implementation Plan

## Simple Step-by-Step Implementation Order

### Phase 1: Project Setup
1. Create project structure (directories: app/, app/models/, app/repositories/, app/queries/, app/routers/)
2. Create requirements.txt with dependencies
3. Create .env.example and app/config.py
4. Create app/database.py (connection pool setup)
5. Create app/main.py (FastAPI app skeleton)

### Phase 2: Simple Aggregates (No Children)
6. Implement Inspector (read-only)
   - Model: app/models/inspector.py
   - Queries: app/queries/inspector/get_by_id.sql
   - Repository: app/repositories/inspector.py
   - Router: app/routers/inspector.py

7. Implement Image
   - Model, queries, repository, router

8. Implement Log (POST only)
   - Model, queries, repository, router

### Phase 3: Aggregates with Children
9. Implement StickerType
   - Models (StickerType + StickerTempRange)
   - Queries (CRUD + child sync)
   - Repository (with child synchronization)
   - Router

10. Implement EquipmentType
    - Models (EquipmentType + ControlPointTemplate)
    - Queries, repository, router

### Phase 4: Plant

11. Implement Plant
    - Models (Plant + Facility + PlantListItem + PlantListResponse)
    - Queries (including get_all_plants, get_equipment_ids_by_facility)
    - Repository (with facility sync and equipment ID loading)
    - Router (including GET /plants, lock/unlock endpoints)

### Phase 5: Equipment

12. Implement Equipment
    - Models (Equipment + ControlPoint + Defect)
    - Queries (including get_inspection_ids)
    - Repository (with children sync and inspection ID loading)
    - Router

### Phase 6: Inspection

13. Implement Inspection
    - Models (Inspection + InspectionStep)
    - Queries (including get_image_ids)
    - Repository (with step sync and image ID loading)
    - Router

---

## Key Implementation Notes

- Start with simple aggregates to establish patterns
- Test each aggregate before moving to the next
- Use transactions for all PUT/DELETE operations
- Follow the child synchronization pattern: match by ID, add new, mark deleted
- Include navigation IDs (equipment_ids, inspection_ids, image_ids) when loading aggregates
- Inspector is read-only (GET only)
- Log is append-only (POST only)
- Image has no is_deleted flag (actual DELETE)
- GET /plants returns lightweight list with wrapped response

---

## API Design Patterns (Established in Phase 4)

### 1. Separate Read and Write Models

**Read Models** (returned from GET endpoints):
- Include all fields: id, business fields, is_deleted, timestamps, navigation IDs
- Child entities include full details (except parent id, see below)
- Example: `Plant`, `Facility`

**Write Models** (used in PUT/POST requests):
- Exclude redundant fields: 
    - aggregate root id (taken from path), 
    - is_deleted - assume not deleted, false
- do not include *child aggreagate* ids (e.g. equipment_ids in facility)
- Example: `PlantWrite`, `FacilityWrite`

### 2. Aggregate Root ID from Path in Write models

- Aggregate root ID comes from URL path parameter, NOT from request body
- Repository `save()` method accepts `id` as separate parameter
- Example: `PUT /plant/{plant_id}` - plant_id from path, not body

### 3. Child Entities Don't Reference Parent

- Child entities within an aggregate do NOT contain parent ID
- Parent ID is implicit from aggregate boundary
- Repository handles parent-child relationship internally
- Example: `Facility` model has no `plant_id` field

### 4. Logical Deletion for Child Entities

- Child entities use logical deletion (is_deleted flag), not physical deletion
- When child is removed from parent's list, it's marked as deleted
- Deleted children are still returned in GET responses
- Use `mark_[entity]_deleted` query pattern

### 5. Ownership Validation

- Validate that child entities cannot be transferred between aggregates
- Check existing ownership before accepting child entity
- Raise `ValueError` with descriptive message
- Router catches `ValueError` and returns 400 Bad Request

### 6. Query Organization

- All queries for an aggregate in a single `.sql` file
- Use aiosql's multi-query support
- Name pattern: `app/queries/[aggregate_name].sql`
- Example: `app/queries/plant.sql` contains all plant and facility queries

### 7. Repository Method Signatures

```python
async def get_by_id(self, conn, entity_id: UUID) -> Optional[Entity]
async def get_all(self, conn) -> EntityListResponse  # for list endpoints
async def save(self, conn, entity_id: UUID, entity: EntityWrite) -> Entity
async def delete(self, conn, entity_id: UUID) -> bool
```

### 8. Child Synchronization Pattern

```python
async def _sync_children(self, conn, parent_id: UUID, children: list[ChildWrite]):
    # 1. Get existing child IDs
    existing_ids = {row['id'] for row in await get_child_ids(parent_id)}
    incoming_ids = {c.id for c in children}
    
    # 2. Validate ownership (prevent transfers)
    for child in children:
        if child.id not in existing_ids:
            existing_parent = await get_child_parent_id(child.id)
            if existing_parent and existing_parent != parent_id:
                raise ValueError(f"Child belongs to another parent")
    
    # 3. Upsert incoming children (is_deleted = False)
    for child in children:
        await upsert_child(child.id, parent_id, child.name, is_deleted=False)
    
    # 4. Mark removed children as deleted
    to_delete = existing_ids - incoming_ids
    for child_id in to_delete:
        await mark_child_deleted(child_id)
```

### 9. Integration Tests

- Test CRUD operations
- Test child synchronization (add, update, remove)
- Test ownership validation (prevent transfers)
- Test logical deletion behavior
- Test error cases (404, 400)
- Use write models in test data (no server-managed fields)

### 10. Error Handling in Router

```python
try:
    async with conn.transaction():
        result = await repo.save(conn, entity_id, entity)
    return result
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
```