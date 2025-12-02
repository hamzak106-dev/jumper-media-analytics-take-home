# Jumper Media Analytics - Take-Home Assignment

Hey! This is my solution for the Jumper Media analytics take-home. I built a system to analyze engagement data, find patterns, and give some recommendations. Here's what's included and how to use it.

## What's Included

✅ PostgreSQL schema + sample data scripts  
✅ SQL query files (with comments)  
✅ Jupyter notebook with visualizations  
✅ Recommendations document  
✅ API endpoint (bonus)

---

## Quick Start

### What You Need

- PostgreSQL 12+ (or newer)
- Python 3.11+ 
- pip for installing packages

### Setup

1. **Create the database:**
```bash
createdb jumper_media
# or if that doesn't work:
psql -U postgres -c "CREATE DATABASE jumper_media;"
```

2. **Load the schema:**
```bash
psql -U postgres -d jumper_media -f database/schema.sql
```

3. **Load sample data:**
```bash
psql -U postgres -d jumper_media -f database/sample_data.sql
```

4. **(Optional) Generate more data for testing:**
```bash
cd database
pip install faker psycopg2-binary
python generate_large_dataset.py
cd ..
```

5. **Install Python packages:**
```bash
cd analysis
pip install -r requirements.txt
```

6. **Set up database connection:**
   Create a `.env` file in the `analysis/` folder:
   ```
   DB_HOST=localhost
   DB_NAME=jumper_media
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_PORT=5432
   ```

7. **Run the notebook:**
```bash
jupyter notebook main_analysis.ipynb
```

---

## Project Structure

```
jumper-media-analytics-take-home/
├── README.md                          # This file
├── database/
│   ├── schema.sql                    # Database schema
│   ├── sample_data.sql                # Sample data
│   └── generate_large_dataset.py      # Script to make more test data
├── queries/
│   ├── 01_top_authors_categories.sql  # Top authors/categories queries
│   ├── 02_time_patterns.sql          # Time pattern analysis
│   └── 03_opportunity_areas.sql       # Finding opportunities
├── analysis/
│   ├── main_analysis.ipynb            # Main notebook
│   ├── requirements.txt               # Python packages needed
│   └── config.py                      # DB connection config
├── visualizations/                    # Charts (created when you run notebook)
├── recommendations/
│   └── recommendations.md             # My recommendations
└── api/                               # Bonus API
    ├── main.py                        # FastAPI app
    ├── requirements.txt               
    ├── Dockerfile                     
    ├── docker-compose.yml             
    └── README.md                      # API docs
```

---

## What I Built

### 1. Database Schema

**File:** `database/schema.sql`

I kept the base schema from the requirements but added some things for performance:
- Indexes on columns we query a lot (like timestamps, foreign keys)
- Composite indexes for common join patterns
- Materialized views for daily aggregates (helps with dashboard queries)
- I also added a partitioning strategy in comments for when data gets really big

The main tables are:
- `authors` - author info
- `posts` - post content
- `engagements` - user interactions (views, likes, comments, shares)
- `post_metadata` - extra post info like tags
- `users` - user demographics

### 2. SQL Queries

**Folder:** `queries/`

I wrote three main query files:

1. **`01_top_authors_categories.sql`**
   - Finds top authors by engagement (for 7, 30, 90 days)
   - Top categories too
   - Engagement trends over time
   - Has some notes about performance

2. **`02_time_patterns.sql`**
   - Engagement by hour of day
   - Engagement by day of week
   - Heatmap data (hour × day)
   - Time-to-engagement analysis

3. **`03_opportunity_areas.sql`**
   - Finds authors who post a lot but get low engagement per post
   - Category performance comparison
   - Data for scatter plot (volume vs engagement)

All queries have comments explaining what they do.

### 3. Visualizations

**File:** `analysis/main_analysis.ipynb`

The notebook runs all the queries and makes charts:
- Bar chart for top authors
- Category comparison charts
- Line charts for trends
- Hour of day patterns
- Day of week patterns
- Heatmap (hour × day)
- Scatter plot for opportunities

Charts get saved to the `visualizations/` folder.

### 4. Recommendations

**File:** `recommendations/recommendations.md`

I wrote up three recommendations with priorities:
1. Content Timing Optimization (high impact, medium effort)
2. Author Engagement Boost Program (medium impact, low effort)
3. Category-Specific Content Strategy (medium-high impact, medium effort)

Also includes:
- Assumptions I made
- What data we're missing
- Performance and scale thoughts
- Trade-offs

### 5. API (Bonus)

**Folder:** `api/`

I built a FastAPI app with three endpoints:
- `GET /api/engagement/trends/post/{post_id}` - trends for a post
- `GET /api/engagement/trends/author/{author_id}` - trends for an author
- `GET /api/analytics/summary` - overall summary

See `api/README.md` for how to set it up.

---

## How to Run the Analysis

### Option 1: Jupyter Notebook (Easiest)

```bash
cd analysis
jupyter notebook
```

Then open `main_analysis.ipynb` and run all cells.

### Option 2: Run SQL Directly

```bash
psql -U postgres -d jumper_media -f queries/01_top_authors_categories.sql
```

### Option 3: Python Script

I also made a script that runs everything:
```bash
python3 run_analysis.py
```

This will generate all the visualizations automatically.

---

## Key Findings

From the analysis:

**Top performers:**
- Some authors consistently get high engagement
- Tech category does pretty well
- Authors who post regularly tend to do better

**Time patterns:**
- Peak engagement is during business hours (9am-5pm)
- Weekdays are better than weekends
- We could optimize posting times

**Opportunities:**
- Some authors post a lot but get low engagement per post - these are good candidates for help
- Some categories underperform even with high volume
- Content format matters (media, length)

See `recommendations/recommendations.md` for more details.

---

## Performance Stuff

I added indexes on the columns we query most - like engagement timestamps and post-author joins. Also created materialized views for daily aggregates which makes dashboard queries faster.

For bigger scale, I documented a partitioning strategy (commented out in schema.sql). At really large scale, I'd probably move to a data warehouse like Redshift or BigQuery.

---
## Testing the API (Bonus)

1. Install packages:
```bash
cd api
pip install -r requirements.txt
```

2. Set up `.env` file with your DB credentials

3. Run it:
```bash
uvicorn main:app --reload
```

4. Check it out:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

5. Test endpoints:
```bash
curl http://localhost:8000/api/engagement/trends/post/101?days=7
curl http://localhost:8000/api/engagement/trends/author/1?days=7
curl http://localhost:8000/api/analytics/summary?days=30
```

---

## Notes

### Schema Changes

I made some changes to the base schema for performance:
- Added indexes (documented in schema.sql)
- Materialized views for aggregates
- Helper function for engagement scoring
- Partitioning strategy (commented, for future)

All changes are explained in comments in the schema file.

### Data Generation

The `generate_large_dataset.py` script makes realistic test data. You can configure the size and it creates realistic patterns for time, engagement types, etc.

### Assumptions

Some things I assumed:
- All engagement types weighted equally (though comments/shares are probably more valuable)
- Engagement patterns are similar across user segments
- We don't have content quality scores, so using engagement as proxy
See recommendations doc for full list.