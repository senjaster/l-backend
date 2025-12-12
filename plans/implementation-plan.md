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

11. Implement Plant
    - Models (Plant + Facility + PlantListItem + PlantListResponse)
    - Queries (including get_all_plants, get_equipment_ids_by_facility)
    - Repository (with facility sync and equipment ID loading)
    - Router (including GET /plants, lock/unlock endpoints)

12. Implement Equipment
    - Models (Equipment + ControlPoint + Defect)
    - Queries (including get_inspection_ids)
    - Repository (with children sync and inspection ID loading)
    - Router

13. Implement Inspection
    - Models (Inspection + InspectionStep)
    - Queries (including get_image_ids)
    - Repository (with step sync and image ID loading)
    - Router

### Phase 4: Testing & Documentation
14. Test each endpoint manually using Swagger UI
15. Fix any issues found during testing
16. Update README.md with setup and running instructions

### Phase 5: Deployment Preparation
17. Create Dockerfile
18. Test with Docker
19. Document deployment process

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