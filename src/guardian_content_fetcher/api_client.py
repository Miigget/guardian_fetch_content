"""
Guardian API Client Module.

This module provides functionality to interact with the Guardian Open Platform API
to search and retrieve articles based on search terms and date filters.
"""

import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Set up logging for better debugging and monitoring
logger = logging.getLogger(__name__)


class GuardianAPIError(Exception):
    """Custom exception for Guardian API related errors."""

    pass


class GuardianAPIClient:
    """
    Client for interacting with the Guardian Open Platform API.

    This class handles authentication, rate limiting, and article retrieval
    from the Guardian API. It provides methods to search for articles
    based on search terms and optional date filters.

    Attributes:
        api_key (str): Guardian API key for authentication
        base_url (str): Base URL for Guardian API endpoints
        rate_limit_delay (float): Delay between API calls to respect rate limits
    """

    # Guardian Open Platform API base URL
    BASE_URL = "https://content.guardianapis.com"

    # Default rate limit delay (2 seconds to stay within free tier limits)
    DEFAULT_RATE_LIMIT_DELAY = 2.0

    def __init__(
        self, api_key: str, rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY
    ):
        """
        Initialize the Guardian API client.

        Args:
            api_key (str): Guardian API key for authentication
            rate_limit_delay (float): Delay between API calls in seconds

        Raises:
            ValueError: If api_key is empty or None
        """
        if not api_key:
            raise ValueError("API key cannot be empty or None")

        self.api_key = api_key
        self.base_url = self.BASE_URL
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0

        logger.info("Guardian API client initialized successfully")

    def _wait_for_rate_limit(self) -> None:
        """
        Implement rate limiting by ensuring minimum delay between requests.

        This method calculates the time elapsed since the last request
        and waits if necessary to respect the rate limit.
        """
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)

        self._last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Guardian API with proper error handling.

        Args:
            endpoint (str): API endpoint to call
            params (Dict[str, Any]): Query parameters for the request

        Returns:
            Dict[str, Any]: JSON response from the API

        Raises:
            GuardianAPIError: If the API request fails or returns an error
        """
        # Apply rate limiting
        self._wait_for_rate_limit()

        # Add API key to parameters
        params["api-key"] = self.api_key

        url = f"{self.base_url}/{endpoint}"

        try:
            logger.debug(f"Making request to {url} with params: {params}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Check if Guardian API returned an error in the response
            if data.get("response", {}).get("status") != "ok":
                error_message = data.get("response", {}).get(
                    "message", "Unknown API error"
                )
                raise GuardianAPIError(f"Guardian API error: {error_message}")

            results_count = len(data.get("response", {}).get("results", []))
            logger.debug(f"API request successful, received {results_count} results")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed: {e}")
            raise GuardianAPIError(f"Failed to make request to Guardian API: {e}")
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise GuardianAPIError(f"Invalid JSON response from Guardian API: {e}")

    def search_content(
        self, search_term: str, date_from: Optional[str] = None, page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for articles using the Guardian API.

        This method searches for articles based on the provided search term
        and optional date filter. It returns up to the specified number
        of most recent articles.

        Args:
            search_term (str): The search term to look for in articles
            date_from (Optional[str]): Filter articles from this date
                (YYYY-MM-DD format)
            page_size (int): Maximum number of articles to return
                (default: 10)

        Returns:
            List[Dict[str, Any]]: List of article dictionaries containing
                                 webPublicationDate, webTitle, webUrl and other fields

        Raises:
            ValueError: If search_term is empty or page_size is invalid
            GuardianAPIError: If the API request fails

        Example:
            >>> client = GuardianAPIClient("your-api-key")
            >>> articles = client.search_content("machine learning", "2023-01-01")
            >>> print(f"Found {len(articles)} articles")
        """
        if not search_term or not search_term.strip():
            raise ValueError("Search term cannot be empty")

        if page_size <= 0 or page_size > 50:
            raise ValueError("Page size must be between 1 and 50")

        # Prepare API parameters
        params = {
            "q": search_term.strip(),
            "page-size": page_size,
            "order-by": "newest",  # Get most recent articles first
            # Include content preview
            "show-fields": "webPublicationDate,webTitle,webUrl,bodyText",
        }

        # Add date filter if provided
        if date_from:
            try:
                # Validate date format
                datetime.strptime(date_from, "%Y-%m-%d")
                params["from-date"] = date_from
                logger.info(f"Filtering articles from date: {date_from}")
            except ValueError:
                raise ValueError("date_from must be in YYYY-MM-DD format")

        logger.info(f"Searching for articles with term: '{search_term}'")

        # Make the API request
        response_data = self._make_request("search", params)

        # Extract articles from response
        articles = response_data.get("response", {}).get("results", [])

        # Transform articles to required format with content preview
        formatted_articles = []
        for article in articles:
            formatted_article = {
                "webPublicationDate": article.get("webPublicationDate", ""),
                "webTitle": article.get("webTitle", ""),
                "webUrl": article.get("webUrl", ""),
            }

            # Add content preview if available (first 1000 characters)
            body_text = article.get("fields", {}).get("bodyText", "")
            if body_text:
                formatted_article["content_preview"] = body_text[:1000]
                if len(body_text) > 1000:
                    formatted_article["content_preview"] += "..."

            formatted_articles.append(formatted_article)

        logger.info(f"Successfully retrieved {len(formatted_articles)} articles")
        return formatted_articles
