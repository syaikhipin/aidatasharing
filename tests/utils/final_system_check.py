#!/usr/bin/env python3
"""
Final System Status Check
Comprehensive test of all proxy services and authentication systems
"""

import requests
import json
import time
from datetime import datetime

def test_all_proxy_ports():
    """Test all proxy ports for functionality"""
    print("🔍 Testing All Proxy Ports...")
    
    ports = {
        10101: "MySQL",
        10102: "PostgreSQL", 
        10103: "API",
        10104: "ClickHouse",
        10105: "MongoDB",
        10106: "S3",
        10107: "Shared Links"
    }
    
    results = {}
    
    for port, service in ports.items():
        try:
            # Test health endpoint
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                results[port] = {
                    "service": service,
                    "status": "✅ HEALTHY",
                    "health": health_data
                }
                print(f"  ✅ Port {port} ({service}): HEALTHY")
            else:
                results[port] = {
                    "service": service,
                    "status": f"⚠️  HTTP {response.status_code}",
                    "health": None
                }
                print(f"  ⚠️  Port {port} ({service}): HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            results[port] = {
                "service": service,
                "status": f"❌ FAILED: {str(e)}",
                "health": None
            }
            print(f"  ❌ Port {port} ({service}): FAILED - {e}")
    
    return results

def test_mysql_proxy_functionality():
    """Test the specific MySQL proxy functionality"""
    print("\n🔗 Testing MySQL Proxy Functionality...")
    
    test_url = "http://localhost:10101/Test%20DB%20Unipa%20Dataset?token=0627b5b4afdba49bb348a870eb152e86"
    
    try:
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("  ✅ MySQL proxy connection successful")
            print(f"  📊 Database: {data.get('database', 'N/A')}")
            print(f"  🔧 Proxy Type: {data.get('proxy_type', 'N/A')}")
            print(f"  📈 Row Count: {data.get('row_count', 'N/A')}")
            print(f"  🔗 Connection: {data.get('connection_info', {}).get('mindsdb_connection', 'N/A')}")
            
            return True
        else:
            print(f"  ❌ MySQL proxy failed: HTTP {response.status_code}")
            print(f"  📄 Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ MySQL proxy connection failed: {e}")
        return False

def test_backend_status():
    """Test backend service status"""
    print("\n🖥️  Testing Backend Service...")
    
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        
        if response.status_code == 200:
            print("  ✅ Backend service is healthy")
            return True
        elif response.status_code == 403:
            print("  ⚠️  Backend service running but returns 403 (auth required)")
            return True
        else:
            print(f"  ⚠️  Backend service status: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Backend service connection failed: {e}")
        return False

def generate_system_report():
    """Generate comprehensive system status report"""
    print("\n" + "="*80)
    print("📋 COMPREHENSIVE SYSTEM STATUS REPORT")
    print("="*80)
    print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test all proxy ports
    proxy_results = test_all_proxy_ports()
    
    # Test MySQL proxy functionality
    mysql_working = test_mysql_proxy_functionality()
    
    # Test backend status
    backend_working = test_backend_status()
    
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    # Proxy services summary
    healthy_proxies = sum(1 for result in proxy_results.values() if "HEALTHY" in result["status"])
    total_proxies = len(proxy_results)
    
    print(f"🔗 Proxy Services: {healthy_proxies}/{total_proxies} healthy")
    for port, result in proxy_results.items():
        print(f"  Port {port} ({result['service']}): {result['status']}")
    
    print(f"\n🔧 MySQL Proxy (Primary): {'✅ WORKING' if mysql_working else '❌ FAILED'}")
    print(f"🖥️  Backend Service: {'✅ WORKING' if backend_working else '❌ FAILED'}")
    
    # Overall system status
    print(f"\n🎯 Overall System Status: ", end="")
    if mysql_working and backend_working and healthy_proxies >= 6:
        print("✅ FULLY OPERATIONAL")
        success_rate = 100
    elif mysql_working and healthy_proxies >= 4:
        print("⚠️  MOSTLY OPERATIONAL")
        success_rate = 75
    elif mysql_working:
        print("⚠️  PARTIALLY OPERATIONAL")
        success_rate = 50
    else:
        print("❌ CRITICAL ISSUES")
        success_rate = 25
    
    print(f"📈 Success Rate: {success_rate}%")
    
    # Usage instructions
    print("\n" + "="*80)
    print("📖 USAGE INSTRUCTIONS")
    print("="*80)
    print("🔗 Primary MySQL Proxy:")
    print("  curl 'http://localhost:10101/Test%20DB%20Unipa%20Dataset?token=0627b5b4afdba49bb348a870eb152e86'")
    print()
    print("🔧 Service Management:")
    print("  Start: ./start-mindsdb-proxy.sh")
    print("  Stop:  ./stop-mindsdb-proxy.sh")
    print()
    print("📊 Health Checks:")
    print("  MySQL:      curl http://localhost:10101/health")
    print("  PostgreSQL: curl http://localhost:10102/health")
    print("  API:        curl http://localhost:10103/health")
    print()
    print("📋 Logs:")
    print("  Proxy: logs/mindsdb_proxy.log")
    print("  Backend: logs/backend.log")
    
    return {
        "proxy_services": proxy_results,
        "mysql_proxy_working": mysql_working,
        "backend_working": backend_working,
        "success_rate": success_rate
    }

if __name__ == "__main__":
    report = generate_system_report()
    
    # Save report to file
    with open("system_status_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Full report saved to: system_status_report.json")
    print("\n🎉 System status check complete!")