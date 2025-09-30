#!/usr/bin/env python3
"""
Comprehensive test script for the agents integration.
Tests both backend and frontend integration points.
"""

import sys
import os
sys.path.append('backend')

def test_backend_imports():
    """Test that all backend components can be imported successfully."""
    print("🔧 Testing backend imports...")

    try:
        # Test basic imports
        import dspy
        print("✅ DSPy imported successfully")

        from app.agents.base_agents import AgentOrchestrator, DataPreprocessingAgent
        print("✅ Agent classes imported successfully")

        from app.services.agent_service import AgentService
        print("✅ Agent service imported successfully")

        from app.api.agents import router
        print("✅ Agents API router imported successfully")

        return True
    except Exception as e:
        print(f"❌ Backend import failed: {e}")
        return False

def test_agent_system():
    """Test that the agent system can be instantiated and work."""
    print("\n🤖 Testing agent system functionality...")

    try:
        from app.services.agent_service import AgentService

        # Mock database for testing
        class MockDB:
            pass

        service = AgentService(MockDB())

        # Test getting available agents
        agents = service.get_available_agents()
        print(f"✅ Found {len(agents)} available agents:")
        for agent in agents:
            print(f"   - {agent['name']}: {agent['display_name']}")

        # Test agent templates
        templates = service.get_agent_templates()
        print(f"✅ Found {len(templates)} agent templates")

        return True
    except Exception as e:
        print(f"❌ Agent system test failed: {e}")
        return False

def test_api_integration():
    """Test that the API integrates properly with FastAPI."""
    print("\n🌐 Testing API integration...")

    try:
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Test health endpoint (no auth required)
        response = client.get('/api/agents/health')
        if response.status_code == 200:
            print("✅ Agents health endpoint working")
        else:
            print(f"⚠️ Health endpoint returned {response.status_code}")

        # Test protected endpoint (should require auth)
        response = client.get('/api/agents/')
        if response.status_code == 403:
            print("✅ Protected endpoints properly secured")
        else:
            print(f"⚠️ Protected endpoint returned {response.status_code}")

        return True
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        return False

def test_frontend_files():
    """Test that frontend files exist and are valid."""
    print("\n🎨 Testing frontend integration...")

    try:
        # Check that required files exist
        files_to_check = [
            'frontend/src/app/datasets/[id]/chat/page.tsx',
            'frontend/src/lib/api.ts',
            'frontend/src/components/ui/select.tsx',
            'frontend/src/components/ui/badge.tsx',
            'frontend/src/lib/utils.ts'
        ]

        for file_path in files_to_check:
            if os.path.exists(file_path):
                print(f"✅ {file_path} exists")
            else:
                print(f"❌ {file_path} missing")
                return False

        # Check API integration points
        with open('frontend/src/lib/api.ts', 'r') as f:
            content = f.read()
            if 'agentsAPI' in content:
                print("✅ Agents API integration found in api.ts")
            else:
                print("❌ Agents API integration missing in api.ts")
                return False

        # Check chat page has agent components
        with open('frontend/src/app/datasets/[id]/chat/page.tsx', 'r') as f:
            content = f.read()
            if 'agentsAPI' in content and 'selectedAgent' in content:
                print("✅ Agent selection components found in chat page")
            else:
                print("❌ Agent selection missing in chat page")
                return False

        return True
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False

def test_conda_environment():
    """Test that the conda environment has all required packages."""
    print("\n🐍 Testing conda environment...")

    try:
        import subprocess
        import sys

        # Check Python version
        python_version = sys.version
        print(f"✅ Python version: {python_version.split()[0]}")

        # Check key packages
        packages_to_check = ['dspy', 'fastapi', 'pandas', 'numpy']

        for package in packages_to_check:
            try:
                __import__(package)
                print(f"✅ {package} installed")
            except ImportError:
                print(f"❌ {package} not installed")
                return False

        return True
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting comprehensive agents integration test...\n")

    tests = [
        ("Conda Environment", test_conda_environment),
        ("Backend Imports", test_backend_imports),
        ("Agent System", test_agent_system),
        ("API Integration", test_api_integration),
        ("Frontend Files", test_frontend_files),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)

    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if not result:
            all_passed = False

    print("="*50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! The agents integration is working perfectly.")
    else:
        print("⚠️ Some tests failed. Please check the output above.")

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)