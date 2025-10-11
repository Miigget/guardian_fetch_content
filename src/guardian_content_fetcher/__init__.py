"""
Guardian Content Fetcher Package.

A Python package for fetching articles from Guardian API and publishing
them to message brokers for data processing pipelines.

This package provides:
- GuardianAPIClient: Interface to Guardian API for article retrieval
- MessageBrokerPublisher: Abstract interface for message broker publishing
- KinesisPublisher: AWS Kinesis implementation of message broker
- GuardianContentFetcher: Main orchestrator class

Example usage:
    >>> from guardian_content_fetcher import GuardianContentFetcherFactory
    >>>
    >>> # Using Kinesis (production)
    >>> fetcher = GuardianContentFetcherFactory.create_with_kinesis(
    ...     guardian_api_key="your-guardian-api-key",
    ...     kinesis_stream_name="guardian-content"
    ... )
    >>> result = fetcher.fetch_and_publish("machine learning", date_from="2023-01-01")
    >>>
    >>> # Using mock broker (testing)
    >>> test_fetcher = GuardianContentFetcherFactory.create_with_mock(
    ...     guardian_api_key="your-guardian-api-key"
    ... )
    >>> result = test_fetcher.fetch_and_publish("python programming")
    >>>
    >>> # Using configuration from environment variables
    >>> from guardian_content_fetcher import load_config_from_env, setup_logging
    >>> config = load_config_from_env()
    >>> setup_logging(config.log_level)
"""

__version__ = "1.0.0"
__author__ = "Marcin Sodel"

# Import main classes for easy access
from .api_client import GuardianAPIClient
from .message_broker import MessageBrokerPublisher, KinesisPublisher, MockPublisher
from .content_fetcher import GuardianContentFetcher, GuardianContentFetcherFactory
from .config import (
    AppConfig,
    load_config_from_env,
    setup_logging,
    print_config_template,
)

__all__ = [
    "GuardianAPIClient",
    "MessageBrokerPublisher",
    "KinesisPublisher",
    "MockPublisher",
    "GuardianContentFetcher",
    "GuardianContentFetcherFactory",
    "AppConfig",
    "load_config_from_env",
    "setup_logging",
    "print_config_template",
]
