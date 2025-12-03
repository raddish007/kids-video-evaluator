-- Supabase Database Schema for Video Evaluator
-- Run this in your Supabase SQL Editor to set up the database

-- ============================================
-- TABLES
-- ============================================

-- Videos table: stores metadata about ingested videos
CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    duration_seconds REAL,
    frame_count INTEGER,
    has_transcript BOOLEAN DEFAULT FALSE,
    youtube_id TEXT,
    youtube_url TEXT,
    ingestion_date TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Evaluations table: stores evaluation results for each rubric
-- Supports multiple versions per video+rubric combination
CREATE TABLE IF NOT EXISTS evaluations (
    id BIGSERIAL PRIMARY KEY,
    video_id TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    rubric_name TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,  -- Version number for multiple runs
    status TEXT NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    evaluator TEXT,  -- 'claude', 'gemini', 'ollama'
    model_name TEXT,
    cost DECIMAL(10,4),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds REAL,
    error_message TEXT,
    result JSONB,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(video_id, rubric_name, version)
);

-- Rubrics reference table: master list of available rubrics
CREATE TABLE IF NOT EXISTS rubrics (
    name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT,
    category TEXT,  -- 'safety', 'quality', 'educational', 'production', 'ethics'
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_evaluations_video_id ON evaluations(video_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_status ON evaluations(status);
CREATE INDEX IF NOT EXISTS idx_evaluations_rubric ON evaluations(rubric_name);
CREATE INDEX IF NOT EXISTS idx_videos_ingestion_date ON videos(ingestion_date DESC);
CREATE INDEX IF NOT EXISTS idx_videos_youtube_id ON videos(youtube_id) WHERE youtube_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_evaluations_completed ON evaluations(completed_at DESC) WHERE completed_at IS NOT NULL;

-- GIN index for JSONB columns to enable fast JSON queries
CREATE INDEX IF NOT EXISTS idx_videos_metadata ON videos USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_evaluations_result ON evaluations USING GIN (result);

-- ============================================
-- VIEWS
-- ============================================

-- Video status view: aggregated status for dashboard overview
CREATE OR REPLACE VIEW video_status AS
SELECT
    v.id,
    v.title,
    v.filename,
    v.duration_seconds,
    v.frame_count,
    v.youtube_id,
    v.ingestion_date,
    v.created_at,
    COUNT(e.id) as total_evaluations,
    COUNT(CASE WHEN e.status = 'completed' THEN 1 END) as completed_count,
    COUNT(CASE WHEN e.status = 'in_progress' THEN 1 END) as in_progress_count,
    COUNT(CASE WHEN e.status = 'pending' THEN 1 END) as pending_count,
    COUNT(CASE WHEN e.status = 'failed' THEN 1 END) as failed_count,
    COALESCE(SUM(e.cost), 0) as total_cost,
    MAX(e.completed_at) as last_evaluation,
    -- Calculate completion percentage
    CASE
        WHEN COUNT(e.id) > 0 THEN
            ROUND((COUNT(CASE WHEN e.status = 'completed' THEN 1 END)::NUMERIC / COUNT(e.id)::NUMERIC) * 100, 1)
        ELSE 0
    END as completion_percentage
FROM videos v
LEFT JOIN evaluations e ON v.id = e.video_id
GROUP BY v.id, v.title, v.filename, v.duration_seconds, v.frame_count, v.youtube_id, v.ingestion_date, v.created_at;

-- Rubric completion view: which rubrics are most/least completed
CREATE OR REPLACE VIEW rubric_completion_stats AS
SELECT
    r.name,
    r.display_name,
    r.category,
    r.sort_order,
    COUNT(e.id) as total_evaluations,
    COUNT(CASE WHEN e.status = 'completed' THEN 1 END) as completed_count,
    COUNT(CASE WHEN e.status = 'failed' THEN 1 END) as failed_count,
    COALESCE(AVG(e.cost), 0) as avg_cost,
    COALESCE(AVG(e.duration_seconds), 0) as avg_duration_seconds
FROM rubrics r
LEFT JOIN evaluations e ON r.name = e.rubric_name AND e.status = 'completed'
WHERE r.is_active = TRUE
GROUP BY r.name, r.display_name, r.category, r.sort_order
ORDER BY r.sort_order;

-- Recent evaluations view: for activity feed
CREATE OR REPLACE VIEW recent_evaluations AS
SELECT
    e.id,
    e.video_id,
    v.title as video_title,
    e.rubric_name,
    r.display_name as rubric_display_name,
    e.status,
    e.evaluator,
    e.model_name,
    e.cost,
    e.completed_at,
    e.created_at
FROM evaluations e
JOIN videos v ON e.video_id = v.id
LEFT JOIN rubrics r ON e.rubric_name = r.name
ORDER BY e.created_at DESC
LIMIT 50;

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function to update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================
-- TRIGGERS
-- ============================================

-- Auto-update updated_at on videos
DROP TRIGGER IF EXISTS update_videos_updated_at ON videos;
CREATE TRIGGER update_videos_updated_at
    BEFORE UPDATE ON videos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Auto-update updated_at on evaluations
DROP TRIGGER IF EXISTS update_evaluations_updated_at ON evaluations;
CREATE TRIGGER update_evaluations_updated_at
    BEFORE UPDATE ON evaluations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Auto-update updated_at on rubrics
DROP TRIGGER IF EXISTS update_rubrics_updated_at ON rubrics;
CREATE TRIGGER update_rubrics_updated_at
    BEFORE UPDATE ON rubrics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- SEED DATA: Rubrics
-- ============================================

INSERT INTO rubrics (name, display_name, description, category, is_active, sort_order) VALUES
    ('academic', '🎓 Academic (4-Pillar Pedagogical Quality)', 'Evidence-based pedagogical quality assessment using Mayer, Bruner, Executive Function, and Bandura frameworks', 'educational', TRUE, 0),
    ('content_safety', 'Content Safety', 'Kijkwijzer-based age rating assessment for Dutch content standards', 'safety', TRUE, 1),
    ('ai_quality', 'AI Quality & Fidelity', 'Detection of AI artifacts, hallucinations, and quality issues', 'quality', TRUE, 2),
    ('media_ethics', 'Media Ethics', 'Assessment of manipulation, commercial pressure, and ethical concerns', 'ethics', TRUE, 3),
    ('production_metrics', 'Production Metrics', 'Technical measurements of video quality and production values', 'production', TRUE, 4),
    ('values', 'Values & Hot Topics', 'Analysis of values-based content and sensitive topics', 'content', TRUE, 5),
    ('educational', 'Educational Quality', 'Learning effectiveness and educational value assessment', 'educational', TRUE, 6),
    ('production', 'Production Quality', 'Comprehensive technical quality evaluation', 'production', TRUE, 7)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    category = EXCLUDED.category,
    is_active = EXCLUDED.is_active,
    sort_order = EXCLUDED.sort_order;

-- ============================================
-- REAL-TIME (Optional - Supabase feature)
-- ============================================

-- Enable real-time updates for evaluations table
-- This allows the dashboard to auto-refresh when evaluations complete
-- Uncomment if you want to use Supabase real-time subscriptions

-- ALTER PUBLICATION supabase_realtime ADD TABLE evaluations;
-- ALTER PUBLICATION supabase_realtime ADD TABLE videos;

-- ============================================
-- ROW LEVEL SECURITY (Optional)
-- ============================================

-- For now, disable RLS since this is a single-user tool
-- Enable if you want to add multi-user access control later

ALTER TABLE videos DISABLE ROW LEVEL SECURITY;
ALTER TABLE evaluations DISABLE ROW LEVEL SECURITY;
ALTER TABLE rubrics DISABLE ROW LEVEL SECURITY;

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE videos IS 'Stores metadata about ingested videos from YouTube or local files';
COMMENT ON TABLE evaluations IS 'Stores evaluation results for each rubric applied to each video';
COMMENT ON TABLE rubrics IS 'Master list of available evaluation rubrics';
COMMENT ON VIEW video_status IS 'Aggregated evaluation status for each video (used by dashboard)';
COMMENT ON VIEW rubric_completion_stats IS 'Statistics about rubric completion across all videos';
COMMENT ON VIEW recent_evaluations IS 'Most recent evaluation activity for dashboard feed';
