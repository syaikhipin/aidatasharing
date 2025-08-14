#!/usr/bin/env python3
"""
Test connection string generation to verify the fix
"""

def generate_connection_string(dataset_name, file_type, token):
    """Simulate the frontend connection string generation"""
    host = "localhost"
    
    # Port mapping
    port_map = {
        'mysql': '10101',
        'postgresql': '10102', 
        'clickhouse': '10104',
        'mongodb': '10105',
        's3': '10106',
        'api': '10103'
    }
    
    port = port_map.get(file_type.lower(), '10103')
    proxy_host = f"{host}:{port}"
    
    # URL encode the dataset name (basic version)
    encoded_name = dataset_name.replace(' ', '%20').replace('&', '%26')
    
    if file_type.lower() == 'api':
        return f"http://{proxy_host}/api/{encoded_name}?token={token}"
    else:
        return f"http://{proxy_host}/{encoded_name}?token={token}"

# Test with the dataset from the feedback
dataset_name = "Animal Facts Knowledge Base"
file_type = "api"
token = "8241cee9ec82ceb84e6d4e9b524dd754"

connection_string = generate_connection_string(dataset_name, file_type, token)
print(f"Expected connection string: {connection_string}")
print(f"Should be HTTP (not HTTPS): {'✅' if connection_string.startswith('http://') else '❌'}")