"""Handler event normalization."""

from handler import normalize_s3_events


def test_normalize_eventbridge_payload():
    raw = {
        "version": "0",
        "source": "aws.s3",
        "time": "2026-04-08T12:00:00Z",
        "detail": {
            "bucket": {"name": "b"},
            "object": {"key": "incoming/a.pdf"},
        },
    }
    recs = normalize_s3_events(raw)
    assert len(recs) == 1
    assert recs[0]["s3"]["bucket"]["name"] == "b"
    assert recs[0]["s3"]["object"]["key"] == "incoming/a.pdf"
    assert recs[0]["eventSource"] == "aws:s3"


def test_normalize_classic_records():
    raw = {
        "Records": [
            {
                "eventSource": "aws:s3",
                "s3": {
                    "bucket": {"name": "b2"},
                    "object": {"key": "incoming/x.pdf"},
                },
            }
        ]
    }
    assert len(normalize_s3_events(raw)) == 1
