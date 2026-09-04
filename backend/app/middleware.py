"""
Simple in-memory rate limiting middleware.
Phase 7: Production Hardening
"""
import time
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# In-memory store: {ip: [timestamp1, timestamp2, ...]}
_rate_limits: dict[str, list[float]] = {}


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Limits requests per IP address within a sliding window.
    Default: 100 requests per 60 seconds.
    """
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for static/docs if needed, but safe to apply globally
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        # Bypass rate limiter for test suite (FastAPI TestClient)
        if client_ip == "testclient":
            return await call_next(request)
        
        now = time.time()
        
        # Clean up old timestamps
        timestamps = _rate_limits.get(client_ip, [])
        timestamps = [ts for ts in timestamps if now - ts < self.window_seconds]
        
        if len(timestamps) >= self.max_requests:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Terlalu banyak permintaan. Silakan coba lagi nanti."},
            )
            
        timestamps.append(now)
        _rate_limits[client_ip] = timestamps
        
        return await call_next(request)
