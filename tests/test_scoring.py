"""
Tests — Scoring Engine & Parser
================================
Run with:  pytest tests/ -v
"""

import pytest
from backend.core.scoring_engine import (
    extract_years_of_experience,
    experience_score,
    scale_to_10,
    score_resumes,
    find_matched_keywords,
)
from backend.core.parser import normalize_text, anonymize_text
from backend.core.classifier import RoleClassifier, generate_synthetic_jd


# ── Experience Extractor ──────────────────────────────────────────────────────
@pytest.mark.parametrize("text,expected", [
    ("5 years of experience in Python",   5),
    ("10+ years experience",              10),
    ("I have two years experience",       2),
    ("3-5 years of relevant experience",  3),
    ("No experience mentioned",           0),
    ("Experience of 7 years",             7),
])
def test_extract_years(text, expected):
    assert extract_years_of_experience(text) == expected


# ── Experience Score ──────────────────────────────────────────────────────────
def test_experience_score_ranges():
    assert 0.0 <= experience_score(0, 3) <= 1.0
    assert 0.0 <= experience_score(3, 3) <= 1.0
    assert 0.0 <= experience_score(10, 3) <= 1.0
    assert experience_score(3, 3) < experience_score(6, 3), "More exp should score higher"


# ── Scale to 10 ───────────────────────────────────────────────────────────────
def test_scale_to_10():
    assert scale_to_10(0.0) == 1.0
    assert scale_to_10(1.0) == 10.0
    assert 1.0 <= scale_to_10(0.5) <= 10.0


# ── Keyword Finder ────────────────────────────────────────────────────────────
def test_find_matched_keywords():
    text = "experienced python developer with aws and machine learning skills"
    kws  = ["python", "aws", "java", "machine learning"]
    matched = find_matched_keywords(text, kws)
    assert "python" in matched
    assert "aws" in matched
    assert "java" not in matched


# ── Normaliser ────────────────────────────────────────────────────────────────
def test_normalize_removes_bullets():
    raw = "• Python\n• Machine Learning\n▸ AWS"
    out = normalize_text(raw)
    assert "•" not in out
    assert "▸" not in out
    assert "python" in out


def test_normalize_lowercases():
    assert normalize_text("JAVA Developer") == "java developer"


# ── Anonymiser ────────────────────────────────────────────────────────────────
def test_anonymize_email():
    text = "Contact me at john.doe@example.com for more info"
    out  = anonymize_text(text)
    assert "@" not in out
    assert "[EMAIL]" in out


def test_anonymize_phone():
    text = "Call me at +91-9876543210"
    out  = anonymize_text(text)
    assert "[PHONE]" in out


# ── Classifier ────────────────────────────────────────────────────────────────
def test_classifier_predicts_role():
    clf  = RoleClassifier()
    text = "machine learning tensorflow pytorch deep learning nlp computer vision"
    pred = clf.predict(text)
    assert "predicted_role" in pred
    assert 0.0 <= pred["confidence"] <= 1.0
    assert len(pred["top3"]) == 3


def test_generate_synthetic_jd():
    jd = generate_synthetic_jd("Data Scientist")
    assert "data scientist" in jd.lower()
    assert len(jd) > 50


# ── Full Scoring Pipeline ─────────────────────────────────────────────────────
def test_score_resumes_ranking():
    jd = "We need a Python developer with 5 years of experience in machine learning and AWS."
    resumes = [
        {"id": "r1", "text": "Python developer with 6 years of experience in machine learning and AWS deployments."},
        {"id": "r2", "text": "Java developer with 2 years in mobile app development."},
        {"id": "r3", "text": "Senior machine learning engineer with 8 years, Python, AWS, deep learning."},
    ]
    results = score_resumes(jd, resumes, required_years=5)
    assert len(results) == 3
    # Best match should be r3 or r1 (not r2)
    assert results[0].candidate_id in {"r1", "r3"}
    # Scores should be in descending order
    scores = [r.final_score for r in results]
    assert scores == sorted(scores, reverse=True)
    # All scores in [1, 10]
    for r in results:
        assert 1.0 <= r.final_score <= 10.0


def test_empty_resumes_returns_empty():
    results = score_resumes("some jd", [], required_years=3)
    assert results == []
