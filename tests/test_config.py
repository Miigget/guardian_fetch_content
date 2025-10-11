"""
Tests for Configuration module.

This module contains comprehensive tests for configuration loading,
validation, and environment variable handling.
"""

import pytest
import os
from unittest.mock import patch, Mock

from guardian_content_fetcher.config import (
    ConfigurationError,
    GuardianConfig,
    AWSConfig,
    KinesisConfig,
    AppConfig,
    load_config_from_env,
    create_config_dict,
    setup_logging,
    validate_aws_credentials,
    print_config_template,
)


class TestGuardianConfig:
    """Test cases for GuardianConfig dataclass."""

    def test_valid_config(self):
        """Test creating valid Guardian configuration."""
        config = GuardianConfig(api_key="test-key", rate_limit_delay=1.5)

        assert config.api_key == "test-key"
        assert config.rate_limit_delay == 1.5

    def test_default_rate_limit(self):
        """Test default rate limit delay."""
        config = GuardianConfig(api_key="test-key")

        assert config.rate_limit_delay == 2.0

    def test_empty_api_key(self):
        """Test that empty API key raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="Guardian API key is required"):
            GuardianConfig(api_key="")

        with pytest.raises(ConfigurationError, match="Guardian API key is required"):
            GuardianConfig(api_key=None)


class TestAWSConfig:
    """Test cases for AWSConfig dataclass."""

    def test_default_config(self):
        """Test AWS config with default values."""
        config = AWSConfig()

        assert config.region == "eu-west-2"
        assert config.access_key_id is None
        assert config.secret_access_key is None

    def test_custom_config(self):
        """Test AWS config with custom values."""
        config = AWSConfig(
            region="eu-west-1",
            access_key_id="test-key",
            secret_access_key="test-secret",
        )

        assert config.region == "eu-west-1"
        assert config.access_key_id == "test-key"
        assert config.secret_access_key == "test-secret"


class TestKinesisConfig:
    """Test cases for KinesisConfig dataclass."""

    def test_valid_config(self):
        """Test creating valid Kinesis configuration."""
        aws_config = AWSConfig()
        config = KinesisConfig(stream_name="test-stream", aws_config=aws_config)

        assert config.stream_name == "test-stream"
        assert config.aws_config == aws_config

    def test_empty_stream_name(self):
        """Test that empty stream name raises ConfigurationError."""
        aws_config = AWSConfig()

        with pytest.raises(ConfigurationError, match="Kinesis stream name is required"):
            KinesisConfig(stream_name="", aws_config=aws_config)

        with pytest.raises(ConfigurationError, match="Kinesis stream name is required"):
            KinesisConfig(stream_name=None, aws_config=aws_config)


class TestAppConfig:
    """Test cases for AppConfig dataclass."""

    def test_valid_config(self):
        """Test creating valid application configuration."""
        guardian_config = GuardianConfig(api_key="test-key")
        aws_config = AWSConfig()
        kinesis_config = KinesisConfig(stream_name="test-stream", aws_config=aws_config)

        config = AppConfig(
            guardian_config=guardian_config,
            kinesis_config=kinesis_config,
            log_level="DEBUG",
            use_mock_broker=True,
        )

        assert config.guardian_config == guardian_config
        assert config.kinesis_config == kinesis_config
        assert config.log_level == "DEBUG"
        assert config.use_mock_broker is True

    def test_default_values(self):
        """Test application config with default values."""
        guardian_config = GuardianConfig(api_key="test-key")
        config = AppConfig(guardian_config=guardian_config)

        assert config.kinesis_config is None
        assert config.log_level == "INFO"
        assert config.use_mock_broker is False


class TestLoadConfigFromEnv:
    """Test cases for load_config_from_env function."""

    def test_load_config_success(self, mock_environment_variables):
        """Test successful configuration loading from environment."""
        config = load_config_from_env()

        assert isinstance(config, AppConfig)
        assert config.guardian_config.api_key == "test-guardian-api-key"
        assert config.kinesis_config.stream_name == "test-stream"
        assert config.kinesis_config.aws_config.region == "eu-west-2"
        assert config.kinesis_config.aws_config.access_key_id == "test-aws-key"
        assert config.kinesis_config.aws_config.secret_access_key == "test-aws-secret"
        assert config.log_level == "INFO"
        assert config.use_mock_broker is False

    def test_load_config_missing_api_key(self):
        """Test configuration loading with missing Guardian API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ConfigurationError,
                match="GUARDIAN_API_KEY environment variable is required",
            ):
                load_config_from_env()

    def test_load_config_with_mock_broker(self):
        """Test configuration loading with mock broker enabled."""
        env_vars = {"GUARDIAN_API_KEY": "test-key", "USE_MOCK_BROKER": "true"}

        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config_from_env()

        assert config.use_mock_broker is True
        assert config.kinesis_config is None

    def test_load_config_custom_log_level(self):
        """Test configuration loading with custom log level."""
        env_vars = {
            "GUARDIAN_API_KEY": "test-key",
            "LOG_LEVEL": "DEBUG",
            "USE_MOCK_BROKER": "true",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config_from_env()

        assert config.log_level == "DEBUG"

    def test_load_config_invalid_log_level(self):
        """Test configuration loading with invalid log level."""
        env_vars = {
            "GUARDIAN_API_KEY": "test-key",
            "LOG_LEVEL": "INVALID",
            "USE_MOCK_BROKER": "true",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config_from_env()

        # Should default to INFO for invalid log level
        assert config.log_level == "INFO"

    def test_load_config_custom_rate_limit(self):
        """Test configuration loading with custom rate limit."""
        env_vars = {
            "GUARDIAN_API_KEY": "test-key",
            "GUARDIAN_RATE_LIMIT_DELAY": "3.0",
            "USE_MOCK_BROKER": "true",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config_from_env()

        assert config.guardian_config.rate_limit_delay == 3.0

    def test_load_config_default_stream_name(self):
        """Test configuration loading with default stream name."""
        env_vars = {
            "GUARDIAN_API_KEY": "test-key"
            # No KINESIS_STREAM_NAME set
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = load_config_from_env()

        assert config.kinesis_config.stream_name == "guardian-content"


class TestCreateConfigDict:
    """Test cases for create_config_dict function."""

    def test_create_config_success(self):
        """Test successful config dictionary creation."""
        config_dict = create_config_dict(
            guardian_api_key="test-key",
            kinesis_stream_name="test-stream",
            aws_region="us-west-2",
            aws_access_key_id="aws-key",
            aws_secret_access_key="aws-secret",
            use_mock_broker=False,
            log_level="DEBUG",
        )

        assert config_dict["guardian_api_key"] == "test-key"
        assert config_dict["kinesis_stream_name"] == "test-stream"
        assert config_dict["aws_region"] == "us-west-2"
        assert config_dict["aws_access_key_id"] == "aws-key"
        assert config_dict["aws_secret_access_key"] == "aws-secret"
        assert config_dict["use_mock_broker"] is False
        assert config_dict["log_level"] == "DEBUG"

    def test_create_config_with_defaults(self):
        """Test config dictionary creation with default values."""
        config_dict = create_config_dict(
            guardian_api_key="test-key", kinesis_stream_name="test-stream"
        )

        assert config_dict["aws_region"] == "eu-west-2"
        assert config_dict["aws_access_key_id"] is None
        assert config_dict["aws_secret_access_key"] is None
        assert config_dict["use_mock_broker"] is False
        assert config_dict["log_level"] == "INFO"

    def test_create_config_missing_api_key(self):
        """Test that missing API key raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="Guardian API key is required"):
            create_config_dict(guardian_api_key="")

    def test_create_config_missing_stream_name_without_mock(self):
        """Test that missing stream name raises error when not using mock."""
        with pytest.raises(ConfigurationError, match="Kinesis stream name is required"):
            create_config_dict(guardian_api_key="test-key", use_mock_broker=False)

    def test_create_config_with_mock_broker(self):
        """Test config creation with mock broker (no stream name required)."""
        config_dict = create_config_dict(
            guardian_api_key="test-key", use_mock_broker=True
        )

        assert config_dict["use_mock_broker"] is True
        assert config_dict["kinesis_stream_name"] is None


class TestSetupLogging:
    """Test cases for setup_logging function."""

    @patch("logging.basicConfig")
    def test_setup_logging_default(self, mock_basic_config):
        """Test logging setup with default level."""
        setup_logging()

        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args[1]
        assert call_args["level"] == 20  # logging.INFO

    @patch("logging.basicConfig")
    def test_setup_logging_debug(self, mock_basic_config):
        """Test logging setup with DEBUG level."""
        setup_logging("DEBUG")

        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args[1]
        assert call_args["level"] == 10  # logging.DEBUG

    @patch("logging.basicConfig")
    def test_setup_logging_error(self, mock_basic_config):
        """Test logging setup with ERROR level."""
        setup_logging("ERROR")

        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args[1]
        assert call_args["level"] == 40  # logging.ERROR

    @patch("logging.basicConfig")
    def test_setup_logging_invalid_level(self, mock_basic_config):
        """Test logging setup with invalid level defaults to INFO."""
        setup_logging("INVALID")

        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args[1]
        assert call_args["level"] == 20  # logging.INFO (default)


class TestValidateAWSCredentials:
    """Test cases for validate_aws_credentials function."""

    @patch("boto3.client")
    def test_validate_credentials_success(self, mock_boto_client):
        """Test successful credential validation."""
        mock_client = Mock()
        mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
        mock_boto_client.return_value = mock_client

        aws_config = AWSConfig(
            access_key_id="test-key", secret_access_key="test-secret"
        )

        result = validate_aws_credentials(aws_config)

        assert result is True
        mock_boto_client.assert_called_once_with(
            "sts",
            region_name="eu-west-2",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
        )
        mock_client.get_caller_identity.assert_called_once()

    @patch("boto3.client")
    def test_validate_credentials_default_chain(self, mock_boto_client):
        """Test credential validation with default credential chain."""
        mock_client = Mock()
        mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
        mock_boto_client.return_value = mock_client

        aws_config = AWSConfig()  # No explicit credentials

        result = validate_aws_credentials(aws_config)

        assert result is True
        mock_boto_client.assert_called_once_with("sts", region_name="eu-west-2")

    @patch("boto3.client")
    def test_validate_credentials_no_credentials_error(self, mock_boto_client):
        """Test credential validation with no credentials available."""
        from botocore.exceptions import NoCredentialsError

        mock_boto_client.side_effect = NoCredentialsError()

        aws_config = AWSConfig()
        result = validate_aws_credentials(aws_config)

        assert result is False

    @patch("boto3.client")
    def test_validate_credentials_client_error(self, mock_boto_client):
        """Test credential validation with client error."""
        from botocore.exceptions import ClientError

        mock_boto_client.side_effect = ClientError(
            {"Error": {"Code": "InvalidUserID.NotFound", "Message": "Invalid user"}},
            "GetCallerIdentity",
        )

        aws_config = AWSConfig()
        result = validate_aws_credentials(aws_config)

        assert result is False

    @patch("boto3.client")
    def test_validate_credentials_unexpected_error(self, mock_boto_client):
        """Test credential validation with unexpected error."""
        mock_boto_client.side_effect = Exception("Unexpected error")

        aws_config = AWSConfig()
        result = validate_aws_credentials(aws_config)

        assert result is False


class TestPrintConfigTemplate:
    """Test cases for print_config_template function."""

    @patch("builtins.print")
    def test_print_config_template(self, mock_print):
        """Test that config template is printed."""
        print_config_template()

        # Verify print was called (template content verification not critical)
        assert mock_print.called

        # Check that important environment variables are mentioned
        printed_content = "".join(
            [str(call.args[0]) for call in mock_print.call_args_list]
        )
        assert "GUARDIAN_API_KEY" in printed_content
        assert "AWS_ACCESS_KEY_ID" in printed_content
        assert "KINESIS_STREAM_NAME" in printed_content


class TestConfigurationIntegration:
    """Integration tests for configuration functionality."""

    def test_full_config_workflow(self):
        """Test complete configuration workflow."""
        # Create config from parameters
        config_dict = create_config_dict(
            guardian_api_key="test-key",
            kinesis_stream_name="test-stream",
            aws_region="us-west-2",
            log_level="DEBUG",
        )

        # Verify all expected keys are present
        expected_keys = [
            "guardian_api_key",
            "kinesis_stream_name",
            "aws_region",
            "aws_access_key_id",
            "aws_secret_access_key",
            "use_mock_broker",
            "log_level",
        ]

        for key in expected_keys:
            assert key in config_dict

        # Verify values
        assert config_dict["guardian_api_key"] == "test-key"
        assert config_dict["kinesis_stream_name"] == "test-stream"
        assert config_dict["aws_region"] == "us-west-2"
        assert config_dict["log_level"] == "DEBUG"
