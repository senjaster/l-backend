# API Design Principles

## Endpoints

- `GET /aggregate/all` - List all IDs. May return additional filds from root aggreagate table only
- `GET /aggregate/by_id/{id}` - Get specific aggregate
- `GET /aggregate/by_plant_id/{plant_id}` - Get aggregates for plant, response: `{"items": [...]}`
- `PUT /aggregate?force=false` - Create or replace aggregate. Supports logical deletion
- no DELETE method use logical deletion in PUT

## PUT Rules

- Aggregate ID value is passed in body only (not in path). 
- Logical deletion via `is_deleted=true` at aggregate and child level
- `server_modified_at` updated on every save

### force=false (default)
- Existing aggregates (update): validate `server_modified_at` matches DB, reject with 409 if mismatch
- New instances (insert): ignore `server_modified_at`
- Reject with 409 if extra  child entities exist on server. 
    - For example server has three child entities, but PUT body has only 2. This request should be rejected. 
    - Or, both server and body has three children, but some of them do not match by id. Reject too.

### force=true
- Ignore `server_modified_at` validation
- Mark extra child entities (present in DB but not in body) as deleted

### Never Allow
- Stealing child entities between aggregates (changing `parent_id` of existing child)

## Lists
- Models should never include List[scalar type]. Always use List[Some model] even if model consists of one field.
- Top level lists (for example in GET /aggregate/all) should be wrapped in "items":  `{"items": [ list of aggreagate models]}` 

## Child aggregates
- GET response should include list of related (child) aggregate ids. 
- Equipment is consideded child aggregate for Plant
- Inspection is consideded child aggregate for Eqipment
- PUT and GET share model, but PUT should ignore values in this field

## Child Entities

- No parent ID shown in model (implicit from aggregate boundary and nesting)
- Logical deletion only (`is_deleted` flag)
- Deleted children still returned in GET responses

## Repository Patterns

### Method Signatures
```python
async def get_by_id(self, conn, entity_id: UUID) -> Optional[Entity]
async def get_all(self, conn) -> EntityListResponse
async def save(self, conn, entity: Entity, force: bool = False) -> Entity
```

### Child Synchronization
1. Get existing child IDs
2. Validate ownership (prevent transfers between aggregates)
3. Upsert incoming children with `is_deleted` from request
4. Mark removed children as deleted if force=true

### Ownership Validation
- Check existing parent before accepting child
- Raise `ValueError` if child belongs to another parent
- Router catches `ValueError` → 400 Bad Request

### Optimistic Concurrency (force=false)
- Validate `server_modified_at` for existing aggregates
- Check for extra children on server
- Raise `ConcurrentModificationError` with conflict details → 409 Conflict

## Query Organization

- Single `.sql` file per aggregate: `app/queries/[aggregate_name].sql`
- Use aiosql multi-query support

## Error Handling

```python
try:
    async with conn.transaction():
        result = await repo.save(conn, entity, force)
    return result
except ConcurrentModificationError as e:
    raise HTTPException(status_code=409, detail=e.conflict_error.model_dump())
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
```

## Special Cases

- Inspector: read-only (GET only)
- Log: append-only (POST only)
- Image: no `is_deleted` flag (physical DELETE)