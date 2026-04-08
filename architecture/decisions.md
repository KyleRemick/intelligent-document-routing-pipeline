# Architecture decisions

## AWS SAM for infrastructure

The stack is defined in `template.yaml` (CloudFormation with the SAM transform). SAM keeps Lambda, S3, DynamoDB, IAM, and EventBridge in one place, which is easy to review in a portfolio and straightforward to deploy with `sam build` and `sam deploy`.

## S3 and EventBridge (not a direct S3→Lambda trigger)

A direct S3 event subscription on a bucket created in the **same** CloudFormation stack as the target Lambda often creates a **circular dependency** (bucket → Lambda → bucket). This template enables **S3 EventBridge notifications** on the bucket and uses an **EventBridge rule** (`Object Created` for that bucket) to invoke Lambda. The rule’s event pattern also matches **`object.key`** with prefix **`incoming/`** so Lambda is not invoked for every object in the bucket (for example under `routed/`). The handler still supports both EventBridge-shaped events and classic S3 `Records[]` payloads.

## Single bucket, prefix-based routing

Incoming files land under `incoming/`. After processing, the object is **copied** to a destination prefix (`routed/<category>/`, `routed/unclassified/`, or `exceptions/`) and **removed** from `incoming/`. One bucket reduces cost and IAM surface for an MVP; isolation by prefix is a common pattern before splitting buckets for compliance or multi-tenant needs.

## Async Textract

`StartDocumentTextDetection` plus polling `GetDocumentTextDetection` supports multi-page PDFs and is the usual integration from Lambda. Synchronous APIs are limited by page count and payload size; async fits batch-style document intake.

## Rule-based classification

Classification uses keyword lists per category with a simple score (number of matched keywords). This is transparent in code and tests—not a substitute for ML or human review. It avoids overstating capabilities while still demonstrating routing logic, DynamoDB metadata, and operational logging.

## DynamoDB for metadata

A single table with `document_id` as the partition key is enough for the demo. Access patterns are write-heavy (`PutItem` per document); on-demand billing matches spiky upload traffic.

## Not a compliance implementation

This project illustrates architecture and automation patterns. It is **not** presented as HIPAA-ready, BAAs, or full PHI protection. Production healthcare workloads require encryption policies, access auditing, retention rules, and organizational controls beyond this repository.

## Security posture (portfolio scope)

- IAM policies scope Lambda to the documents bucket and metadata table; Textract is allowed only for async OCR APIs.
- No secrets in code; configuration comes from environment variables set by SAM.
- S3 default encryption (SSE-S3) is enabled on the bucket in the template.

## Future directions (see `docs/future-improvements.md`)

Higher signal routing (confidence thresholds, Comprehend, human review queues), SNS notifications, idempotency keys, and Step Functions if orchestration grows beyond a single Lambda.
