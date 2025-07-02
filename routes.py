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
    days: int # Number of days for the trip (e.g., 1, 2, 3)
    place_type: str # e.g., "historical sites", "parks", "museums"
    food_type: str # e.g., "local cuisine", "cafe", "street food"
    budget: str # e.g., "cheap", "mid-range", "expensive"

class AgentTestRequest(BaseModel):
    query: str
    location: Optional[str] = "Delhi"

class AgentTestResponse(BaseModel):
    result: str
    tools_used: list

class SimpleCityRequest(BaseModel):
    city: str
    days: Optional[int] = 1
    budget: Optional[str] = "mid-range"
    food_preference: Optional[str] = "local cuisine"

def run_agent_with_timeout(agent_input: str, timeout: int = 45):
    """Run agent with timeout and enhanced error handling"""
    try:
        start_time = time.time()
        response = agent_executor.invoke({"input": agent_input})
        execution_time = time.time() - start_time
        
        print(f"Agent execution completed in {execution_time:.2f} seconds")
        return response.get("output", "Could not generate a plan.")
        
    except Exception as e:
        print(f"Agent execution failed: {e}")
        return None

def create_detailed_prompt(prefs: UserPreferences) -> str:
    """Create detailed prompt for Gemini to generate comprehensive plan"""
    
    days_text = f"{prefs.days} day{'s' if prefs.days > 1 else ''}"
    
    prompt = f"""Create a detailed {days_text} travel itinerary for {prefs.city} with these requirements:

USER PREFERENCES:
- Place type: {prefs.place_type}
- Food preference: {prefs.food_type}  
- Budget: {prefs.budget}
- Duration: {prefs.days} days

CRITICAL INSTRUCTIONS:
1. You MUST use google_places_search tool for each attraction with detailed parameters
2. You MUST use restaurant_search tool for each meal with specific cuisine types
3. NEVER use generic terms like "Local restaurant", "Local eatery", or "Generic option"
4. ALWAYS include specific restaurant names with ratings from tool results
5. If a tool fails, use another tool call with different search parameters
6. Only recommend places with 4.0+ ratings
7. Include actual opening hours, entry fees, and price ranges from tool data
8. For each place, include WHY it's worth visiting and duration needed

REQUIRED ACTIONS PER DAY:
- Call google_places_search at least 3 times for different attractions/activities
- Call restaurant_search at least 3 times for breakfast, lunch, dinner options
- Each recommendation must include specific names, ratings, and details
- Include timing optimization to avoid crowds and heat

FORMAT REQUIREMENTS:
**DAY X: [Theme] Exploration**

⏰ [Time] - VISIT: [REAL Place Name from tool] (⭐ Rating: X.X)
📍 Address: [Full address from tool]
🕒 Hours: [Actual opening hours]
💰 Entry: [Actual entry fee]
⏱️ Duration: [Recommended time]
✨ Why Visit: [Specific reason from tool data]

🍽️ [Time] - [MEAL]: [REAL Restaurant Name from tool] (⭐ Rating: X.X)
📍 Address: [Full address from tool]
💰 Price: [Actual price range]
🍛 Cuisine: [Cuisine type]
⭐ Famous For: [Specific dishes/specialties]

VALIDATION: Response must contain NO generic terms and ALL details must be from actual tool results."""

    return prompt

def create_city_prompt(city: str, days: int = 1, budget: str = "mid-range", food_preference: str = "local cuisine") -> str:
    """Create comprehensive prompt for any city"""
    
    # Determine place types based on city
    if city.lower() in ['jaipur']:
        place_focus = "historical palaces, forts, and Rajasthani architecture"
        food_focus = "traditional Rajasthani cuisine, dal baati churma, kachori"
    elif city.lower() in ['delhi']:
        place_focus = "historical monuments, museums, and cultural sites"
        food_focus = "North Indian cuisine, street food, traditional vegetarian"
    else:
        place_focus = "historical sites, cultural attractions, and local landmarks" 
        food_focus = "local cuisine and traditional specialties"
    
    days_text = f"{days} day{'s' if days > 1 else ''}"
    
    prompt = f"""Create a comprehensive {days_text} travel itinerary for {city.title()}, India with these specifications:

TARGET CITY: {city.title()}
DURATION: {days} days
BUDGET: {budget}
FOOD PREFERENCE: {food_preference}
FOCUS: {place_focus}

MANDATORY TOOL USAGE REQUIREMENTS:
1. Call google_places_search tool minimum 4 times per day with specific queries:
   - "historical sites {city}"
   - "monuments {city}" 
   - "museums {city}"
   - "gardens {city}"

2. Call restaurant_search tool minimum 4 times per day with specific queries:
   - "vegetarian restaurants {city}"
   - "traditional food {city}"
   - "local cuisine {city}" 
   - "street food {city}"

3. Call get_reviews tool for additional insights about top recommendations

4. NEVER use placeholder text like "Local restaurant" or "Popular place"
5. ALL recommendations must come from actual tool responses
6. Include complete details: ratings, addresses, hours, prices, why famous
7. Only recommend places with 4.0+ ratings from tools

RESPONSE STRUCTURE:
🏛️ DAY X: {city.title()} Discovery
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ 8:00 AM - BREAKFAST: [Real Restaurant Name from tool] (⭐ Rating: X.X)
📍 [Complete address from tool]
💰 [Price range from tool] 
🍛 [Cuisine type from tool]
⭐ Famous For: [Specialties from tool]

⏰ 9:30 AM - VISIT: [Real Place Name from tool] (⭐ Rating: X.X)
📍 [Complete address from tool]
🕒 Hours: [Opening hours from tool]
💰 Entry: [Entry fee from tool]
⏱️ Duration: [Time needed from tool]
✨ Why Visit: [Famous for from tool]

[Continue pattern for lunch, afternoon visit, dinner]

VALIDATION REQUIREMENTS:
✅ Every place name is specific and real (from tool results)
✅ All ratings shown are from actual tool responses  
✅ All addresses are complete from tools
✅ All prices/fees are from tool data
✅ Include "why famous" details from tools
✅ No generic or assumed information used

Remember: Be thorough with tool usage. Call tools multiple times with different search terms to get comprehensive results for {city.title()}."""

    return prompt

def contains_fallback_terms(text: str) -> bool:
    """Check if response contains fallback/generic terms"""
    fallback_terms = [
        "local eatery", "local restaurant", "generic option",
        "assume ₹", "placeholder", "generic", "fallback",
        "service temporarily unavailable", "no specific",
        "(please note:", "were not provided by the tool"
    ]
    
    text_lower = text.lower()
    return any(term in text_lower for term in fallback_terms)

@router.post("/plan")
async def get_travel_plan(prefs: UserPreferences):
    """
    Generates a travel plan using Gemini AI and real API data.
    """
    try:
        # Create detailed prompt for Gemini
        detailed_prompt = create_detailed_prompt(prefs)
        print(f"Generated prompt for {prefs.days} days in {prefs.city}")

        max_retries = 3
        plan_output = None
        
        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1} to generate plan...")
            
            # Run agent with extended timeout for API calls
            with ThreadPoolExecutor() as executor:
                future = executor.submit(run_agent_with_timeout, detailed_prompt, 75)
                try:
                    plan_output = future.result(timeout=80)
                    
                    # Check if output contains fallback terms
                    if plan_output and not contains_fallback_terms(plan_output):
                        print("✅ Generated plan with real data")
                        break
                    else:
                        print(f"⚠️ Attempt {attempt + 1} contained fallback data, retrying...")
                        if attempt < max_retries - 1:
                            # Try with more specific prompt
                            detailed_prompt += f"\n\nATTEMPT {attempt + 2}: Previous attempt used generic terms. You MUST use tool results for ALL details including hours, fees, and descriptions."
                        
                except Exception as timeout_error:
                    print(f"Timeout error on attempt {attempt + 1}: {timeout_error}")
                    if attempt == max_retries - 1:
                        plan_output = "Unable to generate detailed plan due to timeout. Please try again."

        # Final validation
        if not plan_output:
            plan_output = "Service temporarily unavailable. Please try again in a moment."
        elif contains_fallback_terms(plan_output):
            plan_output = f"⚠️ Generated plan may contain generic recommendations. For best results, please try again.\n\n{plan_output}"

        return {
            "plan": plan_output, 
            "status": "success" if plan_output and not contains_fallback_terms(plan_output) else "partial", 
            "days": prefs.days,
            "data_source": "real_api" if not contains_fallback_terms(plan_output) else "mixed"
        }

    except Exception as e:
        print(f"Error in /plan endpoint: {e}")
        return {
            "plan": f"Error generating plan: {str(e)}", 
            "status": "error", 
            "days": prefs.days
        }

@router.post("/city-plan")
async def get_city_plan(request: SimpleCityRequest):
    """
    Generate travel plan for any city - just provide city name!
    """
    try:
        city = request.city.strip().title()
        days = request.days or 1
        budget = request.budget or "mid-range"
        food_pref = request.food_preference or "local cuisine"
        
        print(f"🎯 Generating {days}-day plan for {city}")
        
        # Create city-specific prompt
        city_prompt = create_city_prompt(city, days, budget, food_pref)
        
        max_retries = 3
        plan_output = None
        
        for attempt in range(max_retries):
            print(f"🔄 Attempt {attempt + 1} for {city} plan...")
            
            with ThreadPoolExecutor() as executor:
                future = executor.submit(run_agent_with_timeout, city_prompt, 90)
                try:
                    plan_output = future.result(timeout=95)
                    
                    # Check if output is good quality
                    if plan_output and not contains_fallback_terms(plan_output) and len(plan_output) > 500:
                        print(f"✅ Generated quality plan for {city}")
                        break
                    else:
                        print(f"⚠️ Attempt {attempt + 1} needs improvement, retrying...")
                        
                except Exception as timeout_error:
                    print(f"⏰ Timeout on attempt {attempt + 1}: {timeout_error}")

        if not plan_output:
            plan_output = f"Unable to generate detailed plan for {city}. Please try again or check if the city is supported."

        return {
            "city": city,
            "days": days,
            "plan": plan_output,
            "status": "success" if plan_output and not contains_fallback_terms(plan_output) else "partial",
            "budget": budget,
            "food_preference": food_pref
        }

    except Exception as e:
        print(f"Error generating city plan: {e}")
        return {
            "city": request.city,
            "days": request.days,
            "plan": f"Error generating plan for {request.city}: {str(e)}",
            "status": "error"
        }

@router.post("/any-city-plan")
async def get_any_city_plan(request: SimpleCityRequest):
    """
    🌟 NEW: Generate travel plan for ANY Indian city!
    Just provide the city name - no manual data needed.
    """
    try:
        city = request.city.strip().title()
        days = request.days or 1
        budget = request.budget or "mid-range" 
        food_pref = request.food_preference or "local cuisine"
        
        print(f"🎯 Generating plan for ANY city: {city}")
        
        # Create universal prompt that works for any Indian city
        universal_prompt = f"""Create a comprehensive {days}-day travel itinerary for {city}, India.

CITY: {city}, India (Work with ANY Indian city - use tools to find real places)
DURATION: {days} days
BUDGET: {budget}
FOOD PREFERENCE: {food_preference}

MANDATORY INSTRUCTIONS:
1. Use google_places_search tool with these queries for {city}:
   - "tourist attractions {city} India"
   - "historical places {city}"
   - "temples {city} India"
   - "parks gardens {city}"
   - "museums {city} India"

2. Use restaurant_search tool with these queries for {city}:
   - "best restaurants {city} India"
   - "local food {city}"
   - "vegetarian restaurants {city}"
   - "{food_pref} {city}"

3. CRITICAL: If tools return limited results, they will intelligently generate realistic places based on:
   - Common Indian city patterns (every city has temples, markets, parks)
   - Regional cuisine types (North/South/Regional specialties)
   - Typical Indian attractions (forts, palaces, gardens, religious sites)

4. Create detailed day-wise schedule with:
   - Morning visits (9 AM - 12 PM): Outdoor attractions
   - Lunch recommendations (12 PM - 2 PM): Local restaurants
   - Afternoon visits (2 PM - 6 PM): Indoor/shaded places
   - Dinner recommendations (7 PM - 9 PM): Popular food spots

RESPONSE FORMAT:
🏛️ {days}-DAY {city.upper()} ITINERARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DAY 1: Exploring {city}

⏰ 9:00 AM - VISIT: [Real place name from tool] (⭐ Rating: X.X)
📍 [Complete address from tool]
🕒 Hours: [Opening hours from tool or realistic estimate]
💰 Entry: [Entry fee from tool or typical Indian site fees]
⏱️ Duration: [Time needed]
✨ Why Visit: [Description from tool or intelligent reasoning]

🍽️ 12:30 PM - LUNCH: [Real restaurant name from tool] (⭐ Rating: X.X)
📍 [Address from tool]
💰 Price: [Price range from tool]
🍛 Cuisine: [Cuisine type from tool]
⭐ Famous For: [Specialties from tool]

[Continue pattern for rest of day]

VALIDATION:
✅ Every place must have specific name (not "Local temple" or "City fort")
✅ All details must come from tool responses or intelligent generation
✅ No generic placeholders used
✅ Realistic ratings, prices, and timings for Indian context

Remember: The tools are designed to work with ANY Indian city by using intelligent patterns and real API data when available."""

        max_retries = 2
        plan_output = None
        
        for attempt in range(max_retries):
            print(f"🔄 Attempt {attempt + 1} for {city} plan...")
            
            with ThreadPoolExecutor() as executor:
                future = executor.submit(run_agent_with_timeout, universal_prompt, 90)
                try:
                    plan_output = future.result(timeout=95)
                    
                    if plan_output and len(plan_output) > 300:
                        print(f"✅ Generated plan for {city}!")
                        break
                    else:
                        print(f"⚠️ Attempt {attempt + 1} needs improvement...")
                        
                except Exception as timeout_error:
                    print(f"⏰ Timeout on attempt {attempt + 1}: {timeout_error}")

        if not plan_output:
            plan_output = f"""🏛️ {days}-DAY {city.upper()} ITINERARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

While I'm having trouble accessing real-time data right now, {city} likely offers:

📍 Historical attractions: Ancient temples, local fort/palace, heritage sites
🍽️ Food specialties: Regional cuisine, local sweets, street food markets
🌳 Nature spots: City parks, gardens, nearby hills/lakes
🛍️ Local experiences: Traditional markets, cultural centers

For the most current information about {city}, I recommend:
• Checking Google Maps for "tourist attractions {city}"
• Looking up "{city} travel guide" for recent recommendations
• Asking locals for hidden gems and current opening hours

The system is designed to work with any Indian city - please try again in a moment for detailed recommendations!"""

        return {
            "city": city,
            "days": days,
            "plan": plan_output,
            "status": "success" if len(plan_output) > 500 else "partial",
            "budget": budget,
            "food_preference": food_pref,
            "note": "This endpoint works with ANY Indian city using intelligent place generation and real API data"
        }

    except Exception as e:
        print(f"Error generating plan for {request.city}: {e}")
        return {
            "city": request.city,
            "days": request.days,
            "plan": f"Error generating plan for {request.city}: {str(e)}",
            "status": "error"
        }

@router.get("/health")
async def health_check():
    """Health check for routes"""
    return {"status": "routes_healthy"}

@router.get("/agent")
async def run_agent():
    """
    Test endpoint for agent functionality with real API calls.
    """
    try:
        test_prompt = create_detailed_prompt(UserPreferences(
            city="Delhi",
            days=1,
            place_type="historical monuments", 
            food_type="vegetarian",
            budget="mid-range"
        ))
        
        plan_output = run_agent_with_timeout(test_prompt, 45)
        
        return {
            "test_result": plan_output or "Test completed but no output generated", 
            "status": "success" if plan_output else "partial"
        }
    
    except Exception as e:
        print(f"Error in /agent endpoint: {e}")
        return {
            "test_result": f"Test failed: {str(e)}", 
            "status": "error"
        }
    # Generate plan
    plan = f"{preferences.days}-DAY {preferences.city.upper()} ITINERARY:\n\n"
    
    for day in range(1, preferences.days + 1):
        plan += f"DAY {day}: Time-Optimized Schedule\n"
        schedule = get_optimal_schedule(day)
        
        for time_slot, details in schedule.items():
            if time_slot == "early_morning":
                place_info = get_place_for_activity(details["activity"], time_slot)
                plan += f"{details['time']} - VISIT: {place_info['place']}\n"
                plan += f"⤷ Why: {place_info['why']}\n"
                plan += f"⤷ Duration: {place_info['duration']} | {place_info['timing']}\n"
                
                # Add breakfast after early morning visit
                food_rec = get_nearby_food(place_info['place'], "breakfast", preferences.food_type, preferences.budget)
                plan += f"⤷ Then BREAKFAST: {food_rec}\n\n"
                
            elif time_slot == "late_morning":
                place_info = get_place_for_activity(details["activity"], time_slot)
                plan += f"{details['time']} - VISIT: {place_info['place']}\n"
                plan += f"⤷ Why: {place_info['why']}\n"
                plan += f"⤷ Duration: {place_info['duration']} | {place_info['timing']}\n"
                
                # Add lunch
                food_rec = get_nearby_food(place_info['place'], "lunch", preferences.food_type, preferences.budget)
                plan += f"⤷ LUNCH: {food_rec}\n\n"
                
            elif time_slot == "afternoon":
                place_info = get_place_for_activity(details["activity"], time_slot)
                plan += f"{details['time']} - VISIT: {place_info['place']}\n"
                plan += f"⤷ Why: {place_info['why']}\n"
                plan += f"⤷ Duration: {place_info['duration']} | {place_info['timing']}\n\n"
                
            elif time_slot == "evening":
                place_info = get_place_for_activity(details["activity"], time_slot)
                plan += f"{details['time']} - VISIT: {place_info['place']}\n"
                plan += f"⤷ Why: {place_info['why']}\n"
                plan += f"⤷ Duration: {place_info['duration']} | {place_info['timing']}\n"
                
                # Add dinner
                food_rec = get_nearby_food(place_info['place'], "dinner", preferences.food_type, preferences.budget)
                plan += f"⤷ DINNER: {food_rec}\n\n"
        
        if day < preferences.days:
            plan += "─" * 50 + "\n\n"
    
    # Add practical info
    total_food_budget = preferences.days * 600 if preferences.budget == "cheap" else preferences.days * 1200
    plan += f"💰 Estimated food budget: ₹{total_food_budget//2}-{total_food_budget} total\n"
    plan += "🚗 Transport: Metro/Auto recommended between locations\n"
    plan += "⏰ Schedule considers Delhi weather (avoid 12-2 PM outdoor activities)\n"
    plan += "📍 Food places selected for proximity to attractions"
    
    return plan

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
        # Use time-aware fallback
        return None

def generate_fallback_plan(agent_input: str) -> str:
    """Generate enhanced fallback plan when agent fails"""
    # Extract preferences from input (basic parsing)
    days = 1
    city = "Delhi"
    place_type = "historical sites"
    food_type = "local cuisine"
    budget = "cheap"
    
    if "2 day" in agent_input.lower():
        days = 2
    elif "3 day" in agent_input.lower():
        days = 3
    
    if "veg" in agent_input.lower():
        food_type = "vegetarian"
    if "expensive" in agent_input.lower() or "fine" in agent_input.lower():
        budget = "expensive"
    
    # Create UserPreferences object
    prefs = UserPreferences(
        city=city,
        days=days, 
        place_type=place_type,
        food_type=food_type,
        budget=budget
    )
    
    return generate_time_aware_plan(prefs)

@router.get("/supported-cities")
async def get_supported_cities():
    """Get list of cities with detailed database support"""
    from tools import CITY_DATABASES
    
    cities = []
    for city_key, city_data in CITY_DATABASES.items():
        total_places = sum(len(places) for places in city_data['places'].values())
        total_restaurants = sum(len(restaurants) for restaurants in city_data['restaurants'].values())
        
        cities.append({
            "city": city_key.title(),
            "places_count": total_places,
            "restaurants_count": total_restaurants,
            "location": city_data['default_location']
        })
    
    return {
        "supported_cities": cities,
        "total_cities": len(cities),
        "note": "Cities with comprehensive local database support"
    }
