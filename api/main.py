"""
Jumper Media Analytics API
FastAPI application for engagement analytics endpoints
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Jumper Media Analytics API",
    description="API for engagement analytics and trends",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'jumper_media'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'port': os.getenv('DB_PORT', '5432')
}


def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)


# Response Models
class EngagementTrend(BaseModel):
    date: str
    views: int
    likes: int
    comments: int
    shares: int
    total: int


class PostTrendsResponse(BaseModel):
    post_id: int
    post_title: str
    current_period: List[EngagementTrend]
    previous_period: List[EngagementTrend]
    change_percent: float


class AuthorTrendsResponse(BaseModel):
    author_id: int
    author_name: str
    current_period: List[EngagementTrend]
    previous_period: List[EngagementTrend]
    change_percent: float


class SummaryMetrics(BaseModel):
    total_authors: int
    total_posts: int
    total_engagements: int
    total_views: int
    total_likes: int
    total_comments: int
    total_shares: int
    avg_engagement_per_post: float


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Jumper Media Analytics API",
        "version": "1.0.0",
        "endpoints": {
            "post_trends": "/api/engagement/trends/post/{post_id}",
            "author_trends": "/api/engagement/trends/author/{author_id}",
            "summary": "/api/analytics/summary"
        }
    }


@app.get("/api/engagement/trends/post/{post_id}", response_model=PostTrendsResponse)
async def get_post_trends(post_id: int, days: int = 7):
    """
    Get engagement trends for a specific post.
    Compares last N days (default 7) vs previous N days.
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get post title
        cursor.execute("SELECT title FROM posts WHERE post_id = %s", (post_id,))
        post = cursor.fetchone()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post_title = post['title']
        
        # Current period (last N days)
        current_start = datetime.now() - timedelta(days=days)
        current_query = """
        SELECT 
            DATE(engaged_timestamp) AS date,
            COUNT(*) FILTER (WHERE type = 'view') AS views,
            COUNT(*) FILTER (WHERE type = 'like') AS likes,
            COUNT(*) FILTER (WHERE type = 'comment') AS comments,
            COUNT(*) FILTER (WHERE type = 'share') AS shares,
            COUNT(*) AS total
        FROM engagements
        WHERE post_id = %s 
          AND engaged_timestamp >= %s
        GROUP BY DATE(engaged_timestamp)
        ORDER BY date
        """
        cursor.execute(current_query, (post_id, current_start))
        current_period = cursor.fetchall()
        
        # Previous period (N days before that)
        previous_start = current_start - timedelta(days=days)
        previous_query = """
        SELECT 
            DATE(engaged_timestamp) AS date,
            COUNT(*) FILTER (WHERE type = 'view') AS views,
            COUNT(*) FILTER (WHERE type = 'like') AS likes,
            COUNT(*) FILTER (WHERE type = 'comment') AS comments,
            COUNT(*) FILTER (WHERE type = 'share') AS shares,
            COUNT(*) AS total
        FROM engagements
        WHERE post_id = %s 
          AND engaged_timestamp >= %s 
          AND engaged_timestamp < %s
        GROUP BY DATE(engaged_timestamp)
        ORDER BY date
        """
        cursor.execute(previous_query, (post_id, previous_start, current_start))
        previous_period = cursor.fetchall()
        
        # Calculate total engagement for comparison
        current_total = sum(row['total'] for row in current_period)
        previous_total = sum(row['total'] for row in previous_period)
        
        change_percent = 0.0
        if previous_total > 0:
            change_percent = ((current_total - previous_total) / previous_total) * 100
        
        # Format response
        current_trends = [
            EngagementTrend(
                date=str(row['date']),
                views=row['views'],
                likes=row['likes'],
                comments=row['comments'],
                shares=row['shares'],
                total=row['total']
            )
            for row in current_period
        ]
        
        previous_trends = [
            EngagementTrend(
                date=str(row['date']),
                views=row['views'],
                likes=row['likes'],
                comments=row['comments'],
                shares=row['shares'],
                total=row['total']
            )
            for row in previous_period
        ]
        
        return PostTrendsResponse(
            post_id=post_id,
            post_title=post_title,
            current_period=current_trends,
            previous_period=previous_trends,
            change_percent=round(change_percent, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/api/engagement/trends/author/{author_id}", response_model=AuthorTrendsResponse)
async def get_author_trends(author_id: int, days: int = 7):
    """
    Get engagement trends for a specific author.
    Compares last N days (default 7) vs previous N days.
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get author name
        cursor.execute("SELECT name FROM authors WHERE author_id = %s", (author_id,))
        author = cursor.fetchone()
        if not author:
            raise HTTPException(status_code=404, detail="Author not found")
        
        author_name = author['name']
        
        # Current period (last N days)
        current_start = datetime.now() - timedelta(days=days)
        current_query = """
        SELECT 
            DATE(e.engaged_timestamp) AS date,
            COUNT(*) FILTER (WHERE e.type = 'view') AS views,
            COUNT(*) FILTER (WHERE e.type = 'like') AS likes,
            COUNT(*) FILTER (WHERE e.type = 'comment') AS comments,
            COUNT(*) FILTER (WHERE e.type = 'share') AS shares,
            COUNT(*) AS total
        FROM engagements e
        JOIN posts p ON e.post_id = p.post_id
        WHERE p.author_id = %s 
          AND e.engaged_timestamp >= %s
        GROUP BY DATE(e.engaged_timestamp)
        ORDER BY date
        """
        cursor.execute(current_query, (author_id, current_start))
        current_period = cursor.fetchall()
        
        # Previous period (N days before that)
        previous_start = current_start - timedelta(days=days)
        previous_query = """
        SELECT 
            DATE(e.engaged_timestamp) AS date,
            COUNT(*) FILTER (WHERE e.type = 'view') AS views,
            COUNT(*) FILTER (WHERE e.type = 'like') AS likes,
            COUNT(*) FILTER (WHERE e.type = 'comment') AS comments,
            COUNT(*) FILTER (WHERE e.type = 'share') AS shares,
            COUNT(*) AS total
        FROM engagements e
        JOIN posts p ON e.post_id = p.post_id
        WHERE p.author_id = %s 
          AND e.engaged_timestamp >= %s 
          AND e.engaged_timestamp < %s
        GROUP BY DATE(e.engaged_timestamp)
        ORDER BY date
        """
        cursor.execute(previous_query, (author_id, previous_start, current_start))
        previous_period = cursor.fetchall()
        
        # Calculate total engagement for comparison
        current_total = sum(row['total'] for row in current_period)
        previous_total = sum(row['total'] for row in previous_period)
        
        change_percent = 0.0
        if previous_total > 0:
            change_percent = ((current_total - previous_total) / previous_total) * 100
        
        # Format response
        current_trends = [
            EngagementTrend(
                date=str(row['date']),
                views=row['views'],
                likes=row['likes'],
                comments=row['comments'],
                shares=row['shares'],
                total=row['total']
            )
            for row in current_period
        ]
        
        previous_trends = [
            EngagementTrend(
                date=str(row['date']),
                views=row['views'],
                likes=row['likes'],
                comments=row['comments'],
                shares=row['shares'],
                total=row['total']
            )
            for row in previous_period
        ]
        
        return AuthorTrendsResponse(
            author_id=author_id,
            author_name=author_name,
            current_period=current_trends,
            previous_period=previous_trends,
            change_percent=round(change_percent, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/api/analytics/summary", response_model=SummaryMetrics)
async def get_analytics_summary(days: int = 30):
    """
    Get overall analytics summary for the last N days (default 30).
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT 
            COUNT(DISTINCT a.author_id) AS total_authors,
            COUNT(DISTINCT p.post_id) AS total_posts,
            COUNT(e.engagement_id) AS total_engagements,
            COUNT(*) FILTER (WHERE e.type = 'view') AS total_views,
            COUNT(*) FILTER (WHERE e.type = 'like') AS total_likes,
            COUNT(*) FILTER (WHERE e.type = 'comment') AS total_comments,
            COUNT(*) FILTER (WHERE e.type = 'share') AS total_shares,
            ROUND(COUNT(e.engagement_id)::NUMERIC / NULLIF(COUNT(DISTINCT p.post_id), 0), 2) AS avg_engagement_per_post
        FROM authors a
        LEFT JOIN posts p ON a.author_id = p.author_id
        LEFT JOIN engagements e ON p.post_id = e.post_id
        WHERE p.publish_timestamp >= %s OR p.publish_timestamp IS NULL
        """
        cursor.execute(query, (start_date,))
        result = cursor.fetchone()
        
        return SummaryMetrics(
            total_authors=result['total_authors'] or 0,
            total_posts=result['total_posts'] or 0,
            total_engagements=result['total_engagements'] or 0,
            total_views=result['total_views'] or 0,
            total_likes=result['total_likes'] or 0,
            total_comments=result['total_comments'] or 0,
            total_shares=result['total_shares'] or 0,
            avg_engagement_per_post=float(result['avg_engagement_per_post'] or 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

