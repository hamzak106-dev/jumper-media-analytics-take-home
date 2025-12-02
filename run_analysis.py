#!/usr/bin/env python3
"""
Script to run the analysis notebook programmatically
This executes all the key queries and generates visualizations
"""

import sys
import os

# Add analysis directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analysis'))

import pandas as pd
import psycopg2
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

# Import config
from config import DB_CONFIG

# Database connection helper
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def execute_query(query, connection=None):
    """Execute SQL query and return DataFrame"""
    if connection is None:
        conn = get_db_connection()
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    else:
        return pd.read_sql_query(query, connection)

def main():
    print("=" * 60)
    print("Jumper Media Analytics - Running Full Analysis")
    print("=" * 60)
    
    # Create visualizations directory
    viz_dir = os.path.join(os.path.dirname(__file__), 'visualizations')
    os.makedirs(viz_dir, exist_ok=True)
    
    conn = get_db_connection()
    
    try:
        # 1. Executive Summary
        print("\n1. Generating Executive Summary...")
        summary_query = """
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
        WHERE p.publish_timestamp >= CURRENT_DATE - INTERVAL '365 days'
        """
        summary = execute_query(summary_query, conn)
        print("✅ Summary generated")
        print(summary.to_string(index=False))
        
        # 2. Top Authors
        print("\n2. Analyzing Top Authors...")
        top_authors_query = """
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
            ROUND(COUNT(*)::NUMERIC / NULLIF(COUNT(DISTINCT e.post_id), 0), 2) AS avg_engagement_per_post
        FROM authors a
        JOIN posts p ON a.author_id = p.author_id
        JOIN engagements e ON p.post_id = e.post_id
        WHERE e.engaged_timestamp >= CURRENT_DATE - INTERVAL '365 days'
        GROUP BY a.author_id, a.name, a.author_category
        ORDER BY total_engagements DESC
        LIMIT 20
        """
        top_authors = execute_query(top_authors_query, conn)
        print(f"✅ Found {len(top_authors)} authors with engagements")
        
        if len(top_authors) > 0:
            # Create visualization
            fig, ax = plt.subplots(figsize=(14, 8))
            top_10 = top_authors.head(10)
            x = range(len(top_10))
            ax.bar(x, top_10['total_engagements'], width=0.6, color='steelblue')
            ax.set_xlabel('Author', fontsize=12)
            ax.set_ylabel('Total Engagements', fontsize=12)
            ax.set_title('Top Authors by Total Engagement', fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(top_10['name'], rotation=45, ha='right')
            ax.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(viz_dir, 'top_authors.png'), dpi=300, bbox_inches='tight')
            plt.close()
            print("✅ Saved: visualizations/top_authors.png")
        
        # 3. Time Patterns
        print("\n3. Analyzing Time Patterns...")
        hour_query = """
        SELECT 
            EXTRACT(HOUR FROM engaged_timestamp) AS hour_of_day,
            COUNT(*) AS total_engagements
        FROM engagements
        GROUP BY EXTRACT(HOUR FROM engaged_timestamp)
        ORDER BY hour_of_day
        """
        hour_data = execute_query(hour_query, conn)
        print(f"✅ Found engagement data for {len(hour_data)} hours")
        
        if len(hour_data) > 0:
            # Create visualization
            fig, ax = plt.subplots(figsize=(14, 6))
            ax.plot(hour_data['hour_of_day'], hour_data['total_engagements'], 
                    marker='o', linewidth=2, markersize=8, color='steelblue')
            ax.fill_between(hour_data['hour_of_day'], hour_data['total_engagements'], 
                            alpha=0.3, color='steelblue')
            ax.set_xlabel('Hour of Day', fontsize=12)
            ax.set_ylabel('Total Engagements', fontsize=12)
            ax.set_title('Engagement Patterns by Hour of Day', fontsize=14, fontweight='bold')
            ax.set_xticks(range(0, 24))
            ax.grid(alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(viz_dir, 'engagement_by_hour.png'), dpi=300, bbox_inches='tight')
            plt.close()
            print("✅ Saved: visualizations/engagement_by_hour.png")
        
        # 4. Heatmap
        print("\n4. Generating Engagement Heatmap...")
        heatmap_query = """
        SELECT 
            EXTRACT(DOW FROM engaged_timestamp) AS day_of_week,
            EXTRACT(HOUR FROM engaged_timestamp) AS hour_of_day,
            COUNT(*) AS engagement_count
        FROM engagements
        GROUP BY EXTRACT(DOW FROM engaged_timestamp), EXTRACT(HOUR FROM engaged_timestamp)
        ORDER BY day_of_week, hour_of_day
        """
        heatmap_data = execute_query(heatmap_query, conn)
        
        if len(heatmap_data) > 0:
            heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour_of_day', values='engagement_count').fillna(0)
            day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            heatmap_pivot.index = [day_names[int(i)] for i in heatmap_pivot.index]
            
            fig, ax = plt.subplots(figsize=(16, 8))
            sns.heatmap(heatmap_pivot, annot=True, fmt='.0f', cmap='YlOrRd', 
                        cbar_kws={'label': 'Engagement Count'}, ax=ax)
            ax.set_xlabel('Hour of Day', fontsize=12)
            ax.set_ylabel('Day of Week', fontsize=12)
            ax.set_title('Engagement Heatmap: Day of Week vs Hour of Day', fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(os.path.join(viz_dir, 'engagement_heatmap.png'), dpi=300, bbox_inches='tight')
            plt.close()
            print("✅ Saved: visualizations/engagement_heatmap.png")
        
        # 5. Opportunity Analysis
        print("\n5. Analyzing Opportunities...")
        opportunity_query = """
        WITH author_stats AS (
            SELECT 
                a.author_id,
                a.name,
                a.author_category,
                COUNT(DISTINCT p.post_id) AS total_posts,
                COUNT(e.engagement_id) AS total_engagements,
                ROUND(COUNT(e.engagement_id)::NUMERIC / NULLIF(COUNT(DISTINCT p.post_id), 0), 2) AS avg_engagement_per_post
            FROM authors a
            LEFT JOIN posts p ON a.author_id = p.author_id
            LEFT JOIN engagements e ON p.post_id = e.post_id
            WHERE p.publish_timestamp >= CURRENT_DATE - INTERVAL '365 days'
            GROUP BY a.author_id, a.name, a.author_category
        ),
        overall_avg AS (
            SELECT AVG(avg_engagement_per_post) AS overall_avg_engagement
            FROM author_stats
            WHERE total_posts > 0
        )
        SELECT 
            author_stats.author_id,
            author_stats.name,
            author_stats.author_category,
            author_stats.total_posts,
            author_stats.total_engagements,
            author_stats.avg_engagement_per_post,
            oa.overall_avg_engagement
        FROM author_stats
        CROSS JOIN overall_avg oa
        WHERE author_stats.total_posts > 0
        ORDER BY author_stats.total_posts DESC, author_stats.avg_engagement_per_post ASC
        """
        opportunity_data = execute_query(opportunity_query, conn)
        print(f"✅ Analyzed {len(opportunity_data)} authors")
        
        if len(opportunity_data) > 0:
            # Create scatter plot
            fig, ax = plt.subplots(figsize=(14, 8))
            colors = []
            for _, row in opportunity_data.iterrows():
                if row['avg_engagement_per_post'] < row['overall_avg_engagement']:
                    colors.append('red')
                else:
                    colors.append('green')
            ax.scatter(opportunity_data['total_posts'], 
                      opportunity_data['avg_engagement_per_post'],
                      c=colors, alpha=0.6, s=100, edgecolors='black', linewidth=1)
            if len(opportunity_data) > 0:
                avg_engagement = opportunity_data['overall_avg_engagement'].iloc[0]
                ax.axhline(y=avg_engagement, color='blue', linestyle='--', 
                          label=f'Overall Average ({avg_engagement:.2f})', linewidth=2)
            ax.set_xlabel('Post Volume (Total Posts)', fontsize=12)
            ax.set_ylabel('Average Engagement per Post', fontsize=12)
            ax.set_title('Opportunity Analysis: Post Volume vs Engagement Rate', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(viz_dir, 'opportunity_scatter.png'), dpi=300, bbox_inches='tight')
            plt.close()
            print("✅ Saved: visualizations/opportunity_scatter.png")
        
        print("\n" + "=" * 60)
        print("✅ Analysis Complete!")
        print("=" * 60)
        print(f"\nGenerated visualizations in: {viz_dir}")
        print("\nKey Insights:")
        if len(top_authors) > 0:
            print(f"  - Top author: {top_authors.iloc[0]['name']} with {top_authors.iloc[0]['total_engagements']} engagements")
        if len(hour_data) > 0:
            peak_hour = hour_data.loc[hour_data['total_engagements'].idxmax(), 'hour_of_day']
            print(f"  - Peak engagement hour: {int(peak_hour)}:00")
        print("\nSee recommendations/recommendations.md for detailed recommendations")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()

