-- name: get_by_id(work_log_id)^
-- Get work log by ID
SELECT id, started_at, completed_at, installation_percentage, 
       inspector_id, plant_id, is_deleted, server_modified_at
FROM lesiv.work_log
WHERE id = :work_log_id;

-- name: get_by_id_with_username(work_log_id)^
-- Get work log by ID with username of inspector who created it
SELECT wl.id, wl.started_at, wl.completed_at, wl.installation_percentage, 
       wl.inspector_id, wl.plant_id, wl.is_deleted, wl.server_modified_at,
       insp.username as inspector_username
FROM lesiv.work_log wl
LEFT JOIN lesiv.inspector insp ON wl.inspector_id = insp.id
WHERE wl.id = :work_log_id;

-- name: get_by_plant_id(plant_id, modified_since)
-- Get all work logs for plant (full data for aggregates)
-- :modified_since defaults to 1790-01-01 - only return work logs modified after that timestamp
SELECT wl.id, wl.started_at, wl.completed_at, wl.installation_percentage, 
       wl.inspector_id, wl.plant_id, wl.is_deleted, wl.server_modified_at,
       insp.username as inspector_username
FROM lesiv.work_log wl
LEFT JOIN lesiv.inspector insp ON wl.inspector_id = insp.id
WHERE wl.plant_id = :plant_id
  AND wl.server_modified_at > :modified_since
ORDER BY wl.server_modified_at;

-- name: get_by_inspector_id(inspector_id, modified_since)
-- Get all work logs for inspector
-- :modified_since defaults to 1790-01-01 - only return work logs modified after that timestamp
SELECT wl.id, wl.started_at, wl.completed_at, wl.installation_percentage, 
       wl.inspector_id, wl.plant_id, wl.is_deleted, wl.server_modified_at
FROM lesiv.work_log wl
WHERE wl.inspector_id = :inspector_id
  AND wl.server_modified_at > :modified_since
ORDER BY wl.server_modified_at;

-- name: get_by_date_range(start_date, end_date, plant_id, inspector_id)
-- Get work logs within date range with optional filters
SELECT wl.id, wl.started_at, wl.completed_at, wl.installation_percentage, 
       wl.inspector_id, wl.plant_id, wl.is_deleted, wl.server_modified_at,
       insp.username as inspector_username
FROM lesiv.work_log wl
LEFT JOIN lesiv.inspector insp ON wl.inspector_id = insp.id
WHERE wl.started_at >= :start_date
  AND wl.started_at <= :end_date
  AND wl.is_deleted = false
  AND (:plant_id::UUID IS NULL OR wl.plant_id = :plant_id)
  AND (:inspector_id::INT IS NULL OR wl.inspector_id = :inspector_id)
ORDER BY wl.started_at DESC;

-- name: get_inspectors_by_work_log(work_log_id)
-- Get all inspectors assigned to a work log
SELECT wli.inspector_id, insp.username, insp.full_name, wli.work_log_id
FROM lesiv.work_log_inspector wli
JOIN lesiv.inspector insp ON wli.inspector_id = insp.id
WHERE wli.work_log_id = :work_log_id
  AND insp.is_deleted = false;

-- name: get_work_logs_by_inspector_id(inspector_id, modified_since)
-- Get work logs where inspector is assigned (including through work_log_inspector table)
-- :modified_since defaults to 1790-01-01
SELECT wl.id, wl.started_at, wl.completed_at, wl.installation_percentage, 
       wl.inspector_id, wl.plant_id, wl.is_deleted, wl.server_modified_at
FROM lesiv.work_log wl
JOIN lesiv.work_log_inspector wli ON wl.id = wli.work_log_id
WHERE wli.inspector_id = :inspector_id
  AND wl.server_modified_at > :modified_since
ORDER BY wl.server_modified_at;

-- name: upsert_work_log(id, started_at, completed_at, installation_percentage, inspector_id, plant_id, is_deleted, server_modified_at)!
-- Insert or update work log
INSERT INTO lesiv.work_log (id, started_at, completed_at, installation_percentage, 
                             inspector_id, plant_id, is_deleted, server_modified_at)
VALUES (:id, :started_at, :completed_at, :installation_percentage, 
        :inspector_id, :plant_id, :is_deleted, :server_modified_at)
ON CONFLICT (id) DO UPDATE SET
    started_at = EXCLUDED.started_at,
    completed_at = EXCLUDED.completed_at,
    installation_percentage = EXCLUDED.installation_percentage,
    inspector_id = EXCLUDED.inspector_id,
    plant_id = EXCLUDED.plant_id,
    is_deleted = EXCLUDED.is_deleted,
    server_modified_at = EXCLUDED.server_modified_at;

-- name: upsert_work_log_inspector(work_log_id, inspector_id)!
-- Insert or update work log - inspector relationship
INSERT INTO lesiv.work_log_inspector (work_log_id, inspector_id)
VALUES (:work_log_id, :inspector_id)
ON CONFLICT (work_log_id, inspector_id) DO UPDATE SET
    work_log_id = EXCLUDED.work_log_id,
    inspector_id = EXCLUDED.inspector_id;

-- name: delete_work_log_inspector(work_log_id, inspector_id)!
-- Delete work log - inspector relationship
DELETE FROM lesiv.work_log_inspector
WHERE work_log_id = :work_log_id AND inspector_id = :inspector_id;

-- name: delete_all_work_log_inspectors(work_log_id)!
-- Delete all inspectors for a work log
DELETE FROM lesiv.work_log_inspector
WHERE work_log_id = :work_log_id;

-- name: delete_work_log(work_log_id)!
-- Logically delete work log
UPDATE lesiv.work_log
SET is_deleted = true, server_modified_at = CURRENT_TIMESTAMP
WHERE id = :work_log_id;

-- name: restore_work_log(work_log_id)!
-- Restore logically deleted work log
UPDATE lesiv.work_log
SET is_deleted = false, server_modified_at = CURRENT_TIMESTAMP
WHERE id = :work_log_id;

-- name: update_work_log_status(work_log_id, completed_at, installation_percentage)!
-- Update work log completion status
UPDATE lesiv.work_log
SET completed_at = :completed_at,
    installation_percentage = :installation_percentage,
    server_modified_at = CURRENT_TIMESTAMP
WHERE id = :work_log_id;

-- name: get_active_work_logs_by_plant(plant_id)
-- Get active (not completed) work logs for a plant
SELECT id, started_at, installation_percentage, inspector_id, server_modified_at
FROM lesiv.work_log
WHERE plant_id = :plant_id
  AND completed_at IS NULL
  AND is_deleted = false
ORDER BY started_at DESC;

-- name: get_completed_work_logs_by_plant(plant_id, start_date, end_date)
-- Get completed work logs for a plant within date range
SELECT id, started_at, completed_at, installation_percentage, inspector_id
FROM lesiv.work_log
WHERE plant_id = :plant_id
  AND completed_at IS NOT NULL
  AND completed_at >= :start_date
  AND completed_at <= :end_date
  AND is_deleted = false
ORDER BY completed_at DESC;

-- name: get_installation_stats_by_plant(plant_id)
-- Get installation statistics by plant
SELECT 
    COUNT(*) as total_work_logs,
    COUNT(CASE WHEN completed_at IS NOT NULL THEN 1 END) as completed_work_logs,
    AVG(CASE WHEN completed_at IS NOT NULL THEN installation_percentage END) as avg_completed_percentage,
    SUM(CASE WHEN completed_at IS NULL THEN 1 ELSE 0 END) as active_work_logs
FROM lesiv.work_log
WHERE plant_id = :plant_id
  AND is_deleted = false;

-- name: get_installation_stats_by_inspector(inspector_id, start_date, end_date)
-- Get installation statistics by inspector
SELECT 
    COUNT(*) as total_work_logs,
    COUNT(CASE WHEN completed_at IS NOT NULL THEN 1 END) as completed_work_logs,
    AVG(CASE WHEN completed_at IS NOT NULL THEN installation_percentage END) as avg_completed_percentage,
    SUM(CASE WHEN completed_at IS NULL THEN 1 ELSE 0 END) as active_work_logs,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))/3600) as avg_duration_hours
FROM lesiv.work_log
WHERE inspector_id = :inspector_id
  AND (:start_date::TIMESTAMPTZ IS NULL OR started_at >= :start_date)
  AND (:end_date::TIMESTAMPTZ IS NULL OR started_at <= :end_date)
  AND is_deleted = false;

-- name: get_work_log_summary_by_period(start_date, end_date, plant_id)
-- Get work log summary grouped by day/week/month
SELECT 
    DATE_TRUNC('day', started_at) as period,
    COUNT(*) as total_work_logs,
    COUNT(CASE WHEN completed_at IS NOT NULL THEN 1 END) as completed_work_logs,
    AVG(installation_percentage) as avg_installation_percentage,
    COUNT(DISTINCT inspector_id) as unique_inspectors
FROM lesiv.work_log
WHERE started_at >= :start_date
  AND started_at <= :end_date
  AND (:plant_id::UUID IS NULL OR plant_id = :plant_id)
  AND is_deleted = false
GROUP BY DATE_TRUNC('day', started_at)
ORDER BY period DESC;

-- name: get_work_log_timeline(plant_id, days_back)
-- Get timeline of work log activity for a plant
SELECT 
    started_at::date as date,
    COUNT(*) as work_logs_started,
    COUNT(CASE WHEN completed_at::date = started_at::date THEN 1 END) as completed_same_day,
    AVG(installation_percentage) as avg_percentage
FROM lesiv.work_log
WHERE plant_id = :plant_id
  AND started_at >= CURRENT_DATE - (:days_back::INT || ' days')::INTERVAL
  AND is_deleted = false
GROUP BY started_at::date
ORDER BY date DESC;

-- name: get_inspector_performance(inspector_id, start_date, end_date)
-- Get performance metrics for a specific inspector
SELECT 
    inspector_id,
    COUNT(*) as total_work_logs,
    COUNT(CASE WHEN completed_at IS NOT NULL THEN 1 END) as completed_work_logs,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))/3600) as avg_work_duration_hours,
    AVG(installation_percentage) as avg_installation_percentage,
    MODE() WITHIN GROUP (ORDER BY plant_id) as most_frequent_plant
FROM lesiv.work_log
WHERE inspector_id = :inspector_id
  AND started_at >= :start_date
  AND started_at <= :end_date
  AND is_deleted = false
GROUP BY inspector_id;

-- name: get_all_work_logs(modified_since)
-- Get all work logs (lightweight list)
-- :modified_since defaults to 1790-01-01 - only return work logs modified after that timestamp
SELECT id, started_at, completed_at, installation_percentage, inspector_id, plant_id, is_deleted
FROM lesiv.work_log
WHERE server_modified_at > :modified_since
ORDER BY server_modified_at;