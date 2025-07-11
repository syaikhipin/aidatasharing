#!/usr/bin/env python3
"""
Comprehensive Test: Gemini CSV Reading via MindsDB Integration
=============================================================

This test verifies the complete workflow:
1. Create a sample CSV file with meaningful data
2. Upload the CSV to the platform 
3. Create a MindsDB model using the CSV data
4. Query the model with Gemini to analyze the CSV content
5. Verify that Gemini can understand and respond based on actual CSV data

This ensures the MindsDB connector properly feeds CSV data to Gemini.
"""

import os
import sys
import json
import time
import requests
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta
import tempfile


class GeminiCSVIntegrationTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.csv_file_path = None
        self.dataset_id = None
        self.model_name = None
        
    def create_sample_csv(self) -> str:
        """Create a sample CSV file with meaningful business data"""
        print("📊 Creating sample CSV with business data...")
        
        # Create realistic sales data
        data = {
            'date': pd.date_range('2024-01-01', periods=100, freq='D'),
            'product_name': [
                'Laptop Pro', 'Smart Phone', 'Tablet', 'Headphones', 'Smart Watch',
                'Gaming Mouse', 'Keyboard', 'Monitor', 'Webcam', 'Speaker'
            ] * 10,
            'category': [
                'Electronics', 'Electronics', 'Electronics', 'Audio', 'Wearables',
                'Gaming', 'Gaming', 'Electronics', 'Electronics', 'Audio'
            ] * 10,
            'sales_amount': [
                1299.99, 699.99, 399.99, 199.99, 299.99,
                79.99, 129.99, 299.99, 89.99, 149.99
            ] * 10,
            'quantity': [1, 2, 1, 3, 1, 2, 1, 1, 4, 2] * 10,
            'customer_type': ['Premium', 'Regular', 'Regular', 'Premium', 'Regular'] * 20,
            'region': ['North', 'South', 'East', 'West', 'Central'] * 20
        }
        
        df = pd.DataFrame(data)
        
        # Add some calculated fields
        df['total_revenue'] = df['sales_amount'] * df['quantity']
        df['month'] = df['date'].dt.month
        df['day_of_week'] = df['date'].dt.day_name()
        
        # Create temporary CSV file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        df.to_csv(temp_file.name, index=False)
        temp_file.close()
        
        self.csv_file_path = temp_file.name
        print(f"✅ Created CSV file: {self.csv_file_path}")
        print(f"📈 Data shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"💰 Total revenue in dataset: ${df['total_revenue'].sum():,.2f}")
        
        return self.csv_file_path
    
    def authenticate(self) -> bool:
        """Authenticate with the API"""
        try:
            print("🔐 Authenticating with admin credentials...")
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                data={
                    "username": "admin@example.com",
                    "password": "admin123"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.session.headers.update({
                    "Authorization": f"Bearer {token_data['access_token']}"
                })
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def upload_csv_dataset(self) -> bool:
        """Upload the CSV file as a dataset"""
        try:
            print("📤 Uploading CSV dataset...")
            
            with open(self.csv_file_path, 'rb') as file:
                files = {
                    'file': ('sales_data.csv', file, 'text/csv')
                }
                data = {
                    'name': f'Sales Data Test {int(time.time())}',
                    'description': 'Sales data for Gemini CSV integration testing',
                    'sharing_level': 'ORGANIZATION'
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/datasets/upload",
                    files=files,
                    data=data
                )
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.dataset_id = result.get('dataset_id') or result.get('id')
                print(f"✅ Dataset uploaded successfully: ID {self.dataset_id}")
                
                # Wait for processing
                print("⏳ Waiting for dataset processing...")
                time.sleep(3)
                return True
            else:
                print(f"❌ Dataset upload failed: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Dataset upload error: {str(e)}")
            return False
    
    def initialize_gemini_integration(self) -> bool:
        """Initialize Gemini integration"""
        try:
            print("🧠 Initializing Gemini integration...")
            
            response = self.session.post(f"{self.base_url}/api/mindsdb/gemini/initialize")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Gemini integration initialized: {result.get('overall_status', 'Success')}")
                return True
            else:
                print(f"❌ Gemini initialization failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Gemini initialization error: {str(e)}")
            return False
    
    def create_gemini_model(self) -> bool:
        """Create a Gemini model for the uploaded dataset"""
        try:
            print("🤖 Creating Gemini model for dataset analysis...")
            
            self.model_name = f"sales_analysis_model_{int(time.time())}"
            
            model_data = {
                "model_name": self.model_name,
                "dataset_id": self.dataset_id,
                "input_column": "product_name",
                "gemini_model": "gemini-2.0-flash-exp"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/mindsdb/gemini/models",
                json=model_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Gemini model created: {self.model_name}")
                print(f"📊 Model status: {result.get('status', 'Created')}")
                
                # Wait for model to be ready
                print("⏳ Waiting for model to be ready...")
                time.sleep(5)
                return True
            else:
                print(f"❌ Model creation failed: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Model creation error: {str(e)}")
            return False
    
    def test_csv_data_analysis(self) -> List[Dict[str, Any]]:
        """Test various CSV data analysis scenarios with Gemini"""
        test_scenarios = [
            {
                "name": "Total Revenue Analysis",
                "query": "What is the total revenue in this dataset? Which product category generates the most revenue?",
                "expected_keywords": ["revenue", "total", "electronics", "audio"]
            },
            {
                "name": "Product Performance",
                "query": "Which product has the highest sales amount? What are the top 3 selling products?",
                "expected_keywords": ["laptop", "highest", "sales", "product"]
            },
            {
                "name": "Customer Segmentation",
                "query": "How many premium vs regular customers are in the data? Which customer type spends more?",
                "expected_keywords": ["premium", "regular", "customer", "type"]
            },
            {
                "name": "Regional Analysis",
                "query": "Which region has the highest sales? Compare sales performance across different regions.",
                "expected_keywords": ["region", "north", "south", "east", "west", "central"]
            },
            {
                "name": "Time Series Insights",
                "query": "What sales trends can you identify in the data? Are there any seasonal patterns?",
                "expected_keywords": ["trend", "pattern", "date", "month"]
            }
        ]
        
        results = []
        
        for scenario in test_scenarios:
            try:
                print(f"\n🔍 Testing: {scenario['name']}")
                print(f"Query: {scenario['query']}")
                
                query_data = {
                    "model_name": self.model_name,
                    "question": scenario['query'],
                    "context": "sales data analysis"
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/mindsdb/gemini/models/{self.model_name}/query",
                    json=query_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    gemini_response = result.get('response', result.get('answer', ''))
                    
                    print(f"📝 Gemini Response: {gemini_response[:200]}...")
                    
                    # Check if response contains expected keywords
                    response_lower = gemini_response.lower()
                    keyword_matches = [
                        keyword for keyword in scenario['expected_keywords']
                        if keyword.lower() in response_lower
                    ]
                    
                    has_data_insights = len(keyword_matches) > 0
                    has_meaningful_response = len(gemini_response.split()) > 10
                    
                    test_result = {
                        "scenario": scenario['name'],
                        "query": scenario['query'],
                        "response": gemini_response,
                        "keyword_matches": keyword_matches,
                        "has_data_insights": has_data_insights,
                        "has_meaningful_response": has_meaningful_response,
                        "success": has_data_insights and has_meaningful_response,
                        "status_code": response.status_code
                    }
                    
                    if test_result['success']:
                        print(f"✅ Test passed - Gemini provided relevant data insights")
                        print(f"🎯 Matched keywords: {keyword_matches}")
                    else:
                        print(f"⚠️  Test inconclusive - Limited data insights detected")
                        
                else:
                    test_result = {
                        "scenario": scenario['name'],
                        "query": scenario['query'],
                        "response": f"API Error: {response.status_code}",
                        "keyword_matches": [],
                        "has_data_insights": False,
                        "has_meaningful_response": False,
                        "success": False,
                        "status_code": response.status_code
                    }
                    print(f"❌ API call failed: {response.status_code}")
                
                results.append(test_result)
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                test_result = {
                    "scenario": scenario['name'],
                    "query": scenario['query'],
                    "response": f"Error: {str(e)}",
                    "keyword_matches": [],
                    "has_data_insights": False,
                    "has_meaningful_response": False,
                    "success": False,
                    "status_code": None
                }
                results.append(test_result)
                print(f"❌ Test error: {str(e)}")
        
        return results
    
    def test_direct_csv_query(self) -> Dict[str, Any]:
        """Test direct CSV querying capabilities"""
        try:
            print("\n🔍 Testing direct CSV data queries...")
            
            query_data = {
                "query": f"SELECT product_name, SUM(total_revenue) as revenue FROM dataset_{self.dataset_id} GROUP BY product_name ORDER BY revenue DESC LIMIT 3"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/mindsdb/query",
                json=query_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Direct CSV query successful")
                print(f"📊 Query result: {result}")
                return {
                    "success": True,
                    "result": result,
                    "status_code": response.status_code
                }
            else:
                print(f"❌ Direct query failed: {response.status_code}")
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            print(f"❌ Direct query error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    def cleanup(self):
        """Clean up test files"""
        try:
            if self.csv_file_path and os.path.exists(self.csv_file_path):
                os.unlink(self.csv_file_path)
                print("🧹 Cleaned up temporary CSV file")
        except Exception as e:
            print(f"⚠️  Cleanup error: {str(e)}")
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run the complete CSV-Gemini integration test"""
        print("🚀 Starting Comprehensive Gemini CSV Integration Test")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Test steps
        steps = [
            ("create_sample_csv", "Create sample CSV data"),
            ("authenticate", "Authenticate with API"),
            ("upload_csv_dataset", "Upload CSV dataset"),
            ("initialize_gemini_integration", "Initialize Gemini"),
            ("create_gemini_model", "Create Gemini model"),
        ]
        
        # Execute setup steps
        for step_func, step_name in steps:
            print(f"\n📋 Step: {step_name}")
            success = getattr(self, step_func)()
            if not success:
                return {
                    "overall_success": False,
                    "failed_step": step_name,
                    "error": f"Failed at step: {step_name}",
                    "timestamp": datetime.now().isoformat()
                }
        
        # Run CSV analysis tests
        print(f"\n📊 Running CSV Data Analysis Tests...")
        analysis_results = self.test_csv_data_analysis()
        
        # Test direct CSV queries
        direct_query_result = self.test_direct_csv_query()
        
        # Compile final results
        successful_tests = sum(1 for test in analysis_results if test['success'])
        total_tests = len(analysis_results)
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        final_results = {
            "overall_success": success_rate >= 60,  # 60% threshold for meaningful CSV understanding
            "success_rate": success_rate,
            "successful_tests": successful_tests,
            "total_tests": total_tests,
            "analysis_results": analysis_results,
            "direct_query_result": direct_query_result,
            "dataset_id": self.dataset_id,
            "model_name": self.model_name,
            "test_duration_seconds": duration,
            "timestamp": end_time.isoformat()
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 GEMINI CSV INTEGRATION TEST RESULTS")
        print("=" * 60)
        print(f"✅ Overall Success: {'YES' if final_results['overall_success'] else 'NO'}")
        print(f"📊 Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        print(f"⏱️  Test Duration: {duration:.1f} seconds")
        print(f"📄 Dataset ID: {self.dataset_id}")
        print(f"🤖 Model Name: {self.model_name}")
        
        if final_results['overall_success']:
            print("\n🎉 CONCLUSION: Gemini CAN read and analyze CSV data through MindsDB!")
            print("✅ The integration successfully feeds CSV content to Gemini for analysis")
        else:
            print("\n⚠️  CONCLUSION: Limited or no CSV data understanding detected")
            print("❌ Gemini may not be receiving proper CSV data through MindsDB")
        
        # Cleanup
        self.cleanup()
        
        return final_results


def main():
    """Main function to run the comprehensive test"""
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend server is not responding properly")
            print("Please start the backend server with: ./start-dev.sh")
            return False
    except requests.exceptions.RequestException:
        print("❌ Backend server is not running or not accessible")
        print("Please start the backend server with: ./start-dev.sh")
        return False
    
    # Run the comprehensive test
    test = GeminiCSVIntegrationTest()
    results = test.run_comprehensive_test()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"test_results/gemini_csv_integration_{timestamp}.json"
    
    os.makedirs("test_results", exist_ok=True)
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    return results['overall_success']


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 