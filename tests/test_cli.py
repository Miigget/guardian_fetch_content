"""
Tests for CLI module.

This module contains comprehensive tests for the command-line interface,
including argument parsing, configuration loading, and execution workflows.
"""

import pytest
import json
from unittest.mock import patch, Mock
from argparse import Namespace

from guardian_content_fetcher.cli import (
    setup_argument_parser,
    load_configuration,
    configure_logging,
    validate_configuration,
    format_output,
    run_fetch_and_publish,
    main,
    run_interactive_mode,
    CLIError,
)


class TestSetupArgumentParser:
    """Test cases for argument parser setup."""

    def test_parser_creation(self):
        """Test that argument parser is created successfully."""
        parser = setup_argument_parser()

        assert parser.prog is not None
        assert "Guardian Content Fetcher" in parser.description

    def test_required_search_term(self):
        """Test that search term is required."""
        parser = setup_argument_parser()

        # Should parse successfully with search term
        args = parser.parse_args(["machine learning"])
        assert args.search_term == "machine learning"

        # Should fail without search term
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_optional_arguments(self):
        """Test parsing of optional arguments."""
        parser = setup_argument_parser()

        args = parser.parse_args(
            [
                "machine learning",
                "--date-from",
                "2023-01-01",
                "--max-articles",
                "15",
                "--stream-name",
                "custom-stream",
                "--aws-region",
                "eu-west-1",
                "--use-mock",
                "--output-format",
                "json",
                "--verbose",
            ]
        )

        assert args.search_term == "machine learning"
        assert args.date_from == "2023-01-01"
        assert args.max_articles == 15
        assert args.stream_name == "custom-stream"
        assert args.aws_region == "eu-west-1"
        assert args.use_mock is True
        assert args.output_format == "json"
        assert args.verbose is True
        assert args.quiet is False

    def test_default_values(self):
        """Test default values for optional arguments."""
        parser = setup_argument_parser()
        args = parser.parse_args(["test"])

        assert args.date_from is None
        assert args.max_articles == 10
        assert args.stream_name is None
        assert args.aws_region is None
        assert args.use_mock is False
        assert args.output_format == "text"
        assert args.verbose is False
        assert args.quiet is False

    def test_mutually_exclusive_verbose_quiet(self):
        """Test that verbose and quiet can both be set (warning shown later)."""
        parser = setup_argument_parser()

        # Both flags can be set, but warning will be shown in configure_logging
        args = parser.parse_args(["test", "--verbose", "--quiet"])
        assert args.verbose is True
        assert args.quiet is True


class TestLoadConfiguration:
    """Test cases for configuration loading."""

    def test_load_configuration_success(self, cli_args, mock_environment_variables):
        """Test successful configuration loading."""
        config = load_configuration(cli_args)

        assert config["guardian_api_key"] == "test-guardian-api-key"
        assert config["aws_region"] == "eu-west-2"
        assert config["kinesis_stream_name"] == "test-stream"
        assert config["search_term"] == "machine learning"
        assert config["date_from"] == "2023-01-01"
        assert config["max_articles"] == 10
        assert config["use_mock"] is False

    def test_load_configuration_missing_api_key(self, cli_args):
        """Test configuration loading with missing API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(CLIError, match="Guardian API key is required"):
                load_configuration(cli_args)

    def test_load_configuration_override_env_vars(self, mock_environment_variables):
        """Test that CLI arguments override environment variables."""
        args = Namespace(
            search_term="python",
            date_from=None,
            max_articles=5,
            stream_name="cli-stream",
            aws_region="eu-central-1",
            use_mock=True,
            output_format="json",
            verbose=True,
            quiet=False,
        )

        config = load_configuration(args)

        # CLI args should override env vars
        assert config["kinesis_stream_name"] == "cli-stream"  # Override env
        assert config["aws_region"] == "eu-central-1"  # Override env
        assert config["use_mock"] is True
        assert config["max_articles"] == 5

    def test_load_configuration_default_values(self, mock_environment_variables):
        """Test configuration with default values."""
        args = Namespace(
            search_term="test",
            date_from=None,
            max_articles=10,
            stream_name=None,  # Use env var
            aws_region=None,  # Use env var
            use_mock=False,
            output_format="text",
            verbose=False,
            quiet=False,
        )

        config = load_configuration(args)

        assert config["kinesis_stream_name"] == "test-stream"  # From env
        assert config["aws_region"] == "eu-west-2"  # From env


class TestValidateConfiguration:
    """Test cases for configuration validation."""

    def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        config = {
            "search_term": "machine learning",
            "max_articles": 10,
            "date_from": "2023-01-01",
            "use_mock": False,
            "kinesis_stream_name": "test-stream",
        }

        # Should not raise any exception
        validate_configuration(config)

    def test_validate_empty_search_term(self):
        """Test validation with empty search term."""
        config = {
            "search_term": "",
            "max_articles": 10,
            "date_from": None,
            "use_mock": False,
            "kinesis_stream_name": "test-stream",
        }

        with pytest.raises(CLIError, match="Search term cannot be empty"):
            validate_configuration(config)

    def test_validate_invalid_max_articles(self):
        """Test validation with invalid max_articles."""
        config = {
            "search_term": "test",
            "max_articles": 0,
            "date_from": None,
            "use_mock": False,
            "kinesis_stream_name": "test-stream",
        }

        with pytest.raises(CLIError, match="max_articles must be between 1 and 50"):
            validate_configuration(config)

    def test_validate_invalid_date_format(self):
        """Test validation with invalid date format."""
        config = {
            "search_term": "test",
            "max_articles": 10,
            "date_from": "2023/01/01",
            "use_mock": False,
            "kinesis_stream_name": "test-stream",
        }

        with pytest.raises(CLIError, match="date_from must be in YYYY-MM-DD format"):
            validate_configuration(config)

    def test_validate_missing_stream_name(self):
        """Test validation with missing stream name when not using mock."""
        config = {
            "search_term": "test",
            "max_articles": 10,
            "date_from": None,
            "use_mock": False,
            "kinesis_stream_name": "",
        }

        with pytest.raises(CLIError, match="Kinesis stream name is required"):
            validate_configuration(config)

    def test_validate_mock_without_stream_name(self):
        """Test validation with mock broker (stream name not required)."""
        config = {
            "search_term": "test",
            "max_articles": 10,
            "date_from": None,
            "use_mock": True,
            "kinesis_stream_name": "",
        }

        # Should not raise exception
        validate_configuration(config)


class TestFormatOutput:
    """Test cases for output formatting."""

    def test_format_output_json(self):
        """Test JSON output formatting."""
        result = {
            "success": True,
            "articles_found": 2,
            "articles_published": 2,
            "search_term": "machine learning",
            "date_from": "2023-01-01",
            "errors": [],
        }

        output = format_output(result, "json")

        # Should be valid JSON
        parsed = json.loads(output)
        assert parsed == result

    def test_format_output_text(self):
        """Test text output formatting."""
        result = {
            "success": True,
            "articles_found": 2,
            "articles_published": 2,
            "search_term": "machine learning",
            "date_from": "2023-01-01",
            "errors": [],
        }

        output = format_output(result, "text")

        assert "Guardian Content Fetcher Results" in output
        assert "Search term: machine learning" in output
        assert "Date filter: 2023-01-01" in output
        assert "Articles found: 2" in output
        assert "Articles published: 2" in output
        assert "Success: Yes" in output

    def test_format_output_text_with_errors(self):
        """Test text output formatting with errors."""
        result = {
            "success": False,
            "articles_found": 2,
            "articles_published": 1,
            "search_term": "test",
            "date_from": None,
            "errors": ["Connection timeout", "Retry failed"],
        }

        output = format_output(result, "text")

        assert "Success: No" in output
        assert "Date filter: None" in output
        assert "Errors:" in output
        assert "  - Connection timeout" in output
        assert "  - Retry failed" in output


class TestRunFetchAndPublish:
    """Test cases for the main fetch and publish workflow."""

    @patch(
        "guardian_content_fetcher.cli.GuardianContentFetcherFactory.create_with_kinesis"
    )
    def test_run_fetch_and_publish_kinesis_success(self, mock_factory):
        """Test successful fetch and publish with Kinesis."""
        # Mock fetcher and its methods
        mock_fetcher = Mock()
        mock_fetcher.__enter__ = Mock(return_value=mock_fetcher)
        mock_fetcher.__exit__ = Mock(return_value=None)
        mock_fetcher.fetch_and_publish.return_value = {
            "success": True,
            "articles_found": 2,
            "articles_published": 2,
            "search_term": "test",
            "date_from": None,
            "errors": [],
        }
        mock_factory.return_value = mock_fetcher

        config = {
            "use_mock": False,
            "guardian_api_key": "test-key",
            "kinesis_stream_name": "test-stream",
            "aws_region": "eu-west-2",
            "aws_access_key_id": "aws-key",
            "aws_secret_access_key": "aws-secret",
            "search_term": "test",
            "date_from": None,
            "max_articles": 10,
        }

        result = run_fetch_and_publish(config)

        # Verify factory was called correctly
        mock_factory.assert_called_once_with(
            guardian_api_key="test-key",
            kinesis_stream_name="test-stream",
            aws_region="eu-west-2",
            aws_access_key_id="aws-key",
            aws_secret_access_key="aws-secret",
        )

        # Verify fetcher was used correctly
        mock_fetcher.fetch_and_publish.assert_called_once_with(
            search_term="test", date_from=None, max_articles=10
        )

        assert result["success"] is True

    @patch(
        "guardian_content_fetcher.cli.GuardianContentFetcherFactory.create_with_mock"
    )
    def test_run_fetch_and_publish_mock_success(self, mock_factory):
        """Test successful fetch and publish with mock broker."""
        mock_fetcher = Mock()
        mock_fetcher.__enter__ = Mock(return_value=mock_fetcher)
        mock_fetcher.__exit__ = Mock(return_value=None)
        mock_fetcher.fetch_and_publish.return_value = {
            "success": True,
            "articles_found": 1,
            "articles_published": 1,
            "search_term": "test",
            "date_from": None,
            "errors": [],
        }
        mock_factory.return_value = mock_fetcher

        config = {
            "use_mock": True,
            "guardian_api_key": "test-key",
            "search_term": "test",
            "date_from": None,
            "max_articles": 10,
        }

        result = run_fetch_and_publish(config)

        mock_factory.assert_called_once_with(guardian_api_key="test-key")
        assert result["success"] is True

    @patch(
        "guardian_content_fetcher.cli.GuardianContentFetcherFactory.create_with_kinesis"
    )
    def test_run_fetch_and_publish_error(self, mock_factory):
        """Test fetch and publish with error."""
        from guardian_content_fetcher.api_client import GuardianAPIError

        mock_factory.side_effect = GuardianAPIError("API error")

        config = {
            "use_mock": False,
            "guardian_api_key": "test-key",
            "kinesis_stream_name": "test-stream",
            "aws_region": "eu-west-2",
            "aws_access_key_id": None,
            "aws_secret_access_key": None,
            "search_term": "test",
            "date_from": None,
            "max_articles": 10,
        }

        with pytest.raises(CLIError, match="Operation failed"):
            run_fetch_and_publish(config)


class TestConfigureLogging:
    """Test cases for logging configuration."""

    @patch("logging.getLogger")
    def test_configure_logging_normal(self, mock_get_logger):
        """Test normal logging configuration."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        configure_logging(verbose=False, quiet=False)

        # Should not change logging level (stays at default)
        mock_logger.setLevel.assert_not_called()

    @patch("logging.getLogger")
    def test_configure_logging_verbose(self, mock_get_logger):
        """Test verbose logging configuration."""
        import logging

        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        with patch("logging.getLogger", return_value=mock_root_logger):
            configure_logging(verbose=True, quiet=False)

            # Should set DEBUG level
            mock_root_logger.setLevel.assert_called_with(logging.DEBUG)

    @patch("logging.getLogger")
    def test_configure_logging_quiet(self, mock_get_logger):
        """Test quiet logging configuration."""
        import logging

        mock_root_logger = Mock()
        mock_get_logger.return_value = mock_root_logger

        with patch("logging.getLogger", return_value=mock_root_logger):
            configure_logging(verbose=False, quiet=True)

            # Should set ERROR level
            mock_root_logger.setLevel.assert_called_with(logging.ERROR)

    @patch("logging.getLogger")
    def test_configure_logging_both_flags(self, mock_get_logger):
        """Test logging configuration with both verbose and quiet flags."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        configure_logging(verbose=True, quiet=True)

        # Should not change level when both flags are set (warning shown)
        mock_logger.setLevel.assert_not_called()


class TestMainFunction:
    """Test cases for the main CLI function."""

    @patch("guardian_content_fetcher.cli.run_fetch_and_publish")
    @patch("guardian_content_fetcher.cli.validate_configuration")
    @patch("guardian_content_fetcher.cli.load_configuration")
    @patch("guardian_content_fetcher.cli.configure_logging")
    @patch("sys.argv", ["guardian-fetch", "machine learning"])
    @patch("builtins.print")
    def test_main_success(
        self,
        mock_print,
        mock_configure_logging,
        mock_load_config,
        mock_validate_config,
        mock_run_fetch,
    ):
        """Test successful main execution."""
        mock_load_config.return_value = {
            "verbose": False,
            "quiet": False,
            "output_format": "text",
        }
        mock_run_fetch.return_value = {
            "success": True,
            "articles_found": 2,
            "articles_published": 2,
            "search_term": "machine learning",
            "date_from": None,
            "errors": [],
        }

        exit_code = main()

        assert exit_code == 0
        mock_print.assert_called()  # Output should be printed

    @patch("guardian_content_fetcher.cli.run_fetch_and_publish")
    @patch("guardian_content_fetcher.cli.validate_configuration")
    @patch("guardian_content_fetcher.cli.load_configuration")
    @patch("sys.argv", ["guardian-fetch", "test"])
    def test_main_operation_failure(
        self, mock_load_config, mock_validate_config, mock_run_fetch
    ):
        """Test main execution with operation failure."""
        mock_load_config.return_value = {
            "verbose": False,
            "quiet": False,
            "output_format": "text",
        }
        mock_run_fetch.return_value = {
            "success": False,
            "articles_found": 2,
            "articles_published": 0,
            "search_term": "test",
            "date_from": None,
            "errors": ["Publishing failed"],
        }

        with patch("builtins.print"):
            exit_code = main()

        assert exit_code == 1

    @patch("guardian_content_fetcher.cli.load_configuration")
    @patch("sys.argv", ["guardian-fetch", "test"])
    def test_main_cli_error(self, mock_load_config):
        """Test main execution with CLI error."""
        mock_load_config.side_effect = CLIError("Configuration error")

        with patch("builtins.print"):
            exit_code = main()

        assert exit_code == 1

    @patch("sys.argv", ["guardian-fetch", "test"])
    def test_main_keyboard_interrupt(self):
        """Test main execution with keyboard interrupt."""
        with patch("guardian_content_fetcher.cli.setup_argument_parser") as mock_parser:
            mock_parser.side_effect = KeyboardInterrupt()

            with patch("builtins.print"):
                exit_code = main()

        assert exit_code == 1


class TestRunInteractiveMode:
    """Test cases for interactive mode."""

    @patch("builtins.input")
    @patch("guardian_content_fetcher.cli.run_fetch_and_publish")
    @patch("guardian_content_fetcher.cli.validate_configuration")
    @patch("guardian_content_fetcher.cli.load_configuration")
    @patch("builtins.print")
    def test_run_interactive_mode_success(
        self,
        mock_print,
        mock_load_config,
        mock_validate_config,
        mock_run_fetch,
        mock_input,
    ):
        """Test successful interactive mode execution."""
        # Mock user inputs
        mock_input.side_effect = [
            "machine learning",  # search term
            "2023-01-01",  # date filter
            "5",  # max articles
            "n",  # use mock (no)
        ]

        mock_load_config.return_value = {"test": "config"}
        mock_run_fetch.return_value = {
            "success": True,
            "articles_found": 2,
            "articles_published": 2,
            "search_term": "machine learning",
            "date_from": "2023-01-01",
            "errors": [],
        }

        run_interactive_mode()

        # Verify functions were called
        mock_load_config.assert_called_once()
        mock_validate_config.assert_called_once()
        mock_run_fetch.assert_called_once()

        # Verify output was printed
        mock_print.assert_called()

    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_interactive_mode_empty_search_term(self, mock_print, mock_input):
        """Test interactive mode with empty search term."""
        mock_input.side_effect = [""]  # Empty search term

        run_interactive_mode()

        # Should print error message
        error_printed = any(
            "Error: Search term cannot be empty" in str(call)
            for call in mock_print.call_args_list
        )
        assert error_printed

    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_interactive_mode_invalid_max_articles(self, mock_print, mock_input):
        """Test interactive mode with invalid max articles."""
        mock_input.side_effect = [
            "test",  # search term
            "",  # date filter (empty)
            "invalid",  # max articles (invalid)
        ]

        run_interactive_mode()

        # Should print error message
        error_printed = any(
            "Error: Maximum articles must be a number" in str(call)
            for call in mock_print.call_args_list
        )
        assert error_printed

    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_interactive_mode_keyboard_interrupt(self, mock_print, mock_input):
        """Test interactive mode with keyboard interrupt."""
        mock_input.side_effect = KeyboardInterrupt()

        run_interactive_mode()

        # Should print cancellation message
        cancel_printed = any(
            "Operation cancelled" in str(call) for call in mock_print.call_args_list
        )
        assert cancel_printed
