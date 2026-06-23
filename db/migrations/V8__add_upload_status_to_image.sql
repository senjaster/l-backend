-- Add upload_status field to image table
-- This field will store the status of the image upload process

-- Add the column
ALTER TABLE lesiv.image
ADD COLUMN upload_status TEXT NOT NULL DEFAULT 'unknown';
