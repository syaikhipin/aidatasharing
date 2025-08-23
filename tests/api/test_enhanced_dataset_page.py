#!/usr/bin/env python3
"""
Frontend Dataset Page Integration Test
Tests the enhanced functionality and fixed UI on the dataset page
"""

import requests
import json
import time
from datetime import datetime

# Configuration
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

def test_dataset_page_functionality():
    """Test the dataset page with enhanced functionality"""
    print("🧪 Testing Enhanced Dataset Page Functionality")
    print("=" * 60)
    
    # Test dataset page accessibility
    try:
        response = requests.get(f"{FRONTEND_URL}/datasets/10", timeout=10)
        if response.status_code == 200:
            print("✅ Dataset page accessible")
            
            # Check for key components
            content = response.text
            
            # Check for dataset preview section
            if "Dataset Preview" in content:
                print("✅ Dataset preview section found")
            else:
                print("❌ Dataset preview section missing")
            
            # Check for rename functionality
            if "Rename Dataset" in content:
                print("✅ Rename functionality found")
            else:
                print("❌ Rename functionality missing")
                
            # Check for reupload functionality
            if "Reupload" in content or "reupload" in content:
                print("✅ Reupload functionality found")
            else:
                print("❌ Reupload functionality missing")
                
            # Check for download functionality
            if "Download" in content and "onclick" in content.lower():
                print("✅ Download functionality found")
            else:
                print("❌ Download functionality missing")
                
            # Check that inline chat interface was removed
            chat_sections = content.count("Chat with AI about this dataset")
            if chat_sections == 0:
                print("✅ Inline chat interface successfully removed")
            else:
                print(f"❌ Inline chat interface still present ({chat_sections} instances)")
                
            # Check for metadata display
            if "View Metadata" in content:
                print("✅ Metadata functionality found")
            else:
                print("❌ Metadata functionality missing")
                
        else:
            print(f"❌ Dataset page returned status {response.status_code}")
            
    except requests.RequestException as e:
        print(f"❌ Failed to access dataset page: {e}")

def test_backend_enhanced_endpoints():
    """Test the backend enhanced preview and reupload endpoints"""
    print("\n🔧 Testing Backend Enhanced Endpoints")
    print("=" * 40)
    
    try:
        # Test enhanced preview endpoint
        response = requests.get(f"{BACKEND_URL}/api/datasets/10/preview/enhanced", timeout=10)
        if response.status_code == 200:
            print("✅ Enhanced preview endpoint working")
            data = response.json()
            
            # Check for key preview components
            if 'technical_analysis' in data:
                print("✅ Technical analysis in response")
            if 'file_preview' in data:
                print("✅ File preview in response")
            if 'connector_preview' in data:
                print("✅ Connector preview in response")
            if 'statistics' in data:
                print("✅ Statistics in response")
                
        else:
            print(f"❌ Enhanced preview endpoint returned status {response.status_code}")
            
    except requests.RequestException as e:
        print(f"❌ Enhanced preview endpoint error: {e}")
        
    # Note: Reupload endpoint requires file upload, so we'll just check if it exists
    try:
        response = requests.post(f"{BACKEND_URL}/api/datasets/10/reupload", timeout=5)
        # We expect this to fail without a file, but it should return 422 (validation error) not 404
        if response.status_code in [400, 422]:
            print("✅ Reupload endpoint exists (validation error expected without file)")
        elif response.status_code == 404:
            print("❌ Reupload endpoint not found")
        else:
            print(f"⚠️  Reupload endpoint returned unexpected status {response.status_code}")
            
    except requests.RequestException as e:
        print(f"❌ Reupload endpoint error: {e}")

def test_unified_api_client():
    """Test if UnifiedApiClient is properly integrated"""
    print("\n🔄 Testing UnifiedApiClient Integration")
    print("=" * 40)
    
    try:
        # Check if the unified client file exists and is properly structured
        with open('/Users/syaikhipin/Documents/program/simpleaisharing/frontend/unified-api-client.ts', 'r') as f:
            content = f.read()
            
        if 'class UnifiedApiClient' in content:
            print("✅ UnifiedApiClient class found")
        else:
            print("❌ UnifiedApiClient class not found")
            
        if 'getDatasetEnhancedPreview' in content:
            print("✅ Dataset enhanced preview method found")
        else:
            print("❌ Dataset enhanced preview method missing")
            
        if 'reuploadDatasetFile' in content:
            print("✅ Dataset reupload method found")
        else:
            print("❌ Dataset reupload method missing")
            
        if 'createApiClient' in content:
            print("✅ Factory function found")
        else:
            print("❌ Factory function missing")
            
    except FileNotFoundError:
        print("❌ UnifiedApiClient file not found")
    except Exception as e:
        print(f"❌ Error reading UnifiedApiClient: {e}")

def test_frontend_integration():
    """Test if the frontend properly integrates the new functionality"""
    print("\n🎨 Testing Frontend Integration")
    print("=" * 40)
    
    try:
        # Check the dataset page component
        with open('/Users/syaikhipin/Documents/program/simpleaisharing/frontend/src/app/datasets/[id]/page.tsx', 'r') as f:
            content = f.read()
            
        # Check for UnifiedApiClient import
        if 'createApiClient' in content and 'unified-api-client' in content:
            print("✅ UnifiedApiClient properly imported")
        else:
            print("❌ UnifiedApiClient not properly imported")
            
        # Check for enhanced preview functionality
        if 'fetchEnhancedPreview' in content:
            print("✅ Enhanced preview fetch function found")
        else:
            print("❌ Enhanced preview fetch function missing")
            
        # Check for rename functionality
        if 'handleRenameDataset' in content and 'showRenameModal' in content:
            print("✅ Rename functionality implemented")
        else:
            print("❌ Rename functionality missing")
            
        # Check for reupload functionality
        if 'handleReuploadDataset' in content and 'showReuploadModal' in content:
            print("✅ Reupload functionality implemented")
        else:
            print("❌ Reupload functionality missing")
            
        # Check for consolidated chat interface
        chat_count = content.count('Chat with AI')
        if chat_count == 1:
            print("✅ Single chat interface in component")
        else:
            print(f"⚠️  Multiple chat references found ({chat_count})")
            
        # Check for enhanced icons
        if 'Sparkles' in content and 'Edit' in content and 'Upload' in content:
            print("✅ Enhanced icons imported")
        else:
            print("❌ Some enhanced icons missing")
            
    except FileNotFoundError:
        print("❌ Dataset page component not found")
    except Exception as e:
        print(f"❌ Error reading dataset component: {e}")

def main():
    """Run all tests"""
    print("🚀 Frontend Dataset Page Integration Tests")
    print("Testing enhanced preview, rename, reupload, and unified chat interface")
    print("=" * 80)
    
    test_unified_api_client()
    test_frontend_integration()
    test_backend_enhanced_endpoints()
    test_dataset_page_functionality()
    
    print("\n📋 Test Summary")
    print("=" * 20)
    print("✅ = Working correctly")
    print("⚠️  = Needs attention")
    print("❌ = Not working/missing")
    print("\n💡 Next Steps:")
    print("1. Visit http://localhost:3000/datasets/10 to test the enhanced UI")
    print("2. Try the rename functionality (if you're the dataset owner)")
    print("3. Test the reupload feature with a new file")
    print("4. Verify the enhanced preview shows AI analysis and technical details")
    print("5. Confirm only one chat interface is visible")

if __name__ == "__main__":
    main()