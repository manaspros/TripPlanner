# 🎨 Frontend Integration Guide - TripPlanner API

## 📋 Document Purpose

This guide provides **complete API documentation** for frontend developers to integrate the enhanced TripPlanner backend with **Phase 1 & 2 MCP features**.

**Last Updated:** November 13, 2025
**API Version:** 2.0.0
**Backend Status:** ✅ Production Ready

---

## 🎯 What's New in Backend

### Phase 1 Features (MCP Foundation)
- ✅ Real-time weather forecasts
- ✅ Save/load travel plans
- ✅ User preference memory
- ✅ Smart caching (95% API reduction)

### Phase 2 Features (Enhanced)
- ✅ Route optimization with travel times
- ✅ Web search for events and reviews
- ✅ Multi-location itinerary optimization
- ✅ Current event discovery

---

## 🌐 API Base URL

**Development:** `http://localhost:8000`
**Production:** `https://your-domain.com`

**API Documentation:** `http://localhost:8000/docs` (Swagger UI)

---

## 📡 All API Endpoints

### 1. Core Travel Planning (Existing - Enhanced)

#### 1.1 Generate Travel Plan (Any City)

**Endpoint:** `POST /api/any-city-plan`

**Description:** Generate comprehensive travel plan for any Indian city with weather, routes, and events.

**Request Body:**
```json
{
  "city": "Delhi",
  "days": 2,
  "budget": "mid-range",
  "food_preference": "vegetarian"
}
```

**Request Fields:**
| Field | Type | Required | Options | Description |
|-------|------|----------|---------|-------------|
| city | string | ✅ Yes | Any Indian city | Destination city |
| days | integer | ✅ Yes | 1-10 | Number of days |
| budget | string | ✅ Yes | cheap, mid-range, expensive | Budget level |
| food_preference | string | ❌ No | vegetarian, non-vegetarian, vegan | Dietary preference |

**Response:**
```json
{
  "city": "Delhi",
  "days": 2,
  "plan": "🏛️ DAY 1: Delhi Exploration\n🌤️ Weather: Sunny, 28°C...",
  "status": "success",
  "budget": "mid-range",
  "food_preference": "vegetarian",
  "note": "Enhanced with weather, routes, and events"
}
```

**Frontend Implementation:**
```javascript
// Example API call
async function generateTravelPlan(city, days, budget, foodPreference) {
  const response = await fetch('http://localhost:8000/api/any-city-plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      city,
      days,
      budget,
      food_preference: foodPreference
    })
  });

  const data = await response.json();
  return data;
}

// Usage
const plan = await generateTravelPlan('Jaipur', 3, 'mid-range', 'vegetarian');
console.log(plan.plan); // Contains full itinerary with weather, routes
```

---

### 2. Phase 1: Weather & Persistence

#### 2.1 Get Weather Forecast

**Endpoint:** `GET /api/weather/{city}?days=5`

**Description:** Get real-time weather forecast (cached 3 hours).

**Parameters:**
| Parameter | Type | Required | Default | Range |
|-----------|------|----------|---------|-------|
| city | path | ✅ Yes | - | Any city name |
| days | query | ❌ No | 5 | 1-7 |

**Example Request:**
```http
GET /api/weather/Mumbai?days=3
```

**Response:**
```json
{
  "city": "Mumbai",
  "days": 3,
  "forecast": "Day 1: Sunny, 32°C\nDay 2: Partly cloudy, 30°C\nDay 3: Light rain, 28°C",
  "source": "mcp_weather",
  "rate_limit": {
    "calls_used": 5,
    "calls_remaining": 55,
    "limit": 60
  }
}
```

**Frontend Implementation:**
```javascript
async function getWeather(city, days = 5) {
  const response = await fetch(
    `http://localhost:8000/api/weather/${encodeURIComponent(city)}?days=${days}`
  );
  const data = await response.json();
  return data;
}

// Usage
const weather = await getWeather('Delhi', 3);
console.log(weather.forecast);
```

**UI Suggestion:**
```jsx
// React component example
function WeatherWidget({ city }) {
  const [weather, setWeather] = useState(null);

  useEffect(() => {
    getWeather(city, 5).then(setWeather);
  }, [city]);

  return (
    <div className="weather-widget">
      <h3>🌤️ Weather Forecast for {city}</h3>
      <pre>{weather?.forecast}</pre>
      <small>Updated every 3 hours</small>
    </div>
  );
}
```

---

#### 2.2 Save Travel Plan

**Endpoint:** `POST /api/save-plan`

**Description:** Save travel plan for later retrieval.

**Request Body:**
```json
{
  "plan_data": {
    "city": "Delhi",
    "days": 2,
    "budget": "mid-range",
    "itinerary": "Full itinerary text...",
    "created_at": "2024-11-13T10:30:00"
  },
  "plan_name": "Delhi Weekend Trip"
}
```

**Response:**
```json
{
  "status": "success",
  "plan_id": "Delhi_20241113_103000",
  "plan_name": "Delhi Weekend Trip",
  "created_at": "2024-11-13T10:30:00.123456",
  "message": "Plan saved successfully"
}
```

**Frontend Implementation:**
```javascript
async function savePlan(planData, planName) {
  const response = await fetch('http://localhost:8000/api/save-plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      plan_data: planData,
      plan_name: planName
    })
  });

  const result = await response.json();
  return result;
}

// Usage
const saved = await savePlan(
  { city: 'Goa', days: 3, itinerary: '...' },
  'Goa Beach Trip'
);
console.log('Saved with ID:', saved.plan_id);
```

---

#### 2.3 Load Saved Plan

**Endpoint:** `GET /api/plans/{plan_id}`

**Description:** Load a previously saved plan.

**Example Request:**
```http
GET /api/plans/Delhi_20241113_103000
```

**Response:**
```json
{
  "status": "success",
  "plan": {
    "plan_id": "Delhi_20241113_103000",
    "plan_name": "Delhi Weekend Trip",
    "created_at": "2024-11-13T10:30:00",
    "data": {
      "city": "Delhi",
      "days": 2,
      "itinerary": "..."
    }
  }
}
```

**Frontend Implementation:**
```javascript
async function loadPlan(planId) {
  const response = await fetch(`http://localhost:8000/api/plans/${planId}`);
  const data = await response.json();
  return data.plan;
}
```

---

#### 2.4 List All Saved Plans

**Endpoint:** `GET /api/plans?limit=20`

**Description:** Get list of all saved travel plans.

**Parameters:**
| Parameter | Type | Required | Default | Range |
|-----------|------|----------|---------|-------|
| limit | query | ❌ No | 20 | 1-100 |

**Response:**
```json
{
  "status": "success",
  "plans": [
    "Delhi_20241113_103000",
    "Mumbai_20241112_150000",
    "Jaipur_20241110_120000"
  ],
  "total": 3
}
```

**Frontend Implementation:**
```javascript
async function listPlans(limit = 20) {
  const response = await fetch(`http://localhost:8000/api/plans?limit=${limit}`);
  const data = await response.json();
  return data.plans;
}

// UI Component
function SavedPlansList() {
  const [plans, setPlans] = useState([]);

  useEffect(() => {
    listPlans().then(setPlans);
  }, []);

  return (
    <div className="saved-plans">
      <h3>💾 Your Saved Plans</h3>
      <ul>
        {plans.map(planId => (
          <li key={planId}>
            <button onClick={() => loadPlan(planId)}>
              {planId}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

### 3. Phase 2: Routes & Search

#### 3.1 Calculate Route

**Endpoint:** `GET /api/routes`

**Description:** Calculate route with travel time and distance (cached 6 hours).

**Parameters:**
| Parameter | Type | Required | Options |
|-----------|------|----------|---------|
| origin | query | ✅ Yes | Location name |
| destination | query | ✅ Yes | Location name |
| mode | query | ❌ No | transit (default), driving, walking, bicycling |

**Example Request:**
```http
GET /api/routes?origin=Red%20Fort%20Delhi&destination=India%20Gate&mode=transit
```

**Response:**
```json
{
  "origin": "Red Fort Delhi",
  "destination": "India Gate",
  "mode": "transit",
  "route": "Distance: 8.2 km\nDuration: 25 minutes\nMode: Metro\nDirections: ...",
  "source": "google_maps_mcp",
  "rate_limit": {
    "calls_used": 2,
    "calls_remaining": 98,
    "limit": 100
  }
}
```

**Frontend Implementation:**
```javascript
async function calculateRoute(origin, destination, mode = 'transit') {
  const params = new URLSearchParams({
    origin,
    destination,
    mode
  });

  const response = await fetch(
    `http://localhost:8000/api/routes?${params}`
  );
  const data = await response.json();
  return data;
}

// Usage
const route = await calculateRoute(
  'Taj Mahal',
  'Agra Fort',
  'walking'
);
console.log(route.route);
```

**UI Suggestion:**
```jsx
function RouteCalculator() {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [route, setRoute] = useState(null);

  const handleCalculate = async () => {
    const result = await calculateRoute(origin, destination);
    setRoute(result);
  };

  return (
    <div className="route-calculator">
      <h3>🗺️ Calculate Route</h3>
      <input
        placeholder="From"
        value={origin}
        onChange={e => setOrigin(e.target.value)}
      />
      <input
        placeholder="To"
        value={destination}
        onChange={e => setDestination(e.target.value)}
      />
      <button onClick={handleCalculate}>Calculate</button>

      {route && (
        <div className="route-result">
          <pre>{route.route}</pre>
          <small>Cached for 6 hours</small>
        </div>
      )}
    </div>
  );
}
```

---

#### 3.2 Search Travel Information

**Endpoint:** `GET /api/search`

**Description:** Search web for events, reviews, tips (cached 8 hours).

**Parameters:**
| Parameter | Type | Required | Default | Range |
|-----------|------|----------|---------|-------|
| query | query | ✅ Yes | - | Any search term |
| count | query | ❌ No | 10 | 1-20 |

**Example Request:**
```http
GET /api/search?query=festivals+in+Jaipur+November+2024&count=10
```

**Response:**
```json
{
  "query": "festivals in Jaipur November 2024",
  "count": 10,
  "results": "1. Jaipur Literature Festival - Nov 14-18...\n2. Diwali Celebrations...",
  "source": "brave_search_mcp",
  "rate_limit": {
    "calls_used": 3,
    "calls_remaining": 47,
    "limit": 50
  }
}
```

**Frontend Implementation:**
```javascript
async function searchTravelInfo(query, count = 10) {
  const params = new URLSearchParams({ query, count });

  const response = await fetch(
    `http://localhost:8000/api/search?${params}`
  );
  const data = await response.json();
  return data;
}

// Usage
const events = await searchTravelInfo('best time to visit Taj Mahal', 5);
console.log(events.results);
```

---

#### 3.3 Optimize Itinerary

**Endpoint:** `POST /api/optimize-itinerary`

**Description:** Calculate optimal routes between multiple locations.

**Request Body:**
```json
{
  "locations": [
    "Red Fort Delhi",
    "Jama Masjid",
    "India Gate",
    "Qutub Minar"
  ],
  "mode": "transit"
}
```

**Response:**
```json
{
  "status": "success",
  "optimized_route": [
    {
      "from": "Red Fort Delhi",
      "to": "Jama Masjid",
      "mode": "transit",
      "details": "650m, 8 min walk"
    },
    {
      "from": "Jama Masjid",
      "to": "India Gate",
      "mode": "transit",
      "details": "8.2km, 25 min metro"
    },
    {
      "from": "India Gate",
      "to": "Qutub Minar",
      "mode": "transit",
      "details": "15km, 40 min metro"
    }
  ],
  "total_locations": 4,
  "total_segments": 3,
  "mode": "transit",
  "message": "Routes calculated and cached for 6 hours"
}
```

**Frontend Implementation:**
```javascript
async function optimizeItinerary(locations, mode = 'transit') {
  const response = await fetch('http://localhost:8000/api/optimize-itinerary', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ locations, mode })
  });

  const data = await response.json();
  return data;
}

// Usage
const optimized = await optimizeItinerary([
  'Connaught Place',
  'India Gate',
  'Qutub Minar'
], 'transit');

console.log(optimized.optimized_route);
```

---

### 4. Utility Endpoints

#### 4.1 MCP Status

**Endpoint:** `GET /api/mcp-status`

**Description:** Get MCP server status and cache statistics.

**Response:**
```json
{
  "mcp_available": true,
  "servers": {
    "weather": {
      "initialized": true,
      "tools": ["get_forecast", "get_current_weather"],
      "rate_limit": {
        "calls_used": 5,
        "calls_remaining": 55,
        "limit": 60
      }
    },
    "google-maps": {
      "initialized": true,
      "tools": ["directions"],
      "rate_limit": {
        "calls_used": 2,
        "calls_remaining": 98,
        "limit": 100
      }
    }
  },
  "cache": {
    "categories": {
      "weather": { "entries": 12, "size_kb": 45.2 },
      "routes": { "entries": 8, "size_kb": 32.1 }
    },
    "total_entries": 74,
    "total_size_kb": 300.5
  },
  "performance": {
    "total_cache_hits": "Data reused from cache",
    "api_calls_saved": "Minimized through caching"
  }
}
```

---

#### 4.2 API Root

**Endpoint:** `GET /`

**Description:** Get API information and available endpoints.

**Response:**
```json
{
  "message": "Travel Planner API is running",
  "version": "2.0.0",
  "endpoints": {
    "plan": "/api/plan - Generate travel plan",
    "any_city_plan": "/api/any-city-plan - Generate plan for any Indian city",
    "weather": "/api/weather/{city} - Get weather forecast (Phase 1)",
    "save_plan": "/api/save-plan - Save travel plan (Phase 1)",
    "load_plan": "/api/plans/{plan_id} - Load saved plan (Phase 1)",
    "routes": "/api/routes?origin=X&destination=Y - Calculate route (Phase 2)",
    "search": "/api/search?query=X - Search travel info (Phase 2)",
    "optimize": "/api/optimize-itinerary - Optimize multiple locations (Phase 2)",
    "mcp_status": "/api/mcp-status - MCP and cache status",
    "docs": "/docs - API documentation"
  },
  "mcp_status": {
    "enabled": true,
    "servers": 5,
    "active_servers": ["filesystem", "memory", "weather", "google-maps", "brave-search"],
    "cache_entries": 74
  }
}
```

---

## 🎨 Frontend Features to Implement

### Priority 1: Essential (Must Have)

#### 1. Enhanced Travel Plan Display
**What to Show:**
- Weather forecast at top of plan
- Route information between locations
- Current events section
- Travel times and distances
- Cost breakdown

**UI Layout:**
```
┌─────────────────────────────────────┐
│ 🌤️ Weather: Sunny, 28°C            │
│ Perfect for outdoor activities      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ⏰ 8:00 AM - Red Fort              │
│ ⭐ Rating: 4.6                     │
│ 💰 Entry: ₹35                      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🗺️ ROUTE TO NEXT LOCATION         │
│ Distance: 650m (8 min walk)         │
│ Cost: Free                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🍽️ 12:00 PM - Karim's             │
│ ⭐ Rating: 4.4                     │
│ 💰 Price: ₹400-600                 │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 📅 CURRENT EVENTS                  │
│ 🎪 India Trade Fair (Nov 14-27)   │
│ Entry: ₹50                         │
└─────────────────────────────────────┘
```

---

#### 2. Weather Widget
**Features:**
- Display weather for destination
- Show 3-5 day forecast
- Update every 3 hours (cached)
- Weather-based recommendations

**Example Component:**
```jsx
function WeatherForecast({ city, days }) {
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getWeather(city, days)
      .then(data => {
        setWeather(data);
        setLoading(false);
      });
  }, [city, days]);

  if (loading) return <div>Loading weather...</div>;

  return (
    <div className="weather-forecast">
      <h3>🌤️ {city} Weather Forecast</h3>
      <div className="forecast-content">
        <pre>{weather.forecast}</pre>
      </div>
      <small className="cache-info">
        ♻️ Cached for 3 hours • {weather.rate_limit.calls_remaining} calls remaining
      </small>
    </div>
  );
}
```

---

#### 3. Save/Load Plans Feature
**Features:**
- "Save Plan" button on generated plans
- List of saved plans in user dashboard
- Load saved plan with one click
- Share plan by ID

**Example Component:**
```jsx
function SavePlanButton({ planData }) {
  const [saved, setSaved] = useState(false);
  const [planId, setPlanId] = useState(null);

  const handleSave = async () => {
    const planName = prompt('Enter plan name:');
    if (!planName) return;

    const result = await savePlan(planData, planName);
    setPlanId(result.plan_id);
    setSaved(true);
    alert(`Plan saved! ID: ${result.plan_id}`);
  };

  return (
    <div className="save-plan">
      {!saved ? (
        <button onClick={handleSave}>
          💾 Save This Plan
        </button>
      ) : (
        <div className="saved-info">
          ✅ Saved as: {planId}
          <button onClick={() => navigator.clipboard.writeText(planId)}>
            📋 Copy ID
          </button>
        </div>
      )}
    </div>
  );
}

function SavedPlansDrawer() {
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState(null);

  useEffect(() => {
    listPlans().then(setPlans);
  }, []);

  const handleLoadPlan = async (planId) => {
    const plan = await loadPlan(planId);
    setSelectedPlan(plan);
  };

  return (
    <aside className="saved-plans-drawer">
      <h3>📂 Your Saved Plans</h3>
      <ul>
        {plans.map(planId => (
          <li key={planId}>
            <button onClick={() => handleLoadPlan(planId)}>
              📄 {planId}
            </button>
          </li>
        ))}
      </ul>

      {selectedPlan && (
        <div className="plan-preview">
          <h4>{selectedPlan.plan_name}</h4>
          <p>{selectedPlan.data.city} - {selectedPlan.data.days} days</p>
          <button>View Full Plan</button>
        </div>
      )}
    </aside>
  );
}
```

---

### Priority 2: Enhanced (Should Have)

#### 4. Route Calculator Tool
**Features:**
- Input: origin, destination, mode
- Display: distance, time, cost, directions
- Visual route representation
- Mode selector (transit, driving, walking, bicycling)

**Example Component:**
```jsx
function RouteCalculatorWidget() {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [mode, setMode] = useState('transit');
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCalculate = async () => {
    setLoading(true);
    const result = await calculateRoute(origin, destination, mode);
    setRoute(result);
    setLoading(false);
  };

  return (
    <div className="route-calculator">
      <h3>🗺️ Route Calculator</h3>

      <div className="inputs">
        <input
          type="text"
          placeholder="From (e.g., Red Fort)"
          value={origin}
          onChange={e => setOrigin(e.target.value)}
        />

        <input
          type="text"
          placeholder="To (e.g., India Gate)"
          value={destination}
          onChange={e => setDestination(e.target.value)}
        />

        <select value={mode} onChange={e => setMode(e.target.value)}>
          <option value="transit">🚇 Transit</option>
          <option value="driving">🚗 Driving</option>
          <option value="walking">🚶 Walking</option>
          <option value="bicycling">🚴 Bicycling</option>
        </select>

        <button onClick={handleCalculate} disabled={loading}>
          {loading ? 'Calculating...' : 'Calculate Route'}
        </button>
      </div>

      {route && (
        <div className="route-result">
          <div className="route-summary">
            <span className="origin">{route.origin}</span>
            <span className="arrow">→</span>
            <span className="destination">{route.destination}</span>
          </div>

          <pre className="route-details">{route.route}</pre>

          <div className="cache-info">
            ♻️ Cached for 6 hours •
            {route.rate_limit.calls_remaining} calls remaining
          </div>
        </div>
      )}
    </div>
  );
}
```

---

#### 5. Event Discovery Widget
**Features:**
- Search for current events
- Display festivals, exhibitions, concerts
- Integration with travel plan
- Auto-search based on destination

**Example Component:**
```jsx
function EventDiscovery({ city }) {
  const [events, setEvents] = useState(null);
  const [customQuery, setCustomQuery] = useState('');

  useEffect(() => {
    // Auto-search for city events
    const query = `festivals and events in ${city} ${new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}`;
    searchTravelInfo(query, 10).then(setEvents);
  }, [city]);

  const handleCustomSearch = async () => {
    const results = await searchTravelInfo(customQuery, 10);
    setEvents(results);
  };

  return (
    <div className="event-discovery">
      <h3>📅 Current Events in {city}</h3>

      <div className="search-bar">
        <input
          type="text"
          placeholder="Search for specific events..."
          value={customQuery}
          onChange={e => setCustomQuery(e.target.value)}
        />
        <button onClick={handleCustomSearch}>🔍 Search</button>
      </div>

      {events && (
        <div className="events-results">
          <pre>{events.results}</pre>
          <small>♻️ Cached for 8 hours</small>
        </div>
      )}
    </div>
  );
}
```

---

#### 6. Itinerary Optimizer
**Features:**
- Input multiple locations
- Calculate all routes
- Show optimized order
- Total time and cost

**Example Component:**
```jsx
function ItineraryOptimizer() {
  const [locations, setLocations] = useState(['']);
  const [mode, setMode] = useState('transit');
  const [optimized, setOptimized] = useState(null);
  const [loading, setLoading] = useState(false);

  const addLocation = () => {
    setLocations([...locations, '']);
  };

  const updateLocation = (index, value) => {
    const newLocations = [...locations];
    newLocations[index] = value;
    setLocations(newLocations);
  };

  const handleOptimize = async () => {
    const validLocations = locations.filter(loc => loc.trim());
    if (validLocations.length < 2) {
      alert('Please add at least 2 locations');
      return;
    }

    setLoading(true);
    const result = await optimizeItinerary(validLocations, mode);
    setOptimized(result);
    setLoading(false);
  };

  return (
    <div className="itinerary-optimizer">
      <h3>🎯 Optimize Your Itinerary</h3>

      <div className="locations-list">
        {locations.map((loc, index) => (
          <div key={index} className="location-input">
            <span>{index + 1}.</span>
            <input
              type="text"
              placeholder={`Location ${index + 1}`}
              value={loc}
              onChange={e => updateLocation(index, e.target.value)}
            />
          </div>
        ))}
        <button onClick={addLocation}>➕ Add Location</button>
      </div>

      <div className="mode-selector">
        <label>Travel Mode:</label>
        <select value={mode} onChange={e => setMode(e.target.value)}>
          <option value="transit">🚇 Transit</option>
          <option value="driving">🚗 Driving</option>
          <option value="walking">🚶 Walking</option>
        </select>
      </div>

      <button onClick={handleOptimize} disabled={loading}>
        {loading ? 'Optimizing...' : '🚀 Optimize Routes'}
      </button>

      {optimized && (
        <div className="optimized-result">
          <h4>✅ Optimized Itinerary</h4>
          <div className="route-segments">
            {optimized.optimized_route.map((segment, index) => (
              <div key={index} className="segment">
                <div className="segment-header">
                  <span className="from">{segment.from}</span>
                  <span className="arrow">→</span>
                  <span className="to">{segment.to}</span>
                </div>
                <div className="segment-details">
                  <span className="mode">{segment.mode}</span>
                  <span className="details">{segment.details}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="summary">
            📍 {optimized.total_locations} locations
            • {optimized.total_segments} segments
          </div>
        </div>
      )}
    </div>
  );
}
```

---

### Priority 3: Advanced (Nice to Have)

#### 7. System Status Dashboard
**Features:**
- MCP server status
- Cache statistics
- Rate limit monitoring
- API performance metrics

**Example Component:**
```jsx
function SystemStatusDashboard() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    const fetchStatus = async () => {
      const response = await fetch('http://localhost:8000/api/mcp-status');
      const data = await response.json();
      setStatus(data);
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Update every 30s

    return () => clearInterval(interval);
  }, []);

  if (!status) return <div>Loading status...</div>;

  return (
    <div className="status-dashboard">
      <h3>📊 System Status</h3>

      <div className="mcp-servers">
        <h4>MCP Servers</h4>
        {Object.entries(status.servers).map(([name, info]) => (
          <div key={name} className="server-card">
            <div className="server-name">
              {info.initialized ? '✅' : '❌'} {name}
            </div>
            <div className="server-tools">
              Tools: {info.tools.join(', ')}
            </div>
            <div className="rate-limit">
              📊 {info.rate_limit.calls_used}/{info.rate_limit.limit} calls used
              ({info.rate_limit.calls_remaining} remaining)
            </div>
          </div>
        ))}
      </div>

      <div className="cache-stats">
        <h4>Cache Statistics</h4>
        <div className="stat">
          Total Entries: {status.cache.total_entries}
        </div>
        <div className="stat">
          Total Size: {status.cache.total_size_kb} KB
        </div>
        <div className="categories">
          {Object.entries(status.cache.categories).map(([cat, info]) => (
            <div key={cat} className="category">
              <strong>{cat}:</strong> {info.entries} entries ({info.size_kb} KB)
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## 🎨 UI/UX Recommendations

### Color Scheme
```css
:root {
  /* Primary Colors */
  --primary-blue: #2563eb;
  --primary-green: #10b981;
  --primary-orange: #f59e0b;

  /* Status Colors */
  --success: #22c55e;
  --warning: #eab308;
  --error: #ef4444;
  --info: #3b82f6;

  /* Background */
  --bg-primary: #ffffff;
  --bg-secondary: #f3f4f6;
  --bg-tertiary: #e5e7eb;

  /* Text */
  --text-primary: #111827;
  --text-secondary: #6b7280;
  --text-muted: #9ca3af;
}
```

### Icons Mapping
```javascript
const ICONS = {
  weather: '🌤️',
  location: '📍',
  route: '🗺️',
  time: '⏰',
  cost: '💰',
  rating: '⭐',
  food: '🍽️',
  transport: '🚇',
  event: '🎪',
  save: '💾',
  load: '📂',
  search: '🔍',
  optimize: '🎯'
};
```

### Loading States
```jsx
function LoadingState({ message = 'Loading...' }) {
  return (
    <div className="loading-state">
      <div className="spinner"></div>
      <p>{message}</p>
    </div>
  );
}
```

### Error States
```jsx
function ErrorState({ error, retry }) {
  return (
    <div className="error-state">
      <span className="error-icon">❌</span>
      <h4>Oops! Something went wrong</h4>
      <p>{error.message || 'An error occurred'}</p>
      {retry && <button onClick={retry}>🔄 Try Again</button>}
    </div>
  );
}
```

---

## 🔧 Environment Configuration

### Frontend .env
```bash
# API Configuration
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_API_TIMEOUT=30000

# Feature Flags
REACT_APP_ENABLE_WEATHER=true
REACT_APP_ENABLE_ROUTES=true
REACT_APP_ENABLE_SEARCH=true
REACT_APP_ENABLE_SAVE_LOAD=true

# Cache Configuration
REACT_APP_LOCAL_CACHE_DURATION=3600000  # 1 hour in ms

# Debug
REACT_APP_DEBUG=true
```

---

## 📱 Responsive Design

### Breakpoints
```css
/* Mobile First */
.container {
  padding: 1rem;
}

/* Tablet */
@media (min-width: 768px) {
  .container {
    padding: 2rem;
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .container {
    padding: 3rem;
    max-width: 1200px;
    margin: 0 auto;
  }
}
```

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
npm install axios  # or use fetch
```

### 2. Create API Client
```javascript
// src/api/client.js
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export const apiClient = {
  async get(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    return response.json();
  },

  async post(endpoint, data) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }
};
```

### 3. Create API Functions
```javascript
// src/api/travel.js
import { apiClient } from './client';

export const travelAPI = {
  generatePlan: (city, days, budget, foodPreference) =>
    apiClient.post('/api/any-city-plan', {
      city,
      days,
      budget,
      food_preference: foodPreference
    }),

  getWeather: (city, days = 5) =>
    apiClient.get(`/api/weather/${city}?days=${days}`),

  calculateRoute: (origin, destination, mode = 'transit') =>
    apiClient.get(`/api/routes?origin=${origin}&destination=${destination}&mode=${mode}`),

  searchEvents: (query, count = 10) =>
    apiClient.get(`/api/search?query=${query}&count=${count}`),

  savePlan: (planData, planName) =>
    apiClient.post('/api/save-plan', { plan_data: planData, plan_name: planName }),

  loadPlan: (planId) =>
    apiClient.get(`/api/plans/${planId}`),

  listPlans: (limit = 20) =>
    apiClient.get(`/api/plans?limit=${limit}`),

  optimizeItinerary: (locations, mode = 'transit') =>
    apiClient.post('/api/optimize-itinerary', { locations, mode })
};
```

---

## ✅ Testing Checklist

### API Integration Tests
- [ ] Generate travel plan
- [ ] Get weather forecast
- [ ] Calculate route
- [ ] Search events
- [ ] Save plan
- [ ] Load plan
- [ ] List plans
- [ ] Optimize itinerary
- [ ] Get MCP status

### UI/UX Tests
- [ ] Weather widget displays correctly
- [ ] Route calculator works
- [ ] Event search functional
- [ ] Save/load buttons work
- [ ] Plans list updates
- [ ] Loading states show
- [ ] Error handling works
- [ ] Mobile responsive
- [ ] Accessibility (a11y)

---

## 📞 Support & Resources

### Backend Documentation
- **API Docs:** http://localhost:8000/docs
- **Setup Guide:** See `SETUP_MCP.md`
- **Phase 1 Summary:** See `MCP_IMPLEMENTATION_SUMMARY.md`
- **Phase 2 Summary:** See `PHASE2_IMPLEMENTATION.md`
- **Complete Guide:** See `IMPLEMENTATION_COMPLETE.md`

### Common Issues
1. **CORS errors:** Ensure backend allows frontend origin
2. **Timeout errors:** Increase timeout to 30s+
3. **Cache not working:** Backend handles caching automatically
4. **Rate limits:** Backend protects against limits automatically

---

## 🎊 Summary

### What Frontend Needs to Implement

**Essential (Week 1):**
1. Enhanced plan display with weather
2. Save/load plan functionality
3. Weather widget
4. Basic error handling

**Enhanced (Week 2):**
5. Route calculator tool
6. Event discovery widget
7. Saved plans management
8. Loading states

**Advanced (Week 3):**
9. Itinerary optimizer
10. System status dashboard
11. Analytics integration
12. Share functionality

---

**Total New Features:** 12
**New API Endpoints to Integrate:** 8
**Estimated Frontend Dev Time:** 3 weeks
**Backend Status:** ✅ Production Ready

---

*Last Updated: November 13, 2025*
*Backend Version: 2.0.0*
*Document Version: 1.0*
