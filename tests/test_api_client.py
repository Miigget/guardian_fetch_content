"""
Tests for GuardianAPIClient module.

This module contains comprehensive tests for the Guardian API client,
including successful responses, error handling, rate limiting, and
various edge cases.
"""

import pytest
import time
from unittest.mock import patch, Mock
import requests

from guardian_content_fetcher.api_client import GuardianAPIClient, GuardianAPIError
from tests.conftest import create_mock_response, assert_article_format


class TestGuardianAPIClient:
    """Test cases for GuardianAPIClient class."""
    
    def test_initialization_success(self):
        """Test successful client initialization."""
        client = GuardianAPIClient("test-api-key")
        
        assert client.api_key == "test-api-key"
        assert client.base_url == GuardianAPIClient.BASE_URL
        assert client.rate_limit_delay == GuardianAPIClient.DEFAULT_RATE_LIMIT_DELAY
    
    def test_initialization_with_custom_rate_limit(self):
        """Test client initialization with custom rate limit."""
        client = GuardianAPIClient("test-api-key", rate_limit_delay=1.5)
        
        assert client.api_key == "test-api-key"
        assert client.rate_limit_delay == 1.5
    
    def test_initialization_empty_api_key(self):
        """Test that empty API key raises ValueError."""
        with pytest.raises(ValueError, match="API key cannot be empty or None"):
            GuardianAPIClient("")
        
        with pytest.raises(ValueError, match="API key cannot be empty or None"):
            GuardianAPIClient(None)
    
    def test_rate_limiting(self, guardian_api_client):
        """Test that rate limiting works correctly."""
        start_time = time.time()
        
        # First call should not wait
        guardian_api_client._wait_for_rate_limit()
        first_call_time = time.time()
        
        # Second call should wait
        guardian_api_client._wait_for_rate_limit()
        second_call_time = time.time()
        
        # The second call should take at least the rate limit delay
        time_diff = second_call_time - first_call_time
        assert time_diff >= guardian_api_client.rate_limit_delay * 0.9  # Allow for timing variations
    
    def test_search_content_success(self, guardian_api_client, mock_requests_get, sample_guardian_api_response):
        """Test successful article search."""
        # Configure mock response
        mock_response = create_mock_response(sample_guardian_api_response)
        mock_requests_get.return_value = mock_response
        
        # Call search_content
        articles = guardian_api_client.search_content("machine learning")
        
        # Verify request was made correctly
        mock_requests_get.assert_called_once()
        call_args = mock_requests_get.call_args
        
        assert "search" in call_args[0][0]  # URL contains 'search'
        params = call_args[1]['params']
        assert params['q'] == "machine learning"
        assert params['api-key'] == "test-api-key"
        assert params['page-size'] == 10
        assert params['order-by'] == "newest"
        
        # Verify response processing
        assert len(articles) == 2
        for article in articles:
            assert_article_format(article)
        
        # Check specific article content
        assert articles[0]['webTitle'] == "Machine Learning Advances in 2023"
        assert articles[0]['webUrl'] == "https://www.theguardian.com/technology/2023/jan/01/machine-learning-advances"
        assert 'content_preview' in articles[0]
        assert len(articles[0]['content_preview']) <= 1003  # 1000 chars + "..."
    
    def test_search_content_with_date_filter(self, guardian_api_client, mock_requests_get, sample_guardian_api_response):
        """Test article search with date filter."""
        mock_response = create_mock_response(sample_guardian_api_response)
        mock_requests_get.return_value = mock_response
        
        articles = guardian_api_client.search_content(
            "machine learning",
            date_from="2023-01-01"
        )
        
        # Verify date filter was included
        call_args = mock_requests_get.call_args
        params = call_args[1]['params']
        assert params['from-date'] == "2023-01-01"
        
        assert len(articles) == 2
    
    def test_search_content_with_custom_page_size(self, guardian_api_client, mock_requests_get, sample_guardian_api_response):
        """Test article search with custom page size."""
        mock_response = create_mock_response(sample_guardian_api_response)
        mock_requests_get.return_value = mock_response
        
        articles = guardian_api_client.search_content(
            "machine learning",
            page_size=5
        )
        
        # Verify page size was set correctly
        call_args = mock_requests_get.call_args
        params = call_args[1]['params']
        assert params['page-size'] == 5
        
        assert len(articles) == 2
    
    def test_search_content_empty_search_term(self, guardian_api_client):
        """Test that empty search term raises ValueError."""
        with pytest.raises(ValueError, match="Search term cannot be empty"):
            guardian_api_client.search_content("")
        
        with pytest.raises(ValueError, match="Search term cannot be empty"):
            guardian_api_client.search_content("   ")
    
    def test_search_content_invalid_page_size(self, guardian_api_client):
        """Test that invalid page size raises ValueError."""
        with pytest.raises(ValueError, match="Page size must be between 1 and 50"):
            guardian_api_client.search_content("test", page_size=0)
        
        with pytest.raises(ValueError, match="Page size must be between 1 and 50"):
            guardian_api_client.search_content("test", page_size=51)
    
    def test_search_content_invalid_date_format(self, guardian_api_client):
        """Test that invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="date_from must be in YYYY-MM-DD format"):
            guardian_api_client.search_content("test", date_from="2023/01/01")
        
        with pytest.raises(ValueError, match="date_from must be in YYYY-MM-DD format"):
            guardian_api_client.search_content("test", date_from="invalid-date")
    
    def test_search_content_api_error_response(self, guardian_api_client, mock_requests_get, error_response):
        """Test handling of API error responses."""
        mock_response = create_mock_response(error_response)
        mock_requests_get.return_value = mock_response
        
        with pytest.raises(GuardianAPIError, match="Invalid API key"):
            guardian_api_client.search_content("test")
    
    def test_search_content_http_error(self, guardian_api_client, mock_requests_get):
        """Test handling of HTTP errors."""
        mock_requests_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        with pytest.raises(GuardianAPIError, match="Failed to make request to Guardian API"):
            guardian_api_client.search_content("test")
    
    def test_search_content_timeout(self, guardian_api_client, mock_requests_get):
        """Test handling of request timeout."""
        mock_requests_get.side_effect = requests.exceptions.Timeout("Request timeout")
        
        with pytest.raises(GuardianAPIError, match="Failed to make request to Guardian API"):
            guardian_api_client.search_content("test")
    
    def test_search_content_invalid_json(self, guardian_api_client, mock_requests_get):
        """Test handling of invalid JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response
        
        with pytest.raises(GuardianAPIError, match="Invalid JSON response from Guardian API"):
            guardian_api_client.search_content("test")
    
    def test_search_content_no_results(self, guardian_api_client, mock_requests_get, empty_response):
        """Test search with no results."""
        mock_response = create_mock_response(empty_response)
        mock_requests_get.return_value = mock_response
        
        articles = guardian_api_client.search_content("nonexistent-topic")
        
        assert len(articles) == 0
        assert isinstance(articles, list)
    
    def test_search_content_with_long_body_text(self, guardian_api_client, mock_requests_get):
        """Test content preview truncation for long articles."""
        long_text = "This is a very long article. " * 100  # More than 1000 characters
        
        response_data = {
            "response": {
                "status": "ok",
                "results": [
                    {
                        "webPublicationDate": "2023-01-01T10:00:00Z",
                        "webTitle": "Long Article",
                        "webUrl": "https://example.com/long-article",
                        "fields": {
                            "bodyText": long_text
                        }
                    }
                ]
            }
        }
        
        mock_response = create_mock_response(response_data)
        mock_requests_get.return_value = mock_response
        
        articles = guardian_api_client.search_content("test")
        
        assert len(articles) == 1
        content_preview = articles[0]['content_preview']
        assert len(content_preview) <= 1003  # 1000 chars + "..."
        assert content_preview.endswith("...")
    
    def test_search_content_no_body_text(self, guardian_api_client, mock_requests_get):
        """Test article without body text field."""
        response_data = {
            "response": {
                "status": "ok",
                "results": [
                    {
                        "webPublicationDate": "2023-01-01T10:00:00Z",
                        "webTitle": "Article Without Body",
                        "webUrl": "https://example.com/article",
                        "fields": {}  # No bodyText field
                    }
                ]
            }
        }
        
        mock_response = create_mock_response(response_data)
        mock_requests_get.return_value = mock_response
        
        articles = guardian_api_client.search_content("test")
        
        assert len(articles) == 1
        assert 'content_preview' not in articles[0]
    
    def test_make_request_adds_api_key(self, guardian_api_client, mock_requests_get):
        """Test that _make_request adds API key to parameters."""
        response_data = {"response": {"status": "ok", "results": []}}
        mock_response = create_mock_response(response_data)
        mock_requests_get.return_value = mock_response
        
        guardian_api_client._make_request("test-endpoint", {"param1": "value1"})
        
        call_args = mock_requests_get.call_args
        params = call_args[1]['params']
        assert params['api-key'] == "test-api-key"
        assert params['param1'] == "value1"
    
    def test_search_content_strips_whitespace(self, guardian_api_client, mock_requests_get, sample_guardian_api_response):
        """Test that search term whitespace is stripped."""
        mock_response = create_mock_response(sample_guardian_api_response)
        mock_requests_get.return_value = mock_response
        
        guardian_api_client.search_content("  machine learning  ")
        
        call_args = mock_requests_get.call_args
        params = call_args[1]['params']
        assert params['q'] == "machine learning"  # Whitespace stripped
    
    def test_search_content_with_special_characters(self, guardian_api_client, mock_requests_get, sample_guardian_api_response):
        """Test search with special characters in search term."""
        mock_response = create_mock_response(sample_guardian_api_response)
        mock_requests_get.return_value = mock_response
        
        search_term = "machine learning & AI"
        guardian_api_client.search_content(search_term)
        
        call_args = mock_requests_get.call_args
        params = call_args[1]['params']
        assert params['q'] == search_term
