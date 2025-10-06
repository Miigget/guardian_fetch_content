"""
Tests for GuardianContentFetcher module.

This module contains comprehensive tests for the main orchestrator class,
including successful operations, error handling, and factory methods.
"""

import pytest
from unittest.mock import Mock, patch

from guardian_content_fetcher.content_fetcher import (
    GuardianContentFetcher, GuardianContentFetcherFactory, GuardianContentFetcherError
)
from guardian_content_fetcher.api_client import GuardianAPIError
from guardian_content_fetcher.message_broker import MessageBrokerError
from tests.conftest import assert_valid_result_format


class TestGuardianContentFetcher:
    """Test cases for GuardianContentFetcher class."""
    
    def test_initialization_success(self, guardian_api_client, mock_publisher):
        """Test successful fetcher initialization."""
        fetcher = GuardianContentFetcher(guardian_api_client, mock_publisher)
        
        assert fetcher.api_client == guardian_api_client
        assert fetcher.message_broker == mock_publisher
    
    def test_initialization_none_api_client(self, mock_publisher):
        """Test that None API client raises ValueError."""
        with pytest.raises(ValueError, match="API client cannot be None"):
            GuardianContentFetcher(None, mock_publisher)
    
    def test_initialization_none_message_broker(self, guardian_api_client):
        """Test that None message broker raises ValueError."""
        with pytest.raises(ValueError, match="Message broker cannot be None"):
            GuardianContentFetcher(guardian_api_client, None)
    
    def test_fetch_and_publish_success(self, content_fetcher, sample_formatted_articles):
        """Test successful fetch and publish operation."""
        # Mock API client to return sample articles
        content_fetcher.api_client.search_content = Mock(return_value=sample_formatted_articles)
        
        result = content_fetcher.fetch_and_publish("machine learning")
        
        # Verify result format
        assert_valid_result_format(result)
        
        # Verify result content
        assert result['success'] is True
        assert result['articles_found'] == 2
        assert result['articles_published'] == 2
        assert result['search_term'] == "machine learning"
        assert result['date_from'] is None
        assert len(result['errors']) == 0
        
        # Verify API client was called correctly
        content_fetcher.api_client.search_content.assert_called_once_with(
            search_term="machine learning",
            date_from=None,
            page_size=10
        )
        
        # Verify messages were published
        published = content_fetcher.message_broker.get_published_messages()
        assert len(published) == 2
        assert published == sample_formatted_articles
    
    def test_fetch_and_publish_with_date_filter(self, content_fetcher, sample_formatted_articles):
        """Test fetch and publish with date filter."""
        content_fetcher.api_client.search_content = Mock(return_value=sample_formatted_articles)
        
        result = content_fetcher.fetch_and_publish(
            "machine learning",
            date_from="2023-01-01",
            max_articles=5
        )
        
        assert result['success'] is True
        assert result['date_from'] == "2023-01-01"
        
        content_fetcher.api_client.search_content.assert_called_once_with(
            search_term="machine learning",
            date_from="2023-01-01",
            page_size=5
        )
    
    def test_fetch_and_publish_no_articles_found(self, content_fetcher):
        """Test fetch and publish when no articles are found."""
        content_fetcher.api_client.search_content = Mock(return_value=[])
        
        result = content_fetcher.fetch_and_publish("nonexistent-topic")
        
        assert_valid_result_format(result)
        assert result['success'] is True  # No articles is not an error
        assert result['articles_found'] == 0
        assert result['articles_published'] == 0
        assert len(result['errors']) == 0
    
    def test_fetch_and_publish_api_error(self, content_fetcher):
        """Test handling of Guardian API errors."""
        content_fetcher.api_client.search_content = Mock(
            side_effect=GuardianAPIError("API key invalid")
        )
        
        with pytest.raises(GuardianContentFetcherError, match="Service error during fetch and publish"):
            content_fetcher.fetch_and_publish("test")
    
    def test_fetch_and_publish_message_broker_error(self, content_fetcher, sample_formatted_articles):
        """Test handling of message broker errors."""
        content_fetcher.api_client.search_content = Mock(return_value=sample_formatted_articles)
        content_fetcher.message_broker.publish_batch = Mock(
            side_effect=MessageBrokerError("Kinesis unavailable")
        )
        content_fetcher.message_broker.publish_message = Mock(
            side_effect=MessageBrokerError("Kinesis unavailable")
        )
        
        with pytest.raises(GuardianContentFetcherError, match="Service error during fetch and publish"):
            content_fetcher.fetch_and_publish("test")
    
    def test_fetch_and_publish_partial_publish_success(self, content_fetcher, sample_formatted_articles):
        """Test partial publishing success (some messages fail)."""
        content_fetcher.api_client.search_content = Mock(return_value=sample_formatted_articles)
        
        # Mock batch publish to return partial success
        content_fetcher.message_broker.publish_batch = Mock(return_value=1)  # Only 1 out of 2 published
        
        result = content_fetcher.fetch_and_publish("test")
        
        assert result['success'] is True  # Partial success is still success
        assert result['articles_found'] == 2
        assert result['articles_published'] == 1
        assert len(result['errors']) == 1
        assert "Only 1 out of 2 articles were published" in result['errors'][0]
    
    def test_fetch_and_publish_complete_publish_failure(self, content_fetcher, sample_formatted_articles):
        """Test complete publishing failure (no messages published)."""
        content_fetcher.api_client.search_content = Mock(return_value=sample_formatted_articles)
        
        # Mock batch publish to return 0 (complete failure)
        content_fetcher.message_broker.publish_batch = Mock(return_value=0)
        content_fetcher.message_broker.publish_message = Mock(return_value=False)
        
        result = content_fetcher.fetch_and_publish("test")
        
        assert result['success'] is False
        assert result['articles_found'] == 2
        assert result['articles_published'] == 0
        assert len(result['errors']) == 1
        assert "Failed to publish any articles" in result['errors'][0]
    
    def test_fetch_and_publish_fallback_to_individual_publishing(self, content_fetcher, sample_formatted_articles):
        """Test fallback to individual publishing when batch fails."""
        content_fetcher.api_client.search_content = Mock(return_value=sample_formatted_articles)
        
        # Mock batch publish to fail, individual publish to succeed
        content_fetcher.message_broker.publish_batch = Mock(return_value=0)
        content_fetcher.message_broker.publish_message = Mock(return_value=True)
        
        result = content_fetcher.fetch_and_publish("test")
        
        assert result['success'] is True
        assert result['articles_published'] == 2
        
        # Verify both batch and individual methods were called
        content_fetcher.message_broker.publish_batch.assert_called_once()
        assert content_fetcher.message_broker.publish_message.call_count == 2
    
    def test_validate_inputs_empty_search_term(self, content_fetcher):
        """Test validation of empty search term."""
        with pytest.raises(ValueError, match="Search term cannot be empty"):
            content_fetcher._validate_inputs("", None, 10)
        
        with pytest.raises(ValueError, match="Search term cannot be empty"):
            content_fetcher._validate_inputs("   ", None, 10)
    
    def test_validate_inputs_invalid_max_articles(self, content_fetcher):
        """Test validation of invalid max_articles."""
        with pytest.raises(ValueError, match="max_articles must be between 1 and 50"):
            content_fetcher._validate_inputs("test", None, 0)
        
        with pytest.raises(ValueError, match="max_articles must be between 1 and 50"):
            content_fetcher._validate_inputs("test", None, 51)
    
    def test_publish_articles_individually_mixed_results(self, content_fetcher):
        """Test individual publishing with mixed success/failure results."""
        articles = [
            {"webTitle": "Article 1"},
            {"webTitle": "Article 2"},
            {"webTitle": "Article 3"}
        ]
        
        # Mock individual publish to succeed for some, fail for others
        content_fetcher.message_broker.publish_message = Mock(side_effect=[True, False, True])
        
        result = content_fetcher._publish_articles_individually(articles)
        
        assert result == 2  # 2 out of 3 succeeded
        assert content_fetcher.message_broker.publish_message.call_count == 3
    
    def test_publish_articles_individually_with_exceptions(self, content_fetcher):
        """Test individual publishing with exceptions."""
        articles = [
            {"webTitle": "Article 1"},
            {"webTitle": "Article 2"},
            {"webTitle": "Article 3"}
        ]
        
        # Mock individual publish to raise exception for middle article
        content_fetcher.message_broker.publish_message = Mock(
            side_effect=[True, MessageBrokerError("Error"), True]
        )
        
        result = content_fetcher._publish_articles_individually(articles)
        
        assert result == 2  # 2 out of 3 succeeded (exception doesn't stop processing)
    
    def test_close(self, content_fetcher):
        """Test close method."""
        content_fetcher.message_broker.close = Mock()
        
        content_fetcher.close()
        
        content_fetcher.message_broker.close.assert_called_once()
    
    def test_close_with_exception(self, content_fetcher):
        """Test close method when message broker raises exception."""
        content_fetcher.message_broker.close = Mock(side_effect=Exception("Close error"))
        
        # Should not raise exception
        content_fetcher.close()
    
    def test_context_manager(self, guardian_api_client, mock_publisher):
        """Test context manager functionality."""
        mock_publisher.close = Mock()
        
        with GuardianContentFetcher(guardian_api_client, mock_publisher) as fetcher:
            assert isinstance(fetcher, GuardianContentFetcher)
        
        # Close should be called automatically
        mock_publisher.close.assert_called_once()
    
    def test_unexpected_error_handling(self, content_fetcher):
        """Test handling of unexpected errors."""
        content_fetcher.api_client.search_content = Mock(
            side_effect=RuntimeError("Unexpected error")
        )
        
        with pytest.raises(GuardianContentFetcherError, match="Unexpected error during fetch and publish"):
            content_fetcher.fetch_and_publish("test")


class TestGuardianContentFetcherFactory:
    """Test cases for GuardianContentFetcherFactory class."""
    
    @patch('guardian_content_fetcher.content_fetcher.KinesisPublisher')
    @patch('guardian_content_fetcher.content_fetcher.GuardianAPIClient')
    def test_create_with_kinesis(self, mock_api_client_class, mock_kinesis_publisher_class):
        """Test factory method for creating fetcher with Kinesis."""
        mock_api_client = Mock()
        mock_kinesis_publisher = Mock()
        mock_api_client_class.return_value = mock_api_client
        mock_kinesis_publisher_class.return_value = mock_kinesis_publisher
        
        fetcher = GuardianContentFetcherFactory.create_with_kinesis(
            guardian_api_key="test-key",
            kinesis_stream_name="test-stream",
            aws_region="us-west-2",
            aws_access_key_id="aws-key",
            aws_secret_access_key="aws-secret"
        )
        
        # Verify API client was created correctly
        mock_api_client_class.assert_called_once_with(api_key="test-key")
        
        # Verify Kinesis publisher was created correctly
        mock_kinesis_publisher_class.assert_called_once_with(
            stream_name="test-stream",
            region_name="us-west-2",
            aws_access_key_id="aws-key",
            aws_secret_access_key="aws-secret"
        )
        
        # Verify fetcher was created
        assert isinstance(fetcher, GuardianContentFetcher)
        assert fetcher.api_client == mock_api_client
        assert fetcher.message_broker == mock_kinesis_publisher
    
    @patch('guardian_content_fetcher.content_fetcher.KinesisPublisher')
    @patch('guardian_content_fetcher.content_fetcher.GuardianAPIClient')
    def test_create_with_kinesis_default_params(self, mock_api_client_class, mock_kinesis_publisher_class):
        """Test factory method with default parameters."""
        mock_api_client_class.return_value = Mock()
        mock_kinesis_publisher_class.return_value = Mock()
        
        fetcher = GuardianContentFetcherFactory.create_with_kinesis(
            guardian_api_key="test-key",
            kinesis_stream_name="test-stream"
        )
        
        # Verify default parameters were used
        mock_kinesis_publisher_class.assert_called_once_with(
            stream_name="test-stream",
            region_name="us-east-1",  # Default region
            aws_access_key_id=None,
            aws_secret_access_key=None
        )
        
        assert isinstance(fetcher, GuardianContentFetcher)
    
    @patch('guardian_content_fetcher.content_fetcher.KinesisPublisher')
    def test_create_with_kinesis_error(self, mock_kinesis_publisher_class):
        """Test factory method error handling."""
        mock_kinesis_publisher_class.side_effect = Exception("Kinesis error")
        
        with pytest.raises(GuardianContentFetcherError, match="Failed to create fetcher with Kinesis"):
            GuardianContentFetcherFactory.create_with_kinesis(
                guardian_api_key="test-key",
                kinesis_stream_name="test-stream"
            )
    
    @patch('guardian_content_fetcher.content_fetcher.MockPublisher')
    @patch('guardian_content_fetcher.content_fetcher.GuardianAPIClient')
    def test_create_with_mock(self, mock_api_client_class, mock_mock_publisher_class):
        """Test factory method for creating fetcher with mock publisher."""
        mock_api_client = Mock()
        mock_publisher = Mock()
        mock_api_client_class.return_value = mock_api_client
        mock_mock_publisher_class.return_value = mock_publisher
        
        fetcher = GuardianContentFetcherFactory.create_with_mock(
            guardian_api_key="test-key"
        )
        
        # Verify API client was created correctly
        mock_api_client_class.assert_called_once_with(api_key="test-key")
        
        # Verify mock publisher was created
        mock_mock_publisher_class.assert_called_once()
        
        # Verify fetcher was created
        assert isinstance(fetcher, GuardianContentFetcher)
        assert fetcher.api_client == mock_api_client
        assert fetcher.message_broker == mock_publisher
    
    @patch('guardian_content_fetcher.content_fetcher.GuardianAPIClient')
    def test_create_with_mock_error(self, mock_api_client_class):
        """Test factory method error handling for mock creation."""
        mock_api_client_class.side_effect = Exception("API client error")
        
        with pytest.raises(GuardianContentFetcherError, match="Failed to create fetcher with mock"):
            GuardianContentFetcherFactory.create_with_mock("test-key")
