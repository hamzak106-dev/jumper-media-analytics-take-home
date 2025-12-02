-- Query 2: Time-of-Day / Day-of-Week Patterns
-- 
-- Finds when engagement happens most - by hour of day and day of week
-- Helps identify best times to post
-- 
-- Performance: Uses timestamp index for fast filtering

-- Engagement by Hour of Day
SELECT 
    EXTRACT(HOUR FROM engaged_timestamp) AS hour_of_day,
    COUNT(*) AS total_engagements,
    COUNT(*) FILTER (WHERE type = 'view') AS views,
    COUNT(*) FILTER (WHERE type = 'like') AS likes,
    COUNT(*) FILTER (WHERE type = 'comment') AS comments,
    COUNT(*) FILTER (WHERE type = 'share') AS shares,
    ROUND(
        (COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER ()) * 100,
        2
    ) AS percentage_of_total
FROM engagements
GROUP BY EXTRACT(HOUR FROM engaged_timestamp)
ORDER BY hour_of_day;

-- Engagement by Day of Week
SELECT 
    TO_CHAR(engaged_timestamp, 'Day') AS day_of_week,
    EXTRACT(DOW FROM engaged_timestamp) AS day_number, -- 0=Sunday, 6=Saturday
    COUNT(*) AS total_engagements,
    COUNT(*) FILTER (WHERE type = 'view') AS views,
    COUNT(*) FILTER (WHERE type = 'like') AS likes,
    COUNT(*) FILTER (WHERE type = 'comment') AS comments,
    COUNT(*) FILTER (WHERE type = 'share') AS shares,
    ROUND(
        (COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER ()) * 100,
        2
    ) AS percentage_of_total
FROM engagements
GROUP BY TO_CHAR(engaged_timestamp, 'Day'), EXTRACT(DOW FROM engaged_timestamp)
ORDER BY day_number;

-- Heatmap Data: Engagement by Hour and Day of Week
-- Use this for heatmap visualization (day of week vs hour of day)
SELECT 
    EXTRACT(DOW FROM engaged_timestamp) AS day_of_week, -- 0=Sunday, 6=Saturday
    EXTRACT(HOUR FROM engaged_timestamp) AS hour_of_day,
    COUNT(*) AS engagement_count,
    COUNT(*) FILTER (WHERE type = 'view') AS views,
    COUNT(*) FILTER (WHERE type = 'like') AS likes,
    COUNT(*) FILTER (WHERE type = 'comment') AS comments,
    COUNT(*) FILTER (WHERE type = 'share') AS shares
FROM engagements
GROUP BY EXTRACT(DOW FROM engaged_timestamp), EXTRACT(HOUR FROM engaged_timestamp)
ORDER BY day_of_week, hour_of_day;

-- ============================================
-- 2.4 Peak Engagement Times (Last 30 Days)
-- ============================================
SELECT 
    EXTRACT(HOUR FROM engaged_timestamp) AS hour_of_day,
    EXTRACT(DOW FROM engaged_timestamp) AS day_of_week,
    COUNT(*) AS engagement_count,
    ROUND(AVG(COUNT(*)) OVER (PARTITION BY EXTRACT(HOUR FROM engaged_timestamp)), 2) AS avg_for_hour,
    ROUND(AVG(COUNT(*)) OVER (PARTITION BY EXTRACT(DOW FROM engaged_timestamp)), 2) AS avg_for_day
FROM engagements
WHERE engaged_timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY EXTRACT(HOUR FROM engaged_timestamp), EXTRACT(DOW FROM engaged_timestamp)
ORDER BY engagement_count DESC
LIMIT 20;

-- ============================================
-- 2.5 Engagement Patterns by Category and Time
-- ============================================
-- Shows if different categories have different engagement patterns
SELECT 
    p.category,
    EXTRACT(HOUR FROM e.engaged_timestamp) AS hour_of_day,
    COUNT(*) AS engagement_count,
    ROUND(
        (COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER (PARTITION BY p.category)) * 100,
        2
    ) AS percentage_within_category
FROM engagements e
JOIN posts p ON e.post_id = p.post_id
GROUP BY p.category, EXTRACT(HOUR FROM e.engaged_timestamp)
ORDER BY p.category, hour_of_day;

-- ============================================
-- 2.6 Time-to-Engagement Analysis
-- ============================================
-- How long after publishing do engagements occur?
SELECT 
    EXTRACT(HOUR FROM (e.engaged_timestamp - p.publish_timestamp)) AS hours_after_publish,
    COUNT(*) AS engagement_count,
    COUNT(*) FILTER (WHERE e.type = 'view') AS views,
    COUNT(*) FILTER (WHERE e.type = 'like') AS likes,
    COUNT(*) FILTER (WHERE e.type = 'comment') AS comments,
    COUNT(*) FILTER (WHERE e.type = 'share') AS shares
FROM engagements e
JOIN posts p ON e.post_id = p.post_id
WHERE e.engaged_timestamp >= p.publish_timestamp
  AND EXTRACT(HOUR FROM (e.engaged_timestamp - p.publish_timestamp)) <= 168 -- First week
GROUP BY EXTRACT(HOUR FROM (e.engaged_timestamp - p.publish_timestamp))
ORDER BY hours_after_publish;

-- Performance Notes:
-- 
-- If queries are slow, you can:
-- - Add computed columns for hour/day and index them
-- - Use materialized views with pre-computed hour/day
-- - Refresh materialized views hourly for dashboards

