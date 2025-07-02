# filepath: d:\Code\Majorproject\main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from config import config
import uvicorn

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

app = FastAPI(
    title=config.APP_NAME,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION,
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
    
    return {
        "message": "Travel Planner API is running",
        "endpoints": {
            "plan": "/api/plan - Generate travel plan",
            "any_city_plan": "/api/any-city-plan - Generate plan for any Indian city",
            "docs": "/docs - API documentation"
        },
        "api_status": {
            "configured": validation["has_required_keys"],
            "warnings": validation["warnings"],
            "agent_available": AGENT_AVAILABLE,
            "routes_available": ROUTES_AVAILABLE
        }
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