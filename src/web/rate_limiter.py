"""
Rate Limiter Module
Implements API rate limiting with sliding window algorithm
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps
from threading import Lock
from typing import Dict, Optional, Tuple, Callable

try:
    from flask import request, jsonify, g
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    # Requests per window
    requests_per_minute: int = 100
    requests_per_hour: int = 1000

    # Authenticated vs unauthenticated
    auth_multiplier: float = 2.0  # Authenticated users get 2x limit

    # Burst allowance
    burst_size: int = 20

    # Exempt paths
    exempt_paths: list = field(default_factory=lambda: ['/auth/login', '/api/health', '/static'])


@dataclass
class RateLimitEntry:
    """Tracks request counts for a single client"""
    minute_requests: list = field(default_factory=list)
    hour_requests: list = field(default_factory=list)
    blocked_until: float = 0


class RateLimiter:
    """
    Sliding window rate limiter implementation.

    Features:
    - Per-IP rate limiting
    - Different limits for authenticated vs anonymous users
    - Sliding window algorithm for smooth rate limiting
    - Burst allowance for short spikes
    - Automatic cleanup of old entries
    """

    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self._entries: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._lock = Lock()
        self._last_cleanup = time.time()

    def _get_client_id(self) -> str:
        """Get unique client identifier from request"""
        if not FLASK_AVAILABLE:
            return "unknown"

        # Use user ID if authenticated
        if hasattr(g, 'current_user') and g.current_user and hasattr(g.current_user, 'id'):
            return f"user:{g.current_user.id}"

        # Fall back to IP address
        # Handle X-Forwarded-For for proxied requests
        forwarded = request.headers.get('X-Forwarded-For', '')
        if forwarded:
            # Take the first IP (original client)
            ip = forwarded.split(',')[0].strip()
        else:
            ip = request.remote_addr or 'unknown'

        return f"ip:{ip}"

    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from rate limiting"""
        for exempt in self.config.exempt_paths:
            if path.startswith(exempt):
                return True
        return False

    def _get_limits(self, client_id: str) -> Tuple[int, int]:
        """Get rate limits for client"""
        base_minute = self.config.requests_per_minute
        base_hour = self.config.requests_per_hour

        # Authenticated users get higher limits
        if client_id.startswith('user:'):
            return (
                int(base_minute * self.config.auth_multiplier),
                int(base_hour * self.config.auth_multiplier)
            )

        return base_minute, base_hour

    def _cleanup_old_entries(self, now: float, entry: RateLimitEntry) -> None:
        """Remove expired request timestamps"""
        minute_ago = now - 60
        hour_ago = now - 3600

        entry.minute_requests = [t for t in entry.minute_requests if t > minute_ago]
        entry.hour_requests = [t for t in entry.hour_requests if t > hour_ago]

    def _periodic_cleanup(self) -> None:
        """Periodically clean up stale entries"""
        now = time.time()
        if now - self._last_cleanup < 300:  # Every 5 minutes
            return

        self._last_cleanup = now
        stale_threshold = now - 3600

        # Remove entries with no recent activity
        stale_keys = [
            key for key, entry in self._entries.items()
            if not entry.hour_requests or max(entry.hour_requests) < stale_threshold
        ]
        for key in stale_keys:
            del self._entries[key]

    def check_rate_limit(self, client_id: str = None) -> Tuple[bool, dict]:
        """
        Check if request is within rate limits.

        Returns:
            Tuple of (allowed, headers_dict)
        """
        now = time.time()

        if client_id is None:
            client_id = self._get_client_id()

        with self._lock:
            entry = self._entries[client_id]

            # Check if client is blocked
            if entry.blocked_until > now:
                retry_after = int(entry.blocked_until - now)
                return False, {
                    'X-RateLimit-Limit': '0',
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(int(entry.blocked_until)),
                    'Retry-After': str(retry_after)
                }

            # Cleanup old timestamps
            self._cleanup_old_entries(now, entry)

            # Get limits
            minute_limit, hour_limit = self._get_limits(client_id)

            # Check limits
            minute_count = len(entry.minute_requests)
            hour_count = len(entry.hour_requests)

            # Allow burst
            if minute_count < self.config.burst_size:
                allowed = True
            elif minute_count >= minute_limit:
                # Block for remainder of minute
                entry.blocked_until = now + 60
                allowed = False
            elif hour_count >= hour_limit:
                # Block for remainder of hour
                entry.blocked_until = now + 3600
                allowed = False
            else:
                allowed = True

            if allowed:
                # Record request
                entry.minute_requests.append(now)
                entry.hour_requests.append(now)

            # Build headers
            remaining = max(0, minute_limit - len(entry.minute_requests))
            reset_time = int(now + 60)

            headers = {
                'X-RateLimit-Limit': str(minute_limit),
                'X-RateLimit-Remaining': str(remaining),
                'X-RateLimit-Reset': str(reset_time)
            }

            if not allowed:
                headers['Retry-After'] = str(int(entry.blocked_until - now))

            # Periodic cleanup
            self._periodic_cleanup()

            return allowed, headers

    def get_usage(self, client_id: str = None) -> dict:
        """Get current usage stats for a client"""
        if client_id is None:
            client_id = self._get_client_id()

        with self._lock:
            entry = self._entries.get(client_id, RateLimitEntry())
            minute_limit, hour_limit = self._get_limits(client_id)

            now = time.time()
            self._cleanup_old_entries(now, entry)

            return {
                'client_id': client_id,
                'minute_requests': len(entry.minute_requests),
                'minute_limit': minute_limit,
                'hour_requests': len(entry.hour_requests),
                'hour_limit': hour_limit,
                'blocked_until': entry.blocked_until if entry.blocked_until > now else None
            }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def rate_limit(f: Callable = None, *, exempt: bool = False):
    """
    Decorator to apply rate limiting to a route.

    Usage:
        @app.route('/api/resource')
        @rate_limit
        def get_resource():
            ...

        @app.route('/api/public')
        @rate_limit(exempt=True)
        def public_resource():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not FLASK_AVAILABLE:
                return func(*args, **kwargs)

            limiter = get_rate_limiter()

            # Check exemption
            if exempt or limiter._is_exempt(request.path):
                return func(*args, **kwargs)

            # Check rate limit
            allowed, headers = limiter.check_rate_limit()

            if not allowed:
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.',
                    'retry_after': headers.get('Retry-After')
                })
                response.status_code = 429
                for key, value in headers.items():
                    response.headers[key] = value
                return response

            # Execute the actual function
            response = func(*args, **kwargs)

            # Add rate limit headers to response
            if hasattr(response, 'headers'):
                for key, value in headers.items():
                    response.headers[key] = value

            return response

        return wrapper

    # Handle both @rate_limit and @rate_limit() syntax
    if f is not None:
        return decorator(f)
    return decorator


def init_rate_limiter(app, config: RateLimitConfig = None):
    """Initialize rate limiting for a Flask app"""
    global _rate_limiter
    _rate_limiter = RateLimiter(config)

    @app.before_request
    def check_global_rate_limit():
        """Apply rate limiting to all API requests"""
        if not request.path.startswith('/api/'):
            return None

        limiter = get_rate_limiter()

        if limiter._is_exempt(request.path):
            return None

        allowed, headers = limiter.check_rate_limit()

        if not allowed:
            response = jsonify({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.',
                'retry_after': headers.get('Retry-After')
            })
            response.status_code = 429
            for key, value in headers.items():
                response.headers[key] = value
            return response

        # Store headers to add to response
        g.rate_limit_headers = headers

    @app.after_request
    def add_rate_limit_headers(response):
        """Add rate limit headers to all responses"""
        if hasattr(g, 'rate_limit_headers'):
            for key, value in g.rate_limit_headers.items():
                response.headers[key] = value
        return response

    return _rate_limiter
