-- name: insert_one!
INSERT INTO lesiv.log (
    logged_at,
    plant_id,
    inspector_id,
    entity_id,
    entity_type,
    op,
    data,
    message
) VALUES (
    :logged_at,
    :plant_id,
    :inspector_id,
    :entity_id,
    :entity_type,
    :op,
    :data,
    :message
);