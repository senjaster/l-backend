-- name: upsert_template!
-- Insert or update control point template
INSERT INTO lesiv.equipment_control_point_template 
    (id, equipment_type_id, name, short_name, t_max, t_excess, default_sticker_id)
VALUES (:id, :equipment_type_id, :name, :short_name, :t_max, :t_excess, :default_sticker_id)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    t_max = EXCLUDED.t_max,
    t_excess = EXCLUDED.t_excess,
    default_sticker_id = EXCLUDED.default_sticker_id;