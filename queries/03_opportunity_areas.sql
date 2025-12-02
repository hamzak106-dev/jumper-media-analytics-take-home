-- Query 3: High Volume, Low Engagement (Opportunity Areas)
-- 
-- Finds authors and categories that post a lot but get low engagement per post
-- These are good candidates for improvement
-- 
-- Performance: Uses indexes on posts and engagements tables

-- Authors: Post Volume vs Engagement Per Post
-- Finds authors who post a lot but get low engagement per post
WITH author_stats AS (
    SELECT 
        a.author_id,
        a.name,
        a.author_category,
        COUNT(DISTINCT p.post_id) AS total_posts,
        COUNT(e.engagement_id) AS total_engagements,
        ROUND(
            COUNT(e.engagement_id)::NUMERIC / NULLIF(COUNT(DISTINCT p.post_id), 0),
            2
        ) AS avg_engagement_per_post,
        COUNT(DISTINCT DATE(p.publish_timestamp)) AS active_days
    FROM authors a
    LEFT JOIN posts p ON a.author_id = p.author_id
    LEFT JOIN engagements e ON p.post_id = e.post_id
    WHERE p.publish_timestamp >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY a.author_id, a.name, a.author_category
),
overall_avg AS (
    SELECT 
        AVG(avg_engagement_per_post) AS overall_avg_engagement
    FROM author_stats
    WHERE total_posts > 0
)
SELECT 
    as.author_id,
    as.name,
    as.author_category,
    as.total_posts,
    as.total_engagements,
    as.avg_engagement_per_post,
    oa.overall_avg_engagement,
    ROUND(
        ((as.avg_engagement_per_post - oa.overall_avg_engagement) / NULLIF(oa.overall_avg_engagement, 0)) * 100,
        2
    ) AS performance_vs_avg_percent,
    CASE 
        WHEN as.total_posts >= (SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_posts) FROM author_stats)
         AND as.avg_engagement_per_post < oa.overall_avg_engagement
        THEN 'HIGH_VOLUME_LOW_ENGAGEMENT'
        WHEN as.total_posts >= (SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_posts) FROM author_stats)
         AND as.avg_engagement_per_post >= oa.overall_avg_engagement
        THEN 'HIGH_VOLUME_HIGH_ENGAGEMENT'
        WHEN as.total_posts < (SELECT PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_posts) FROM author_stats)
        THEN 'LOW_VOLUME'
        ELSE 'MEDIUM'
    END AS opportunity_category
FROM author_stats as
CROSS JOIN overall_avg oa
WHERE as.total_posts > 0
ORDER BY as.total_posts DESC, as.avg_engagement_per_post ASC;

-- ============================================
-- 3.2 Categories: Post Volume vs Engagement Per Post
-- ============================================
-- Identifies categories with high post volume but low engagement
WITH category_stats AS (
    SELECT 
        p.category,
        COUNT(DISTINCT p.post_id) AS total_posts,
        COUNT(DISTINCT p.author_id) AS unique_authors,
        COUNT(e.engagement_id) AS total_engagements,
        ROUND(
            COUNT(e.engagement_id)::NUMERIC / NULLIF(COUNT(DISTINCT p.post_id), 0),
            2
        ) AS avg_engagement_per_post
    FROM posts p
    LEFT JOIN engagements e ON p.post_id = e.post_id
    WHERE p.publish_timestamp >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY p.category
),
overall_avg AS (
    SELECT 
        AVG(avg_engagement_per_post) AS overall_avg_engagement
    FROM category_stats
    WHERE total_posts > 0
)
SELECT 
    cs.category,
    cs.total_posts,
    cs.unique_authors,
    cs.total_engagements,
    cs.avg_engagement_per_post,
    oa.overall_avg_engagement,
    ROUND(
        ((cs.avg_engagement_per_post - oa.overall_avg_engagement) / NULLIF(oa.overall_avg_engagement, 0)) * 100,
        2
    ) AS performance_vs_avg_percent,
    CASE 
        WHEN cs.total_posts >= (SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_posts) FROM category_stats)
         AND cs.avg_engagement_per_post < oa.overall_avg_engagement
        THEN 'OPPORTUNITY'
        ELSE 'PERFORMING_WELL'
    END AS status
FROM category_stats cs
CROSS JOIN overall_avg oa
WHERE cs.total_posts > 0
ORDER BY cs.total_posts DESC, cs.avg_engagement_per_post ASC;

-- ============================================
-- 3.3 Detailed Opportunity Analysis: Top Underperformers
-- ============================================
-- Focuses on authors with high volume but low engagement
WITH author_metrics AS (
    SELECT 
        a.author_id,
        a.name,
        a.author_category,
        COUNT(DISTINCT p.post_id) AS post_count,
        COUNT(e.engagement_id) AS engagement_count,
        ROUND(
            COUNT(e.engagement_id)::NUMERIC / NULLIF(COUNT(DISTINCT p.post_id), 0),
            2
        ) AS engagement_per_post,
        MIN(p.publish_timestamp) AS first_post_date,
        MAX(p.publish_timestamp) AS last_post_date
    FROM authors a
    JOIN posts p ON a.author_id = p.author_id
    LEFT JOIN engagements e ON p.post_id = e.post_id
    WHERE p.publish_timestamp >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY a.author_id, a.name, a.author_category
    HAVING COUNT(DISTINCT p.post_id) >= 5  -- At least 5 posts
),
percentiles AS (
    SELECT 
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY post_count) AS p75_post_count,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY engagement_per_post) AS p25_engagement
    FROM author_metrics
)
SELECT 
    am.author_id,
    am.name,
    am.author_category,
    am.post_count,
    am.engagement_count,
    am.engagement_per_post,
    am.first_post_date,
    am.last_post_date,
    ROUND(
        (am.post_count::NUMERIC / NULLIF(EXTRACT(EPOCH FROM (am.last_post_date - am.first_post_date)) / 86400, 0)),
        2
    ) AS posts_per_day,
    'HIGH_VOLUME_LOW_ENGAGEMENT' AS opportunity_type
FROM author_metrics am
CROSS JOIN percentiles p
WHERE am.post_count >= p.p75_post_count
  AND am.engagement_per_post <= p.p25_engagement
ORDER BY am.post_count DESC, am.engagement_per_post ASC;

-- ============================================
-- 3.4 Engagement Rate by Post Characteristics
-- ============================================
-- Identifies if certain post characteristics correlate with low engagement
SELECT 
    CASE 
        WHEN p.has_media THEN 'With Media'
        ELSE 'No Media'
    END AS media_status,
    CASE 
        WHEN p.content_length < 1000 THEN 'Short (<1000)'
        WHEN p.content_length < 2000 THEN 'Medium (1000-2000)'
        ELSE 'Long (2000+)'
    END AS content_length_category,
    pm.is_promoted,
    COUNT(DISTINCT p.post_id) AS post_count,
    COUNT(e.engagement_id) AS total_engagements,
    ROUND(
        COUNT(e.engagement_id)::NUMERIC / NULLIF(COUNT(DISTINCT p.post_id), 0),
        2
    ) AS avg_engagement_per_post
FROM posts p
LEFT JOIN post_metadata pm ON p.post_id = pm.post_id
LEFT JOIN engagements e ON p.post_id = e.post_id
WHERE p.publish_timestamp >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY 
    CASE WHEN p.has_media THEN 'With Media' ELSE 'No Media' END,
    CASE 
        WHEN p.content_length < 1000 THEN 'Short (<1000)'
        WHEN p.content_length < 2000 THEN 'Medium (1000-2000)'
        ELSE 'Long (2000+)'
    END,
    pm.is_promoted
ORDER BY avg_engagement_per_post ASC;

-- ============================================
-- 3.5 Scatter Plot Data: Volume vs Engagement
-- ============================================
-- Provides data points for scatter plot visualization
-- X-axis: Post volume, Y-axis: Average engagement per post
SELECT 
    a.author_id,
    a.name,
    a.author_category,
    COUNT(DISTINCT p.post_id) AS post_volume,
    ROUND(
        COUNT(e.engagement_id)::NUMERIC / NULLIF(COUNT(DISTINCT p.post_id), 0),
        2
    ) AS avg_engagement_per_post,
    COUNT(e.engagement_id) AS total_engagements
FROM authors a
LEFT JOIN posts p ON a.author_id = p.author_id
LEFT JOIN engagements e ON p.post_id = e.post_id
WHERE p.publish_timestamp >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY a.author_id, a.name, a.author_category
HAVING COUNT(DISTINCT p.post_id) > 0
ORDER BY post_volume DESC;

-- Performance Notes:
-- 
-- If you run this query a lot:
-- - Consider materialized views for opportunity analysis
-- - Cache percentile calculations (they can be expensive)
-- - Pre-compute metrics in a summary table for dashboards
-- - Could add engagement_score column to posts table if needed

