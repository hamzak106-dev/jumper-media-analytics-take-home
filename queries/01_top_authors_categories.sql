-- Query 1: Top Authors/Categories by Engagement
-- 
-- Finds top authors and categories by engagement for different time periods
-- (last 7 days, 30 days, 90 days)
-- 
-- Performance: Uses indexes on engagements and posts tables for faster queries

-- Top Authors by Engagement (Last 30 Days)
SELECT 
    a.author_id,
    a.name,
    a.author_category,
    COUNT(*) FILTER (WHERE e.type = 'view') AS total_views,
    COUNT(*) FILTER (WHERE e.type = 'like') AS total_likes,
    COUNT(*) FILTER (WHERE e.type = 'comment') AS total_comments,
    COUNT(*) FILTER (WHERE e.type = 'share') AS total_shares,
    COUNT(*) AS total_engagements,
    COUNT(DISTINCT e.post_id) AS posts_with_engagement,
    ROUND(
        COUNT(*)::NUMERIC / NULLIF(COUNT(DISTINCT e.post_id), 0),
        2
    ) AS avg_engagement_per_post
FROM authors a
JOIN posts p ON a.author_id = p.author_id
JOIN engagements e ON p.post_id = e.post_id
WHERE e.engaged_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY a.author_id, a.name, a.author_category
ORDER BY total_engagements DESC
LIMIT 20;

-- Top Authors by Engagement (Last 7 Days)
SELECT 
    a.author_id,
    a.name,
    a.author_category,
    COUNT(*) FILTER (WHERE e.type = 'view') AS total_views,
    COUNT(*) FILTER (WHERE e.type = 'like') AS total_likes,
    COUNT(*) FILTER (WHERE e.type = 'comment') AS total_comments,
    COUNT(*) FILTER (WHERE e.type = 'share') AS total_shares,
    COUNT(*) AS total_engagements,
    ROUND(
        COUNT(*)::NUMERIC / NULLIF(COUNT(DISTINCT e.post_id), 0),
        2
    ) AS avg_engagement_per_post
FROM authors a
JOIN posts p ON a.author_id = p.author_id
JOIN engagements e ON p.post_id = e.post_id
WHERE e.engaged_timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY a.author_id, a.name, a.author_category
ORDER BY total_engagements DESC
LIMIT 20;

-- Top Authors by Engagement (Last 90 Days)
SELECT 
    a.author_id,
    a.name,
    a.author_category,
    COUNT(*) FILTER (WHERE e.type = 'view') AS total_views,
    COUNT(*) FILTER (WHERE e.type = 'like') AS total_likes,
    COUNT(*) FILTER (WHERE e.type = 'comment') AS total_comments,
    COUNT(*) FILTER (WHERE e.type = 'share') AS total_shares,
    COUNT(*) AS total_engagements,
    COUNT(DISTINCT e.post_id) AS posts_with_engagement,
    ROUND(
        COUNT(*)::NUMERIC / NULLIF(COUNT(DISTINCT e.post_id), 0),
        2
    ) AS avg_engagement_per_post
FROM authors a
JOIN posts p ON a.author_id = p.author_id
JOIN engagements e ON p.post_id = e.post_id
WHERE e.engaged_timestamp >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY a.author_id, a.name, a.author_category
ORDER BY total_engagements DESC
LIMIT 20;

-- Top Categories by Engagement (Last 30 Days)
SELECT 
    p.category,
    COUNT(*) FILTER (WHERE e.type = 'view') AS total_views,
    COUNT(*) FILTER (WHERE e.type = 'like') AS total_likes,
    COUNT(*) FILTER (WHERE e.type = 'comment') AS total_comments,
    COUNT(*) FILTER (WHERE e.type = 'share') AS total_shares,
    COUNT(*) AS total_engagements,
    COUNT(DISTINCT e.post_id) AS posts_with_engagement,
    COUNT(DISTINCT p.author_id) AS unique_authors,
    ROUND(
        COUNT(*)::NUMERIC / NULLIF(COUNT(DISTINCT e.post_id), 0),
        2
    ) AS avg_engagement_per_post,
    ROUND(
        (COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER ()) * 100,
        2
    ) AS engagement_percentage
FROM posts p
JOIN engagements e ON p.post_id = e.post_id
WHERE e.engaged_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY p.category
ORDER BY total_engagements DESC;

-- Author Engagement Trends (Monthly)
-- Shows how engagement changes over time for top authors
SELECT 
    DATE_TRUNC('month', e.engaged_timestamp) AS month,
    a.author_id,
    a.name,
    COUNT(*) AS total_engagements,
    COUNT(*) FILTER (WHERE e.type = 'view') AS views,
    COUNT(*) FILTER (WHERE e.type = 'like') AS likes,
    COUNT(*) FILTER (WHERE e.type = 'comment') AS comments,
    COUNT(*) FILTER (WHERE e.type = 'share') AS shares
FROM authors a
JOIN posts p ON a.author_id = p.author_id
JOIN engagements e ON p.post_id = e.post_id
WHERE e.engaged_timestamp >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY DATE_TRUNC('month', e.engaged_timestamp), a.author_id, a.name
ORDER BY month DESC, total_engagements DESC;

-- Performance Notes:
-- 
-- To check query performance, run: EXPLAIN ANALYZE [query]
-- 
-- For large datasets, you might want to:
-- - Use materialized views (daily_author_engagement) instead
-- - Partition engagements table by month
-- - Add more specific indexes if needed

