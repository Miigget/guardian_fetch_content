# Deploying to AWS Lambda

This guide provides step-by-step instructions for deploying the Guardian Content Fetcher as a serverless function on AWS Lambda. This is useful for scheduling regular fetches, for example, using Amazon EventBridge to trigger the function on a schedule.

## Step 1: Package the Application

To deploy to Lambda, you need to create a ZIP file containing the application code and its optimized dependencies. The AWS Lambda Python runtime already includes the `boto3` library, so we must exclude it from our package to keep the size small.

This project includes an automated build script to handle this for you.

From the project's root directory, simply run:

```bash
python scripts/build_lambda_package.py
```

This script will:
1.  Create a clean temporary directory.
2.  Copy your application source code.
3.  Install all dependencies from `requirements.txt` **except** `boto3` and its components.
4.  Create a final `lambda_deployment_package.zip` file in the project root, ready for upload.
5.  Clean up all temporary files.

The output will show the final, much smaller, file size of your deployment package.

## Step 2: Create an IAM Role for Lambda

Your Lambda function needs permissions to write to Kinesis and to create logs in CloudWatch.

1.  Go to the **IAM** console in your AWS account.
2.  Navigate to **Roles** and click **Create role**.
3.  For **Trusted entity type**, select **AWS service**.
4.  For **Use case**, select **Lambda**, then click **Next**.
5.  Search for and add the following AWS managed policies:
    *   `AWSLambdaBasicExecutionRole` (for CloudWatch Logs)
    *   `AmazonKinesisFullAccess` (for simplicity, provides full access. For production, it's better to create a custom policy with `kinesis:PutRecord` and `kinesis:PutRecords` permissions restricted to your specific stream).
6.  Click **Next**.
7.  Give the role a descriptive name (e.g., `GuardianFetcherLambdaRole`) and click **Create role**.

## Step 3: Create the Lambda Function

1.  Go to the **AWS Lambda** console and click **Create function**.
2.  Select **Author from scratch**.
3.  **Function name**: `guardian-content-fetcher`
4.  **Runtime**: Python 3.9 (or a newer supported version)
5.  **Architecture**: `x86_64`
6.  **Permissions**: Choose **Use an existing role** and select the `GuardianFetcherLambdaRole` you created in the previous step.
7.  Click **Create function**.

## Step 4: Configure the Lambda Function

1.  In the function's main page, under the **Code source** section, click **Upload from** and select **.zip file**. Upload the `lambda_deployment_package.zip` file.
2.  Go to the **Configuration** > **General configuration** tab and click **Edit**.
    *   Change the **Handler** to `guardian_content_fetcher.lambda_handler.handler`. This tells Lambda which function to execute from your code.
    *   Increase the **Timeout** to at least 30 seconds to prevent the function from timing out during API calls.
    *   Click **Save**.
3.  Go to the **Configuration** > **Environment variables** tab and click **Edit**. Add the following variables, which your code will use for configuration:
    *   `GUARDIAN_API_KEY`: `your-actual-api-key-here`
    *   `KINESIS_STREAM_NAME`: `guardian-content` (or the name of your stream)
    *   Click **Save**.

## Step 5: Test the Lambda Function

You can test your function directly from the AWS console to ensure it's working correctly.

1.  Navigate to the **Test** tab within your function's page.
2.  Create a new test event. Give it a name like `TestSearchEvent`.
3.  Use the following JSON as the event payload. This simulates the data that will trigger your function.
    ```json
    {
      "search_term": "cloud computing",
      "date_from": "2023-01-01",
      "max_articles": 5
    }
    ```
4.  Click **Save**, then click the **Test** button.

You should see an execution result with a `statusCode: 200`. You can inspect the detailed logs in the **Monitor** > **Logs** tab (which will take you to CloudWatch) and verify that new data has appeared in your Kinesis stream using the "Trim horizon" method.
