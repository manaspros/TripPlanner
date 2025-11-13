# filepath: d:\Code\Majorproject\tools.py
# Define your tools here - AI-powered version without predefined data
import os
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from typing import Optional, Type, List
import json
import time
from urllib.parse import quote_plus
import random
from config import config

# Import cache manager for API call optimization
try:
    from cache_manager import cache_manager
    CACHE_AVAILABLE = True
except ImportError:
    print("Warning: cache_manager not available, caching disabled")
    CACHE_AVAILABLE = False

# Handle imports with fallbacks
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    print("Warning: google.generativeai not available")
    GENAI_AVAILABLE = False

# Configure Gemini for tools
GOOGLE_API_KEY = config.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")

if GENAI_AVAILABLE and GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # Initialize Gemini model for tools
    try:
        tool_model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Gemini model configured for tools")
    except Exception as e:
        print(f"⚠️ Gemini model configuration failed: {e}")
        tool_model = None
else:
    tool_model = None

# --- Input Schemas ---
class PlaceSearchInput(BaseModel):
    query: str = Field(description="Search query for places")
    location: Optional[str] = Field(None, description="Location bias")
    type: Optional[str] = Field(None, description="Type of place")
    time_of_day: Optional[str] = Field(None, description="Time preference: morning/afternoon/evening")

class FoodSearchInput(BaseModel):
    query: str = Field(description="Food type search query")
    location: Optional[str] = Field(None, description="Location for search")
    near_place: Optional[str] = Field(None, description="Find food near this place")
    meal_type: Optional[str] = Field(None, description="breakfast/lunch/dinner/snacks")

# --- AI-Powered Google Places Tool ---
class AIGooglePlacesTool(BaseTool):
    name: str = "google_places_search"
    description: str = "AI-powered place search that generates comprehensive information about tourist attractions"
    args_schema: Type[BaseModel] = PlaceSearchInput

    def _generate_places_with_ai(self, query: str, location: str, place_type: str = None, time_of_day: str = "morning"):
        """Use Gemini AI to generate realistic place recommendations"""
        if not tool_model:
            # No fallback: return error message
            return None
        
        try:
            prompt = f"""
            Generate 3-5 realistic and popular tourist attractions for the query "{query}" in {location}, India.
            
            Requirements:
            - Only suggest REAL places that actually exist in {location}
            - Focus on places suitable for {time_of_day} visits
            - Include places matching type: {place_type or 'any tourist attraction'}
            - Provide accurate, realistic information
            
            For each place, provide:
            1. Name (real place name)
            2. Rating (4.0-4.8 range, realistic)
            3. Complete address with pincode
            4. Opening hours (realistic for Indian attractions)
            5. Entry fee (realistic Indian prices)
            6. Recommended duration
            7. Why it's famous (2-3 sentences)
            
            Format as JSON array:
            [
              {{
                "name": "Exact Place Name",
                "rating": 4.5,
                "address": "Complete address with area and pincode",
                "place_id": "unique_id",
                "hours": "Opening hours",
                "entry_fee": "Entry fee details",
                "duration": "Recommended visit duration",
                "why_famous": "Why this place is famous and worth visiting"
              }}
            ]
            
            Important: Only include places that actually exist in {location}. Be accurate and realistic.
            """
            
            response = tool_model.generate_content(prompt)
            
            # Parse JSON response
            try:
                # Extract JSON from response
                response_text = response.text
                if '```json' in response_text:
                    json_start = response_text.find('```json') + 7
                    json_end = response_text.find('```', json_start)
                    json_text = response_text[json_start:json_end].strip()
                elif '[' in response_text and ']' in response_text:
                    json_start = response_text.find('[')
                    json_end = response_text.rfind(']') + 1
                    json_text = response_text[json_start:json_end]
                else:
                    json_text = response_text
                
                places = json.loads(json_text)
                
                # Validate and ensure we have proper data
                validated_places = []
                for place in places[:5]:
                    if isinstance(place, dict) and place.get('name'):
                        validated_places.append({
                            'name': place.get('name', 'Unknown Place'),
                            'rating': float(place.get('rating', 4.2)),
                            'address': place.get('address', f'{location}, India'),
                            'place_id': place.get('place_id', f"ai_generated_{place.get('name', '').lower().replace(' ', '_')}"),
                            'hours': place.get('hours', '9:00 AM - 6:00 PM'),
                            'entry_fee': place.get('entry_fee', 'Entry fee varies'),
                            'duration': place.get('duration', '2-3 hours'),
                            'why_famous': place.get('why_famous', 'Popular local attraction')
                        })
                
                return validated_places if validated_places else None
                
            except json.JSONDecodeError:
                print("⚠️ Failed to parse AI response as JSON, using fallback")
                return None
                
        except Exception as e:
            print(f"⚠️ AI place generation failed: {e}")
            return None

    def _run(self, query: str, location: Optional[str] = None, type: Optional[str] = None, time_of_day: Optional[str] = None) -> str:
        location = location or "Delhi"
        time_of_day = time_of_day or "morning"
        
        places = self._generate_places_with_ai(query, location, type, time_of_day)
        
        if not places:
            return f"Unable to generate place recommendations for {query} in {location}. Please try again later."
        
        result = f"🏛️ PLACES FOR {time_of_day.upper()} VISIT in {location}:\n\n"
        for i, place in enumerate(places[:3]):
            result += f"📍 {place['name']} (⭐ Rating: {place['rating']})\n"
            result += f"   📍 Address: {place['address']}\n"
            result += f"   🕒 Hours: {place['hours']}\n"
            result += f"   💰 Entry: {place['entry_fee']}\n"
            result += f"   ⏱️ Duration: {place['duration']}\n"
            result += f"   ✨ Why Visit: {place['why_famous']}\n"
            
            if i < len(places) - 1:
                result += "\n"
        
        return result

    async def _arun(self, query: str, location: Optional[str] = None, type: Optional[str] = None, time_of_day: Optional[str] = None) -> str:
        return self._run(query, location, type, time_of_day)

# --- AI-Powered Restaurant Search Tool ---
class AIRestaurantSearchTool(BaseTool):
    name: str = "restaurant_search"
    description: str = "Searches for real restaurants using Google Places API only. Does NOT generate restaurants."
    args_schema: Type[BaseModel] = FoodSearchInput

    def _search_restaurants_google_places(self, query: str, location: str, meal_type: str = "lunch", near_place: str = None):
        """Search for real restaurants using Google Places API only (with caching)"""
        GOOGLE_PLACES_API_KEY = config.GOOGLE_PLACES_API_KEY or os.getenv("GOOGLE_PLACES_API_KEY")
        if not GOOGLE_PLACES_API_KEY:
            return None

        # Try cache first (if available)
        if CACHE_AVAILABLE:
            cached_result = cache_manager.get(
                "restaurants",
                query=query,
                location=location,
                meal_type=meal_type,
                near_place=near_place
            )
            if cached_result is not None:
                print(f"✅ Using cached restaurant data for {query} in {location}")
                return cached_result

            # Check rate limit
            if not cache_manager.check_rate_limit("google_places"):
                print(f"⚠️ Google Places rate limit reached, using any available cache")
                # Try to return even expired cache
                return None

        # Build the search URL
        base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        search_query = f"{query} restaurants in {location}"
        params = {
            "query": search_query,
            "type": "restaurant",
            "key": GOOGLE_PLACES_API_KEY,
        }
        try:
            # Record API call for rate limiting
            if CACHE_AVAILABLE:
                cache_manager.record_api_call("google_places")

            response = requests.get(base_url, params=params, timeout=10)
            data = response.json()
            if data.get("status") != "OK" or not data.get("results"):
                return None

            # Filter and format results
            restaurants = []
            for r in data["results"]:
                rating = r.get("rating", 0)
                if rating and float(rating) >= 4.0:
                    restaurants.append({
                        "name": r.get("name", ""),
                        "rating": float(rating),
                        "address": r.get("formatted_address", ""),
                        "price_level": r.get("price_level", None),
                        "cuisine": query.title(),
                        "famous_for": "",
                        "specialties": "",
                        "meal_type": [meal_type],
                        "place_id": r.get("place_id", ""),
                    })
                if len(restaurants) >= 5:
                    break

            # Cache the results (if available)
            if CACHE_AVAILABLE and restaurants:
                cache_manager.set(
                    "restaurants",
                    restaurants,
                    query=query,
                    location=location,
                    meal_type=meal_type,
                    near_place=near_place
                )
                print(f"✅ Cached restaurant data for {query} in {location}")

            return restaurants if restaurants else None
        except Exception as e:
            print(f"⚠️ Google Places restaurant search failed: {e}")
            return None

    def _run(self, query: str, location: Optional[str] = None, near_place: Optional[str] = None, meal_type: Optional[str] = None) -> str:
        location = location or "Delhi"
        meal_type = meal_type or "lunch"

        # Only use Google Places API for restaurant search
        restaurants = self._search_restaurants_google_places(query, location, meal_type, near_place)

        if not restaurants:
            return f"Unable to find real restaurants for {query} in {location} using Google Places. Please try a different search or check your API key."

        result = f"🍽️ RESTAURANTS FOR {meal_type.upper()} in {location} (from Google Places):\n\n"
        for i, restaurant in enumerate(restaurants[:3]):
            result += f"🏪 {restaurant['name']} (⭐ Rating: {restaurant['rating']})\n"
            result += f"   📍 Address: {restaurant['address']}\n"
            if restaurant.get("price_level") is not None:
                result += f"   💰 Price Level: {restaurant['price_level']}\n"
            result += f"   🍛 Cuisine: {restaurant['cuisine']}\n"
            # No AI-generated famous_for or specialties
            result += f"   🕒 Perfect for: {', '.join(restaurant['meal_type'])}\n"
            if i < len(restaurants) - 1:
                result += "\n"
        return result

    async def _arun(self, query: str, location: Optional[str] = None, near_place: Optional[str] = None, meal_type: Optional[str] = None) -> str:
        return self._run(query, location, near_place, meal_type)

# --- AI-Powered Reviews and Insights Tool ---
class AIReviewsTool(BaseTool):
    name: str = "get_reviews"
    description: str = "AI-powered tool that generates detailed insights and travel tips for places and restaurants"
    args_schema: Type[BaseModel] = FoodSearchInput

    def _generate_insights_with_ai(self, query: str, location: str):
        """Use Gemini AI to generate travel insights and tips"""
        if not tool_model:
            return self._generate_fallback_insights(query, location)
        
        try:
            prompt = f"""
            Generate detailed travel insights and tips for "{query}" in {location}, India.
            
            Provide practical information including:
            1. Best time to visit
            2. What to expect
            3. Insider tips
            4. Cost considerations
            5. Cultural etiquette if relevant
            6. Transportation tips
            7. What to bring/wear
            
            Make it practical and helpful for tourists visiting {location}.
            Focus on real, actionable advice.
            """
            
            response = tool_model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"⚠️ AI insights generation failed: {e}")
            return self._generate_fallback_insights(query, location)
    
    def _generate_fallback_insights(self, query: str, location: str):
        """Generate basic fallback insights when AI fails"""
        return f"""
        📝 TRAVEL TIPS for {query} in {location}:
        
        🕒 Best Time: Early morning or late afternoon for comfortable weather
        💡 Tip: Carry water and wear comfortable walking shoes
        💰 Budget: Keep cash handy as many places prefer cash payments
        📱 Preparation: Check opening hours before visiting
        🎒 Essentials: Carry ID proof for heritage sites and attractions
        """

    def _run(self, query: str, location: Optional[str] = None, near_place: Optional[str] = None, meal_type: Optional[str] = None) -> str:
        location = location or "Delhi"
        
        insights = self._generate_insights_with_ai(query, location)
        
        return f"📝 DETAILED INSIGHTS for {query} in {location}:\n\n{insights}"

    async def _arun(self, query: str, location: Optional[str] = None, near_place: Optional[str] = None, meal_type: Optional[str] = None) -> str:
        return self._run(query, location, near_place, meal_type)

# --- Tools List ---
tools = [
    AIGooglePlacesTool(),
    AIRestaurantSearchTool(),
    AIReviewsTool()
]