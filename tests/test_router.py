"""Tests for S3 routing key construction."""

import router
from config import AppConfig


def _cfg() -> AppConfig:
    return AppConfig(
        dynamodb_table_name="t",
        documents_bucket_name="my-bucket",
        ingest_prefix="incoming/",
        routed_prefix="routed/",
        exceptions_prefix="exceptions/",
        unclassified_prefix="routed/unclassified/",
        text_preview_max_chars=2000,
        textract_poll_interval_sec=2.0,
        textract_max_wait_sec=120.0,
    )


def test_destination_key_includes_document_id():
    cfg = _cfg()
    key = router.build_destination_key(
        cfg, "referral", "incoming/referral_001.pdf", "doc-uuid-123"
    )
    assert key.startswith("routed/referral/")
    assert "doc-uuid-123" in key
    assert key.endswith("referral_001.pdf")


def test_unclassified_prefix():
    cfg = _cfg()
    key = router.build_destination_key(
        cfg, "unclassified", "incoming/foo.pdf", "id1"
    )
    assert key.startswith("routed/unclassified/")


def test_exception_destination():
    cfg = _cfg()
    key = router.build_destination_key(
        cfg, router.EXCEPTION_DEST, "incoming/bad.pdf", "id2"
    )
    assert key.startswith("exceptions/")


def test_routing_destination_uri():
    cfg = _cfg()
    dest = router.build_routing_destination(cfg, "lab_result")
    assert dest.startswith("s3://my-bucket/")
    assert "lab_result" in dest
