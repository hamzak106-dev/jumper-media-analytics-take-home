#!/usr/bin/env python3
"""
Verification script to test all components of the Jumper Media Analytics setup
"""

import sys
import os

# Add analysis directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analysis'))

def test_database_connection():
    """Test database connection and basic queries"""
    print("=" * 60)
    print("1. Testing Database Connection")
    print("=" * 60)
    
    try:
        import psycopg2
        from analysis.config import DB_CONFIG
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Test basic query
        cur.execute("SELECT COUNT(*) FROM authors")
        author_count = cur.fetchone()[0]
        print(f"✅ Database connection successful")
        print(f"   Authors in database: {author_count}")
        
        # Test joins
        cur.execute("""
            SELECT COUNT(*) 
            FROM authors a
            JOIN posts p ON a.author_id = p.author_id
            JOIN engagements e ON p.post_id = e.post_id
        """)
        engagement_count = cur.fetchone()[0]
        print(f"   Total engagements: {engagement_count}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_pandas_integration():
    """Test pandas with PostgreSQL"""
    print("\n" + "=" * 60)
    print("2. Testing Pandas Integration")
    print("=" * 60)
    
    try:
        import pandas as pd
        import psycopg2
        from analysis.config import DB_CONFIG
        
        conn = psycopg2.connect(**DB_CONFIG)
        
        query = """
        SELECT 
            a.name,
            COUNT(p.post_id) as post_count,
            COUNT(e.engagement_id) as engagement_count
        FROM authors a
        LEFT JOIN posts p ON a.author_id = p.author_id
        LEFT JOIN engagements e ON p.post_id = e.post_id
        GROUP BY a.name
        ORDER BY engagement_count DESC
        """
        
        df = pd.read_sql_query(query, conn)
        print("✅ Pandas integration successful")
        print(f"   Retrieved {len(df)} authors")
        print("\n   Sample data:")
        print(df.to_string(index=False))
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Pandas integration failed: {e}")
        return False

def test_visualization_libraries():
    """Test visualization libraries"""
    print("\n" + "=" * 60)
    print("3. Testing Visualization Libraries")
    print("=" * 60)
    
    try:
        import matplotlib
        import seaborn
        import plotly
        print("✅ matplotlib available")
        print("✅ seaborn available")
        print("✅ plotly available")
        return True
    except ImportError as e:
        print(f"❌ Missing visualization library: {e}")
        return False

def test_sql_queries():
    """Test SQL query files"""
    print("\n" + "=" * 60)
    print("4. Testing SQL Queries")
    print("=" * 60)
    
    try:
        import psycopg2
        from analysis.config import DB_CONFIG
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Test time pattern query
        query = """
        SELECT 
            EXTRACT(HOUR FROM engaged_timestamp) AS hour_of_day,
            COUNT(*) AS total_engagements
        FROM engagements
        GROUP BY EXTRACT(HOUR FROM engaged_timestamp)
        ORDER BY hour_of_day
        """
        
        cur.execute(query)
        results = cur.fetchall()
        print(f"✅ SQL query execution successful")
        print(f"   Found engagement data for {len(results)} hours")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ SQL query test failed: {e}")
        return False

def test_api_imports():
    """Test API dependencies"""
    print("\n" + "=" * 60)
    print("5. Testing API Dependencies")
    print("=" * 60)
    
    try:
        import fastapi
        import uvicorn
        import pydantic
        print("✅ FastAPI available")
        print("✅ Uvicorn available")
        print("✅ Pydantic available")
        return True
    except ImportError as e:
        print(f"⚠️  API dependencies not installed: {e}")
        print("   (This is optional - install with: pip install -r api/requirements.txt)")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Jumper Media Analytics - Setup Verification")
    print("=" * 60 + "\n")
    
    results = []
    results.append(("Database Connection", test_database_connection()))
    results.append(("Pandas Integration", test_pandas_integration()))
    results.append(("Visualization Libraries", test_visualization_libraries()))
    results.append(("SQL Queries", test_sql_queries()))
    results.append(("API Dependencies", test_api_imports()))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result for _, result in results[:4])  # API is optional
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All core components verified successfully!")
        print("\nNext steps:")
        print("  1. Run: jupyter notebook analysis/main_analysis.ipynb")
        print("  2. Or test API: cd api && uvicorn main:app --reload")
    else:
        print("⚠️  Some components need attention")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()

