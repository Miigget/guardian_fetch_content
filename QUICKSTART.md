# Guardian Content Fetcher - Quick Start Guide

Get up and running with Guardian Content Fetcher in under 5 minutes! 🚀

## Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] Guardian API key (free)
- [ ] AWS account (optional, for Kinesis)

## Step 1: Get Guardian API Key (2 minutes)

1. Go to [Guardian Open Platform](https://open-platform.theguardian.com/access/)
2. Click "Register for an API key"
3. Fill out the form (it's free!)
4. Save your API key

## Step 2: Install the Package (1 minute)

```bash
# Clone the repository
git clone <repository-url>
cd guardian_fetch_content

# Install dependencies
pip install -r requirements.txt

# For development (testing, linting, etc.), install dev dependencies:
pip install -r requirements-dev.txt

# Install the package
pip install -e .
```

## Step 3: Configure Environment (1 minute)

```bash
# Copy the template
cp env_template.txt .env

# Edit with your API key
echo "GUARDIAN_API_KEY=your-actual-api-key-here" > .env
```

## Step 4: Test with Mock Broker (30 seconds)

```bash
# Test with mock broker (no AWS needed)
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

## Step 5: Set Up AWS Kinesis (Optional, 2 minutes)

If you want to use real AWS Kinesis:

```bash
# Add AWS credentials to .env
echo "AWS_ACCESS_KEY_ID=your-aws-key" >> .env
echo "AWS_SECRET_ACCESS_KEY=your-aws-secret" >> .env
echo "KINESIS_STREAM_NAME=guardian-content" >> .env

# Create Kinesis stream (AWS CLI required)
aws kinesis create-stream --stream-name guardian-content --shard-count 1
```

## Step 6: Deploy to AWS Lambda (Optional)

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
# Use longer delays between requests
echo "GUARDIAN_RATE_LIMIT_DELAY=3.0" >> .env
```

### Test Your Setup

```bash
# Run all tests to verify everything works
python scripts/run_tests.py --tests-only

# Quick functionality test
guardian-fetch "test" --use-mock --max-articles 1
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

## Configuration Reference

### Minimal Configuration (.env)
```bash
GUARDIAN_API_KEY=your-api-key-here
USE_MOCK_BROKER=true
```

### Production Configuration (.env)
```bash
GUARDIAN_API_KEY=your-api-key-here
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_DEFAULT_REGION=us-east-1
KINESIS_STREAM_NAME=guardian-content
LOG_LEVEL=INFO
```

## Success! 🎉

You're now ready to fetch Guardian articles and publish them to message brokers. 

Start exploring with:
```bash
guardian-fetch "your favorite topic" --use-mock --verbose
```

Happy coding! 🚀
