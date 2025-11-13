# TripPlanner - Installation & Testing Guide

## 🚀 Quick Start Commands

### 1. Installation Commands

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install MCP servers globally (optional but recommended for Phase 1 & 2 features)
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-memory
npm install -g @modelcontextprotocol/server-weather
npm install -g @modelcontextprotocol/server-google-maps
npm install -g @modelcontextprotocol/server-brave-search
```

### 2. Environment Setup

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file and add your API keys:
# - GOOGLE_API_KEY (required)
# - OPENWEATHER_API_KEY (for weather features)
# - GOOGLE_MAPS_API_KEY (for route optimization)
# - BRAVE_API_KEY (for web search)
```

### 3. Run the Server

```bash
# Method 1: Using uvicorn directly
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Method 2: Using Python
python main.py

# Method 3: Using uvicorn with custom host/port
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

**Server will start at:** `http://127.0.0.1:8000`
**API Documentation:** `http://127.0.0.1:8000/docs`

---

## 📮 Postman API Calls

### Setup in Postman

1. **Create Environment Variable:**
   - Variable: `BASE_URL`
   - Value: `http://127.0.0.1:8000`

### API Endpoints

---

## 1️⃣ Health Check

**GET** `{{BASE_URL}}/health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {
    "agent": true,
    "routes": true
  }
}
```

---

## 2️⃣ Root Endpoint (Status Overview)

**GET** `{{BASE_URL}}/`

**Response:**
```json
{
  "message": "Travel Planner API is running",
  "version": "1.0.0",
  "endpoints": {
    "plan": "/api/plan - Generate travel plan",
    "any_city_plan": "/api/any-city-plan - Generate plan for any Indian city",
    "weather": "/api/weather/{city} - Get weather forecast",
    "routes": "/api/routes?origin=X&destination=Y - Calculate route",
    "search": "/api/search?query=X - Search travel info"
  },
  "api_status": {
    "configured": true,
    "agent_available": true,
    "routes_available": true
  },
  "mcp_status": {
    "enabled": true,
    "servers": 5,
    "active_servers": ["filesystem", "memory", "weather", "google-maps", "brave-search"]
  }
}
```

---

## 3️⃣ Generate Travel Plan (Original Endpoint)

**POST** `{{BASE_URL}}/plan`

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "city": "Mumbai",
  "days": 3,
  "place_type": "tourist attractions",
  "food_type": "vegetarian",
  "budget": "medium"
}
```

**Response:**
```json
{
  "plan": "Detailed 3-day itinerary...",
  "sources_used": ["Google Places", "Zomato", "TripAdvisor", "Reddit"]
}
```

---

## 4️⃣ Generate Plan for Any Indian City (AI-Powered)

**POST** `{{BASE_URL}}/api/any-city-plan`

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "city": "Jaipur",
  "days": 2,
  "budget": "low",
  "food_preference": "non-vegetarian",
  "interests": "historical sites and local markets"
}
```

**Response:**
```json
{
  "city": "Jaipur",
  "plan": "Day 1:\nMorning: Visit Amber Fort...",
  "sources_used": ["MCP Weather", "Web Search", "Agent Knowledge"],
  "weather_included": true,
  "cached": false
}
```

---

## 5️⃣ Get Weather Forecast (Phase 1)

**GET** `{{BASE_URL}}/api/weather/Mumbai?days=5`

**Query Parameters:**
- `days` (optional): Number of days (1-7, default: 5)

**Response:**
```json
{
  "city": "Mumbai",
  "forecast": [
    {
      "date": "2025-11-13",
      "temperature": "28°C",
      "conditions": "Partly cloudy",
      "humidity": "75%"
    }
  ],
  "source": "cache",
  "message": "Weather data from cache (3hr TTL)",
  "cached_at": "2025-11-13T10:30:00"
}
```

---

## 6️⃣ Save Travel Plan (Phase 1)

**POST** `{{BASE_URL}}/api/save-plan`

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "plan_name": "Mumbai Weekend Trip",
  "plan_content": {
    "city": "Mumbai",
    "days": 2,
    "itinerary": "Day 1: Gateway of India...",
    "budget": "medium",
    "created_at": "2025-11-13"
  },
  "user_id": "user123"
}
```

**Response:**
```json
{
  "success": true,
  "plan_id": "mumbai-weekend-trip-20251113",
  "message": "Plan saved successfully",
  "storage_path": "./travel-plans/mumbai-weekend-trip-20251113.json"
}
```

---

## 7️⃣ Load Saved Plan (Phase 1)

**GET** `{{BASE_URL}}/api/plans/mumbai-weekend-trip-20251113`

**Response:**
```json
{
  "plan_id": "mumbai-weekend-trip-20251113",
  "plan_name": "Mumbai Weekend Trip",
  "plan_content": {
    "city": "Mumbai",
    "days": 2,
    "itinerary": "Day 1: Gateway of India..."
  },
  "user_id": "user123",
  "created_at": "2025-11-13"
}
```

---

## 8️⃣ List All Saved Plans (Phase 1)

**GET** `{{BASE_URL}}/api/plans?limit=20`

**Query Parameters:**
- `limit` (optional): Max plans to return (default: 10)

**Response:**
```json
{
  "plans": [
    {
      "plan_id": "mumbai-weekend-trip-20251113",
      "plan_name": "Mumbai Weekend Trip",
      "created_at": "2025-11-13"
    }
  ],
  "count": 1,
  "limit": 20
}
```

---

## 9️⃣ Calculate Route (Phase 2)

**GET** `{{BASE_URL}}/api/routes?origin=Gateway of India, Mumbai&destination=Marine Drive, Mumbai&mode=walking`

**Query Parameters:**
- `origin` (required): Starting location
- `destination` (required): Ending location
- `mode` (optional): `driving`, `walking`, `bicycling`, `transit` (default: `transit`)

**Response:**
```json
{
  "route": {
    "origin": "Gateway of India, Mumbai",
    "destination": "Marine Drive, Mumbai",
    "distance": "3.2 km",
    "duration": "40 minutes",
    "mode": "walking",
    "steps": [
      "Head south on Apollo Bandar",
      "Turn right onto Mahatma Gandhi Road"
    ]
  },
  "source": "cache",
  "message": "Route from cache (6hr TTL)",
  "cached_at": "2025-11-13T11:00:00"
}
```

---

## 🔟 Search Travel Info (Phase 2)

**GET** `{{BASE_URL}}/api/search?query=best street food in Mumbai&count=10`

**Query Parameters:**
- `query` (required): Search query
- `count` (optional): Number of results (1-20, default: 10)

**Response:**
```json
{
  "query": "best street food in Mumbai",
  "results": [
    {
      "title": "Top 10 Street Food Places in Mumbai",
      "url": "https://example.com/mumbai-street-food",
      "snippet": "Discover the best vada pav, pav bhaji..."
    }
  ],
  "count": 10,
  "source": "cache",
  "message": "Search results from cache (8hr TTL)"
}
```

---

## 1️⃣1️⃣ Optimize Itinerary (Phase 2)

**POST** `{{BASE_URL}}/api/optimize-itinerary`

**Headers:**
```
Content-Type: application/json
```

**Body (raw JSON):**
```json
{
  "locations": [
    "Gateway of India, Mumbai",
    "Chhatrapati Shivaji Terminus, Mumbai",
    "Marine Drive, Mumbai",
    "Haji Ali Dargah, Mumbai"
  ],
  "start_location": "Gateway of India, Mumbai",
  "mode": "driving"
}
```

**Response:**
```json
{
  "optimized_route": {
    "locations": [
      "Gateway of India, Mumbai",
      "Chhatrapati Shivaji Terminus, Mumbai",
      "Haji Ali Dargah, Mumbai",
      "Marine Drive, Mumbai"
    ],
    "total_distance": "15.2 km",
    "total_duration": "45 minutes",
    "mode": "driving",
    "routes": [
      {
        "from": "Gateway of India",
        "to": "Chhatrapati Shivaji Terminus",
        "distance": "3.5 km",
        "duration": "12 minutes"
      }
    ]
  },
  "savings": {
    "distance_saved": "2.3 km",
    "time_saved": "8 minutes"
  }
}
```

---

## 1️⃣2️⃣ MCP Status & Cache Statistics

**GET** `{{BASE_URL}}/api/mcp-status`

**Response:**
```json
{
  "mcp_available": true,
  "servers": {
    "filesystem": {
      "status": "active",
      "uptime": "2h 15m"
    },
    "weather": {
      "status": "active",
      "api_key_configured": true
    },
    "google-maps": {
      "status": "active",
      "api_key_configured": true
    },
    "brave-search": {
      "status": "active",
      "api_key_configured": true
    }
  },
  "cache_stats": {
    "total_entries": 45,
    "weather": 5,
    "routes": 12,
    "search": 8,
    "restaurants": 20,
    "cache_hit_rate": "94%"
  },
  "rate_limits": {
    "weather": {
      "used": 15,
      "limit": 60,
      "remaining": 45
    },
    "google_maps": {
      "used": 8,
      "limit": 100,
      "remaining": 92
    }
  }
}
```

---

## 🧪 Testing Workflow

### 1. Basic Flow
```
1. GET /health → Check server is running
2. GET / → Check MCP status
3. POST /api/any-city-plan → Generate a plan
4. POST /api/save-plan → Save the plan
5. GET /api/plans → List saved plans
```

### 2. Weather Flow
```
1. GET /api/weather/Mumbai?days=5 → Get forecast
2. POST /api/any-city-plan (with Mumbai) → Plan includes weather
```

### 3. Route Optimization Flow
```
1. GET /api/routes?origin=X&destination=Y → Single route
2. POST /api/optimize-itinerary → Multi-location optimization
```

### 4. Search Flow
```
1. GET /api/search?query=events in Mumbai → Find events
2. Use results to enhance travel planning
```

---

## 🔧 Troubleshooting

### Issue: Server won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn main:app --reload --port 8080
```

### Issue: MCP servers not initializing
```bash
# Check if Node.js is installed
node --version

# Install MCP servers
npm install -g @modelcontextprotocol/server-weather

# Verify .env file has API keys
cat .env | grep API_KEY
```

### Issue: Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version (requires 3.8+)
python --version
```

---

## 📊 Expected Performance

| Endpoint | First Call | Cached Call | Cache Duration |
|----------|-----------|-------------|----------------|
| Weather | 1.5s | 50ms | 3 hours |
| Routes | 2.0s | 40ms | 6 hours |
| Search | 1.8s | 45ms | 8 hours |
| Restaurants | 2.5s | 60ms | 12 hours |
| Plans (save/load) | 100ms | 30ms | N/A |

---

## 🎯 Postman Collection Import

Create a new collection in Postman and import these requests, or use the Postman Collection JSON format:

```json
{
  "info": {
    "name": "TripPlanner API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "BASE_URL",
      "value": "http://127.0.0.1:8000"
    }
  ]
}
```

---

## 💡 Tips

1. **Use Swagger UI**: Visit `http://127.0.0.1:8000/docs` for interactive API testing
2. **Check Logs**: Monitor terminal for MCP initialization messages
3. **Cache Monitoring**: Use `/api/mcp-status` to track cache performance
4. **Rate Limits**: Check status before making many API calls
5. **Environment Variables**: Keep `.env` file secure, never commit it

---

## 📚 Additional Resources

- **API Documentation**: http://127.0.0.1:8000/docs
- **Frontend Integration Guide**: `FRONTEND_INTEGRATION_GUIDE.md`
- **Phase 2 Setup**: `PHASE2_IMPLEMENTATION.md`
- **Complete Implementation**: `IMPLEMENTATION_COMPLETE.md`
