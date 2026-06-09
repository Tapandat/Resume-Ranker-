"""
Hybrid Scoring Engine
=====================
Combines semantic embeddings + TF-IDF keyword match + Experience factor.

Score = (0.50 × Semantic) + (0.30 × Keyword) + (0.20 × Experience)

Semantic backend — tried in order:
  1. SBERT  all-mpnet-base-v2   (best quality, needs sentence-transformers)
  2. TF-IDF cosine on full text (instant fallback, no extra deps)
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ── Semantic backend ──────────────────────────────────────────────────────────
_SBERT_MODEL = None
_SBERT_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    _SBERT_AVAILABLE = True
    logger.info("sentence-transformers available — will use SBERT for semantics.")
except ImportError:
    logger.warning(
        "sentence-transformers not installed. "
        "Falling back to TF-IDF cosine similarity for semantic scoring. "
        "Install sentence-transformers for higher accuracy."
    )


def get_sbert_model() -> "SentenceTransformer":
    global _SBERT_MODEL
    if _SBERT_MODEL is None:
        logger.info("Loading SBERT model: all-mpnet-base-v2 …")
        _SBERT_MODEL = SentenceTransformer("all-mpnet-base-v2")
    return _SBERT_MODEL


# ── Data class ────────────────────────────────────────────────────────────────
@dataclass
class ResumeScore:
    candidate_id:     str
    raw_text:         str
    semantic_score:   float = 0.0
    keyword_score:    float = 0.0
    experience_score: float = 0.0
    final_score:      float = 0.0
    matched_keywords: list[str] = field(default_factory=list)
    years_of_experience: int    = 0
    predicted_role:   Optional[str] = None
    explanation:      str = ""


# ── Experience extraction ─────────────────────────────────────────────────────
_YEAR_PATTERNS = [
    re.compile(r"(\d+)\+?\s*(?:–|-|to)?\s*\d*\s*years?\s+(?:of\s+)?experience", re.I),
    re.compile(r"(\d+)\+?\s*years?\s+(?:of\s+)?(?:relevant\s+)?(?:work\s+)?experience", re.I),
    re.compile(r"experience\s+of\s+(\d+)\+?\s*years?", re.I),
    re.compile(r"(\d+)\+?\s*yrs?", re.I),
    re.compile(r"(\d+)\+?\s*years?", re.I),   # bare "10+ years" or "5 years"
]
_WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}


def extract_years_of_experience(text: str) -> int:
    found = []
    for pat in _YEAR_PATTERNS:
        for m in pat.finditer(text):
            try:
                found.append(int(m.group(1)))
            except (IndexError, ValueError):
                pass
    for word, num in _WORD_TO_NUM.items():
        if re.search(rf"\b{word}\b\s*years?", text, re.I):
            found.append(num)
    return max(found, default=0)


def experience_score(years: int, required_years: int = 3) -> float:
    if years <= 0:
        return 0.20
    if years < required_years:
        return 0.20 + (years / required_years) * 0.60
    bonus = min((years - required_years) / max(required_years, 1), 1.0)
    return 0.80 + bonus * 0.20


# ── Keyword scoring ───────────────────────────────────────────────────────────
def extract_keywords_tfidf(
    jd_text: str,
    resume_texts: list[str],
    top_n: int = 30,
) -> tuple[list[str], np.ndarray]:
    corpus    = [jd_text] + resume_texts
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        stop_words="english",
        sublinear_tf=True,
    )
    mat = vectorizer.fit_transform(corpus)
    jd_vec      = mat[0]
    resume_vecs = mat[1:]

    feature_names = vectorizer.get_feature_names_out()
    jd_scores     = jd_vec.toarray().flatten()
    top_idx       = jd_scores.argsort()[-top_n:][::-1]
    jd_keywords   = [feature_names[i] for i in top_idx if jd_scores[i] > 0]

    keyword_sims = cosine_similarity(jd_vec, resume_vecs).flatten()
    return jd_keywords, keyword_sims


def find_matched_keywords(resume_text: str, keywords: list[str]) -> list[str]:
    lower = resume_text.lower()
    return [kw for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", lower)]


# ── Semantic scoring ──────────────────────────────────────────────────────────
def compute_semantic_scores(jd_text: str, resume_texts: list[str]) -> np.ndarray:
    """SBERT if available, else TF-IDF cosine on full text."""
    if _SBERT_AVAILABLE:
        model   = get_sbert_model()
        texts   = [jd_text] + resume_texts
        embs    = model.encode(texts, batch_size=16, show_progress_bar=False, normalize_embeddings=True)
        return np.dot(embs[1:], embs[0])
    else:
        # TF-IDF fallback — fast, no GPU needed
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=10000,
            sublinear_tf=True,
        )
        mat  = vectorizer.fit_transform([jd_text] + resume_texts)
        sims = cosine_similarity(mat[0], mat[1:]).flatten()
        logger.debug("Semantic (TF-IDF fallback) scores: %s", sims)
        return sims


# ── Main scoring API ──────────────────────────────────────────────────────────
WEIGHTS = {"semantic": 0.50, "keyword": 0.30, "experience": 0.20}


def scale_to_10(value: float) -> float:
    return round(1.0 + float(np.clip(value, 0, 1)) * 9.0, 2)


def score_resumes(
    jd_text:       str,
    resumes:       list[dict],
    required_years: int  = 3,
    top_keywords:   int  = 30,
    weights:        Optional[dict] = None,
) -> list[ResumeScore]:
    if not resumes:
        return []

    w = weights or WEIGHTS
    assert abs(sum(w.values()) - 1.0) < 1e-6, "Weights must sum to 1.0"

    texts = [r["text"] for r in resumes]

    logger.info("Computing semantic scores for %d resumes …", len(texts))
    semantic_sims = compute_semantic_scores(jd_text, texts)

    logger.info("Computing TF-IDF keyword scores …")
    jd_keywords, keyword_sims = extract_keywords_tfidf(jd_text, texts, top_n=top_keywords)

    results: list[ResumeScore] = []
    for i, resume in enumerate(resumes):
        years  = extract_years_of_experience(resume["text"])
        exp_sc = experience_score(years, required_years)

        raw_score = (
            w["semantic"]   * float(np.clip(semantic_sims[i], 0, 1))
            + w["keyword"]  * float(np.clip(keyword_sims[i],  0, 1))
            + w["experience"] * exp_sc
        )
        final   = scale_to_10(raw_score)
        matched = find_matched_keywords(resume["text"], jd_keywords)

        results.append(ResumeScore(
            candidate_id     = resume["id"],
            raw_text         = resume["text"],
            semantic_score   = round(float(semantic_sims[i]), 4),
            keyword_score    = round(float(keyword_sims[i]),  4),
            experience_score = round(exp_sc, 4),
            final_score      = final,
            matched_keywords = matched,
            years_of_experience = years,
            explanation      = _build_explanation(
                semantic=float(semantic_sims[i]),
                keyword=float(keyword_sims[i]),
                exp_sc=exp_sc,
                years=years,
                matched=matched,
                final=final,
                backend="SBERT" if _SBERT_AVAILABLE else "TF-IDF fallback",
            ),
        ))

    results.sort(key=lambda r: r.final_score, reverse=True)
    logger.info("Scoring complete. Top: %.2f", results[0].final_score if results else 0)
    return results


def _build_explanation(
    semantic: float, keyword: float, exp_sc: float,
    years: int, matched: list[str], final: float, backend: str = "SBERT",
) -> str:
    return "\n".join([
        f"Final Score: {final}/10",
        f"• Semantic Alignment  : {semantic:.1%}  ({backend} cosine similarity)",
        f"• Keyword Match       : {keyword:.1%}  (TF-IDF bigram overlap)",
        f"• Experience Factor   : {exp_sc:.1%}  ({years} yrs detected)",
        f"• Matched Keywords    : {', '.join(matched[:10]) or 'None'}",
    ])
