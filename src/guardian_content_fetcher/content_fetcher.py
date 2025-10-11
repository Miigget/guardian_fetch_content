"""
Guardian Content Fetcher Module.

This module provides the main orchestrator class that coordinates
article retrieval from Guardian API and publishing to message brokers.
"""

import logging
from typing import Dict, List, Any, Optional
from .api_client import GuardianAPIClient, GuardianAPIError
from .message_broker import MessageBrokerPublisher, MessageBrokerError

# Set up logging for better debugging and monitoring
logger = logging.getLogger(__name__)


class GuardianContentFetcherError(Exception):
    """Custom exception for GuardianContentFetcher related errors."""
    pass


class GuardianContentFetcher:
    """
    Main orchestrator class for fetching Guardian articles and publishing to message brokers.
    
    This class coordinates the entire workflow:
    1. Search for articles using Guardian API
    2. Transform articles to required format
    3. Publish articles to configured message broker
    
    It handles errors gracefully and provides detailed logging for monitoring
    and debugging purposes.
    
    Attributes:
        api_client (GuardianAPIClient): Client for Guardian API interactions
        message_broker (MessageBrokerPublisher): Publisher for message broker
    """
    
    def __init__(
        self, 
        api_client: GuardianAPIClient, 
        message_broker: MessageBrokerPublisher
    ):
        """
        Initialize the Guardian Content Fetcher.
        
        Args:
            api_client (GuardianAPIClient): Configured Guardian API client
            message_broker (MessageBrokerPublisher): Configured message broker publisher
            
        Raises:
            ValueError: If api_client or message_broker is None
        """
        if not api_client:
            raise ValueError("API client cannot be None")
        if not message_broker:
            raise ValueError("Message broker cannot be None")
            
        self.api_client = api_client
        self.message_broker = message_broker
        
        logger.info("Guardian Content Fetcher initialized successfully")
    
    def fetch_and_publish(
        self, 
        search_term: str, 
        date_from: Optional[str] = None,
        max_articles: int = 10
    ) -> Dict[str, Any]:
        """
        Fetch articles from Guardian API and publish them to the message broker.
        
        This is the main method that orchestrates the entire workflow:
        1. Validates input parameters
        2. Searches for articles using the Guardian API
        3. Publishes found articles to the message broker
        4. Returns a summary of the operation
        
        Args:
            search_term (str): The search term to look for in articles
            date_from (Optional[str]): Filter articles from this date (YYYY-MM-DD format)
            max_articles (int): Maximum number of articles to process (default: 10)
            
        Returns:
            Dict[str, Any]: Summary containing:
                - success (bool): Whether the operation completed successfully
                - articles_found (int): Number of articles found by API
                - articles_published (int): Number of articles successfully published
                - search_term (str): The search term used
                - date_from (Optional[str]): The date filter applied
                - errors (List[str]): Any errors encountered during processing
                
        Raises:
            GuardianContentFetcherError: If the operation fails completely
            
        Example:
            >>> fetcher = GuardianContentFetcher(api_client, message_broker)
            >>> result = fetcher.fetch_and_publish("machine learning", "2023-01-01")
            >>> print(f"Published {result['articles_published']} articles")
        """
        # Initialize result dictionary
        result = {
            'success': False,
            'articles_found': 0,
            'articles_published': 0,
            'search_term': search_term,
            'date_from': date_from,
            'errors': []
        }
        
        try:
            # Validate input parameters
            self._validate_inputs(search_term, date_from, max_articles)
            
            logger.info(f"Starting article fetch and publish process for term: '{search_term}'")
            
            # Step 1: Fetch articles from Guardian API
            articles = self._fetch_articles(search_term, date_from, max_articles)
            result['articles_found'] = len(articles)
            
            if not articles:
                logger.warning(f"No articles found for search term: '{search_term}'")
                result['success'] = True  # No articles is not an error
                return result
            
            logger.info(f"Found {len(articles)} articles to publish")
            
            # Step 2: Publish articles to message broker
            published_count = self._publish_articles(articles)
            result['articles_published'] = published_count
            
            # Step 3: Determine overall success
            if published_count == len(articles):
                result['success'] = True
                logger.info(f"Successfully published all {published_count} articles")
            elif published_count > 0:
                result['success'] = True  # Partial success is still success
                logger.warning(f"Published {published_count} out of {len(articles)} articles")
                result['errors'].append(f"Only {published_count} out of {len(articles)} articles were published")
            else:
                result['success'] = False
                error_msg = "Failed to publish any articles to message broker"
                logger.error(error_msg)
                result['errors'].append(error_msg)
            
            return result
            
        except (GuardianAPIError, MessageBrokerError) as e:
            error_msg = f"Service error during fetch and publish: {e}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            raise GuardianContentFetcherError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error during fetch and publish: {e}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            raise GuardianContentFetcherError(error_msg) from e
    
    def _validate_inputs(
        self, 
        search_term: str, 
        date_from: Optional[str], 
        max_articles: int
    ) -> None:
        """
        Validate input parameters for the fetch and publish operation.
        
        Args:
            search_term (str): The search term to validate
            date_from (Optional[str]): The date filter to validate
            max_articles (int): The max articles limit to validate
            
        Raises:
            ValueError: If any input parameter is invalid
        """
        if not search_term or not search_term.strip():
            raise ValueError("Search term cannot be empty or whitespace")
        
        if max_articles <= 0 or max_articles > 50:
            raise ValueError("max_articles must be between 1 and 50")
        
        # Date validation is handled by the API client
        logger.debug("Input validation passed")
    
    def _fetch_articles(
        self, 
        search_term: str, 
        date_from: Optional[str], 
        max_articles: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch articles from Guardian API with error handling.
        
        Args:
            search_term (str): The search term to look for
            date_from (Optional[str]): Date filter for articles
            max_articles (int): Maximum number of articles to fetch
            
        Returns:
            List[Dict[str, Any]]: List of articles from the API
            
        Raises:
            GuardianAPIError: If API request fails
        """
        try:
            logger.debug(f"Fetching articles with term: '{search_term}', date_from: {date_from}")
            articles = self.api_client.search_content(
                search_term=search_term,
                date_from=date_from,
                page_size=max_articles
            )
            
            logger.info(f"Successfully fetched {len(articles)} articles from Guardian API")
            return articles
            
        except GuardianAPIError as e:
            logger.error(f"Failed to fetch articles from Guardian API: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching articles: {e}")
            raise
    
    def _publish_articles(self, articles: List[Dict[str, Any]]) -> int:
        """
        Publish articles to the message broker with error handling.
        
        This method attempts to publish all articles in a batch first,
        and falls back to individual publishing if batch fails.
        
        Args:
            articles (List[Dict[str, Any]]): Articles to publish
            
        Returns:
            int: Number of articles successfully published
            
        Raises:
            MessageBrokerError: If publishing fails completely
        """
        if not articles:
            return 0
        
        try:
            # Try batch publishing first for better performance
            logger.debug(f"Attempting batch publish of {len(articles)} articles")
            published_count = self.message_broker.publish_batch(articles)
            
            if published_count == len(articles):
                logger.info(f"Successfully published all {published_count} articles in batch")
                return published_count
            elif published_count > 0:
                logger.warning(f"Batch publish partially successful: {published_count}/{len(articles)}")
                return published_count
            else:
                # Batch failed completely, try individual publishing
                logger.warning("Batch publish failed, falling back to individual publishing")
                return self._publish_articles_individually(articles)
                
        except MessageBrokerError as e:
            logger.error(f"Batch publishing failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during batch publishing: {e}")
            raise MessageBrokerError(f"Unexpected error during publishing: {e}")
    
    def _publish_articles_individually(self, articles: List[Dict[str, Any]]) -> int:
        """
        Publish articles one by one as a fallback method.
        
        This method is used when batch publishing fails or partially succeeds.
        It provides more granular control and error handling.
        
        Args:
            articles (List[Dict[str, Any]]): Articles to publish
            
        Returns:
            int: Number of articles successfully published
        """
        published_count = 0
        
        for i, article in enumerate(articles, 1):
            try:
                success = self.message_broker.publish_message(article)
                if success:
                    published_count += 1
                    logger.debug(f"Published article {i}/{len(articles)}: {article.get('webTitle', 'Unknown')}")
                else:
                    logger.warning(f"Failed to publish article {i}/{len(articles)}: {article.get('webTitle', 'Unknown')}")
                    
            except MessageBrokerError as e:
                logger.error(f"Error publishing article {i}/{len(articles)}: {e}")
                # Continue with next article instead of failing completely
                continue
            except Exception as e:
                logger.error(f"Unexpected error publishing article {i}/{len(articles)}: {e}")
                continue
        
        logger.info(f"Individual publishing completed: {published_count}/{len(articles)} articles published")
        return published_count
    
    def close(self) -> None:
        """
        Clean up resources and close connections.
        
        This method should be called when the fetcher is no longer needed
        to ensure proper cleanup of underlying resources.
        """
        try:
            self.message_broker.close()
            logger.info("Guardian Content Fetcher closed successfully")
        except Exception as e:
            logger.error(f"Error closing Guardian Content Fetcher: {e}")
    
    def __enter__(self):
        """Support for context manager protocol."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support for context manager protocol with automatic cleanup."""
        self.close()


class GuardianContentFetcherFactory:
    """
    Factory class for creating GuardianContentFetcher instances with different configurations.
    
    This factory simplifies the creation of fetcher instances by providing
    convenient methods for common configurations like Kinesis publishing.
    """
    
    @staticmethod
    def create_with_kinesis(
        guardian_api_key: str,
        kinesis_stream_name: str,
        aws_region: str = 'eu-west-2',
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ) -> GuardianContentFetcher:
        """
        Create a GuardianContentFetcher configured for AWS Kinesis publishing.
        
        Args:
            guardian_api_key (str): Guardian API key for authentication
            kinesis_stream_name (str): Name of the Kinesis stream
            aws_region (str): AWS region for Kinesis (default: eu-west-2)
            aws_access_key_id (Optional[str]): AWS access key ID
            aws_secret_access_key (Optional[str]): AWS secret access key
            
        Returns:
            GuardianContentFetcher: Configured fetcher instance
            
        Raises:
            GuardianContentFetcherError: If configuration fails
        """
        try:
            from .api_client import GuardianAPIClient
            from .message_broker import KinesisPublisher
            
            # Create API client
            api_client = GuardianAPIClient(api_key=guardian_api_key)
            
            # Create Kinesis publisher
            kinesis_publisher = KinesisPublisher(
                stream_name=kinesis_stream_name,
                region_name=aws_region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
            
            # Create and return fetcher
            fetcher = GuardianContentFetcher(api_client, kinesis_publisher)
            logger.info(f"Created GuardianContentFetcher with Kinesis stream: {kinesis_stream_name}")
            return fetcher
            
        except Exception as e:
            raise GuardianContentFetcherError(f"Failed to create fetcher with Kinesis: {e}")
    
    @staticmethod
    def create_with_mock(guardian_api_key: str) -> GuardianContentFetcher:
        """
        Create a GuardianContentFetcher configured with mock message broker for testing.
        
        Args:
            guardian_api_key (str): Guardian API key for authentication
            
        Returns:
            GuardianContentFetcher: Configured fetcher instance with mock publisher
            
        Raises:
            GuardianContentFetcherError: If configuration fails
        """
        try:
            from .api_client import GuardianAPIClient
            from .message_broker import MockPublisher
            
            # Create API client
            api_client = GuardianAPIClient(api_key=guardian_api_key)
            
            # Create mock publisher
            mock_publisher = MockPublisher()
            
            # Create and return fetcher
            fetcher = GuardianContentFetcher(api_client, mock_publisher)
            logger.info("Created GuardianContentFetcher with mock publisher")
            return fetcher
            
        except Exception as e:
            raise GuardianContentFetcherError(f"Failed to create fetcher with mock: {e}")
