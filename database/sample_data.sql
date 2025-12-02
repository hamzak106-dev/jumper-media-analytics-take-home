-- Jumper Media Analytics - Sample Data
-- Base sample data as specified in requirements

-- Insert authors
INSERT INTO authors (author_id, name, joined_date, author_category) VALUES
(1, 'Alice', '2020-01-14', 'Tech'),
(2, 'Bob', '2019-06-30', 'Lifestyle'),
(3, 'Carlos', '2021-11-05', 'Tech');

-- Insert posts
INSERT INTO posts (post_id, author_id, category, publish_timestamp, title, content_length, has_media) VALUES
(101, 1, 'Tech', '2025-08-01 10:15:00', 'Deep Dive into X', 1200, true),
(102, 2, 'Lifestyle', '2025-08-02 17:30:00', '5 Morning Routines', 800, false),
(103, 3, 'Tech', '2025-08-03 08:45:00', 'Why we love SQL', 950, true);

-- Insert sample users (before engagements due to foreign key)
INSERT INTO users (user_id, signup_date, country, user_segment) VALUES
(501, '2025-01-10', 'US', 'free'),
(502, '2025-02-12', 'UK', 'subscriber'),
(503, '2024-12-05', 'US', 'trial'),
(504, '2025-03-20', 'CA', 'subscriber'),
(505, '2025-04-15', 'US', 'free');

-- Insert engagements
INSERT INTO engagements (engagement_id, post_id, type, user_id, engaged_timestamp) VALUES
(2001, 101, 'view', 501, '2025-08-01 10:16:00'),
(2002, 101, 'like', 502, '2025-08-01 10:17:00'),
(2003, 102, 'comment', 503, '2025-08-02 17:45:00'),
(2004, 101, 'share', 504, '2025-08-01 11:00:00'),
(2005, 103, 'view', 505, '2025-08-03 09:00:00');

-- Insert post metadata
INSERT INTO post_metadata (post_id, tags, is_promoted, language) VALUES
(101, ARRAY['SQL', 'Optimization'], false, 'en'),
(102, ARRAY['Wellness', 'Morning'], true, 'en'),
(103, ARRAY['SQL', 'Postgres', 'Tips'], false, 'en');

-- Refresh materialized views after data load
REFRESH MATERIALIZED VIEW daily_post_engagement;
REFRESH MATERIALIZED VIEW daily_author_engagement;

