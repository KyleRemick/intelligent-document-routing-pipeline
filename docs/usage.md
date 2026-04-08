# Usage

## Upload path

Upload PDFs (and other formats Textract supports for async detection) to:

`s3://<DocumentsBucketName>/incoming/<your-file.pdf>`

Ingest uses the **`incoming/`** prefix. The handler skips keys that do not start with `incoming/` and skips keys under `routed/` or `exceptions/` so routed objects are not reprocessed.

## Example flow

1. Upload `referral_001.pdf` to `incoming/referral_001.pdf`.
2. Lambda runs Textract, extracts text, applies keyword rules.
3. If keywords match **referral**, the file is copied to `routed/referral/<document_id>_referral_001.pdf` and the ingest object is deleted.
4. Metadata is written to DynamoDB with classification, matched keywords, and routing fields.
5. CloudWatch Logs show JSON-oriented lines for `process_start` and `process_complete`.

## Event shape (EventBridge)

This stack delivers **S3 `Object Created` events through Amazon EventBridge** (not a direct S3→Lambda subscription), which avoids a CloudFormation circular dependency. Lambda receives an event similar to:

```json
{
  "version": "0",
  "detail-type": "Object Created",
  "source": "aws.s3",
  "time": "2026-04-08T12:00:00Z",
  "region": "us-east-1",
  "resources": ["arn:aws:s3:::your-bucket"],
  "detail": {
    "bucket": { "name": "your-bucket" },
    "object": { "key": "incoming/sample.pdf", "size": 12345 },
    "reason": "PutObject"
  }
}
```

The handler normalizes this into the same internal shape used for classic S3 `Records[]` notifications. Keys may be URL-encoded; the handler decodes them.

For local testing, you can still invoke the function with a classic S3 `Records` payload; see [handler.py](../src/handler.py) (`normalize_s3_events`).

## Viewing results

- **DynamoDB**: Query or scan the metadata table; look up `document_id` or filter by `classification`.
- **CloudWatch Logs**: Log group `/aws/lambda/<function-name>`; search for `"event": "process_complete"`.
- **S3**: Inspect `routed/<category>/` or `exceptions/` for the moved object.

## Failure behavior

If Textract fails or an unexpected error occurs, the document is routed to `exceptions/` and metadata records `processing_status` = `failed` and `classification` = `error` with an `error_message` when available.
