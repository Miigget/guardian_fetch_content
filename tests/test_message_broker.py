"""
Tests for Message Broker module.

This module contains comprehensive tests for message broker publishers,
including KinesisPublisher, MockPublisher, and error handling scenarios.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from guardian_content_fetcher.message_broker import (
    MessageBrokerPublisher, KinesisPublisher, MockPublisher, MessageBrokerError
)


class TestMessageBrokerPublisher:
    """Test cases for abstract MessageBrokerPublisher class."""
    
    def test_abstract_class_cannot_be_instantiated(self):
        """Test that abstract class cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MessageBrokerPublisher()


class TestMockPublisher:
    """Test cases for MockPublisher class."""
    
    def test_initialization(self):
        """Test MockPublisher initialization."""
        publisher = MockPublisher()
        
        assert publisher.published_messages == []
    
    def test_publish_single_message(self, mock_publisher):
        """Test publishing a single message."""
        message = {
            "webTitle": "Test Article",
            "webUrl": "https://example.com/test",
            "webPublicationDate": "2023-01-01T10:00:00Z"
        }
        
        result = mock_publisher.publish_message(message)
        
        assert result is True
        published = mock_publisher.get_published_messages()
        assert len(published) == 1
        assert published[0] == message
    
    def test_publish_batch_messages(self, mock_publisher):
        """Test publishing a batch of messages."""
        messages = [
            {"webTitle": "Article 1", "webUrl": "https://example.com/1"},
            {"webTitle": "Article 2", "webUrl": "https://example.com/2"},
            {"webTitle": "Article 3", "webUrl": "https://example.com/3"}
        ]
        
        result = mock_publisher.publish_batch(messages)
        
        assert result == 3
        published = mock_publisher.get_published_messages()
        assert len(published) == 3
        assert published == messages
    
    def test_publish_empty_batch(self, mock_publisher):
        """Test publishing empty batch."""
        result = mock_publisher.publish_batch([])
        
        assert result == 0
        assert len(mock_publisher.get_published_messages()) == 0
    
    def test_clear_messages(self, mock_publisher):
        """Test clearing published messages."""
        mock_publisher.publish_message({"test": "message"})
        assert len(mock_publisher.get_published_messages()) == 1
        
        mock_publisher.clear_messages()
        assert len(mock_publisher.get_published_messages()) == 0
    
    def test_close(self, mock_publisher):
        """Test close method."""
        mock_publisher.close()  # Should not raise any exceptions
    
    def test_multiple_publishes_accumulate(self, mock_publisher):
        """Test that multiple publishes accumulate messages."""
        mock_publisher.publish_message({"message": "1"})
        mock_publisher.publish_message({"message": "2"})
        mock_publisher.publish_batch([{"message": "3"}, {"message": "4"}])
        
        published = mock_publisher.get_published_messages()
        assert len(published) == 4
        assert published[0]["message"] == "1"
        assert published[1]["message"] == "2"
        assert published[2]["message"] == "3"
        assert published[3]["message"] == "4"


class TestKinesisPublisher:
    """Test cases for KinesisPublisher class."""
    
    def test_initialization_success(self, mock_kinesis_client):
        """Test successful KinesisPublisher initialization."""
        publisher = KinesisPublisher(
            stream_name="test-stream",
            region_name="eu-west-2",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret"
        )
        
        assert publisher.stream_name == "test-stream"
        assert publisher.region_name == "eu-west-2"
        
        # Verify that describe_stream was called to verify stream existence
        mock_kinesis_client.describe_stream.assert_called_once_with(StreamName="test-stream")
    
    def test_initialization_empty_stream_name(self):
        """Test that empty stream name raises ValueError."""
        with pytest.raises(ValueError, match="Stream name cannot be empty"):
            KinesisPublisher("")
    
    @patch('boto3.client')
    def test_initialization_no_credentials_error(self, mock_boto_client):
        """Test handling of missing AWS credentials."""
        mock_boto_client.side_effect = NoCredentialsError()
        
        with pytest.raises(MessageBrokerError, match="AWS credentials not found"):
            KinesisPublisher("test-stream")
    
    @patch('boto3.client')
    def test_initialization_client_error(self, mock_boto_client):
        """Test handling of AWS client creation errors."""
        mock_boto_client.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "CreateClient"
        )
        
        with pytest.raises(MessageBrokerError, match="Failed to create Kinesis client"):
            KinesisPublisher("test-stream")
    
    def test_stream_verification_inactive_stream(self, mock_kinesis_client):
        """Test handling of inactive stream."""
        mock_kinesis_client.describe_stream.return_value = {
            'StreamDescription': {
                'StreamStatus': 'CREATING',
                'StreamName': 'test-stream'
            }
        }
        
        with pytest.raises(MessageBrokerError, match="is not active"):
            KinesisPublisher("test-stream")
    
    def test_stream_verification_nonexistent_stream(self, mock_kinesis_client):
        """Test handling of nonexistent stream."""
        mock_kinesis_client.describe_stream.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Stream not found"}},
            "DescribeStream"
        )
        
        with pytest.raises(MessageBrokerError, match="does not exist"):
            KinesisPublisher("test-stream")
    
    def test_publish_message_success(self, kinesis_publisher, mock_kinesis_client):
        """Test successful message publishing."""
        message = {
            "webTitle": "Test Article",
            "webUrl": "https://example.com/test",
            "webPublicationDate": "2023-01-01T10:00:00Z"
        }
        
        result = kinesis_publisher.publish_message(message)
        
        assert result is True
        
        # Verify put_record was called correctly
        mock_kinesis_client.put_record.assert_called_once()
        call_args = mock_kinesis_client.put_record.call_args
        
        assert call_args[1]['StreamName'] == "test-stream"
        assert call_args[1]['PartitionKey'] == "Test Article"
        
        # Verify message data is JSON
        data = call_args[1]['Data']
        parsed_message = json.loads(data.decode('utf-8'))
        assert parsed_message == message
    
    def test_publish_message_long_title_partition_key(self, kinesis_publisher, mock_kinesis_client):
        """Test partition key truncation for long titles."""
        long_title = "Very long article title " * 20  # Over 256 characters
        message = {
            "webTitle": long_title,
            "webUrl": "https://example.com/test"
        }
        
        kinesis_publisher.publish_message(message)
        
        call_args = mock_kinesis_client.put_record.call_args
        partition_key = call_args[1]['PartitionKey']
        assert len(partition_key) <= 256
        assert partition_key == long_title[:256]
    
    def test_publish_message_no_title_default_partition_key(self, kinesis_publisher, mock_kinesis_client):
        """Test default partition key when no title is provided."""
        message = {
            "webUrl": "https://example.com/test",
            "webPublicationDate": "2023-01-01T10:00:00Z"
        }
        
        kinesis_publisher.publish_message(message)
        
        call_args = mock_kinesis_client.put_record.call_args
        assert call_args[1]['PartitionKey'] == "default"
    
    def test_publish_message_kinesis_error(self, kinesis_publisher, mock_kinesis_client):
        """Test handling of Kinesis put_record errors."""
        mock_kinesis_client.put_record.side_effect = ClientError(
            {"Error": {"Code": "InternalFailure", "Message": "Internal error"}},
            "PutRecord"
        )
        
        message = {"webTitle": "Test"}
        
        with pytest.raises(MessageBrokerError, match="Failed to publish message"):
            kinesis_publisher.publish_message(message)
    
    def test_publish_batch_success(self, kinesis_publisher, mock_kinesis_client):
        """Test successful batch publishing."""
        messages = [
            {"webTitle": "Article 1", "webUrl": "https://example.com/1"},
            {"webTitle": "Article 2", "webUrl": "https://example.com/2"},
            {"webTitle": "Article 3", "webUrl": "https://example.com/3"}
        ]
        
        result = kinesis_publisher.publish_batch(messages)
        
        assert result == 3
        
        # Verify put_records was called
        mock_kinesis_client.put_records.assert_called_once()
        call_args = mock_kinesis_client.put_records.call_args
        
        assert call_args[1]['StreamName'] == "test-stream"
        records = call_args[1]['Records']
        assert len(records) == 3
        
        # Verify each record
        for i, record in enumerate(records):
            assert record['PartitionKey'] == f"Article {i+1}"
            parsed_data = json.loads(record['Data'].decode('utf-8'))
            assert parsed_data == messages[i]
    
    def test_publish_batch_empty(self, kinesis_publisher):
        """Test publishing empty batch."""
        result = kinesis_publisher.publish_batch([])
        assert result == 0
    
    def test_publish_batch_partial_failure(self, kinesis_publisher, mock_kinesis_client):
        """Test handling of partial batch failures."""
        messages = [
            {"webTitle": "Article 1"},
            {"webTitle": "Article 2"},
            {"webTitle": "Article 3"}
        ]
        
        # Mock partial failure response
        mock_kinesis_client.put_records.return_value = {
            'FailedRecordCount': 1,
            'Records': [
                {'SequenceNumber': '123', 'ShardId': 'shard-1'},
                {'ErrorCode': 'InternalFailure', 'ErrorMessage': 'Error'},
                {'SequenceNumber': '456', 'ShardId': 'shard-1'}
            ]
        }
        
        result = kinesis_publisher.publish_batch(messages)
        
        assert result == 2  # 3 messages - 1 failed = 2 successful
    
    def test_publish_batch_large_batch(self, kinesis_publisher, mock_kinesis_client):
        """Test publishing large batch that requires splitting."""
        # Create 1000 messages (more than 500 batch limit)
        messages = [{"webTitle": f"Article {i}"} for i in range(1000)]
        
        kinesis_publisher.publish_batch(messages)
        
        # Should be called twice (500 + 500)
        assert mock_kinesis_client.put_records.call_count == 2
        
        # Verify first batch has 500 records
        first_call_args = mock_kinesis_client.put_records.call_args_list[0]
        assert len(first_call_args[1]['Records']) == 500
        
        # Verify second batch has 500 records
        second_call_args = mock_kinesis_client.put_records.call_args_list[1]
        assert len(second_call_args[1]['Records']) == 500
    
    def test_publish_batch_kinesis_error(self, kinesis_publisher, mock_kinesis_client):
        """Test handling of Kinesis put_records errors."""
        mock_kinesis_client.put_records.side_effect = ClientError(
            {"Error": {"Code": "InternalFailure", "Message": "Internal error"}},
            "PutRecords"
        )
        
        messages = [{"webTitle": "Test"}]
        
        with pytest.raises(MessageBrokerError, match="Failed to publish batch"):
            kinesis_publisher.publish_batch(messages)
    
    def test_close(self, kinesis_publisher):
        """Test close method."""
        kinesis_publisher.close()
        
        # After close, client should be None
        assert kinesis_publisher.client is None
    
    def test_publish_message_unicode_content(self, kinesis_publisher, mock_kinesis_client):
        """Test publishing message with unicode content."""
        message = {
            "webTitle": "Article with émojis 🚀 and ünïcødé",
            "webUrl": "https://example.com/unicode"
        }
        
        result = kinesis_publisher.publish_message(message)
        
        assert result is True
        
        call_args = mock_kinesis_client.put_record.call_args
        data = call_args[1]['Data']
        
        # Verify data can be decoded back to original message
        parsed_message = json.loads(data.decode('utf-8'))
        assert parsed_message == message
    
    def test_initialization_with_default_credentials(self, mock_kinesis_client):
        """Test initialization without explicit AWS credentials."""
        publisher = KinesisPublisher("test-stream")
        
        assert publisher.stream_name == "test-stream"
        assert publisher.region_name == "eu-west-2"  # Default region
    
    def test_initialization_custom_region(self, mock_kinesis_client):
        """Test initialization with custom AWS region."""
        publisher = KinesisPublisher("test-stream", region_name="eu-west-1")
        
        assert publisher.region_name == "eu-west-1"
