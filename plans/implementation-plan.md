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
    - Router (including GET /plants, grab/release endpoints)

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
