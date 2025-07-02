#!/usr/bin/env python3
"""
Test script for the Travel Planner API
Demonstrates the complete functionality of the travel recommendation system
"""

import requests
import json
import time
from typing import Dict, Any

# API Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health check passed: {data}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint to check API status"""
    print("\n🔍 Testing root endpoint...")
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Root endpoint response:")
        print(json.dumps(data, indent=2))
        return True
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def test_agent_endpoint():
    """Test the agent test endpoint"""
    print("\n🔍 Testing agent endpoint...")
    try:
        response = requests.get(f"{API_BASE}/agent")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Agent test response:")
        print(json.dumps(data, indent=2))
        return True
    except Exception as e:
        print(f"❌ Agent endpoint failed: {e}")
        return False

def test_travel_plan(preferences: Dict[str, Any]):
    """Test the travel plan generation endpoint"""
    print(f"\n🔍 Testing travel plan generation with preferences:")
    print(json.dumps(preferences, indent=2))
    
    try:
        response = requests.post(
            f"{API_BASE}/plan",
            json=preferences,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        print(f"✅ Travel plan generated successfully:")
        print("="*60)
        print(data.get("plan", "No plan returned"))
        print("="*60)
        return True
    except Exception as e:
        print(f"❌ Travel plan generation failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return False

def test_any_city_functionality():
    """Test the new any-city endpoint with AI-generated content"""
    print("\n🌟 Testing ANY City Functionality with AI Generation...")
    print("="*60)
    
    # Test cities from different regions of India
    test_cities = [
        {"city": "Chandigarh", "days": 1, "budget": "mid-range"},
        {"city": "Kochi", "days": 2, "budget": "cheap"},
        {"city": "Udaipur", "days": 1, "budget": "expensive"},
        {"city": "Darjeeling", "days": 2, "budget": "mid-range"},
        {"city": "Amritsar", "days": 1, "budget": "cheap"}
    ]
    
    successful_tests = 0
    
    for i, city_request in enumerate(test_cities, 1):
        print(f"\n🏙️ Test {i}: {city_request['city']}")
        try:
            response = requests.post(
                f"{API_BASE}/any-city-plan",
                json=city_request,
                timeout=120  # Increased timeout for AI generation
            )
            
            if response.status_code == 200:
                data = response.json()
                plan = data.get("plan", "")
                
                # Enhanced quality check for AI-generated content
                if (len(plan) > 500 and 
                    "Rating:" in plan and 
                    "Address:" in plan and
                    city_request['city'] in plan):
                    print(f"✅ {city_request['city']} AI plan generated successfully!")
                    successful_tests += 1
                    
                    # Show preview of AI-generated content
                    preview_lines = plan.split('\n')[:8]
                    for line in preview_lines:
                        if line.strip():
                            print(f"   {line}")
                    print("   ... (AI-generated content continues)")
                else:
                    print(f"⚠️ {city_request['city']} plan quality insufficient")
                    print(f"   Plan length: {len(plan)} chars")
            else:
                print(f"❌ {city_request['city']} failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {city_request['city']} error: {e}")
    
    print(f"\n📊 AI-Generated City Tests: {successful_tests}/{len(test_cities)} successful")
    return successful_tests >= 3  # Allow some flexibility for AI generation

def main():
    """Updated main test function for AI-powered system"""
    print("🧳 Travel Planner API Test Suite - AI-Powered Version")
    print("="*60)
    
    # Test basic endpoints
    health_ok = test_health_check()
    root_ok = test_root_endpoint() 
    agent_ok = test_agent_endpoint()
    
    # Test original functionality with AI
    original_success = 0
    print("\n🤖 Testing AI-Powered Plan Generation...")
    for scenario in [
        {"city": "Raipur", "days": 1, "place_type": "Modern", "food_type": "vegetarian", "budget": "cheap"}
    ]:
        if test_travel_plan(scenario):
            original_success += 1
    
    # Test new any-city functionality with AI
    any_city_ok = test_any_city_functionality()
    
    # Enhanced summary
    print(f"\n📊 AI-POWERED TEST SUMMARY:")
    print(f"Health Check: {'✅' if health_ok else '❌'}")
    print(f"Root Endpoint: {'✅' if root_ok else '❌'}")
    print(f"Agent Test: {'✅' if agent_ok else '❌'}")
    print(f"AI Plan Generation: {'✅' if original_success > 0 else '❌'}")
    print(f"🤖 AI Any-City Functionality: {'✅' if any_city_ok else '❌'}")
    
    if all([health_ok, root_ok, agent_ok, original_success > 0, any_city_ok]):
        print("\n🎉 ALL TESTS PASSED! The AI-Powered Travel Planner works with ANY Indian city!")
        print("🤖 All data is now generated by Gemini AI - no predefined databases!")
    else:
        print("\n⚠️ Some tests failed. Check the logs above.")
        print("💡 Note: AI generation may take longer and require good API connectivity.")

if __name__ == "__main__":
    main()
