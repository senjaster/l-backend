-- Add server_uploaded_at field to image table
-- This field will store the timestamp of when the image was uploaded to the server

-- Add the column
ALTER TABLE lesiv.image
ADD COLUMN server_uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;