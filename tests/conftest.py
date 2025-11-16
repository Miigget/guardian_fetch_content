"""
Test configuration and fixtures for Guardian Content Fetcher tests.

This module provides common test fixtures and configuration
used across all test modules.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional

from guardian_content_fetcher.api_client import GuardianAPIClient
from guardian_content_fetcher.message_broker import MockPublisher, KinesisPublisher
from guardian_content_fetcher.content_fetcher import GuardianContentFetcher
from guardian_content_fetcher.config import (
    AppConfig,
    GuardianConfig,
    KinesisConfig,
    AWSConfig,
)


@pytest.fixture
def sample_guardian_api_response():
    """
    Sample Guardian API response for testing.

    Returns:
        Dict: Mock API response with sample articles
    """
    return {
        "response": {
            "status": "ok",
            "total": 2,
            "startIndex": 1,
            "pageSize": 10,
            "currentPage": 1,
            "pages": 1,
            "results": [
                {
                    "id": "technology/2023/jan/01/machine-learning-advances",
                    "type": "article",
                    "sectionId": "technology",
                    "sectionName": "Technology",
                    "webPublicationDate": "2023-01-01T10:00:00Z",
                    "webTitle": "Machine Learning Advances in 2023",
                    "webUrl": (
                        "https://www.theguardian.com/technology/2023/jan/01/"
                        "machine-learning-advances"
                    ),
                    "apiUrl": (
                        "https://content.guardianapis.com/technology/"
                        "2023/jan/01/machine-learning-advances"
                    ),
                    "fields": {
                        "bodyText": (
                            "This is a sample article about machine learning "
                            "advances. " * 50
                        )
                    },
                },
                {
                    "id": "technology/2023/jan/02/ai-breakthrough",
                    "type": "article",
                    "sectionId": "technology",
                    "sectionName": "Technology",
                    "webPublicationDate": "2023-01-02T15:30:00Z",
                    "webTitle": "AI Breakthrough in Natural Language Processing",
                    "webUrl": (
                        "https://www.theguardian.com/technology/2023/jan/02/"
                        "ai-breakthrough"
                    ),
                    "apiUrl": (
                        "https://content.guardianapis.com/technology/"
                        "2023/jan/02/ai-breakthrough"
                    ),
                    "fields": {
                        "bodyText": "Another sample article about AI developments. "
                        * 30
                    },
                },
            ],
        }
    }


@pytest.fixture
def sample_formatted_articles():
    """
    Sample formatted articles as returned by GuardianAPIClient.

    Returns:
        List: List of formatted article dictionaries
    """
    return [
        {
            "webPublicationDate": "2023-01-01T10:00:00Z",
            "webTitle": "Machine Learning Advances in 2023",
            "webUrl": (
                "https://www.theguardian.com/technology/2023/jan/01/"
                "machine-learning-advances"
            ),
            "content_preview": (
                "This is a sample article about machine learning advances. " * 20
                + "..."
            ),
        },
        {
            "webPublicationDate": "2023-01-02T15:30:00Z",
            "webTitle": "AI Breakthrough in Natural Language Processing",
            "webUrl": (
                "https://www.theguardian.com/technology/2023/jan/02/" "ai-breakthrough"
            ),
            "content_preview": (
                "Another sample article about AI developments. " * 20 + "..."
            ),
        },
    ]


@pytest.fixture
def mock_requests_get():
    """
    Mock for requests.get method.

    Returns:
        Mock: Configured mock for requests.get
    """
    with patch("requests.get") as mock_get:
        yield mock_get


@pytest.fixture
def guardian_api_client():
    """
    Guardian API client instance for testing.

    Returns:
        GuardianAPIClient: Test API client instance
    """
    return GuardianAPIClient(api_key="test-api-key", rate_limit_delay=0.1)


@pytest.fixture
def mock_publisher():
    """
    Mock message broker publisher for testing.

    Returns:
        MockPublisher: Mock publisher instance
    """
    return MockPublisher()


@pytest.fixture
def mock_kinesis_client():
    """
    Mock boto3 Kinesis client for testing.

    Returns:
        Mock: Configured mock for boto3 Kinesis client
    """
    with patch("boto3.client") as mock_client:
        # Configure the mock client
        client_instance = MagicMock()
        mock_client.return_value = client_instance

        # Mock successful stream description
        client_instance.describe_stream.return_value = {
            "StreamDescription": {
                "StreamStatus": "ACTIVE",
                "StreamName": "test-stream",
            }
        }

        # Mock successful put_record
        client_instance.put_record.return_value = {
            "SequenceNumber": "12345678901234567890",
            "ShardId": "shardId-000000000000",
        }

        # Mock successful put_records
        client_instance.put_records.return_value = {
            "FailedRecordCount": 0,
            "Records": [
                {
                    "SequenceNumber": "12345678901234567890",
                    "ShardId": "shardId-000000000000",
                }
            ],
        }

        yield client_instance


@pytest.fixture
def kinesis_publisher(mock_kinesis_client):
    """
    Kinesis publisher instance for testing.

    Returns:
        KinesisPublisher: Test Kinesis publisher instance
    """
    return KinesisPublisher(
        stream_name="test-stream",
        region_name="eu-west-2",
        aws_access_key_id="test-key",
        aws_secret_access_key="test-secret",
    )


@pytest.fixture
def content_fetcher(guardian_api_client, mock_publisher):
    """
    Guardian Content Fetcher instance for testing.

    Returns:
        GuardianContentFetcher: Test fetcher instance
    """
    return GuardianContentFetcher(guardian_api_client, mock_publisher)


@pytest.fixture
def mock_environment_variables():
    """
    Mock environment variables for testing configuration.

    Returns:
        Dict: Dictionary of environment variables
    """
    env_vars = {
        "GUARDIAN_API_KEY": "test-guardian-api-key",
        "AWS_ACCESS_KEY_ID": "test-aws-key",
        "AWS_SECRET_ACCESS_KEY": "test-aws-secret",
        "AWS_DEFAULT_REGION": "eu-west-2",
        "KINESIS_STREAM_NAME": "test-stream",
        "LOG_LEVEL": "INFO",
        "USE_MOCK_BROKER": "false",
    }

    with patch.dict("os.environ", env_vars, clear=True):
        yield env_vars


@pytest.fixture
def cli_args():
    """
    Sample CLI arguments for testing.

    Returns:
        argparse.Namespace: Mock CLI arguments
    """
    from argparse import Namespace

    return Namespace(
        search_term="machine learning",
        date_from="2023-01-01",
        max_articles=10,
        stream_name="test-stream",
        aws_region="eu-west-2",
        use_mock=False,
        output_format="text",
        verbose=False,
        quiet=False,
    )


@pytest.fixture
def error_response():
    """
    Sample error response from Guardian API.

    Returns:
        Dict: Mock error response
    """
    return {"response": {"status": "error", "message": "Invalid API key"}}


@pytest.fixture
def empty_response():
    """
    Sample empty response from Guardian API (no articles found).

    Returns:
        Dict: Mock empty response
    """
    return {"response": {"status": "ok", "total": 0, "results": []}}


@pytest.fixture
def large_article_batch():
    """
    Large batch of articles for testing batch operations.

    Returns:
        List: List of 100 sample articles
    """
    articles = []
    for i in range(100):
        articles.append(
            {
                "webPublicationDate": f"2023-01-{i+1:02d}T10:00:00Z",
                "webTitle": f"Sample Article {i+1}",
                "webUrl": f"https://www.theguardian.com/article-{i+1}",
                "content_preview": f"This is sample article number {i+1}. " * 10,
            }
        )
    return articles


# Test utility functions
def create_mock_response(data: Dict[str, Any], status_code: int = 200):
    """
    Create a mock HTTP response object.

    Args:
        data (Dict[str, Any]): Response data
        status_code (int): HTTP status code

    Returns:
        Mock: Mock response object
    """
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = data
    mock_response.raise_for_status.return_value = None
    return mock_response


def assert_article_format(article: Dict[str, Any]):
    """
    Assert that an article has the required format.

    Args:
        article (Dict[str, Any]): Article to validate
    """
    required_fields = ["webPublicationDate", "webTitle", "webUrl"]
    for field in required_fields:
        assert field in article, f"Missing required field: {field}"
        assert isinstance(article[field], str), f"Field {field} should be string"
        assert article[field], f"Field {field} should not be empty"


def assert_valid_result_format(result: Dict[str, Any]):
    """
    Assert that a fetch_and_publish result has the correct format.

    Args:
        result (Dict[str, Any]): Result to validate
    """
    required_fields = [
        "success",
        "articles_found",
        "articles_published",
        "search_term",
        "date_from",
        "errors",
    ]

    for field in required_fields:
        assert field in result, f"Missing required field: {field}"

    assert isinstance(result["success"], bool)
    assert isinstance(result["articles_found"], int)
    assert isinstance(result["articles_published"], int)
    assert isinstance(result["search_term"], str)
    assert isinstance(result["errors"], list)
    assert result["articles_found"] >= 0
    assert result["articles_published"] >= 0
    assert result["articles_published"] <= result["articles_found"]


@pytest.fixture
def mock_app_config():
    """
    Mock AppConfig for Lambda handler tests.

    Provides a default valid configuration that can be customized via parameters.
    Most tests use this standard configuration, but it can be overridden for
    special cases (e.g., missing Kinesis config, different regions).

    Returns:
        AppConfig: Default mock application configuration
    """
    return AppConfig(
        guardian_config=GuardianConfig(api_key="test-key"),
        kinesis_config=KinesisConfig(
            stream_name="test-stream", aws_config=AWSConfig(region="eu-west-2")
        ),
    )


@pytest.fixture
def create_mock_config():
    """
    Factory fixture to create custom AppConfig instances for tests.

    This allows tests to easily create configs with different parameters
    without duplicating the AppConfig construction code.

    Returns:
        function: Factory function to create AppConfig instances
    """

    def _create_config(
        api_key: str = "test-key",
        stream_name: str = "test-stream",
        region: str = "eu-west-2",
        kinesis_config: Optional[KinesisConfig] = None,
        use_mock_broker: bool = False,
    ) -> AppConfig:
        """
        Create an AppConfig instance with specified parameters.

        Args:
            api_key: Guardian API key
            stream_name: Kinesis stream name
            region: AWS region
            kinesis_config: Optional KinesisConfig (if None, creates one)
            use_mock_broker: Whether to use mock broker

        Returns:
            AppConfig: Configured AppConfig instance
        """
        guardian_config = GuardianConfig(api_key=api_key)

        if kinesis_config is None and not use_mock_broker:
            kinesis_config = KinesisConfig(
                stream_name=stream_name, aws_config=AWSConfig(region=region)
            )

        return AppConfig(
            guardian_config=guardian_config,
            kinesis_config=kinesis_config,
            use_mock_broker=use_mock_broker,
        )

    return _create_config
