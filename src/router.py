"""
Build S3 object keys for routed documents and processing exceptions.

Destination layout (single bucket):
  incoming/              — uploads (ingest)
  routed/<category>/     — successful routing by classification
  routed/unclassified/   — no keyword match
  exceptions/            — Textract or pipeline failures
"""

from __future__ import annotations

import posixpath
from typing import Final

import classifier
from config import AppConfig

EXCEPTION_DEST: Final = "__exception__"


def _basename_from_key(key: str) -> str:
    base = key.rstrip("/").split("/")[-1]
    return base or "document"


def category_to_prefix(config: AppConfig, category: str) -> str:
    """Return the S3 prefix (with trailing slash) for a classification label."""
    if category == classifier.UNCLASSIFIED:
        return config.unclassified_prefix
    if category == EXCEPTION_DEST:
        return config.exceptions_prefix
    # Known routed categories share routed/<label>/
    sub = category.strip().lower()
    return posixpath.join(config.routed_prefix.rstrip("/") + "/", sub) + "/"


def build_routing_destination(config: AppConfig, category: str) -> str:
    """Human-readable destination for metadata (prefix + category)."""
    prefix = category_to_prefix(config, category)
    return f"s3://{config.documents_bucket_name}/{prefix}"


def build_destination_key(
    config: AppConfig,
    category: str,
    source_key: str,
    document_id: str,
) -> str:
    """
    Build the full destination key under the bucket.

    Uses document_id + original basename to reduce overwrites when the same
    filename is uploaded more than once.
    """
    prefix = category_to_prefix(config, category)
    basename = _basename_from_key(source_key)
    safe_doc = document_id.replace("/", "_")[:36]
    filename = f"{safe_doc}_{basename}"
    return posixpath.join(prefix.rstrip("/"), filename)
