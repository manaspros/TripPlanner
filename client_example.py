#!/usr/bin/env python3
"""
Simple client example for the Travel Planner API
Shows how to use the API from a Python client
"""

import requests
import json

def get_travel_plan(city, time_of_day, place_type, food_type, budget):
    """
    Get a travel plan from the API
    
    Args:
        city (str): City to visit (e.g., "Delhi", "Mumbai")
        time_of_day (str): Time of day (e.g., "morning", "afternoon", "evening")
        place_type (str): Type of places to visit (e.g., "historical sites", "museums", "parks")
        food_type (str): Type of food (e.g., "local cuisine", "street food", "Italian")
        budget (str): Budget level (e.g., "cheap", "mid-range", "expensive")
    
    Returns:
        str: Travel plan or error message
    """
    url = "http://127.0.0.1:8000/api/plan"
    
    preferences = {
        "city": city,
        "time_of_day": time_of_day,
        "place_type": place_type,
        "food_type": food_type,
        "budget": budget
    }
    
    try:
        response = requests.post(url, json=preferences)
        response.raise_for_status()
        
        data = response.json()
        return data.get("plan", "No plan returned")
    
    except requests.exceptions.RequestException as e:
        return f"Error: Failed to get travel plan - {e}"
    except Exception as e:
        return f"Error: {e}"

def main():
    """Example usage of the travel planner"""
    print("🧳 Travel Planner Client Example")
    print("="*40)
    
    # Example 1: Delhi evening tour
    print("\n📍 Example 1: Delhi Evening Historical Tour")
    plan1 = get_travel_plan(
        city="Delhi",
        time_of_day="evening", 
        place_type="historical sites",
        food_type="Mughlai cuisine",
        budget="mid-range"
    )
    print(plan1)
    
    # Example 2: Mumbai afternoon exploration
    print("\n📍 Example 2: Mumbai Afternoon Museums")
    plan2 = get_travel_plan(
        city="Mumbai",
        time_of_day="afternoon",
        place_type="museums",
        food_type="street food", 
        budget="cheap"
    )
    print(plan2)
    
    # Interactive example
    print("\n" + "="*40)
    print("🎯 Create Your Own Plan!")
    
    try:
        city = input("Enter city: ").strip()
        time_of_day = input("Enter time of day (morning/afternoon/evening): ").strip()
        place_type = input("Enter place type (historical sites/museums/parks): ").strip()
        food_type = input("Enter food type: ").strip()
        budget = input("Enter budget (cheap/mid-range/expensive): ").strip()
        
        if all([city, time_of_day, place_type, food_type, budget]):
            print(f"\n🎯 Your Custom Plan for {city}:")
            custom_plan = get_travel_plan(city, time_of_day, place_type, food_type, budget)
            print(custom_plan)
        else:
            print("❌ Please provide all required fields.")
            
    except KeyboardInterrupt:
        print("\n👋 Thanks for using Travel Planner!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
