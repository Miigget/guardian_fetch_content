# Guardian Content Fetcher - Quick Start Guide

Get up and running with Guardian Content Fetcher in under 5 minutes! 🚀

## Prerequisites Checklist

- [ ] Python 3.8+ installed ([download](https://www.python.org/downloads/))
- [ ] Guardian API key (free) ([get one](https://open-platform.theguardian.com/access/))
- [ ] AWS account (optional, for Kinesis)

## Step 1: Get Guardian API Key (2 minutes)

1. Go to [Guardian Open Platform](https://open-platform.theguardian.com/access/)
2. Click "Register for an API key"
3. Fill out the form (it's free!)
4. Save your API key

## Step 2: Install the Package (1 minute)

```bash
# Clone the repository
git clone https://github.com/Miigget/guardian_fetch_content
cd guardian_fetch_content

# Install dependencies
pip install -r requirements.txt

# For development (testing, linting, etc.), install dev dependencies:
pip install -r requirements-dev.txt

# Install the package
pip install -e .
```

## Step 3: Configure Environment (1 minute)

Copy the template to create your local `.env`:
```bash
cp env_template.txt .env
```

Open `.env` in your editor and set:
```
GUARDIAN_API_KEY=your-actual-api-key-here
```

> ℹ️ Tip for development: when using the mock broker, you can set `GUARDIAN_API_KEY=test`. Replace it with your real key in production.

## Step 4: Test Your Setup

> ℹ️ Before running the checks, make sure the developer dependencies are installed (production `requirements.txt` alone does not include the tooling needed by `scripts/run_tests.py`):
>
 ```bash
 pip install -r requirements-dev.txt
 ```

```bash
# Run the full quality gate (install, tests+coverage, lint, security)
python scripts/run_tests.py
```

The optional flags below let you run each quality gate independently, so you can execute only the part you need at any moment.

```bash
# Only run unit tests (add --coverage for report, -v for verbose pytest)
python scripts/run_tests.py --tests-only --coverage -v

# Only run style/format checks (Flake8 + Black)
python scripts/run_tests.py --lint-only

# Only run security scanning with Bandit (JSON output saved to bandit-report.json)
python scripts/run_tests.py --security-only

# Only verify editable installation works
python scripts/run_tests.py --install-only
```

## Step 5: Test with Mock Broker (30 seconds)

```bash
# Quick functionality tests (no AWS needed)
guardian-fetch "test" --use-mock --max-articles 1

guardian-fetch "machine learning" --use-mock --verbose
```

You should see output like:
```
Guardian Content Fetcher Results
================================
Search term: machine learning
Date filter: None
Articles found: 10
Articles published: 10
Success: Yes
```

## Step 6: Set Up AWS Kinesis for CLI Usage (Optional, 2 minutes)

If you want to use real AWS Kinesis via CLI:

Open `.env` and add the AWS settings (or verify they exist):
```
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_DEFAULT_REGION=eu-west-2
KINESIS_STREAM_NAME=guardian-content
```

Then create the Kinesis stream (AWS CLI required):
```bash
aws kinesis create-stream --stream-name guardian-content --shard-count 1
```

## Step 7: Deploy to AWS Lambda (Optional)

You can run this tool as a serverless function on AWS Lambda, which is ideal for scheduled or event-driven execution.

For detailed, step-by-step instructions on how to package, configure, and deploy the application to AWS Lambda, please see the dedicated guide:

➡️ **[Full Guide: Deploying to AWS Lambda](./DEPLOY_LAMBDA.md)**

## Quick Examples

### Basic CLI Usage

```bash
# Simple search
guardian-fetch "artificial intelligence"

# With date filter
guardian-fetch "python programming" --date-from 2023-01-01

# Custom article count
guardian-fetch "data science" --max-articles 5

# JSON output
guardian-fetch "cloud computing" --output-format json
```

### Python API Usage

```python
from guardian_content_fetcher import GuardianContentFetcherFactory

# Using mock broker (no AWS needed)
fetcher = GuardianContentFetcherFactory.create_with_mock(
    guardian_api_key="your-api-key"
)

result = fetcher.fetch_and_publish("machine learning")
print(f"Published {result['articles_published']} articles")
```

### Interactive Mode

```bash
# Run without arguments for guided setup
guardian-fetch
```

## Troubleshooting

### Common Issues

**"Guardian API key is required"**
```bash
# Check your .env file
cat .env
# Should contain: GUARDIAN_API_KEY=your-actual-key
```

**"Command 'guardian-fetch' not found"**
```bash
# Reinstall the package
pip install -e .

# Or run directly
python -m guardian_content_fetcher.cli "machine learning" --use-mock
```

**Rate limiting errors**
```bash
# Use longer delays between requests (in seconds)
echo "GUARDIAN_RATE_LIMIT_DELAY=3.0" >> .env
```

## Next Steps

Once you have the basic setup working:

1. **Read the Full Documentation**: Check `README.md` for detailed usage
2. **Configure AWS Kinesis**: Set up real message broker
3. **Explore Advanced Features**: Date filtering, custom streams, etc.
4. **Integrate into Your Pipeline**: Use the Python API in your applications

## Getting Help

- **Documentation**: `README.md` has comprehensive information
- **Examples**: Check the `tests/` directory for usage examples
- **Issues**: Report bugs on GitHub
- **Configuration**: See `env_template.txt` for all options

Notes:
- AWS Lambda: do not put static access keys in `.env`. Use the function’s IAM role for AWS credentials. Only set non-secret variables like `KINESIS_STREAM_NAME` and `LOG_LEVEL`. Leave `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` unset.

## Success! 🎉

You're now ready to fetch Guardian articles and publish them to message brokers. 

Start exploring with:
```bash
guardian-fetch "your favorite topic" --use-mock --verbose
```

Happy coding! 🚀
