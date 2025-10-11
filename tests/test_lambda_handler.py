"""
Tests for Lambda Handler module.

This module contains comprehensive tests for the AWS Lambda handler,
including event parsing, configuration, and error handling.
"""

import json
from unittest.mock import patch, Mock, MagicMock

from guardian_content_fetcher.lambda_handler import handler


class TestLambdaHandler:
    """Test cases for Lambda handler function."""

    @patch("guardian_content_fetcher.lambda_handler.GuardianContentFetcherFactory")
    @patch.dict(
        "os.environ",
        {
            "GUARDIAN_API_KEY": "test-api-key",
            "KINESIS_STREAM_NAME": "test-stream",
            "AWS_DEFAULT_REGION": "us-east-1",
        },
    )
    def test_handler_success(self, mock_factory):
        """Test successful Lambda handler execution."""
        # Setup mock fetcher
        mock_fetcher = MagicMock()
        mock_fetcher.__enter__ = Mock(return_value=mock_fetcher)
        mock_fetcher.__exit__ = Mock(return_value=None)
        mock_fetcher.fetch_and_publish.return_value = {
            "success": True,
            "articles_found": 5,
            "articles_published": 5,
            "search_term": "test",
            "date_from": None,
            "errors": [],
        }
        mock_factory.create_with_kinesis.return_value = mock_fetcher

        # Create test event
        event = {"search_term": "machine learning", "max_articles": 10}

        # Call handler
        response = handler(event, None)

        # Verify response
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["articles_found"] == 5
        assert body["articles_published"] == 5

        # Verify factory was called correctly
        mock_factory.create_with_kinesis.assert_called_once_with(
            guardian_api_key="test-api-key",
            kinesis_stream_name="test-stream",
            aws_region="us-east-1",
        )

        # Verify fetch_and_publish was called
        mock_fetcher.fetch_and_publish.assert_called_once_with(
            search_term="machine learning", date_from=None, max_articles=10
        )

    @patch("guardian_content_fetcher.lambda_handler.GuardianContentFetcherFactory")
    @patch.dict(
        "os.environ",
        {
            "GUARDIAN_API_KEY": "test-api-key",
            "KINESIS_STREAM_NAME": "test-stream",
            "AWS_DEFAULT_REGION": "eu-west-1",
        },
    )
    def test_handler_with_date_filter(self, mock_factory):
        """Test handler with date filter parameter."""
        # Setup mock fetcher
        mock_fetcher = MagicMock()
        mock_fetcher.__enter__ = Mock(return_value=mock_fetcher)
        mock_fetcher.__exit__ = Mock(return_value=None)
        mock_fetcher.fetch_and_publish.return_value = {
            "success": True,
            "articles_found": 3,
            "articles_published": 3,
            "search_term": "AI",
            "date_from": "2023-01-01",
            "errors": [],
        }
        mock_factory.create_with_kinesis.return_value = mock_fetcher

        # Create test event with date filter
        event = {
            "search_term": "AI",
            "date_from": "2023-01-01",
            "max_articles": 15,
        }

        # Call handler
        response = handler(event, None)

        # Verify response
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True

        # Verify fetch_and_publish was called with correct params
        mock_fetcher.fetch_and_publish.assert_called_once_with(
            search_term="AI", date_from="2023-01-01", max_articles=15
        )

    def test_handler_missing_search_term(self):
        """Test handler with missing search_term parameter."""
        event = {"max_articles": 10}

        response = handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
        assert "search_term" in body["error"]

    @patch.dict("os.environ", {}, clear=True)
    def test_handler_missing_api_key(self):
        """Test handler with missing GUARDIAN_API_KEY environment variable."""
        event = {"search_term": "test"}

        response = handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
        assert "GUARDIAN_API_KEY" in body["error"]

    @patch.dict(
        "os.environ",
        {"GUARDIAN_API_KEY": "test-key"},
        clear=True,
    )
    def test_handler_missing_kinesis_stream(self):
        """Test handler with missing KINESIS_STREAM_NAME."""
        event = {"search_term": "test"}

        response = handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
        assert "KINESIS_STREAM_NAME" in body["error"]

    @patch("guardian_content_fetcher.lambda_handler.GuardianContentFetcherFactory")
    @patch.dict(
        "os.environ",
        {
            "GUARDIAN_API_KEY": "test-key",
            "KINESIS_STREAM_NAME": "test-stream",
            # Don't set AWS_DEFAULT_REGION to test default
        },
        clear=False,
    )
    def test_handler_default_region(self, mock_factory):
        """Test handler uses default AWS region when not specified."""
        import os

        # Remove AWS_DEFAULT_REGION if it exists
        os.environ.pop("AWS_DEFAULT_REGION", None)

        mock_fetcher = MagicMock()
        mock_fetcher.__enter__ = Mock(return_value=mock_fetcher)
        mock_fetcher.__exit__ = Mock(return_value=None)
        mock_fetcher.fetch_and_publish.return_value = {
            "success": True,
            "articles_found": 1,
            "articles_published": 1,
            "search_term": "test",
            "date_from": None,
            "errors": [],
        }
        mock_factory.create_with_kinesis.return_value = mock_fetcher

        event = {"search_term": "test"}

        handler(event, None)

        # Verify default region from lambda_handler is passed (us-east-1)
        call_args = mock_factory.create_with_kinesis.call_args
        assert call_args.kwargs["guardian_api_key"] == "test-key"
        assert call_args.kwargs["kinesis_stream_name"] == "test-stream"
        assert call_args.kwargs["aws_region"] == "us-east-1"

    @patch("guardian_content_fetcher.lambda_handler.GuardianContentFetcherFactory")
    @patch.dict(
        "os.environ",
        {
            "GUARDIAN_API_KEY": "test-key",
            "KINESIS_STREAM_NAME": "test-stream",
        },
    )
    def test_handler_default_max_articles(self, mock_factory):
        """Test handler uses default max_articles when not specified."""
        mock_fetcher = MagicMock()
        mock_fetcher.__enter__ = Mock(return_value=mock_fetcher)
        mock_fetcher.__exit__ = Mock(return_value=None)
        mock_fetcher.fetch_and_publish.return_value = {
            "success": True,
            "articles_found": 1,
            "articles_published": 1,
            "search_term": "test",
            "date_from": None,
            "errors": [],
        }
        mock_factory.create_with_kinesis.return_value = mock_fetcher

        event = {"search_term": "test"}

        handler(event, None)

        # Verify default max_articles is 10
        mock_fetcher.fetch_and_publish.assert_called_once_with(
            search_term="test", date_from=None, max_articles=10
        )

    @patch("guardian_content_fetcher.lambda_handler.GuardianContentFetcherFactory")
    @patch.dict(
        "os.environ",
        {
            "GUARDIAN_API_KEY": "test-key",
            "KINESIS_STREAM_NAME": "test-stream",
        },
    )
    def test_handler_fetcher_error(self, mock_factory):
        """Test handler handles GuardianContentFetcherError."""
        from guardian_content_fetcher.content_fetcher import (
            GuardianContentFetcherError,
        )

        mock_fetcher = MagicMock()
        mock_fetcher.__enter__ = Mock(return_value=mock_fetcher)
        mock_fetcher.__exit__ = Mock(return_value=None)
        mock_fetcher.fetch_and_publish.side_effect = GuardianContentFetcherError(
            "Test error"
        )
        mock_factory.create_with_kinesis.return_value = mock_fetcher

        event = {"search_term": "test"}

        response = handler(event, None)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body
        assert "application error" in body["error"].lower()

    @patch("guardian_content_fetcher.lambda_handler.GuardianContentFetcherFactory")
    @patch.dict(
        "os.environ",
        {
            "GUARDIAN_API_KEY": "test-key",
            "KINESIS_STREAM_NAME": "test-stream",
        },
    )
    def test_handler_unexpected_error(self, mock_factory):
        """Test handler handles unexpected exceptions."""
        mock_fetcher = MagicMock()
        mock_fetcher.__enter__ = Mock(return_value=mock_fetcher)
        mock_fetcher.__exit__ = Mock(return_value=None)
        mock_fetcher.fetch_and_publish.side_effect = RuntimeError("Unexpected error")
        mock_factory.create_with_kinesis.return_value = mock_fetcher

        event = {"search_term": "test"}

        response = handler(event, None)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body
        assert "unexpected error" in body["error"].lower()

    @patch("guardian_content_fetcher.lambda_handler.GuardianContentFetcherFactory")
    @patch.dict(
        "os.environ",
        {
            "GUARDIAN_API_KEY": "test-key",
            "KINESIS_STREAM_NAME": "test-stream",
        },
    )
    def test_handler_invalid_max_articles(self, mock_factory):
        """Test handler with invalid max_articles value."""
        event = {"search_term": "test", "max_articles": "invalid"}

        response = handler(event, None)

        # Should return 400 for invalid parameter
        assert response["statusCode"] in [400, 500]
        body = json.loads(response["body"])
        assert "error" in body

    @patch("guardian_content_fetcher.lambda_handler.GuardianContentFetcherFactory")
    @patch.dict(
        "os.environ",
        {
            "GUARDIAN_API_KEY": "test-key",
            "KINESIS_STREAM_NAME": "test-stream",
        },
    )
    def test_handler_context_manager_cleanup(self, mock_factory):
        """Test that handler properly uses context manager for cleanup."""
        mock_fetcher = MagicMock()
        mock_enter = Mock(return_value=mock_fetcher)
        mock_exit = Mock(return_value=None)
        mock_fetcher.__enter__ = mock_enter
        mock_fetcher.__exit__ = mock_exit
        mock_fetcher.fetch_and_publish.return_value = {
            "success": True,
            "articles_found": 1,
            "articles_published": 1,
            "search_term": "test",
            "date_from": None,
            "errors": [],
        }
        mock_factory.create_with_kinesis.return_value = mock_fetcher

        event = {"search_term": "test"}

        handler(event, None)

        # Verify context manager methods were called
        mock_enter.assert_called_once()
        mock_exit.assert_called_once()

    @patch("guardian_content_fetcher.lambda_handler.GuardianContentFetcherFactory")
    @patch.dict(
        "os.environ",
        {
            "GUARDIAN_API_KEY": "test-key",
            "KINESIS_STREAM_NAME": "test-stream",
        },
    )
    def test_handler_partial_success(self, mock_factory):
        """Test handler with partial success result."""
        mock_fetcher = MagicMock()
        mock_fetcher.__enter__ = Mock(return_value=mock_fetcher)
        mock_fetcher.__exit__ = Mock(return_value=None)
        mock_fetcher.fetch_and_publish.return_value = {
            "success": True,
            "articles_found": 10,
            "articles_published": 7,
            "search_term": "test",
            "date_from": None,
            "errors": ["Failed to publish 3 articles"],
        }
        mock_factory.create_with_kinesis.return_value = mock_fetcher

        event = {"search_term": "test"}

        response = handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["articles_found"] == 10
        assert body["articles_published"] == 7
        assert len(body["errors"]) > 0
