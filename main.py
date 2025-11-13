# filepath: d:\Code\Majorproject\main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from config import config
import uvicorn
from contextlib import asynccontextmanager
import asyncio

# Handle imports with error handling
try:
    from agent import agent_executor
    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Agent import failed: {e}")
    AGENT_AVAILABLE = False
    # Create fallback
    class FallbackAgent:
        def invoke(self, input_dict):
            return {"output": "Agent not available - check dependencies"}
    agent_executor = FallbackAgent()

try:
    from routes import router as api_router
    ROUTES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Routes import failed: {e}")
    ROUTES_AVAILABLE = False

# Import MCP integration (optional)
try:
    from mcp_integration import initialize_mcp_servers, mcp_manager, get_mcp_status
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"ℹ️ MCP integration not available: {e}")
    print("   Install with: pip install mcp && npm install -g @modelcontextprotocol/server-*")
    MCP_AVAILABLE = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for FastAPI - handles startup and shutdown
    Initializes MCP servers on startup and cleans up on shutdown
    """
    # Startup
    print("=" * 60)
    print("🚀 TripPlanner Starting Up")
    print("=" * 60)

    if MCP_AVAILABLE:
        print("\n📡 Initializing MCP servers...")
        try:
            init_results = await initialize_mcp_servers()
            successful = sum(1 for v in init_results.values() if v)
            total = len(init_results)

            if successful > 0:
                print(f"✅ MCP Initialized: {successful}/{total} servers ready")
                print(f"   Enabled features: ", end="")
                enabled = [name for name, status in init_results.items() if status]
                print(", ".join(enabled))
            else:
                print("⚠️ No MCP servers initialized - using fallback mode")
                print("   Check your .env file for API keys:")
                print("   - OPENWEATHER_API_KEY (for weather forecasts)")
        except Exception as e:
            print(f"⚠️ MCP initialization failed: {e}")
            print("   Continuing without MCP features")
    else:
        print("\nℹ️ MCP not available - running in basic mode")
        print("   To enable advanced features:")
        print("   1. pip install mcp")
        print("   2. npm install -g @modelcontextprotocol/server-filesystem")
        print("   3. npm install -g @modelcontextprotocol/server-memory")
        print("   4. npm install -g @modelcontextprotocol/server-weather")

    # Import and clean up cache on startup
    try:
        from cache_manager import cache_manager
        cache_manager.cleanup_expired()
        print("\n🧹 Cleaned up expired cache entries")
    except ImportError:
        pass

    print("\n" + "=" * 60)
    print(f"✅ TripPlanner Ready on http://{config.HOST}:{config.PORT}")
    print(f"📚 API Docs: http://{config.HOST}:{config.PORT}/docs")
    print("=" * 60 + "\n")

    yield  # Server runs here

    # Shutdown
    print("\n" + "=" * 60)
    print("🛑 TripPlanner Shutting Down")
    print("=" * 60)

    if MCP_AVAILABLE:
        print("📡 Closing MCP connections...")
        try:
            await mcp_manager.cleanup()
            print("✅ MCP connections closed")
        except Exception as e:
            print(f"⚠️ MCP cleanup error: {e}")

    print("👋 Goodbye!\n")

app = FastAPI(
    title=config.APP_NAME,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION,
    lifespan=lifespan
)

class TravelRequest(BaseModel):
    city: str
    days: int
    place_type: str
    food_type: str
    budget: str

class TravelResponse(BaseModel):
    plan: str
    sources_used: list

# Include the router in the main application if available
if ROUTES_AVAILABLE:
    app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    validation = config.validate_api_keys()

    # Get MCP status if available
    mcp_info = {}
    if MCP_AVAILABLE:
        try:
            mcp_status = get_mcp_status()
            mcp_info = {
                "enabled": True,
                "servers": len(mcp_status.get("servers", {})),
                "active_servers": list(mcp_status.get("servers", {}).keys()),
                "cache_entries": mcp_status.get("cache_stats", {}).get("total_entries", 0)
            }
        except Exception as e:
            mcp_info = {"enabled": False, "error": str(e)}
    else:
        mcp_info = {"enabled": False, "reason": "MCP not installed"}

    return {
        "message": "Travel Planner API is running",
        "version": config.APP_VERSION,
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
        "api_status": {
            "configured": validation["has_required_keys"],
            "warnings": validation["warnings"],
            "agent_available": AGENT_AVAILABLE,
            "routes_available": ROUTES_AVAILABLE
        },
        "mcp_status": mcp_info
    }

@app.post("/plan", response_model=TravelResponse)
async def create_travel_plan(request: TravelRequest):
    try:
        # Format the query for the agent
        days_text = f"{request.days} day{'s' if request.days > 1 else ''}"
        query = f"""
        Plan {days_text} itinerary for {request.city}:
        - Looking for {request.place_type} to visit
        - Want {request.food_type} food within {request.budget} budget
        - Need places with 4.0+ rating
        - Include opening hours and why places are recommended
        - Create day-wise schedule with morning, lunch, and afternoon activities
        """
        
        # Execute the agent
        result = agent_executor.invoke({"input": query})
        
        return TravelResponse(
            plan=result["output"],
            sources_used=["Google Places", "Zomato", "TripAdvisor", "Reddit"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating plan: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "version": config.APP_VERSION,
        "dependencies": {
            "agent": AGENT_AVAILABLE,
            "routes": ROUTES_AVAILABLE
        }
    }

# To run this file: uvicorn main:app --reload
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=config.HOST, 
        port=config.PORT, 
        reload=config.DEBUG
    )