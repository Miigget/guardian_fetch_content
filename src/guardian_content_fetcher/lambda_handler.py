"""
Lambda Handler Module for Guardian Content Fetcher.

This module provides the entry point for running the Guardian Content Fetcher
as an AWS Lambda function. It handles parsing the Lambda event, setting up
configuration from environment variables, and invoking the core fetching logic.
"""

import json
import logging
import os
from typing import Dict, Any

from .content_fetcher import GuardianContentFetcherFactory, GuardianContentFetcherError

# Configure logging for Lambda's CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: object) -> Dict[str, Any]:
    """
    AWS Lambda handler function.

    This function is triggered by an event (e.g., from EventBridge, API
    Gateway, or manual invocation). It fetches articles from the Guardian API
    based on parameters in the event and publishes them to a Kinesis stream.

    Args:
        event (Dict[str, Any]): The event data passed to the Lambda function.
                               Expected keys:
                               - 'search_term' (str): The term to search for.
                               - 'date_from' (str, optional): Start date
                                 (YYYY-MM-DD).
                               - 'max_articles' (int, optional): Number of
                                 articles (1-50).
        context (object): The Lambda runtime information. Not used in this function.

    Returns:
        Dict[str, Any]: A dictionary with a status code and a JSON body containing
                        the result of the operation.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # --- 1. Get Parameters from Event ---
        search_term = event.get("search_term")
        if not search_term:
            raise ValueError("'search_term' is a required parameter in the event.")

        date_from = event.get("date_from")
        max_articles = int(event.get("max_articles", 10))

        # --- 2. Load Configuration from Environment Variables ---
        guardian_api_key = os.environ.get("GUARDIAN_API_KEY")
        kinesis_stream_name = os.environ.get("KINESIS_STREAM_NAME")
        aws_region = os.environ.get("AWS_DEFAULT_REGION", "eu-west-2")

        if not guardian_api_key or not kinesis_stream_name:
            raise EnvironmentError(
                "Missing required environment variables: GUARDIAN_API_KEY "
                "and KINESIS_STREAM_NAME must be set."
            )

        # --- 3. Execute the Fetch and Publish Logic ---
        logger.info(
            f"Initializing fetcher for Kinesis stream "
            f"'{kinesis_stream_name}' in region '{aws_region}'"
        )

        fetcher = GuardianContentFetcherFactory.create_with_kinesis(
            guardian_api_key=guardian_api_key,
            kinesis_stream_name=kinesis_stream_name,
            aws_region=aws_region,
        )

        with fetcher:
            result = fetcher.fetch_and_publish(
                search_term=search_term, date_from=date_from, max_articles=max_articles
            )

        logger.info(f"Operation completed. Result: {json.dumps(result)}")

        # --- 4. Return a Success Response ---
        return {"statusCode": 200, "body": json.dumps(result)}

    except (ValueError, EnvironmentError) as e:
        logger.error(f"Configuration or parameter error: {e}")
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}
    except GuardianContentFetcherError as e:
        logger.error(f"Application error during fetch and publish: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"An application error occurred: {e}"}),
        }
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"An unexpected error occurred: {e}"}),
        }
