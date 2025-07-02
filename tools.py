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
            return self._generate_fallback_places(query, location)
        
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
                
                return validated_places if validated_places else self._generate_fallback_places(query, location)
                
            except json.JSONDecodeError:
                print("⚠️ Failed to parse AI response as JSON, using fallback")
                return self._generate_fallback_places(query, location)
                
        except Exception as e:
            print(f"⚠️ AI place generation failed: {e}")
            return self._generate_fallback_places(query, location)
    
    def _generate_fallback_places(self, query: str, location: str):
        """Generate basic fallback places when AI fails"""
        return [
            {
                'name': f'Popular {query.title()} Attraction in {location}',
                'rating': 4.2,
                'address': f'{location}, India',
                'place_id': 'fallback_place_1',
                'hours': '9:00 AM - 6:00 PM',
                'entry_fee': 'Entry fee varies',
                'duration': '2-3 hours',
                'why_famous': f'Well-known {query} destination in {location}'
            },
            {
                'name': f'{location} Heritage Site',
                'rating': 4.3,
                'address': f'{location}, India',
                'place_id': 'fallback_place_2',
                'hours': '9:00 AM - 5:00 PM',
                'entry_fee': 'Varies by location',
                'duration': '2-4 hours',
                'why_famous': f'Important cultural heritage site in {location}'
            }
        ]

    def _run(self, query: str, location: Optional[str] = None, type: Optional[str] = None, time_of_day: Optional[str] = None) -> str:
        location = location or "Delhi"
        time_of_day = time_of_day or "morning"
        
        places = self._generate_places_with_ai(query, location, type, time_of_day)
        
        if not places:
            return f"Unable to generate place recommendations for {query} in {location}. Please try a different search."
        
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
    description: str = "AI-powered restaurant search that generates comprehensive food recommendations"
    args_schema: Type[BaseModel] = FoodSearchInput

    def _generate_restaurants_with_ai(self, query: str, location: str, meal_type: str = "lunch", near_place: str = None):
        """Use Gemini AI to generate realistic restaurant recommendations"""
        if not tool_model:
            return self._generate_fallback_restaurants(query, location)
        
        try:
            near_text = f" near {near_place}" if near_place else ""
            prompt = f"""
            Generate 3-5 realistic and popular restaurants for "{query}" food in {location}, India{near_text}.
            
            Requirements:
            - Only suggest restaurants that could realistically exist in {location}
            - Focus on {meal_type} options
            - Include variety: local favorites, established chains, street food places
            - Provide accurate, realistic information for Indian restaurants
            
            For each restaurant, provide:
            1. Name (realistic restaurant name)
            2. Rating (4.0-4.7 range)
            3. Complete address
            4. Price range in Indian rupees per person
            5. Cuisine type
            6. Famous dishes (specific to cuisine)
            7. What makes it special
            8. Suitable meal types
            
            Format as JSON array:
            [
              {{
                "name": "Restaurant Name",
                "rating": 4.4,
                "address": "Complete address in {location}",
                "price_range": "₹200-400 per person",
                "cuisine": "Cuisine Type",
                "famous_for": "Famous dishes and specialties",
                "specialties": "Specific dishes",
                "meal_type": ["lunch", "dinner"]
              }}
            ]
            
            Make it realistic for {location}, India.
            """
            
            response = tool_model.generate_content(prompt)
            
            # Parse JSON response
            try:
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
                
                restaurants = json.loads(json_text)
                
                # Validate and ensure proper data
                validated_restaurants = []
                for restaurant in restaurants[:5]:
                    if isinstance(restaurant, dict) and restaurant.get('name'):
                        validated_restaurants.append({
                            'name': restaurant.get('name', 'Local Restaurant'),
                            'rating': float(restaurant.get('rating', 4.2)),
                            'address': restaurant.get('address', f'{location}, India'),
                            'price_range': restaurant.get('price_range', '₹200-400 per person'),
                            'cuisine': restaurant.get('cuisine', 'Multi-cuisine'),
                            'famous_for': restaurant.get('famous_for', 'Quality food and service'),
                            'specialties': restaurant.get('specialties', 'Local favorites'),
                            'meal_type': restaurant.get('meal_type', [meal_type])
                        })
                
                return validated_restaurants if validated_restaurants else self._generate_fallback_restaurants(query, location)
                
            except json.JSONDecodeError:
                print("⚠️ Failed to parse restaurant AI response, using fallback")
                return self._generate_fallback_restaurants(query, location)
                
        except Exception as e:
            print(f"⚠️ AI restaurant generation failed: {e}")
            return self._generate_fallback_restaurants(query, location)
    
    def _generate_fallback_restaurants(self, query: str, location: str):
        """Generate basic fallback restaurants when AI fails"""
        return [
            {
                'name': f'{location} {query.title()} Restaurant',
                'rating': 4.2,
                'address': f'{location}, India',
                'price_range': '₹200-400 per person',
                'cuisine': f'{query.title()} Cuisine',
                'famous_for': f'Authentic {query} dishes',
                'specialties': f'Traditional {query} preparations',
                'meal_type': ['lunch', 'dinner']
            },
            {
                'name': f'Popular {query.title()} Dhaba {location}',
                'rating': 4.3,
                'address': f'{location}, India',
                'price_range': '₹150-300 per person',
                'cuisine': f'Traditional {query.title()}',
                'famous_for': f'Home-style {query} cooking',
                'specialties': f'Fresh {query} meals',
                'meal_type': ['lunch', 'dinner']
            }
        ]

    def _run(self, query: str, location: Optional[str] = None, near_place: Optional[str] = None, meal_type: Optional[str] = None) -> str:
        location = location or "Delhi"
        meal_type = meal_type or "lunch"
        
        restaurants = self._generate_restaurants_with_ai(query, location, meal_type, near_place)
        
        if not restaurants:
            return f"Unable to generate restaurant recommendations for {query} in {location}. Please try a different cuisine."
        
        result = f"🍽️ RESTAURANTS FOR {meal_type.upper()} in {location}:\n\n"
        for i, restaurant in enumerate(restaurants[:3]):
            result += f"🏪 {restaurant['name']} (⭐ Rating: {restaurant['rating']})\n"
            result += f"   📍 Address: {restaurant['address']}\n"
            result += f"   💰 Price Range: {restaurant['price_range']}\n"
            result += f"   🍛 Cuisine: {restaurant['cuisine']}\n"
            result += f"   ⭐ Famous For: {restaurant['famous_for']}\n"
            result += f"   🍴 Specialties: {restaurant['specialties']}\n"
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