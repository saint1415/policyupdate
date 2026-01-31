"""
Tests for Web Application
Tests the Flask web application routes, API endpoints, and rate limiting
"""

import json
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestRateLimiter:
    """Test the rate limiter module"""

    def test_rate_limiter_creation(self):
        """Test rate limiter can be created"""
        from web.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100
        )
        limiter = RateLimiter(config)

        assert limiter is not None
        assert limiter.config.requests_per_minute == 10
        assert limiter.config.requests_per_hour == 100

    def test_rate_limit_check_allowed(self):
        """Test rate limit allows requests under limit"""
        from web.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(requests_per_minute=100)
        limiter = RateLimiter(config)

        # First request should be allowed
        allowed, headers = limiter.check_rate_limit("test-client")

        assert allowed is True
        assert 'X-RateLimit-Limit' in headers
        assert 'X-RateLimit-Remaining' in headers

    def test_rate_limit_check_blocked(self):
        """Test rate limit blocks requests over limit"""
        from web.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(
            requests_per_minute=5,
            burst_size=2
        )
        limiter = RateLimiter(config)

        # Make requests until blocked
        for i in range(10):
            allowed, headers = limiter.check_rate_limit("test-client-block")
            if not allowed:
                break

        # Should eventually be blocked
        assert allowed is False
        assert 'Retry-After' in headers

    def test_rate_limit_different_clients(self):
        """Test rate limits are per-client"""
        from web.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(requests_per_minute=3, burst_size=1)
        limiter = RateLimiter(config)

        # Client 1 makes requests
        for _ in range(5):
            limiter.check_rate_limit("client-1")

        # Client 2 should still be allowed
        allowed, _ = limiter.check_rate_limit("client-2")
        assert allowed is True

    def test_rate_limit_usage(self):
        """Test usage statistics"""
        from web.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(requests_per_minute=100)
        limiter = RateLimiter(config)

        # Make some requests
        for _ in range(5):
            limiter.check_rate_limit("usage-client")

        usage = limiter.get_usage("usage-client")

        assert usage['minute_requests'] == 5
        assert usage['client_id'] == "usage-client"

    def test_exempt_paths(self):
        """Test exempt paths configuration"""
        from web.rate_limiter import RateLimitConfig

        config = RateLimitConfig(
            exempt_paths=['/auth/login', '/api/health']
        )

        assert '/auth/login' in config.exempt_paths
        assert '/api/health' in config.exempt_paths

    def test_auth_multiplier(self):
        """Test authenticated user multiplier"""
        from web.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(
            requests_per_minute=100,
            auth_multiplier=2.0
        )
        limiter = RateLimiter(config)

        # Get limits for anonymous user
        anon_minute, anon_hour = limiter._get_limits("ip:127.0.0.1")

        # Get limits for authenticated user
        auth_minute, auth_hour = limiter._get_limits("user:123")

        assert auth_minute == anon_minute * 2


class TestWebAppCreation:
    """Test Flask app creation"""

    def test_create_app_without_flask(self):
        """Test app creation fails gracefully without Flask"""
        # This test just ensures the module can be imported
        try:
            from web.app import create_app
            # If Flask is available, app should be creatable
            app = create_app()
            assert app is not None
        except ImportError:
            # If Flask not available, that's expected
            pass

    def test_app_has_routes(self):
        """Test app has expected routes"""
        try:
            from web.app import create_app
            app = create_app()

            # Check routes exist
            rules = [rule.rule for rule in app.url_map.iter_rules()]

            assert '/' in rules
            assert '/api/policies' in rules
            assert '/api/frameworks' in rules
            assert '/api/clients' in rules
            assert '/api/health' in rules
        except ImportError:
            pytest.skip("Flask not installed")


class TestAPIEndpoints:
    """Test API endpoint responses"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        try:
            from web.app import create_app
            app = create_app({'TESTING': True})
            return app.test_client()
        except ImportError:
            pytest.skip("Flask not installed")

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data

    def test_policies_endpoint(self, client):
        """Test policies list endpoint"""
        response = client.get('/api/policies')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_frameworks_endpoint(self, client):
        """Test frameworks list endpoint"""
        response = client.get('/api/frameworks')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_clients_endpoint(self, client):
        """Test clients list endpoint"""
        response = client.get('/api/clients')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_policy_search_empty(self, client):
        """Test policy search with no query"""
        response = client.get('/api/policies/search')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data == []

    def test_policy_search_with_query(self, client):
        """Test policy search with query"""
        response = client.get('/api/policies/search?q=access')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_framework_not_found(self, client):
        """Test framework detail with invalid ID"""
        response = client.get('/api/frameworks/nonexistent')
        assert response.status_code == 404

    def test_policy_not_found(self, client):
        """Test policy detail with invalid ID"""
        response = client.get('/api/policies/nonexistent')
        assert response.status_code == 404

    def test_404_api(self, client):
        """Test 404 response for API routes"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404

        data = json.loads(response.data)
        assert 'error' in data

    def test_create_client_no_data(self, client):
        """Test client creation without data"""
        response = client.post('/api/clients',
                              data='{}',
                              content_type='application/json')
        assert response.status_code == 400

    def test_monitor_feeds_endpoint(self, client):
        """Test monitor feeds endpoint"""
        response = client.get('/api/monitor/feeds')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_monitor_recent_endpoint(self, client):
        """Test monitor recent items endpoint"""
        response = client.get('/api/monitor/recent')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, list)


class TestPageRoutes:
    """Test page routes render correctly"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        try:
            from web.app import create_app
            app = create_app({'TESTING': True})
            return app.test_client()
        except ImportError:
            pytest.skip("Flask not installed")

    def test_index_page(self, client):
        """Test index page loads"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'PolicyUpdate' in response.data or b'Dashboard' in response.data

    def test_policies_page(self, client):
        """Test policies page loads"""
        response = client.get('/policies')
        assert response.status_code == 200

    def test_frameworks_page(self, client):
        """Test frameworks page loads"""
        response = client.get('/frameworks')
        assert response.status_code == 200

    def test_clients_page(self, client):
        """Test clients page loads"""
        response = client.get('/clients')
        assert response.status_code == 200

    def test_generate_page(self, client):
        """Test generate page loads"""
        response = client.get('/generate')
        assert response.status_code == 200

    def test_monitor_page(self, client):
        """Test monitor page loads"""
        response = client.get('/monitor')
        assert response.status_code == 200


class TestValidation:
    """Test input validation"""

    def test_sanitize_filename_valid(self):
        """Test valid filename passes"""
        from core.validation import sanitize_filename

        result = sanitize_filename("test_file.docx")
        assert result == "test_file.docx"

    def test_sanitize_filename_path_traversal(self):
        """Test path traversal is blocked"""
        from core.validation import sanitize_filename, ValidationError

        with pytest.raises(ValidationError):
            sanitize_filename("../../../etc/passwd")

    def test_sanitize_filename_dots(self):
        """Test filename with dots (not traversal) is allowed"""
        from core.validation import sanitize_filename

        result = sanitize_filename("my.file.name.docx")
        assert result == "my.file.name.docx"

    def test_validate_email_valid(self):
        """Test valid email passes"""
        from core.validation import validate_email

        assert validate_email("user@example.com") is True
        assert validate_email("user.name@sub.domain.com") is True

    def test_validate_email_invalid(self):
        """Test invalid email fails"""
        from core.validation import validate_email

        assert validate_email("not-an-email") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False

    def test_validate_url_valid(self):
        """Test valid URL passes"""
        from core.validation import validate_url

        assert validate_url("https://example.com") is True
        assert validate_url("http://localhost:5000") is True

    def test_validate_url_invalid(self):
        """Test invalid URL fails"""
        from core.validation import validate_url

        assert validate_url("not-a-url") is False
        assert validate_url("ftp://example.com") is False  # Only http/https


class TestRateLimitHeaders:
    """Test rate limit headers are set correctly"""

    def test_headers_format(self):
        """Test header format is correct"""
        from web.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(requests_per_minute=100)
        limiter = RateLimiter(config)

        allowed, headers = limiter.check_rate_limit("header-test")

        assert 'X-RateLimit-Limit' in headers
        assert 'X-RateLimit-Remaining' in headers
        assert 'X-RateLimit-Reset' in headers

        # Values should be strings (for HTTP headers)
        assert isinstance(headers['X-RateLimit-Limit'], str)
        assert int(headers['X-RateLimit-Limit']) == 100

    def test_remaining_decrements(self):
        """Test remaining count decrements"""
        from web.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(requests_per_minute=100, burst_size=100)
        limiter = RateLimiter(config)

        _, headers1 = limiter.check_rate_limit("decrement-test")
        _, headers2 = limiter.check_rate_limit("decrement-test")

        remaining1 = int(headers1['X-RateLimit-Remaining'])
        remaining2 = int(headers2['X-RateLimit-Remaining'])

        assert remaining2 == remaining1 - 1
