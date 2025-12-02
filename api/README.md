# Jumper Media Analytics API

FastAPI-based REST API for engagement analytics and trends.

## Features

- **Post Engagement Trends**: Compare engagement for a specific post over time periods
- **Author Engagement Trends**: Track author performance over time
- **Analytics Summary**: Overall platform metrics and statistics

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL database (see main README for setup)
- Docker (optional, for containerized deployment)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables (create `.env` file):
```
DB_HOST=localhost
DB_NAME=jumper_media
DB_USER=postgres
DB_PASSWORD=postgres
DB_PORT=5432
```

3. Run the API:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Endpoints

### 1. Get Post Engagement Trends
```
GET /api/engagement/trends/post/{post_id}?days=7
```

**Parameters:**
- `post_id` (path): Post ID
- `days` (query, optional): Number of days to compare (default: 7)

**Response:**
```json
{
  "post_id": 101,
  "post_title": "Deep Dive into X",
  "current_period": [
    {
      "date": "2025-08-01",
      "views": 10,
      "likes": 5,
      "comments": 2,
      "shares": 1,
      "total": 18
    }
  ],
  "previous_period": [...],
  "change_percent": 15.5
}
```

### 2. Get Author Engagement Trends
```
GET /api/engagement/trends/author/{author_id}?days=7
```

**Parameters:**
- `author_id` (path): Author ID
- `days` (query, optional): Number of days to compare (default: 7)

**Response:**
Similar structure to post trends, but aggregated across all author's posts.

### 3. Get Analytics Summary
```
GET /api/analytics/summary?days=30
```

**Parameters:**
- `days` (query, optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "total_authors": 50,
  "total_posts": 1000,
  "total_engagements": 50000,
  "total_views": 40000,
  "total_likes": 8000,
  "total_comments": 1500,
  "total_shares": 500,
  "avg_engagement_per_post": 50.0
}
```

## Docker Deployment

### Using Docker Compose

1. Update `docker-compose.yml` with your database configuration
2. Run:
```bash
docker-compose up -d
```

The API will be available at `http://localhost:8000`

### Using Docker directly

1. Build the image:
```bash
docker build -t jumper-analytics-api .
```

2. Run the container:
```bash
docker run -p 8000:8000 \
  -e DB_HOST=your_db_host \
  -e DB_NAME=jumper_media \
  -e DB_USER=postgres \
  -e DB_PASSWORD=your_password \
  jumper-analytics-api
```

## Microservice Architecture Considerations

### Production Deployment

1. **API Gateway**: Use API Gateway (Kong, AWS API Gateway) for:
   - Rate limiting
   - Authentication/Authorization
   - Request routing

2. **Caching**: Implement Redis caching for:
   - Frequently accessed metrics
   - Reduce database load
   - Improve response times

3. **Load Balancing**: Use load balancer for:
   - Multiple API instances
   - High availability
   - Traffic distribution

4. **Monitoring**: Add:
   - Application performance monitoring (APM)
   - Log aggregation
   - Health check endpoints

5. **Database Connection Pooling**: Use connection pooler (PgBouncer) for:
   - Efficient database connections
   - Better resource utilization

### Example Architecture

```
[Client] 
  → [API Gateway] 
  → [Load Balancer] 
  → [API Instances] 
  → [Connection Pooler] 
  → [PostgreSQL/Data Warehouse]
```

## Testing

Example curl commands:

```bash
# Get post trends
curl http://localhost:8000/api/engagement/trends/post/101?days=7

# Get author trends
curl http://localhost:8000/api/engagement/trends/author/1?days=7

# Get summary
curl http://localhost:8000/api/analytics/summary?days=30
```

## Performance Considerations

- Queries use indexed columns for optimal performance
- Consider adding caching layer (Redis) for production
- For high-traffic scenarios, use read replicas for analytics queries
- Monitor query performance with database monitoring tools

