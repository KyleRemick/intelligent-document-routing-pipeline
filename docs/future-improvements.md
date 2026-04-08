# Future improvements

## Confidence and thresholds

Expose a minimum confidence score before accepting a classification; route low-confidence cases to a **manual review** prefix or queue.

## Notifications

Publish processing outcomes to **SNS** (success, failure, or exception) for operations or downstream systems.

## EventBridge

Emit domain events (e.g. `DocumentClassified`, `DocumentRoutingFailed`) for analytics, auditing, or decoupled consumers.

## Step Functions

If orchestration grows (multiple OCR passes, human-in-the-loop, branching on file type), consider **Step Functions** to coordinate Lambdas and manage retries. For the current single-pass flow, Step Functions is optional complexity.

## ML / NLP classification

Replace or augment keyword rules with **Amazon Comprehend** custom classification, or a hosted model, for higher accuracy—especially when layout and vocabulary vary.

## Idempotency and deduplication

Use deterministic **document_id** (hash of bucket + key + version) or S3 object version IDs to avoid duplicate processing when events retry.

## Dead-letter handling

For poison messages or repeated failures, send payloads to a **DLQ** (SQS) or a dedicated failure bucket with alerting.

## Security and compliance hardening

For regulated workloads: KMS keys, bucket policies, VPC endpoints, audit trails, data retention, and formal access reviews—beyond this portfolio scope.
