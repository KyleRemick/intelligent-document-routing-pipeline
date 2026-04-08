# Interview prep (quick reference)

Use this as a cheat sheet for technical conversations. Expand with your own experience.

## One-sentence pitch

“I built a serverless document pipeline on AWS: uploads land in S3, EventBridge triggers Lambda, Textract does OCR, rule-based keywords classify the document, metadata goes to DynamoDB, and the file moves to prefix-based destinations—with CloudWatch for traceability.”

## Trigger path (why EventBridge?)

- **What:** S3 sends `Object Created` events to **Amazon EventBridge**; an **EventBridge rule** invokes the Lambda function.
- **Why not S3 → Lambda directly in the same CloudFormation stack?** Wiring a bucket notification to a Lambda in the **same** template often creates a **circular dependency** (bucket needs the function; the function’s policy needs the bucket). EventBridge breaks that cycle while staying in one stack.
- **Filter:** The rule matches the documents bucket and **`incoming/`** key prefix so routed objects do not re-trigger the function.

## OCR (Textract)

- **What:** `StartDocumentTextDetection` (async) plus polling `GetDocumentTextDetection`; LINE blocks are concatenated for classification.
- **Why async:** Fits multi-page PDFs from S3; sync APIs have tighter limits.
- **Ops note:** Jobs can take **minutes** on busy accounts; the stack uses a **300s** Lambda timeout and Textract poll window (see environment variables). If Textract times out, the file routes to **`exceptions/`** and DynamoDB records `failed`.

## Classification (not ML)

- **What:** Keyword lists per category; score = number of matched keywords; tie-break order is fixed in code.
- **Honesty:** This is **transparent rules**, not Comprehend or custom ML—good for interviews if you say so upfront.

## Observability and metadata

- **CloudWatch:** JSON-style log lines (`process_start`, `process_complete`, `textract_failed`).
- **DynamoDB:** One item per document with classification, preview text, routing destination, status, errors.

## Security and compliance (boundaries)

- **What you did:** Least-privilege IAM via SAM policies, SSE-S3 on the bucket, no secrets in code.
- **What this repo is not:** A HIPAA or regulated production design—no BAA, no full PHI program—say that clearly if asked.

## Likely follow-up questions

| Question | Direction |
|----------|-----------|
| **Duplicate events?** | Mention idempotency (hash of bucket+key+version) or DLQ as future work. |
| **Wrong classification?** | Keyword limits; future: Comprehend, human review queue, confidence thresholds. |
| **Cost?** | Textract per page; Lambda/DynamoDB on-demand; S3 storage. |
| **Step Functions?** | Only if orchestration grows; single Lambda is enough for this MVP. |
