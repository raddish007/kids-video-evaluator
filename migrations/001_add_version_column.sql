-- Migration: Add version column to evaluations table
-- Run this in Supabase SQL Editor to enable multiple evaluation versions

-- Step 1: Add version column with default value
ALTER TABLE evaluations
ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

-- Step 2: Drop the old unique constraint
ALTER TABLE evaluations
DROP CONSTRAINT IF EXISTS evaluations_video_id_rubric_name_key;

-- Step 3: Add new unique constraint that includes version
ALTER TABLE evaluations
ADD CONSTRAINT evaluations_video_id_rubric_name_version_key
UNIQUE (video_id, rubric_name, version);

-- Step 4: Create index for version queries
CREATE INDEX IF NOT EXISTS idx_evaluations_version
ON evaluations(video_id, rubric_name, version DESC);

-- Verify the migration
SELECT
    column_name,
    data_type,
    column_default
FROM information_schema.columns
WHERE table_name = 'evaluations'
AND column_name = 'version';
