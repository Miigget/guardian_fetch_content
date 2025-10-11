"""
Command Line Interface Module.

This module provides a command-line interface for the Guardian Content Fetcher.
It handles argument parsing, configuration loading, and execution of the
main fetching and publishing workflow.
"""

import argparse
import json
import logging
import os
import sys
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from .content_fetcher import GuardianContentFetcherFactory, GuardianContentFetcherError
from .api_client import GuardianAPIError
from .message_broker import MessageBrokerError

# Load environment variables from .env file if it exists
load_dotenv()

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class CLIError(Exception):
    """Custom exception for CLI related errors."""
    pass


def setup_argument_parser() -> argparse.ArgumentParser:
    """
    Set up and configure the command line argument parser.
    
    This function defines all available command line arguments
    and their validation rules.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Guardian Content Fetcher - Fetch articles from Guardian API and publish to message brokers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with environment variables
  guardian-fetch "machine learning"
  
  # With date filter
  guardian-fetch "artificial intelligence" --date-from 2023-01-01
  
  # With custom stream name
  guardian-fetch "data science" --stream-name my-stream --max-articles 5
  
  # Using mock publisher for testing
  guardian-fetch "python" --use-mock --verbose
  
Environment Variables:
  GUARDIAN_API_KEY       Guardian API key (required)
  AWS_ACCESS_KEY_ID      AWS access key (optional, uses IAM roles if not set)
  AWS_SECRET_ACCESS_KEY  AWS secret key (optional, uses IAM roles if not set)
  AWS_DEFAULT_REGION     AWS region (default: us-east-1)
  KINESIS_STREAM_NAME    Default Kinesis stream name (default: guardian-content)
        """
    )
    
    # Required arguments
    parser.add_argument(
        'search_term',
        help='Search term to look for in Guardian articles'
    )
    
    # Optional arguments
    parser.add_argument(
        '--date-from',
        type=str,
        help='Filter articles from this date onwards (YYYY-MM-DD format)'
    )
    
    parser.add_argument(
        '--max-articles',
        type=int,
        default=10,
        help='Maximum number of articles to fetch and publish (1-50, default: 10)'
    )
    
    parser.add_argument(
        '--stream-name',
        type=str,
        help='Kinesis stream name (overrides KINESIS_STREAM_NAME env var)'
    )
    
    parser.add_argument(
        '--aws-region',
        type=str,
        help='AWS region (overrides AWS_DEFAULT_REGION env var, default: us-east-1)'
    )
    
    parser.add_argument(
        '--use-mock',
        action='store_true',
        help='Use mock message broker instead of Kinesis (for testing)'
    )
    
    parser.add_argument(
        '--output-format',
        choices=['json', 'text'],
        default='text',
        help='Output format for results (default: text)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Enable quiet mode (ERROR level only)'
    )
    
    return parser


def load_configuration(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Load configuration from environment variables and command line arguments.
    
    This function combines settings from environment variables with
    command line arguments, giving priority to command line values.
    
    Args:
        args (argparse.Namespace): Parsed command line arguments
        
    Returns:
        Dict[str, Any]: Configuration dictionary
        
    Raises:
        CLIError: If required configuration is missing
    """
    config = {}
    
    # Guardian API key (required)
    config['guardian_api_key'] = os.getenv('GUARDIAN_API_KEY')
    if not config['guardian_api_key']:
        raise CLIError(
            "Guardian API key is required. Set GUARDIAN_API_KEY environment variable."
        )
    
    # AWS configuration
    config['aws_region'] = args.aws_region or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    config['aws_access_key_id'] = os.getenv('AWS_ACCESS_KEY_ID')
    config['aws_secret_access_key'] = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    # Kinesis stream configuration
    config['kinesis_stream_name'] = args.stream_name or os.getenv('KINESIS_STREAM_NAME', 'guardian-content')
    
    # Search parameters
    config['search_term'] = args.search_term
    config['date_from'] = args.date_from
    config['max_articles'] = args.max_articles
    
    # CLI options
    config['use_mock'] = args.use_mock
    config['output_format'] = args.output_format
    config['verbose'] = args.verbose
    config['quiet'] = args.quiet
    
    logger.debug(f"Loaded configuration: {config}")
    return config


def configure_logging(verbose: bool, quiet: bool) -> None:
    """
    Configure logging based on CLI options.
    
    Args:
        verbose (bool): Enable verbose (DEBUG) logging
        quiet (bool): Enable quiet (ERROR only) logging
    """
    if verbose and quiet:
        logger.warning("Both --verbose and --quiet specified, using normal logging level")
        return
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)


def validate_configuration(config: Dict[str, Any]) -> None:
    """
    Validate the loaded configuration.
    
    Args:
        config (Dict[str, Any]): Configuration to validate
        
    Raises:
        CLIError: If configuration is invalid
    """
    # Validate search term
    if not config['search_term'] or not config['search_term'].strip():
        raise CLIError("Search term cannot be empty")
    
    # Validate max articles
    if config['max_articles'] < 1 or config['max_articles'] > 50:
        raise CLIError("max_articles must be between 1 and 50")
    
    # Validate date format if provided
    if config['date_from']:
        try:
            from datetime import datetime
            datetime.strptime(config['date_from'], '%Y-%m-%d')
        except ValueError:
            raise CLIError("date_from must be in YYYY-MM-DD format")
    
    # Validate AWS configuration if not using mock
    if not config['use_mock']:
        if not config['kinesis_stream_name']:
            raise CLIError("Kinesis stream name is required when not using mock")
    
    logger.debug("Configuration validation passed")


def format_output(result: Dict[str, Any], output_format: str) -> str:
    """
    Format the operation result for display.
    
    Args:
        result (Dict[str, Any]): Result from fetch_and_publish operation
        output_format (str): Output format ('json' or 'text')
        
    Returns:
        str: Formatted output string
    """
    if output_format == 'json':
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    # Text format
    lines = [
        f"Guardian Content Fetcher Results",
        f"================================",
        f"Search term: {result['search_term']}",
        f"Date filter: {result['date_from'] or 'None'}",
        f"Articles found: {result['articles_found']}",
        f"Articles published: {result['articles_published']}",
        f"Success: {'Yes' if result['success'] else 'No'}",
    ]
    
    if result['errors']:
        lines.append(f"Errors:")
        for error in result['errors']:
            lines.append(f"  - {error}")
    
    return '\n'.join(lines)


def run_fetch_and_publish(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the main fetch and publish workflow.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        
    Returns:
        Dict[str, Any]: Result from the operation
        
    Raises:
        CLIError: If the operation fails
    """
    try:
        # Create fetcher instance based on configuration
        if config['use_mock']:
            logger.info("Using mock message broker for testing")
            fetcher = GuardianContentFetcherFactory.create_with_mock(
                guardian_api_key=config['guardian_api_key']
            )
        else:
            logger.info(f"Using Kinesis stream: {config['kinesis_stream_name']}")
            fetcher = GuardianContentFetcherFactory.create_with_kinesis(
                guardian_api_key=config['guardian_api_key'],
                kinesis_stream_name=config['kinesis_stream_name'],
                aws_region=config['aws_region'],
                aws_access_key_id=config['aws_access_key_id'],
                aws_secret_access_key=config['aws_secret_access_key']
            )
        
        # Use context manager for proper cleanup
        with fetcher:
            result = fetcher.fetch_and_publish(
                search_term=config['search_term'],
                date_from=config['date_from'],
                max_articles=config['max_articles']
            )
            
        return result
        
    except (GuardianAPIError, MessageBrokerError, GuardianContentFetcherError) as e:
        logger.error(f"Service error: {e}")
        raise CLIError(f"Operation failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise CLIError(f"Unexpected error: {e}")


def main() -> int:
    """
    Main entry point for the CLI application.
    
    This function orchestrates the entire CLI workflow:
    1. Parse command line arguments
    2. Load and validate configuration
    3. Execute the fetch and publish operation
    4. Display results
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        # Parse command line arguments
        parser = setup_argument_parser()
        args = parser.parse_args()
        
        # Configure logging first
        configure_logging(args.verbose, args.quiet)
        
        logger.info("Guardian Content Fetcher CLI started")
        
        # Load and validate configuration
        config = load_configuration(args)
        validate_configuration(config)
        
        # Execute the main operation
        result = run_fetch_and_publish(config)
        
        # Display results
        output = format_output(result, config['output_format'])
        print(output)
        
        # Determine exit code based on success
        if result['success']:
            logger.info("Operation completed successfully")
            return 0
        else:
            logger.error("Operation completed with errors")
            return 1
            
    except CLIError as e:
        logger.error(f"CLI error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\nOperation cancelled by user", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def run_interactive_mode():
    """
    Run the CLI in interactive mode for easier testing and development.
    
    This function provides a simplified interface for users who prefer
    interactive prompts over command line arguments.
    """
    print("Guardian Content Fetcher - Interactive Mode")
    print("==========================================")
    
    try:
        # Collect input from user
        search_term = input("Enter search term: ").strip()
        if not search_term:
            print("Error: Search term cannot be empty")
            return
        
        date_from = input("Enter date filter (YYYY-MM-DD, optional): ").strip()
        if date_from and len(date_from) != 10:
            print("Error: Date must be in YYYY-MM-DD format")
            return
        
        max_articles = input("Maximum articles (1-50, default 10): ").strip()
        if max_articles:
            try:
                max_articles = int(max_articles)
            except ValueError:
                print("Error: Maximum articles must be a number")
                return
        else:
            max_articles = 10
        
        use_mock = input("Use mock publisher? (y/N): ").strip().lower() == 'y'
        
        # Create synthetic args
        class Args:
            def __init__(self):
                self.search_term = search_term
                self.date_from = date_from if date_from else None
                self.max_articles = max_articles
                self.stream_name = None
                self.aws_region = None
                self.use_mock = use_mock
                self.output_format = 'text'
                self.verbose = False
                self.quiet = False
        
        args = Args()
        
        # Run the main workflow
        config = load_configuration(args)
        validate_configuration(config)
        result = run_fetch_and_publish(config)
        
        # Display results
        output = format_output(result, 'text')
        print("\n" + output)
        
    except CLIError as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nOperation cancelled")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == '__main__':
    # If no arguments provided, run in interactive mode
    if len(sys.argv) == 1:
        run_interactive_mode()
    else:
        sys.exit(main())
