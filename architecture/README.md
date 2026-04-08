# Architecture notes

The root [README.md](../README.md) includes a Mermaid diagram of the end-to-end flow.

Conceptual path: **S3 (incoming/) → EventBridge → Lambda → Textract → classifier → DynamoDB → S3 (routed/ or exceptions/)** with **CloudWatch Logs** for traceability.

EventBridge is used instead of wiring S3 directly to Lambda in the same template, which avoids a CloudFormation circular dependency between the bucket and the function while keeping a single stack.
