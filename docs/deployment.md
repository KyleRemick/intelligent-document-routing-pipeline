# Deployment

## Prerequisites

- AWS account with permissions to create S3, Lambda, DynamoDB, IAM, EventBridge, and CloudFormation stacks
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) configured (`aws configure`)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) (Windows: `winget install --id Amazon.SAM-CLI -e`)

## Build and deploy

From the repository root:

```bash
sam build
sam deploy --guided
```

The guided flow creates `samconfig.toml` (gitignored by default). You can start from `samconfig.toml.example` and adjust stack name and region.

Confirm IAM capability `CAPABILITY_IAM` when prompted so SAM can create execution roles.

Non-interactive deploy (same stack name and region as your choice):

```bash
sam deploy --stack-name doc-routing-pipeline --capabilities CAPABILITY_IAM --resolve-s3 --no-confirm-changeset --region us-east-1
```

## Post-deploy checks

1. **Outputs**: Note `DocumentsBucketName`, `MetadataTableName`, and the Lambda ARN from the stack outputs.
2. **EventBridge**: The bucket has S3 EventBridge notifications enabled. An EventBridge rule matches `Object Created` for that bucket and invokes the Lambda. In the **EventBridge** console, open **Rules** and confirm the rule (name contains `s3-object-created`) is **Enabled** and lists the Lambda as a target.
3. **Smoke test**: Upload a sample PDF to `s3://<bucket>/incoming/test.pdf` and confirm CloudWatch Logs for the function, a new DynamoDB item, and the object under `routed/` or `exceptions/`.

## IAM notes

The Lambda role allows:

- Read/write/delete on the documents bucket (move from ingest to routed or exceptions).
- `dynamodb:PutItem` (via SAM policy template) on the metadata table.
- `textract:StartDocumentTextDetection` and `textract:GetDocumentTextDetection` (async OCR).

Tighten Textract `Resource` if your organization requires it; async Textract jobs are account-scoped.

## Textract timing

Async OCR can take **one to several minutes** depending on document size and service load. The Lambda timeout and `TEXTRACT_MAX_WAIT_SEC` are set to **300 seconds** in `template.yaml`. If Textract does not finish in time, the pipeline routes the file to **`exceptions/`** and records `processing_status` = `failed`.

## Costs

Textract charges per page; S3, Lambda, DynamoDB on-demand, and CloudWatch Logs incur small usage charges. Use the AWS pricing calculator before large tests.
