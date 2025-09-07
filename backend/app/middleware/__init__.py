"""
Middleware package for the AI Share Platform
"""

from .ssl_middleware import SSLMiddleware, FlexibleSSLConfig

__all__ = ["SSLMiddleware", "FlexibleSSLConfig"]