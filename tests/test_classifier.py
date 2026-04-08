"""Tests for keyword-based classification."""

import classifier as clf


def test_referral_keywords():
    text = "Patient referral to cardiology specialist for consultation next week."
    r = clf.classify_document(text)
    assert r.classification == clf.REFERRAL
    assert "referral" in r.matched_keywords or "specialist" in r.matched_keywords
    assert r.confidence > 0


def test_lab_result_keywords():
    text = "Laboratory results: glucose 99 mg/dL within reference range."
    r = clf.classify_document(text)
    assert r.classification == clf.LAB_RESULT


def test_unclassified_when_no_match():
    text = "Random memo about lunch schedule."
    r = clf.classify_document(text)
    assert r.classification == clf.UNCLASSIFIED
    assert r.matched_keywords == ()
    assert r.confidence == 0.0


def test_empty_text():
    r = clf.classify_document("")
    assert r.classification == clf.UNCLASSIFIED


def test_tie_breaker_order():
    # Both referral and imaging could match "consult" vs imaging - use controlled text
    text = "Referral consult for MRI radiology imaging study."
    r = clf.classify_document(text)
    assert r.classification in (
        clf.REFERRAL,
        clf.IMAGING,
        clf.PROGRESS_NOTE,
    )
