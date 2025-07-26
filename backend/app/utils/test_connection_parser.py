"""
Tests for connection URL parser
"""

import pytest
from app.utils.connection_parser import (
    parse_connection_url,
    ConnectionParseError,
    validate_connection_url
)


def test_parse_mysql_url():
    """Test MySQL URL parsing"""
    url = "mysql://user:pass@localhost:3306/mydb"
    config, credentials = parse_connection_url(url, "mysql")
    
    assert config == {
        "host": "localhost",
        "port": 3306,
        "database": "mydb"
    }
    assert credentials == {
        "user": "user",
        "password": "pass"
    }


def test_parse_postgresql_url():
    """Test PostgreSQL URL parsing"""
    url = "postgresql://user:pass@localhost:5432/postgres"
    config, credentials = parse_connection_url(url, "postgresql")
    
    assert config == {
        "host": "localhost",
        "port": 5432,
        "database": "postgres"
    }
    assert credentials == {
        "user": "user",
        "password": "pass"
    }


def test_parse_s3_url():
    """Test S3 URL parsing"""
    url = "s3://AKIA123:secret@my-bucket/us-east-1"
    config, credentials = parse_connection_url(url, "s3")
    
    assert config == {
        "bucket_name": "my-bucket",
        "region": "us-east-1"
    }
    assert credentials == {
        "aws_access_key_id": "AKIA123",
        "aws_secret_access_key": "secret"
    }


def test_parse_api_url():
    """Test API URL parsing"""
    url = "https://api.example.com/users?api_key=abc123&limit=10"
    config, credentials = parse_connection_url(url, "api")
    
    assert config == {
        "base_url": "https://api.example.com",
        "endpoint": "/users?limit=10",
        "method": "GET"
    }
    assert credentials == {
        "api_key": "abc123",
        "auth_header": "Authorization"
    }


def test_invalid_mysql_url():
    """Test invalid MySQL URL"""
    url = "http://invalid"
    with pytest.raises(ConnectionParseError):
        parse_connection_url(url, "mysql")


def test_validate_connection_url():
    """Test URL validation"""
    valid_url = "mysql://user:pass@localhost:3306/mydb"
    is_valid, error = validate_connection_url(valid_url, "mysql")
    assert is_valid is True
    assert error is None
    
    invalid_url = "invalid"
    is_valid, error = validate_connection_url(invalid_url, "mysql")
    assert is_valid is False
    assert error is not None


if __name__ == "__main__":
    pytest.main([__file__])