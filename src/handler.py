"""
AWS Lambda entry point: S3 event -> Textract -> classify -> DynamoDB -> route.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any
from urllib.parse import unquote_plus

import boto3
from botocore.exceptions import ClientError

import classifier
from config import AppConfig
from logger_util import get_logger, log_json, truncate_for_log
from metadata_store import build_metadata_item, put_metadata
from router import EXCEPTION_DEST, build_destination_key, build_routing_destination
from textract_service import TextractError, extract_text_from_s3

LOGGER = get_logger()
S3 = boto3.client("s3")


def _should_skip_key(key: str, config: AppConfig) -> bool:
    if not key or key.endswith("/"):
        return True
    ingest = config.ingest_prefix
    if not key.startswith(ingest):
        return True
    # Avoid reprocessing outputs if notification config is mis-scoped.
    for prefix in (config.routed_prefix, config.exceptions_prefix):
        if key.startswith(prefix):
            return True
    return False


def _parse_event_time(record: dict[str, Any]) -> str:
    return str(record.get("eventTime") or "")


def normalize_s3_events(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Accept direct S3 event notifications (Records[]) or S3 events delivered via
    EventBridge (source aws.s3, detail-type Object Created).
    """
    records = raw.get("Records")
    if records:
        return [r for r in records if r.get("eventSource") == "aws:s3"]
    if raw.get("source") == "aws.s3" and isinstance(raw.get("detail"), dict):
        d = raw["detail"]
        bucket = d.get("bucket", {}).get("name")
        key = d.get("object", {}).get("key")
        if not bucket or not key:
            return []
        return [
            {
                "eventSource": "aws:s3",
                "eventTime": str(raw.get("time") or ""),
                "s3": {
                    "bucket": {"name": bucket},
                    "object": {"key": key},
                },
            }
        ]
    return []


def process_s3_record(record: dict[str, Any], config: AppConfig) -> None:
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]
    # S3 notifications URL-encode keys; boto3 event may contain + or %20.
    key = unquote_plus(key)

    if _should_skip_key(key, config):
        log_json(
            LOGGER,
            logging.INFO,
            "skip_object",
            {"bucket": bucket, "key": key, "reason": "ingest_filter"},
        )
        return

    upload_ts = _parse_event_time(record)
    original_filename = key.rstrip("/").split("/")[-1]
    document_id = str(uuid.uuid4())

    log_json(
        LOGGER,
        logging.INFO,
        "process_start",
        {
            "document_id": document_id,
            "bucket": bucket,
            "key": key,
            "original_filename": original_filename,
        },
    )

    extracted_text = ""
    error_message: str | None = None
    classification = classifier.UNCLASSIFIED
    matched_keywords: tuple[str, ...] = ()
    confidence = 0.0
    processing_status = "completed"
    route_category = classifier.UNCLASSIFIED

    try:
        extracted_text = extract_text_from_s3(bucket, key, config)
        result = classifier.classify_document(extracted_text)
        classification = result.classification
        matched_keywords = result.matched_keywords
        confidence = result.confidence
        route_category = classification
    except TextractError as e:
        error_message = str(e)
        processing_status = "failed"
        route_category = EXCEPTION_DEST
        log_json(
            LOGGER,
            logging.ERROR,
            "textract_failed",
            {"document_id": document_id, "error": error_message},
        )
    except Exception as e:  # noqa: BLE001 — log and route to exceptions
        error_message = str(e)
        processing_status = "failed"
        route_category = EXCEPTION_DEST
        LOGGER.exception("processing_failed")

    preview = extracted_text[: config.text_preview_max_chars]

    if processing_status == "completed":
        dest_key = build_destination_key(
            config, route_category, key, document_id
        )
        routing_destination = build_routing_destination(config, route_category)
    else:
        dest_key = build_destination_key(
            config, EXCEPTION_DEST, key, document_id
        )
        routing_destination = build_routing_destination(config, EXCEPTION_DEST)

    item = build_metadata_item(
        document_id=document_id,
        original_filename=original_filename,
        upload_timestamp=upload_ts,
        source_bucket=bucket,
        source_key=key,
        extracted_text_preview=preview,
        classification=classification if processing_status == "completed" else "error",
        matched_keywords=list(matched_keywords),
        routing_destination=routing_destination,
        processing_status=processing_status,
        destination_key=dest_key,
        confidence=confidence if processing_status == "completed" else None,
        error_message=error_message,
    )

    try:
        put_metadata(config, item)
    except RuntimeError as e:
        log_json(
            LOGGER,
            logging.ERROR,
            "metadata_write_failed",
            {"document_id": document_id, "error": str(e)},
        )

    # Copy then delete from ingest (move) so the same key can be re-uploaded later.
    try:
        copy_source = {"Bucket": bucket, "Key": key}
        S3.copy_object(
            Bucket=bucket,
            Key=dest_key,
            CopySource=copy_source,
            ServerSideEncryption="AES256",
        )
        S3.delete_object(Bucket=bucket, Key=key)
    except ClientError as e:
        log_json(
            LOGGER,
            logging.ERROR,
            "s3_route_failed",
            {"document_id": document_id, "dest_key": dest_key, "error": str(e)},
        )
        raise

    log_json(
        LOGGER,
        logging.INFO,
        "process_complete",
        {
            "document_id": document_id,
            "classification": classification,
            "route_category": route_category,
            "confidence": confidence,
            "processing_status": processing_status,
            "destination_key": dest_key,
            "text_preview": truncate_for_log(extracted_text, 500),
        },
    )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    config = AppConfig.from_environment()
    records = normalize_s3_events(event)
    for record in records:
        process_s3_record(record, config)
    return {"statusCode": 200, "body": json.dumps({"processed": len(records)})}
