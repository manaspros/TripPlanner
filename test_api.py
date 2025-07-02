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

def main():
    """Main test function"""
    print("🧳 Travel Planner API Test Suite")
    print("="*50)
    
    # Test basic endpoints
    health_ok = test_health_check()
    root_ok = test_root_endpoint()
    
    if not health_ok or not root_ok:
        print("\n❌ Basic endpoints failed. Check if the server is running.")
        return
    
    # Test agent functionality
    agent_ok = test_agent_endpoint()
    
    # Test travel plan generation with different scenarios
    test_scenarios = [
        {
            "city": "Delhi",
            "time_of_day": "evening",
            "place_type": "historical sites",
            "food_type": "local cuisine",
            "budget": "cheap"
        },
        {
            "city": "Mumbai", 
            "time_of_day": "afternoon",
            "place_type": "museums",
            "food_type": "street food",
            "budget": "mid-range"
        },
        {
            "city": "Bengaluru",
            "time_of_day": "morning",
            "place_type": "parks",
            "food_type": "South Indian",
            "budget": "expensive"
        }
    ]
    
    successful_tests = 0
    total_tests = len(test_scenarios)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 Test Scenario {i}/{total_tests}")
        if test_travel_plan(scenario):
            successful_tests += 1
        time.sleep(2)  # Add delay between requests
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"Health Check: {'✅' if health_ok else '❌'}")
    print(f"Root Endpoint: {'✅' if root_ok else '❌'}")
    print(f"Agent Endpoint: {'✅' if agent_ok else '❌'}")
    print(f"Travel Plans: {successful_tests}/{total_tests} successful")
    
    if successful_tests == total_tests and health_ok and root_ok and agent_ok:
        print("\n🎉 All tests passed! The Travel Planner API is working perfectly!")
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()
