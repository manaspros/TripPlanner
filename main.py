# filepath: d:\Code\Majorproject\main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import agent_executor
from config import config
from routes import router as api_router
import uvicorn

app = FastAPI(
    title=config.APP_NAME,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION,
)

class TravelRequest(BaseModel):
    city: str
    time_of_day: str
    place_type: str
    food_type: str
    budget: str

class TravelResponse(BaseModel):
    plan: str
    sources_used: list

# Include the router in the main application
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    validation = config.validate_api_keys()
    
    return {
        "message": "Travel Planner API is running",
        "endpoints": {
            "plan": "/api/plan - Generate travel plan",
            "agent_test": "/api/agent - Test agent functionality",
            "docs": "/docs - API documentation"
        },
        "api_status": {
            "configured": validation["has_required_keys"],
            "warnings": validation["warnings"]
        }
    }

@app.post("/plan", response_model=TravelResponse)
async def create_travel_plan(request: TravelRequest):
    try:
        # Format the query for the agent
        query = f"""
        Plan for {request.time_of_day} in {request.city}:
        - Looking for {request.place_type} to visit
        - Want {request.food_type} food within {request.budget} budget
        - Need places with 4.0+ rating
        - Include opening hours and why places are recommended
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
    return {"status": "healthy", "version": config.APP_VERSION}

# To run this file: uvicorn main:app --reload
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=config.HOST, 
        port=config.PORT, 
        reload=config.DEBUG
    )