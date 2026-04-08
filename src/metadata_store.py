"""
Persist processing metadata to DynamoDB (single-table MVP).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import ClientError

from config import AppConfig


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def put_metadata(
    config: AppConfig,
    item: dict[str, Any],
    dynamodb_resource: Any | None = None,
) -> None:
    """Write one item to the metadata table. Raises on client errors."""
    table_name = config.dynamodb_table_name
    resource = dynamodb_resource or boto3.resource("dynamodb")
    table = resource.Table(table_name)
    try:
        table.put_item(Item=item)
    except ClientError as e:
        raise RuntimeError(f"DynamoDB put_item failed: {e}") from e


def build_metadata_item(
    *,
    document_id: str,
    original_filename: str,
    upload_timestamp: str,
    source_bucket: str,
    source_key: str,
    extracted_text_preview: str,
    classification: str,
    matched_keywords: list[str],
    routing_destination: str,
    processing_status: str,
    destination_key: str,
    confidence: float | None = None,
    error_message: str | None = None,
) -> dict[str, Any]:
    """Shape the DynamoDB item (all values JSON-serializable for boto3)."""
    item: dict[str, Any] = {
        "document_id": document_id,
        "original_filename": original_filename,
        "upload_timestamp": upload_timestamp,
        "processing_timestamp": _utc_iso(),
        "source_bucket": source_bucket,
        "source_key": source_key,
        "extracted_text_preview": extracted_text_preview,
        "classification": classification,
        "matched_keywords": matched_keywords,
        "routing_destination": routing_destination,
        "destination_key": destination_key,
        "processing_status": processing_status,
        "error_message": error_message or "",
    }
    if confidence is not None:
        item["confidence"] = Decimal(str(confidence))
    return item
