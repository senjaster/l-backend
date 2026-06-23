-- Add upload_status and server_uploaded_at fields to image table
-- upload_status tracks whether the image file has been uploaded to S3
-- server_uploaded_at records when the S3 upload event was received

CREATE TYPE lesiv.image_upload_status AS ENUM ('UNKNOWN', 'UPLOADED', 'MISSING');

ALTER TABLE lesiv.image
ADD COLUMN upload_status lesiv.image_upload_status NOT NULL DEFAULT 'UNKNOWN';

ALTER TABLE lesiv.image
ADD COLUMN server_uploaded_at TIMESTAMPTZ NULL;
