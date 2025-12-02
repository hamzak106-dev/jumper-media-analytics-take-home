#!/usr/bin/env python3
"""
Generate larger synthetic dataset for performance testing and analysis.
This script creates realistic data distributions for testing queries at scale.
"""

import psycopg2
import random
from datetime import datetime, timedelta
from faker import Faker

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'jumper_media',
    'user': 'postgres',
    'password': 'postgres'  # Update with your password
}

# Dataset size configuration
NUM_AUTHORS = 50
NUM_POSTS = 10000
NUM_ENGAGEMENTS = 100000
NUM_USERS = 5000

# Categories and engagement patterns
CATEGORIES = ['Tech', 'Lifestyle', 'Business', 'Health', 'Entertainment', 'Education']
AUTHOR_CATEGORIES = ['Tech', 'Lifestyle', 'Business', 'Health', 'Entertainment']
COUNTRIES = ['US', 'UK', 'CA', 'AU', 'DE', 'FR', 'JP', 'BR', 'IN', 'MX']
USER_SEGMENTS = ['free', 'subscriber', 'trial', 'premium']

fake = Faker()

def get_db_connection():
    """Create database connection."""
    return psycopg2.connect(**DB_CONFIG)

def generate_authors(conn, num_authors):
    """Generate author data."""
    cursor = conn.cursor()
    
    # Clear existing authors (keep IDs 1-3 from sample data)
    cursor.execute("DELETE FROM authors WHERE author_id > 3")
    
    for i in range(4, num_authors + 4):
        name = fake.name()
        joined_date = fake.date_between(start_date='-5y', end_date='today')
        category = random.choice(AUTHOR_CATEGORIES)
        
        cursor.execute(
            "INSERT INTO authors (author_id, name, joined_date, author_category) VALUES (%s, %s, %s, %s)",
            (i, name, joined_date, category)
        )
    
    conn.commit()
    cursor.close()
    print(f"Generated {num_authors} authors")

def generate_users(conn, num_users):
    """Generate user data."""
    cursor = conn.cursor()
    
    # Clear existing users (keep IDs 501-505 from sample data)
    cursor.execute("DELETE FROM users WHERE user_id > 505")
    
    for i in range(506, num_users + 506):
        signup_date = fake.date_between(start_date='-2y', end_date='today')
        country = random.choice(COUNTRIES)
        segment = random.choice(USER_SEGMENTS)
        
        cursor.execute(
            "INSERT INTO users (user_id, signup_date, country, user_segment) VALUES (%s, %s, %s, %s)",
            (i, signup_date, country, segment)
        )
    
    conn.commit()
    cursor.close()
    print(f"Generated {num_users} users")

def generate_posts(conn, num_posts):
    """Generate post data with realistic patterns."""
    cursor = conn.cursor()
    
    # Get author IDs
    cursor.execute("SELECT author_id FROM authors")
    author_ids = [row[0] for row in cursor.fetchall()]
    
    # Clear existing posts (keep IDs 101-103 from sample data)
    cursor.execute("DELETE FROM posts WHERE post_id > 103")
    cursor.execute("DELETE FROM post_metadata WHERE post_id > 103")
    
    # Generate posts with realistic time distribution
    start_date = datetime.now() - timedelta(days=180)  # Last 6 months
    
    for i in range(104, num_posts + 104):
        author_id = random.choice(author_ids)
        
        # Get author's category, but allow some variation
        cursor.execute("SELECT author_category FROM authors WHERE author_id = %s", (author_id,))
        author_cat = cursor.fetchone()[0]
        category = author_cat if random.random() > 0.2 else random.choice(CATEGORIES)
        
        # Realistic publish times (more posts during business hours)
        hours = random.choices(
            range(24),
            weights=[1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 2, 1, 1, 1, 1, 1, 1]
        )[0]
        minutes = random.randint(0, 59)
        
        publish_date = start_date + timedelta(
            days=random.randint(0, 180),
            hours=hours,
            minutes=minutes
        )
        
        title = fake.sentence(nb_words=6).rstrip('.')
        content_length = random.randint(500, 3000)
        has_media = random.random() > 0.4  # 60% have media
        
        cursor.execute(
            """INSERT INTO posts (post_id, author_id, category, publish_timestamp, title, content_length, has_media)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (i, author_id, category, publish_date, title, content_length, has_media)
        )
        
        # Generate metadata
        num_tags = random.randint(1, 4)
        tags = [fake.word().capitalize() for _ in range(num_tags)]
        is_promoted = random.random() > 0.85  # 15% promoted
        language = 'en'  # Simplified
        
        cursor.execute(
            "INSERT INTO post_metadata (post_id, tags, is_promoted, language) VALUES (%s, %s, %s, %s)",
            (i, tags, is_promoted, language)
        )
    
    conn.commit()
    cursor.close()
    print(f"Generated {num_posts} posts")

def generate_engagements(conn, num_engagements):
    """Generate engagement data with realistic patterns."""
    cursor = conn.cursor()
    
    # Get post IDs and publish times
    cursor.execute("SELECT post_id, publish_timestamp FROM posts")
    posts = cursor.fetchall()
    
    # Get user IDs
    cursor.execute("SELECT user_id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]
    
    # Clear existing engagements (keep IDs 2001-2005 from sample data)
    cursor.execute("DELETE FROM engagements WHERE engagement_id > 2005")
    
    engagement_types = ['view', 'like', 'comment', 'share']
    # Engagement type distribution (views are most common)
    type_weights = [0.7, 0.2, 0.07, 0.03]
    
    # Generate engagements with realistic time patterns
    for i in range(2006, num_engagements + 2006):
        post_id, publish_time = random.choice(posts)
        engagement_type = random.choices(engagement_types, weights=type_weights)[0]
        user_id = random.choice(user_ids) if random.random() > 0.1 else None  # 10% anonymous
        
        # Engagement happens after publish, with most happening within first 48 hours
        hours_after_publish = random.expovariate(0.1)  # Exponential decay
        hours_after_publish = min(hours_after_publish, 720)  # Cap at 30 days
        
        engaged_time = publish_time + timedelta(hours=hours_after_publish)
        
        # Add some randomness to hour of day (more engagement during peak hours)
        hour_adjustment = random.choices(
            range(-3, 4),
            weights=[1, 2, 3, 4, 3, 2, 1]
        )[0]
        engaged_time = engaged_time + timedelta(hours=hour_adjustment)
        
        cursor.execute(
            """INSERT INTO engagements (engagement_id, post_id, type, user_id, engaged_timestamp)
               VALUES (%s, %s, %s, %s, %s)""",
            (i, post_id, engagement_type, user_id, engaged_time)
        )
        
        # Batch commit for performance
        if i % 1000 == 0:
            conn.commit()
            print(f"Generated {i - 2005} engagements...")
    
    conn.commit()
    cursor.close()
    print(f"Generated {num_engagements} engagements")

def refresh_materialized_views(conn):
    """Refresh materialized views after data generation."""
    cursor = conn.cursor()
    cursor.execute("REFRESH MATERIALIZED VIEW daily_post_engagement")
    cursor.execute("REFRESH MATERIALIZED VIEW daily_author_engagement")
    conn.commit()
    cursor.close()
    print("Refreshed materialized views")

def main():
    """Main function to generate all data."""
    print("Starting large dataset generation...")
    print(f"Configuration: {NUM_AUTHORS} authors, {NUM_POSTS} posts, {NUM_ENGAGEMENTS} engagements, {NUM_USERS} users")
    
    try:
        conn = get_db_connection()
        
        print("\n1. Generating authors...")
        generate_authors(conn, NUM_AUTHORS)
        
        print("\n2. Generating users...")
        generate_users(conn, NUM_USERS)
        
        print("\n3. Generating posts...")
        generate_posts(conn, NUM_POSTS)
        
        print("\n4. Generating engagements...")
        generate_engagements(conn, NUM_ENGAGEMENTS)
        
        print("\n5. Refreshing materialized views...")
        refresh_materialized_views(conn)
        
        conn.close()
        print("\n✅ Dataset generation complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()

