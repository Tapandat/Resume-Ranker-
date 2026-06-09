"""
FastAPI — Resume Ranker API v2.2
=================================
POST /api/rank      → Score + skill-extract + project-extract + skill-gap resumes
GET  /api/health    → Health check
GET  /api/roles     → Available ML roles
POST /api/retrain   → Invalidate classifier cache
"""

from __future__ import annotations

import logging
import uuid
from collections import Counter
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.core.parser import parse_resume_batch
from backend.core.scoring_engine import score_resumes, ResumeScore
from backend.core.classifier import (
    RoleClassifier, generate_synthetic_jd,
    skill_gap_for_role, ROLE_CORPUS,
)
from backend.api.auth import router as auth_router
from backend.api.admin import router as admin_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Resume Ranker API",
    version="2.2.0",
    description="Hybrid NLP resume ranking with project extraction and skill-gap analysis.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)


# ── Pydantic models ────────────────────────────────────────────────────────────
class ProjectEntry(BaseModel):
    title:            str
    description:      str
    skills_mentioned: list[str]


class SkillGap(BaseModel):
    role:            str
    expected_skills: list[str]
    present:         list[str]
    missing:         list[str]
    coverage_pct:    float


class CandidateResult(BaseModel):
    rank:                int
    candidate_id:        str
    filename:            str
    final_score:         float
    semantic_score:      float
    keyword_score:       float
    experience_score:    float
    years_of_experience: int
    predicted_role:      Optional[str]
    role_confidence:     Optional[float]
    matched_keywords:    list[str]
    skills:              dict[str, list[str]]
    all_skills:          list[str]
    projects:            list[ProjectEntry]       # NEW
    skill_gap:           Optional[SkillGap]       # NEW
    word_count:          int
    explanation:         str


class RankResponse(BaseModel):
    job_title:     Optional[str]
    jd_mode:       str
    detected_role: Optional[str]
    total_resumes: int
    ranked:        list[CandidateResult]


# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.2.0"}


@app.get("/api/roles")
def get_roles():
    return {"roles": sorted(ROLE_CORPUS.keys())}


@app.post("/api/retrain")
def retrain():
    RoleClassifier.reset()
    return {"status": "cache cleared — classifier retrains on next /api/rank call"}


@app.post("/api/rank", response_model=RankResponse)
async def rank_resumes(
    files:          list[UploadFile] = File(...),
    jd_text:        Optional[str]    = Form(None),
    job_title:      Optional[str]    = Form(None),
    required_years: int              = Form(3),
    anonymize:      bool             = Form(True),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    # 1. Parse + skill + project extract
    raw_files = [(await f.read(), f.filename or "unknown") for f in files]
    parsed    = parse_resume_batch(raw_files, anonymize=anonymize)
    valid     = [p for p in parsed if not p["parse_error"] and p["clean_text"]]

    if not valid:
        raise HTTPException(status_code=422, detail="Could not extract text from any file.")

    # 2. JD mode
    jd_mode       = "provided"
    detected_role: Optional[str] = None
    role_preds:    dict[str, dict] = {}

    if not jd_text or not jd_text.strip():
        jd_mode    = "classifier"
        classifier = RoleClassifier()
        for p in valid:
            pred = classifier.predict(p["clean_text"])
            role_preds[p["filename"]] = pred
        top_role      = Counter(v["predicted_role"] for v in role_preds.values()).most_common(1)[0][0]
        detected_role = top_role
        jd_text       = generate_synthetic_jd(top_role)
        logger.info("No JD. Predicted role: %s. Synthetic JD generated.", top_role)

    # 3. Score
    resume_inputs = [
        {"id": str(uuid.uuid4()), "text": p["clean_text"], "filename": p["filename"]}
        for p in valid
    ]
    scored: list[ResumeScore] = score_resumes(
        jd_text=jd_text,
        resumes=[{"id": r["id"], "text": r["text"]} for r in resume_inputs],
        required_years=required_years,
    )

    id_to_filename     = {r["id"]: r["filename"] for r in resume_inputs}
    filename_to_parsed = {p["filename"]: p for p in valid}

    # 4. Build response
    ranked_results = []
    for rank, score in enumerate(scored, start=1):
        filename   = id_to_filename.get(score.candidate_id, "unknown")
        pred_info  = role_preds.get(filename, {})
        parsed_doc = filename_to_parsed.get(filename, {})

        # Determine role for skill gap (predicted or job_title if provided)
        gap_role = (
            pred_info.get("predicted_role")
            or job_title
            or detected_role
        )
        skill_gap = None
        if gap_role and gap_role in ROLE_CORPUS:
            skill_gap = skill_gap_for_role(
                role=gap_role,
                candidate_skills=parsed_doc.get("all_skills", []),
            )

        ranked_results.append(CandidateResult(
            rank                = rank,
            candidate_id        = score.candidate_id,
            filename            = filename,
            final_score         = score.final_score,
            semantic_score      = score.semantic_score,
            keyword_score       = score.keyword_score,
            experience_score    = score.experience_score,
            years_of_experience = score.years_of_experience,
            predicted_role      = pred_info.get("predicted_role", job_title),
            role_confidence     = round(pred_info["confidence"], 3) if pred_info.get("confidence") else None,
            matched_keywords    = score.matched_keywords[:20],
            skills              = parsed_doc.get("skills", {}),
            all_skills          = parsed_doc.get("all_skills", []),
            projects            = [ProjectEntry(**p) for p in parsed_doc.get("projects", [])],
            skill_gap           = SkillGap(**skill_gap) if skill_gap else None,
            word_count          = parsed_doc.get("word_count", 0),
            explanation         = score.explanation,
        ))

    return RankResponse(
        job_title     = job_title,
        jd_mode       = jd_mode,
        detected_role = detected_role,
        total_resumes = len(valid),
        ranked        = ranked_results,
    )
