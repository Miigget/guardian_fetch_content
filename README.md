# Guardian Content Fetcher

**A robust Python application for fetching articles from Guardian API and publishing to message brokers**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🚀 Quick Start

For a step-by-step, friendly onboarding (prerequisites, installation,
environment setup, sample commands, troubleshooting), open the dedicated
[`QUICKSTART.md`](./QUICKSTART.md). That document is the canonical source for:

- Installing and testing the project locally.
- Preparing the `.env` file with your Guardian API key and optional AWS credentials.
- Running the CLI in mock or AWS-backed modes.
- Verifying the setup with the bundled quality gate (`scripts/run_tests.py`).

The rest of this README focuses on what the project does, how it is structured, and
reference information you may need after the initial setup.

## 📋 Features

- ✅ **Guardian API Integration**: Fetch articles with search terms and date filters
- ✅ **AWS Kinesis Support**: Publish articles to Kinesis Data Streams
- ✅ **Mock Publisher**: Test functionality without AWS resources
- ✅ **CLI Interface**: Easy command-line operation with extensive options
- ✅ **Rate Limiting**: Respects Guardian API free tier limits (2 seconds between requests)
- ✅ **Content Preview**: Optional article content preview (first 1000 characters)
- ✅ **Comprehensive Logging**: Detailed logging for monitoring and debugging
- ✅ **Error Handling**: Graceful error handling with fallback strategies
- ✅ **Security**: No credentials stored in code, environment variable configuration
- ✅ **Testing**: 90%+ test coverage with unit tests and integration tests
- ✅ **Type Hints**: Full type annotations for better code clarity
- ✅ **Code Quality**: PEP-8 compliance, security scanning with Bandit

## 🛠 Installation & Setup

- **Need a guided walkthrough?** Follow the instructions in [`QUICKSTART.md`](./QUICKSTART.md) for
  cloning the repo, installing dependencies, configuring `.env`, and running smoke tests.
- **Want the packaged release?** When the project is published to PyPI you can simply run
  `pip install guardian-content-fetcher` on any machine with Python 3.8+.
- **Environment variables.** Copy `env_template.txt` to `.env`, then fill in your Guardian API key
  and (optionally) AWS credentials. Quickstart explains every field in plain language.
- **Prerequisites recap.** Python 3.8+, a Guardian API key, and AWS credentials only if you plan to
  push data to Kinesis. Mock mode works without AWS access.

## ⚙️ Configuration

The application is configured entirely through environment variables. `env_template.txt` and the
Quick Start Guide explain each field in detail; the snippets below highlight the most important
values so you can quickly see what's available.

### Required Configuration

```bash
# Guardian API key (required)
GUARDIAN_API_KEY=your-guardian-api-key-here
```

### AWS Configuration (Optional)

```bash
# AWS credentials (optional if using IAM roles)
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_DEFAULT_REGION=eu-west-2

# Kinesis stream name
KINESIS_STREAM_NAME=guardian-content
```

### Optional Settings

```bash
# Use mock broker instead of Kinesis
USE_MOCK_BROKER=false

# Logging level
LOG_LEVEL=INFO

# API rate limiting (seconds between requests)
GUARDIAN_RATE_LIMIT_DELAY=2.0
```

## 📖 Usage

- **Need CLI or basic Python examples?** Use the scenarios documented in
  [`QUICKSTART.md`](./QUICKSTART.md); they cover searches, mock mode, JSON output, and interactive
  runs.
- **Prefer to wire components manually?** The advanced pattern below shows how to assemble the core
  classes yourself.

```python
from guardian_content_fetcher import (
    GuardianAPIClient, KinesisPublisher, GuardianContentFetcher
)

# Manual configuration
api_client = GuardianAPIClient(
    api_key="your-guardian-api-key",
    rate_limit_delay=1.5  # Custom rate limiting
)

kinesis_publisher = KinesisPublisher(
    stream_name="my-stream",
    region_name="eu-west-2"
)

# Create fetcher with custom components
with GuardianContentFetcher(api_client, kinesis_publisher) as fetcher:
    result = fetcher.fetch_and_publish("data engineering")
```

## 📁 Project Structure

```
guardian_fetch_content/
├── src/guardian_content_fetcher/
│   ├── __init__.py              # Package initialization and exports
│   ├── api_client.py            # Guardian API client implementation
│   ├── message_broker.py        # Message broker publishers (Kinesis, Mock)
│   ├── content_fetcher.py       # Main orchestrator class
│   ├── config.py                # Configuration management
│   ├── cli.py                   # Command-line interface
│   └── lambda_handler.py        # AWS Lambda handler
├── tests/                       # Comprehensive test suite
│   ├── conftest.py             # Test fixtures and utilities
│   ├── test_api_client.py      # API client tests
│   ├── test_message_broker.py  # Message broker tests
│   ├── test_content_fetcher.py # Main class tests
│   ├── test_config.py          # Configuration tests
│   ├── test_cli.py             # CLI tests
│   └── test_lambda_handler.py  # Lambda handler tests
├── scripts/                    # Helper scripts
│   ├── run_tests.py           # Test runner script
│   └── build_lambda_package.py # Lambda deployment packager
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Development dependencies
├── setup.py                     # Package configuration
├── pyproject.toml              # Black and pytest configuration
├── .flake8                     # Flake8 linting configuration (88 chars)
├── pytest.ini                  # Test configuration
├── env_template.txt             # Environment configuration template
├── README.md                    # Overview & reference (this file)
├── QUICKSTART.md                # Step-by-step setup guide
├── DEPLOY_LAMBDA.md             # AWS Lambda deployment how-to
└── CODE_STYLE.md               # Detailed code style documentation
```

## 🧪 Testing

- `python scripts/run_tests.py` runs the entire quality gate (package install check, unit tests with
  coverage, linting, and security scan).
- Quickstart documents every flag (`--tests-only`, `--lint-only`, `--security-only`, `--install-only`,
  `--coverage`, `-v`) plus troubleshooting steps if any tool fails.
- Prefer raw `pytest` or `flake8` commands? Feel free to call them directly—`scripts/run_tests.py`
  simply orchestrates the required checks described in `task_description_pl.md`.

## 🏗 Architecture

### Components

1. **GuardianAPIClient**: Handles Guardian API communication with rate limiting
2. **MessageBrokerPublisher**: Abstract interface for message brokers
3. **KinesisPublisher**: AWS Kinesis implementation with batch support
4. **MockPublisher**: Testing implementation
5. **GuardianContentFetcher**: Main orchestrator coordinating the workflow
6. **CLI**: Command-line interface with argument parsing and configuration

### Data Flow

```
CLI Input → Configuration → GuardianAPIClient → Articles → MessageBroker → AWS Kinesis
```

### Error Handling

- **API Errors**: Graceful handling of Guardian API failures
- **Network Issues**: Retry logic and timeout handling  
- **Publishing Failures**: Batch fallback to individual publishing
- **Configuration Errors**: Clear error messages and validation

## 📊 Output Format

Articles are published in JSON format with the following structure:

```json
{
    "webPublicationDate": "2023-01-01T10:00:00Z",
    "webTitle": "Machine Learning Advances in 2023",
    "webUrl": "https://www.theguardian.com/technology/2023/jan/01/machine-learning-advances",
    "content_preview": "This article discusses the latest advances in machine learning..."
}
```

### CLI Output

```
Guardian Content Fetcher Results
================================
Search term: machine learning
Date filter: 2023-01-01
Articles found: 10
Articles published: 10
Success: Yes
```

## 🚀 Deployment

### AWS Lambda

The package is designed to work within AWS Lambda memory limits. For a full, click-by-click
deployment walkthrough (packaging, IAM role, environment variables, and testing in the AWS
console), see the dedicated guide: [`DEPLOY_LAMBDA.md`](./DEPLOY_LAMBDA.md).

```python
# Lambda handler example (see lambda_handler.py for the actual implementation)
import json
from guardian_content_fetcher import (
    load_config_from_env,
    GuardianContentFetcherFactory,
    ConfigurationError
)

def lambda_handler(event, context):
    # Load configuration from environment variables using config module
    config = load_config_from_env()
    
    # Validate Kinesis config is available (Lambda requires real broker)
    if not config.kinesis_config:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Kinesis configuration required. Set KINESIS_STREAM_NAME.'
            })
        }
    
    # Create fetcher and execute
    fetcher = GuardianContentFetcherFactory.create_with_kinesis(
        guardian_api_key=config.guardian_config.api_key,
        kinesis_stream_name=config.kinesis_config.stream_name,
        aws_region=config.kinesis_config.aws_config.region,
        aws_access_key_id=config.kinesis_config.aws_config.access_key_id,
        aws_secret_access_key=config.kinesis_config.aws_config.secret_access_key,
    )
    
    with fetcher:
        result = fetcher.fetch_and_publish(
            search_term=event['search_term'],
            date_from=event.get('date_from'),
            max_articles=event.get('max_articles', 10)
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
```

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

CMD ["guardian-fetch", "--help"]
```

## 🔧 Development

### Setting up Development Environment

- Start with the instructions in [`QUICKSTART.md`](./QUICKSTART.md) to clone the repository, install
  dependencies, configure `.env`, and run the smoke tests.
- Create an isolated virtual environment so your global Python installation stays clean:
  `python -m venv venv && source venv/bin/activate` (Windows: `venv\Scripts\activate`).
- Install the extra tooling required for linting, formatting, and security scans:

  ```bash
  pip install -r requirements-dev.txt
  ```

### Code Quality Standards

As required by project specification:

- **Testing**: 90%+ test coverage requirement with pytest
- **Security**: Bandit security scanning for vulnerabilities
- **Documentation**: Comprehensive docstrings and comments
- **Style**: Black formatting (88 char), Flake8 linting (88 char) - PEP-8 compliant

**To switch to strict PEP-8 (79 characters):**

See detailed instructions in [CODE_STYLE.md](CODE_STYLE.md)

## 📚 API Reference

### GuardianContentFetcher

Main orchestrator class for the entire workflow.

#### Methods

- `fetch_and_publish(search_term, date_from=None, max_articles=10)`: Main operation
- `close()`: Clean up resources

### GuardianAPIClient

Interface to Guardian Open Platform API.

#### Methods

- `search_content(search_term, date_from=None, page_size=10)`: Search for articles

### MessageBrokerPublisher

Abstract base class for message broker implementations.

#### Methods

- `publish_message(message)`: Publish single message
- `publish_batch(messages)`: Publish multiple messages

## 🤝 Support

For questions, issues, or contributions:

1. Check existing [GitHub issues](https://github.com/Miigget/guardian_fetch_content/issues)
2. Create a new issue with detailed description
3. For security issues, please email directly

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Guardian Open Platform](https://open-platform.theguardian.com/) for providing the API
- AWS for Kinesis Data Streams
- Python community for excellent libraries

---
