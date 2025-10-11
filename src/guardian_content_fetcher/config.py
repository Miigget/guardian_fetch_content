"""
Configuration Module.

This module provides configuration management for the Guardian Content Fetcher.
It handles loading settings from environment variables, validation, and
provides default values for optional settings.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Custom exception for configuration related errors."""
    pass


@dataclass
class GuardianConfig:
    """
    Configuration class for Guardian API settings.
    
    Attributes:
        api_key (str): Guardian API key for authentication
        rate_limit_delay (float): Delay between API calls in seconds
    """
    api_key: str
    rate_limit_delay: float = 2.0
    
    def __post_init__(self):
        """Validate Guardian configuration after initialization."""
        if not self.api_key:
            raise ConfigurationError("Guardian API key is required")


@dataclass 
class AWSConfig:
    """
    Configuration class for AWS settings.
    
    Attributes:
        region (str): AWS region name
        access_key_id (Optional[str]): AWS access key ID
        secret_access_key (Optional[str]): AWS secret access key
    """
    region: str = 'eu-west-2'
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None


@dataclass
class KinesisConfig:
    """
    Configuration class for Kinesis settings.
    
    Attributes:
        stream_name (str): Name of the Kinesis stream
        aws_config (AWSConfig): AWS configuration for Kinesis
    """
    stream_name: str
    aws_config: AWSConfig
    
    def __post_init__(self):
        """Validate Kinesis configuration after initialization."""
        if not self.stream_name:
            raise ConfigurationError("Kinesis stream name is required")


@dataclass
class AppConfig:
    """
    Main application configuration.
    
    Attributes:
        guardian_config (GuardianConfig): Guardian API configuration
        kinesis_config (Optional[KinesisConfig]): Kinesis configuration
        log_level (str): Logging level
        use_mock_broker (bool): Whether to use mock message broker
    """
    guardian_config: GuardianConfig
    kinesis_config: Optional[KinesisConfig] = None
    log_level: str = 'INFO'
    use_mock_broker: bool = False


def load_config_from_env() -> AppConfig:
    """
    Load application configuration from environment variables.
    
    This function reads configuration values from environment variables
    and creates a complete configuration object with validation.
    
    Returns:
        AppConfig: Loaded and validated application configuration
        
    Raises:
        ConfigurationError: If required configuration is missing or invalid
        
    Environment Variables:
        GUARDIAN_API_KEY: Guardian API key (required)
        AWS_ACCESS_KEY_ID: AWS access key ID (optional)
        AWS_SECRET_ACCESS_KEY: AWS secret access key (optional)
        AWS_DEFAULT_REGION: AWS region (default: eu-west-2)
        KINESIS_STREAM_NAME: Kinesis stream name (default: guardian-content)
        LOG_LEVEL: Logging level (default: INFO)
        USE_MOCK_BROKER: Use mock broker instead of Kinesis (default: false)
    """
    try:
        # Load Guardian API configuration
        guardian_api_key = os.getenv('GUARDIAN_API_KEY')
        if not guardian_api_key:
            raise ConfigurationError(
                "GUARDIAN_API_KEY environment variable is required. "
                "Get your free API key from: https://open-platform.theguardian.com/access/"
            )
        
        guardian_config = GuardianConfig(
            api_key=guardian_api_key,
            rate_limit_delay=float(os.getenv('GUARDIAN_RATE_LIMIT_DELAY', '2.0'))
        )
        
        # Load AWS configuration
        aws_config = AWSConfig(
            region=os.getenv('AWS_DEFAULT_REGION', 'eu-west-2'),
            access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Load Kinesis configuration (optional if using mock)
        use_mock_broker = os.getenv('USE_MOCK_BROKER', 'false').lower() == 'true'
        kinesis_config = None
        
        if not use_mock_broker:
            kinesis_stream_name = os.getenv('KINESIS_STREAM_NAME', 'guardian-content')
            kinesis_config = KinesisConfig(
                stream_name=kinesis_stream_name,
                aws_config=aws_config
            )
        
        # Load application settings
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            logger.warning(f"Invalid log level '{log_level}', using INFO")
            log_level = 'INFO'
        
        config = AppConfig(
            guardian_config=guardian_config,
            kinesis_config=kinesis_config,
            log_level=log_level,
            use_mock_broker=use_mock_broker
        )
        
        logger.info("Configuration loaded successfully from environment variables")
        return config
        
    except ConfigurationError:
        raise
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration from environment: {e}")


def create_config_dict(
    guardian_api_key: str,
    kinesis_stream_name: Optional[str] = None,
    aws_region: str = 'eu-west-2',
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    use_mock_broker: bool = False,
    log_level: str = 'INFO'
) -> Dict[str, Any]:
    """
    Create a configuration dictionary from provided parameters.
    
    This function is useful for programmatic configuration creation
    when environment variables are not available or when overriding
    specific settings.
    
    Args:
        guardian_api_key (str): Guardian API key
        kinesis_stream_name (Optional[str]): Kinesis stream name
        aws_region (str): AWS region (default: eu-west-2)
        aws_access_key_id (Optional[str]): AWS access key ID
        aws_secret_access_key (Optional[str]): AWS secret access key
        use_mock_broker (bool): Use mock broker (default: False)
        log_level (str): Logging level (default: INFO)
        
    Returns:
        Dict[str, Any]: Configuration dictionary
        
    Raises:
        ConfigurationError: If required parameters are missing
    """
    if not guardian_api_key:
        raise ConfigurationError("Guardian API key is required")
    
    if not use_mock_broker and not kinesis_stream_name:
        raise ConfigurationError("Kinesis stream name is required when not using mock broker")
    
    return {
        'guardian_api_key': guardian_api_key,
        'kinesis_stream_name': kinesis_stream_name,
        'aws_region': aws_region,
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key,
        'use_mock_broker': use_mock_broker,
        'log_level': log_level
    }


def setup_logging(log_level: str = 'INFO') -> None:
    """
    Configure application logging.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    import sys
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers to appropriate levels
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger.info(f"Logging configured at {log_level} level")


def validate_aws_credentials(aws_config: AWSConfig) -> bool:
    """
    Validate AWS credentials by attempting to create a client.
    
    Args:
        aws_config (AWSConfig): AWS configuration to validate
        
    Returns:
        bool: True if credentials are valid, False otherwise
    """
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
        
        # Try to create a client with the provided credentials
        if aws_config.access_key_id and aws_config.secret_access_key:
            client = boto3.client(
                'sts',  # Use STS service for credential validation
                region_name=aws_config.region,
                aws_access_key_id=aws_config.access_key_id,
                aws_secret_access_key=aws_config.secret_access_key
            )
        else:
            # Use default credential chain
            client = boto3.client('sts', region_name=aws_config.region)
        
        # Test credentials by calling get_caller_identity
        response = client.get_caller_identity()
        logger.info(f"AWS credentials validated for account: {response.get('Account', 'Unknown')}")
        return True
        
    except NoCredentialsError:
        logger.error("No AWS credentials found")
        return False
    except ClientError as e:
        logger.error(f"AWS credential validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating AWS credentials: {e}")
        return False


def print_config_template():
    """
    Print a template for environment variable configuration.
    
    This function outputs a template that users can copy to create
    their .env file with all available configuration options.
    """
    template = """
# Guardian Content Fetcher Environment Configuration
# Copy this content to a .env file and fill in your actual values

# Guardian API Configuration (Required)
# Get your free API key from: https://open-platform.theguardian.com/access/
GUARDIAN_API_KEY=your-guardian-api-key-here

# AWS Configuration (Optional - will use IAM roles if not provided)
# If running on EC2 or Lambda, these can be omitted to use IAM roles
# AWS_ACCESS_KEY_ID=your-aws-access-key-id
# AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key

# AWS Region (Optional - defaults to eu-west-2)
AWS_DEFAULT_REGION=eu-west-2

# Kinesis Stream Configuration (Required unless using mock)
# Name of the Kinesis stream to publish articles to
KINESIS_STREAM_NAME=guardian-content

# Application Configuration (Optional)
# Use mock broker instead of Kinesis (useful for testing)
# USE_MOCK_BROKER=false

# Logging Configuration (Optional)
# LOG_LEVEL=INFO

# Guardian API Rate Limiting (Optional)
# GUARDIAN_RATE_LIMIT_DELAY=2.0
    """
    print(template.strip())


if __name__ == '__main__':
    """
    When run as a script, print the configuration template.
    """
    print("Guardian Content Fetcher Configuration Template")
    print("=" * 50)
    print_config_template()
