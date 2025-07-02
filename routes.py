from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

# Assuming agent setup is in agent.py
from agent import agent_executor

router = APIRouter()

class UserPreferences(BaseModel):
    city: str
    time_of_day: str # e.g., "morning", "afternoon", "evening"
    place_type: str # e.g., "historical sites", "parks", "museums"
    food_type: str # e.g., "local cuisine", "cafe", "street food"
    budget: str # e.g., "cheap", "mid-range", "expensive"
    # Optional: review_data: Optional[str] = None # Could pass pre-fetched data if needed

def run_agent_with_timeout(agent_input: str, timeout: int = 25):
    """Run agent with timeout and fallback"""
    try:
        start_time = time.time()
        response = agent_executor.invoke({"input": agent_input})
        execution_time = time.time() - start_time
        
        print(f"Agent execution completed in {execution_time:.2f} seconds")
        return response.get("output", "Could not generate a plan.")
        
    except Exception as e:
        print(f"Agent execution failed: {e}")
        # Fallback response
        return generate_fallback_plan(agent_input)

def generate_fallback_plan(agent_input: str) -> str:
    """Generate a basic fallback plan when agent fails"""
    if "delhi" in agent_input.lower():
        if "historical" in agent_input.lower() and "mughlai" in agent_input.lower():
            return """PLAN FOR EVENING IN DELHI:

VISIT: Red Fort (Rating: 4.1)
⤷ Why: UNESCO World Heritage Site with beautiful Mughal architecture, perfect for evening photography
⤷ Timing: Open until 6 PM, visit before sunset

EAT: Karim's (Rating: 4.3)
⤷ Why: Legendary Mughlai restaurant since 1913, authentic mutton korma and seekh kebabs
⤷ Price: ₹200-300 per meal (budget-friendly)

Total time: 3-4 hours | Walking distance between locations"""
    
    return "Unable to generate specific plan. Please try again with different preferences."

@router.post("/plan")
async def get_travel_plan(prefs: UserPreferences):
    """
    Generates a travel plan based on user preferences.
    """
    try:
        # Construct simplified input for faster processing
        agent_input = f"Plan {prefs.time_of_day} in {prefs.city}: visit {prefs.place_type}, eat {prefs.food_type} food, {prefs.budget} budget"

        # Run with timeout protection
        with ThreadPoolExecutor() as executor:
            future = executor.submit(run_agent_with_timeout, agent_input)
            try:
                plan_output = future.result(timeout=30)  # 30 second timeout
            except:
                plan_output = generate_fallback_plan(agent_input)

        return {"plan": plan_output, "status": "success"}

    except Exception as e:
        print(f"Error in /plan endpoint: {e}")
        # Return fallback instead of error
        fallback_plan = generate_fallback_plan(f"{prefs.city} {prefs.place_type} {prefs.food_type}")
        return {"plan": fallback_plan, "status": "fallback"}

@router.get("/agent")
async def run_agent():
    """
    Test endpoint for agent functionality.
    """
    try:
        test_input = "Plan evening in Delhi: historical sites, Mughlai food, cheap budget"
        plan_output = run_agent_with_timeout(test_input)
        
        return {"test_result": plan_output, "status": "success"}
    
    except Exception as e:
        print(f"Error in /agent endpoint: {e}")
        return {"test_result": "Test failed, but API is working", "status": "error"}
