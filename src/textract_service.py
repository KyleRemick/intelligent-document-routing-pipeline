"""
Amazon Textract async document text detection for S3 objects.

Uses StartDocumentTextDetection and polls GetDocumentTextDetection until the job
completes or times out. LINE blocks are concatenated in reading order.
"""

from __future__ import annotations

import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

from config import AppConfig


class TextractError(Exception):
    """Raised when OCR fails or times out."""


def _get_textract_client() -> Any:
    return boto3.client("textract")


def extract_text_from_s3(
    bucket: str,
    key: str,
    config: AppConfig,
    textract_client: Any | None = None,
) -> str:
    """
    Run async text detection on an S3 object; return normalized plain text.

    Raises TextractError on failure or timeout.
    """
    client = textract_client or _get_textract_client()
    try:
        start = client.start_document_text_detection(
            DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}}
        )
    except ClientError as e:
        raise TextractError(f"StartDocumentTextDetection failed: {e}") from e

    job_id = start.get("JobId")
    if not job_id:
        raise TextractError("Textract did not return JobId")

    deadline = time.monotonic() + config.textract_max_wait_sec
    next_token: str | None = None

    while time.monotonic() < deadline:
        kwargs: dict[str, Any] = {"JobId": job_id}
        if next_token:
            kwargs["NextToken"] = next_token

        try:
            resp = client.get_document_text_detection(**kwargs)
        except ClientError as e:
            raise TextractError(f"GetDocumentTextDetection failed: {e}") from e

        status = resp.get("JobStatus")
        if status == "SUCCEEDED":
            lines: list[str] = []
            for block in resp.get("Blocks", []) or []:
                if block.get("BlockType") == "LINE" and block.get("Text"):
                    lines.append(block["Text"])
            # Paginate if needed
            next_token = resp.get("NextToken")
            while next_token:
                resp = client.get_document_text_detection(
                    JobId=job_id, NextToken=next_token
                )
                for block in resp.get("Blocks", []) or []:
                    if block.get("BlockType") == "LINE" and block.get("Text"):
                        lines.append(block["Text"])
                next_token = resp.get("NextToken")
            return "\n".join(lines)

        if status == "FAILED":
            err = resp.get("StatusMessage", "unknown")
            raise TextractError(f"Textract job failed: {err}")

        time.sleep(config.textract_poll_interval_sec)

    raise TextractError(
        f"Textract job {job_id} did not complete within {config.textract_max_wait_sec}s"
    )
