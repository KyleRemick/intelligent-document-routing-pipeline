# Smoke test: upload sample PDF to incoming/ and print verification hints.
# Prerequisites: AWS CLI configured; stack deployed; sample PDF at ../sample_documents/smoke_referral.pdf
# Usage (from repo root): .\scripts\smoke_test.ps1 -BucketName YOUR_BUCKET

param(
    [Parameter(Mandatory = $true)]
    [string] $BucketName,
    [string] $Region = "us-east-1",
    [string] $Key = "incoming/smoke_manual.pdf"
)

$ErrorActionPreference = "Stop"
$pdf = Join-Path $PSScriptRoot "..\sample_documents\smoke_referral.pdf" | Resolve-Path

Write-Host "Uploading $pdf -> s3://$BucketName/$Key"
aws s3 cp $pdf "s3://$BucketName/$Key" --region $Region

Write-Host @"

Next (after ~2–4 minutes for Textract):
  - S3: s3://$BucketName/routed/referral/ (or exceptions/ if OCR fails)
  - DynamoDB: scan metadata table for original_filename = $(Split-Path $Key -Leaf)
  - Logs: aws logs tail /aws/lambda/<function-name> --since 15m --region $Region
"@
