"""
Environment-driven configuration for the document routing Lambda.

Values are supplied by AWS SAM (template parameters / function environment).
Defaults support local unit tests without requiring a full AWS environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is not None and value.strip() != "":
        return value
    return default


@dataclass(frozen=True)
class AppConfig:
    """Runtime settings for routing, storage, and logging."""

    dynamodb_table_name: str
    # Single bucket for ingest + routed output (prefix-separated) is typical for MVP.
    documents_bucket_name: str
    ingest_prefix: str
    routed_prefix: str
    exceptions_prefix: str
    unclassified_prefix: str
    text_preview_max_chars: int
    textract_poll_interval_sec: float
    textract_max_wait_sec: float

    @classmethod
    def from_environment(cls) -> "AppConfig":
        table = _env("DYNAMODB_TABLE_NAME", "doc-routing-metadata-test")
        bucket = _env("DOCUMENTS_BUCKET_NAME", "local-test-bucket")
        return cls(
            dynamodb_table_name=table or "doc-routing-metadata-test",
            documents_bucket_name=bucket or "local-test-bucket",
            ingest_prefix=_env("INGEST_PREFIX", "incoming/") or "incoming/",
            routed_prefix=_env("ROUTED_PREFIX", "routed/") or "routed/",
            exceptions_prefix=_env("EXCEPTIONS_PREFIX", "exceptions/") or "exceptions/",
            unclassified_prefix=_env("UNCLASSIFIED_PREFIX", "routed/unclassified/")
            or "routed/unclassified/",
            text_preview_max_chars=int(_env("TEXT_PREVIEW_MAX_CHARS", "2000") or "2000"),
            textract_poll_interval_sec=float(
                _env("TEXTRACT_POLL_INTERVAL_SEC", "2.0") or "2.0"
            ),
            textract_max_wait_sec=float(_env("TEXTRACT_MAX_WAIT_SEC", "300") or "300"),
        )
