"""
Message Broker Module.

This module provides abstract and concrete implementations for publishing
messages to various message brokers. It supports AWS Kinesis and can be
extended to support other brokers like Kafka or RabbitMQ.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Set up logging for better debugging and monitoring
logger = logging.getLogger(__name__)


class MessageBrokerError(Exception):
    """Custom exception for message broker related errors."""

    pass


class MessageBrokerPublisher(ABC):
    """
    Abstract base class for message broker publishers.

    This class defines the interface that all message broker implementations
    must follow. It provides a consistent API for publishing messages
    regardless of the underlying broker technology.
    """

    @abstractmethod
    def publish_message(self, message: Dict[str, Any]) -> bool:
        """
        Publish a single message to the broker.

        Args:
            message (Dict[str, Any]): The message data to publish

        Returns:
            bool: True if message was published successfully, False otherwise

        Raises:
            MessageBrokerError: If publishing fails
        """
        pass

    @abstractmethod
    def publish_batch(self, messages: List[Dict[str, Any]]) -> int:
        """
        Publish multiple messages to the broker in a batch.

        Args:
            messages (List[Dict[str, Any]]): List of message data to publish

        Returns:
            int: Number of messages successfully published

        Raises:
            MessageBrokerError: If batch publishing fails
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Clean up resources and close connections to the broker.

        This method should be called when the publisher is no longer needed
        to ensure proper cleanup of resources.
        """
        pass


class KinesisPublisher(MessageBrokerPublisher):
    """
    AWS Kinesis implementation of MessageBrokerPublisher.

    This class provides functionality to publish messages to AWS Kinesis
    Data Streams. It handles authentication, error handling, and batch
    operations for efficient message publishing.

    Attributes:
        stream_name (str): Name of the Kinesis stream
        region_name (str): AWS region where the stream is located
        client: Boto3 Kinesis client for API operations
    """

    def __init__(
        self,
        stream_name: str,
        region_name: str = "eu-west-2",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        """
        Initialize the Kinesis publisher.

        Args:
            stream_name (str): Name of the Kinesis stream to publish to
            region_name (str): AWS region name (default: eu-west-2)
            aws_access_key_id (Optional[str]): AWS access key ID
                (if not using IAM roles)
            aws_secret_access_key (Optional[str]): AWS secret key
                (if not using IAM roles)

        Raises:
            ValueError: If stream_name is empty
            MessageBrokerError: If AWS credentials are invalid or client creation fails
        """
        if not stream_name:
            raise ValueError("Stream name cannot be empty")

        self.stream_name = stream_name
        self.region_name = region_name

        try:
            # Create Kinesis client with optional credentials
            if aws_access_key_id and aws_secret_access_key:
                self.client = boto3.client(
                    "kinesis",
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                )
                logger.info("Kinesis client created with provided credentials")
            else:
                # Use default credential chain (IAM roles, environment variables, etc.)
                self.client = boto3.client("kinesis", region_name=region_name)
                logger.info("Kinesis client created with default credential chain")

            # Verify stream exists and is accessible
            self._verify_stream_exists()

        except NoCredentialsError:
            raise MessageBrokerError(
                "AWS credentials not found. Please configure credentials "
                "or provide them explicitly."
            )
        except ClientError as e:
            raise MessageBrokerError(f"Failed to create Kinesis client: {e}")
        except Exception as e:
            raise MessageBrokerError(f"Unexpected error creating Kinesis client: {e}")

    def _verify_stream_exists(self) -> None:
        """
        Verify that the specified Kinesis stream exists and is accessible.

        Raises:
            MessageBrokerError: If stream doesn't exist or is not accessible
        """
        try:
            response = self.client.describe_stream(StreamName=self.stream_name)
            stream_status = response["StreamDescription"]["StreamStatus"]

            if stream_status not in ["ACTIVE", "UPDATING"]:
                raise MessageBrokerError(
                    f"Kinesis stream '{self.stream_name}' is not active. "
                    f"Status: {stream_status}"
                )

            logger.info(
                f"Successfully verified Kinesis stream "
                f"'{self.stream_name}' is accessible"
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "ResourceNotFoundException":
                raise MessageBrokerError(
                    f"Kinesis stream '{self.stream_name}' does not exist"
                )
            else:
                raise MessageBrokerError(f"Failed to verify stream existence: {e}")

    def publish_message(self, message: Dict[str, Any]) -> bool:
        """
        Publish a single message to the Kinesis stream.

        Args:
            message (Dict[str, Any]): The message data to publish

        Returns:
            bool: True if message was published successfully

        Raises:
            MessageBrokerError: If publishing fails
        """
        try:
            # Convert message to JSON string
            message_data = json.dumps(message, ensure_ascii=False)

            # Use web title as partition key for better distribution
            partition_key = message.get("webTitle", "default")[:256]  # Kinesis limit

            response = self.client.put_record(
                StreamName=self.stream_name,
                Data=message_data.encode("utf-8"),
                PartitionKey=partition_key,
            )

            sequence_number = response["SequenceNumber"]
            logger.debug(
                f"Message published successfully. "
                f"Sequence number: {sequence_number}"
            )
            return True

        except ClientError as e:
            logger.error(f"Failed to publish message to Kinesis: {e}")
            raise MessageBrokerError(f"Failed to publish message: {e}")
        except Exception as e:
            logger.error(f"Unexpected error publishing message: {e}")
            raise MessageBrokerError(f"Unexpected error: {e}")

    def publish_batch(self, messages: List[Dict[str, Any]]) -> int:
        """
        Publish multiple messages to Kinesis in a batch for better efficiency.

        Kinesis supports up to 500 records per batch operation.
        If more messages are provided, they will be split into multiple batches.

        Args:
            messages (List[Dict[str, Any]]): List of message data to publish

        Returns:
            int: Number of messages successfully published

        Raises:
            MessageBrokerError: If batch publishing fails
        """
        if not messages:
            return 0

        successful_count = 0
        batch_size = 500  # Kinesis batch limit

        try:
            # Process messages in batches of 500
            for i in range(0, len(messages), batch_size):
                batch = messages[i : i + batch_size]

                # Prepare records for Kinesis batch operation
                records = []
                for message in batch:
                    message_data = json.dumps(message, ensure_ascii=False)
                    partition_key = message.get("webTitle", "default")[:256]

                    records.append(
                        {
                            "Data": message_data.encode("utf-8"),
                            "PartitionKey": partition_key,
                        }
                    )

                # Send batch to Kinesis
                response = self.client.put_records(
                    StreamName=self.stream_name, Records=records
                )

                # Count successful records
                failed_count = response.get("FailedRecordCount", 0)
                batch_successful = len(records) - failed_count
                successful_count += batch_successful

                if failed_count > 0:
                    logger.warning(
                        f"Batch had {failed_count} failed records "
                        f"out of {len(records)}"
                    )
                else:
                    logger.debug(
                        f"Batch of {len(records)} records published successfully"
                    )

            logger.info(
                f"Published {successful_count} out of {len(messages)} "
                "messages successfully"
            )
            return successful_count

        except ClientError as e:
            logger.error(f"Failed to publish batch to Kinesis: {e}")
            raise MessageBrokerError(f"Failed to publish batch: {e}")
        except Exception as e:
            logger.error(f"Unexpected error publishing batch: {e}")
            raise MessageBrokerError(f"Unexpected error: {e}")

    def close(self) -> None:
        """
        Clean up Kinesis client resources.

        For boto3 clients, this typically involves closing any underlying
        connections, though the client handles most cleanup automatically.
        """
        if hasattr(self, "client"):
            # boto3 clients don't have an explicit close method
            # but we can clear the reference to help with garbage collection
            self.client = None
            logger.info("Kinesis client resources cleaned up")


class MockPublisher(MessageBrokerPublisher):
    """
    Mock implementation of MessageBrokerPublisher for testing purposes.

    This class simulates message publishing without actually sending
    messages to any broker. Useful for unit tests and development.
    """

    def __init__(self):
        """Initialize the mock publisher."""
        self.published_messages = []
        logger.info("Mock publisher initialized")

    def publish_message(self, message: Dict[str, Any]) -> bool:
        """
        Mock publish a single message.

        Args:
            message (Dict[str, Any]): The message data to publish

        Returns:
            bool: Always returns True
        """
        self.published_messages.append(message)
        logger.debug(
            f"Mock published message: {message.get('webTitle', 'Unknown title')}"
        )
        return True

    def publish_batch(self, messages: List[Dict[str, Any]]) -> int:
        """
        Mock publish multiple messages.

        Args:
            messages (List[Dict[str, Any]]): List of message data to publish

        Returns:
            int: Number of messages (always all of them)
        """
        self.published_messages.extend(messages)
        logger.debug(f"Mock published batch of {len(messages)} messages")
        for message in messages:
            logger.debug(f"Mock published message: {message}")
        return len(messages)

    def close(self) -> None:
        """Clean up mock publisher."""
        logger.info("Mock publisher closed")

    def get_published_messages(self) -> List[Dict[str, Any]]:
        """
        Get all published messages for testing verification.

        Returns:
            List[Dict[str, Any]]: All messages that were published
        """
        return self.published_messages.copy()

    def clear_messages(self) -> None:
        """Clear all published messages."""
        self.published_messages.clear()
        logger.debug("Mock publisher messages cleared")
