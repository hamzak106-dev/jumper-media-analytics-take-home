-- Jumper Media Analytics - PostgreSQL Schema
-- 
-- Base schema with some performance improvements added

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS engagements CASCADE;
DROP TABLE IF EXISTS post_metadata CASCADE;
DROP TABLE IF EXISTS posts CASCADE;
DROP TABLE IF EXISTS authors CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Authors table
CREATE TABLE authors (
    author_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    joined_date DATE NOT NULL,
    author_category VARCHAR(100) NOT NULL
);

-- Users table (optional, for user demographics)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    signup_date DATE,
    country VARCHAR(100),
    user_segment VARCHAR(50)
);

-- Posts table
CREATE TABLE posts (
    post_id SERIAL PRIMARY KEY,
    author_id INTEGER NOT NULL REFERENCES authors(author_id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    publish_timestamp TIMESTAMP NOT NULL,
    title VARCHAR(500) NOT NULL,
    content_length INTEGER NOT NULL,
    has_media BOOLEAN DEFAULT FALSE
);

-- Post metadata table
CREATE TABLE post_metadata (
    post_id INTEGER PRIMARY KEY REFERENCES posts(post_id) ON DELETE CASCADE,
    tags TEXT[], -- Array of tags
    is_promoted BOOLEAN DEFAULT FALSE,
    language VARCHAR(10) DEFAULT 'en'
);

-- Engagements table (high volume - consider partitioning for scale)
CREATE TABLE engagements (
    engagement_id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES posts(post_id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('view', 'like', 'comment', 'share')),
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    engaged_timestamp TIMESTAMP NOT NULL
);

-- Performance Optimizations
-- 
-- Indexes for foreign keys (helps with joins)
CREATE INDEX idx_posts_author_id ON posts(author_id);
CREATE INDEX idx_engagements_post_id ON engagements(post_id);
CREATE INDEX idx_engagements_user_id ON engagements(user_id);

-- Composite indexes for common query patterns
-- These make queries much faster when filtering by these columns together

-- For author performance queries over time
CREATE INDEX idx_posts_author_timestamp ON posts(author_id, publish_timestamp DESC);

-- For category trends
CREATE INDEX idx_posts_category_timestamp ON posts(category, publish_timestamp DESC);

-- For engagement queries - this one is most important for analytics
CREATE INDEX idx_engagements_post_type_timestamp ON engagements(post_id, type, engaged_timestamp DESC);

-- For time-based analysis
CREATE INDEX idx_engagements_timestamp ON engagements(engaged_timestamp DESC);

-- For filtering by engagement type
CREATE INDEX idx_engagements_type ON engagements(type);

-- Partitioning Strategy (for scale)
-- 
-- For really large datasets (millions of engagements), you can partition by month
-- This is commented out since we don't need it yet, but here's how to do it:
/*
-- Create parent table without primary key constraint
ALTER TABLE engagements DROP CONSTRAINT engagements_pkey;
ALTER TABLE engagements ADD PRIMARY KEY (engagement_id, engaged_timestamp);

-- Create monthly partitions
CREATE TABLE engagements_2025_01 PARTITION OF engagements
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE engagements_2025_02 PARTITION OF engagements
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
-- ... continue for other months
*/

-- Materialized Views (for pre-computed aggregates)
-- 
-- These store daily aggregates so dashboard queries run faster
-- You need to refresh them periodically (after data loads, or hourly in production)

-- Daily engagement aggregates by post
CREATE MATERIALIZED VIEW daily_post_engagement AS
SELECT 
    DATE(engaged_timestamp) AS engagement_date,
    post_id,
    type,
    COUNT(*) AS engagement_count
FROM engagements
GROUP BY DATE(engaged_timestamp), post_id, type;

CREATE INDEX idx_daily_post_engagement_date ON daily_post_engagement(engagement_date);
CREATE INDEX idx_daily_post_engagement_post ON daily_post_engagement(post_id);

-- Daily engagement aggregates by author
CREATE MATERIALIZED VIEW daily_author_engagement AS
SELECT 
    DATE(e.engaged_timestamp) AS engagement_date,
    p.author_id,
    e.type,
    COUNT(*) AS engagement_count
FROM engagements e
JOIN posts p ON e.post_id = p.post_id
GROUP BY DATE(e.engaged_timestamp), p.author_id, e.type;

CREATE INDEX idx_daily_author_engagement_date ON daily_author_engagement(engagement_date);
CREATE INDEX idx_daily_author_engagement_author ON daily_author_engagement(author_id);

-- Refresh materialized views after data loads:
-- REFRESH MATERIALIZED VIEW daily_post_engagement;
-- REFRESH MATERIALIZED VIEW daily_author_engagement;

-- Helper Functions

-- Calculates engagement score for a post (weighted: views=1, likes=2, comments=3, shares=4)
CREATE OR REPLACE FUNCTION get_post_engagement_score(p_post_id INTEGER)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT 
            COUNT(*) FILTER (WHERE type = 'view') * 1 +
            COUNT(*) FILTER (WHERE type = 'like') * 2 +
            COUNT(*) FILTER (WHERE type = 'comment') * 3 +
            COUNT(*) FILTER (WHERE type = 'share') * 4
        FROM engagements
        WHERE post_id = p_post_id
    );
END;
$$ LANGUAGE plpgsql;

-- Table Comments

COMMENT ON TABLE authors IS 'Author information including category and join date';
COMMENT ON TABLE posts IS 'Post content with metadata including publish time and content length';
COMMENT ON TABLE engagements IS 'User engagement events (views, likes, comments, shares)';
COMMENT ON TABLE post_metadata IS 'Extended post metadata including tags, promotion status, and language';
COMMENT ON TABLE users IS 'User demographics for segmentation analysis';

COMMENT ON INDEX idx_engagements_post_type_timestamp IS 'Most important index for engagement analytics queries';
COMMENT ON INDEX idx_posts_author_timestamp IS 'Speeds up author performance queries over time';
COMMENT ON INDEX idx_posts_category_timestamp IS 'Speeds up category trend analysis';

