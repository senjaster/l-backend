-- name: upsert_temp_range!
-- Insert or update temperature range
INSERT INTO lesiv.sticker_temp_range (id, sticker_id, name, t_min, t_max)
VALUES (:id, :sticker_id, :name, :t_min, :t_max)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    t_min = EXCLUDED.t_min,
    t_max = EXCLUDED.t_max;