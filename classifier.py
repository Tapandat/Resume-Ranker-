"""
Role Classifier — "No JD" Branch
==================================
Two-stage classifier for predicting candidate role when no JD supplied.

  Stage 1 (fast): TF-IDF + Random Forest — trained on bundled corpus + synthetic data.
  Stage 2 (quality): SBERT embeddings → cosine similarity against role prototypes.

Train on the bundled dataset (resume_dataset.csv) when available; falls back
to keyword corpus augmentation if CSV not found.
"""

from __future__ import annotations

import logging
import pickle
import re
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

# ── Standard role corpus ──────────────────────────────────────────────────────
ROLE_CORPUS: dict[str, str] = {
    "Data Scientist": (
        "machine learning deep learning neural networks tensorflow pytorch scikit-learn "
        "pandas numpy statistics regression classification clustering nlp computer vision "
        "data analysis exploratory data a/b testing feature engineering model deployment "
        "jupyter python r statistical modeling hypothesis testing data visualization"
    ),
    "Machine Learning Engineer": (
        "mlops model serving kubernetes docker mlflow airflow spark feature store "
        "real-time inference pipeline automation tensorflow serving torchserve "
        "distributed training model optimisation quantisation onnx cuda gpu "
        "model monitoring drift detection retraining ci/cd for ml"
    ),
    "Software Engineer": (
        "software development algorithms data structures system design rest api microservices "
        "java python c++ go backend frontend full-stack ci/cd agile scrum unit testing "
        "code review version control git distributed systems scalability object oriented "
        "design patterns solid principles test driven development"
    ),
    "Frontend Developer": (
        "react angular vue javascript typescript html css sass webpack redux next.js "
        "responsive design ui ux component library accessibility performance optimisation "
        "browser compatibility figma adobe xd tailwind graphql rest api "
        "cross-browser testing web performance core web vitals"
    ),
    "DevOps Engineer": (
        "devops ci/cd jenkins github actions gitlab terraform ansible kubernetes helm "
        "docker aws azure gcp infrastructure as code monitoring prometheus grafana elk "
        "sre incident management on-call reliability linux bash scripting "
        "service mesh istio vault secrets management"
    ),
    "Data Engineer": (
        "data pipeline etl spark kafka airflow dbt snowflake bigquery redshift databricks "
        "sql data warehouse data lake hadoop flink streaming batch processing "
        "data modelling schema design data quality orchestration python scala "
        "dimensional modelling star schema slowly changing dimensions"
    ),
    "HR Manager": (
        "human resources talent acquisition recruitment onboarding payroll performance "
        "management employee relations labour law compliance training development "
        "succession planning hris workday bamboohr engagement retention "
        "organizational development change management diversity inclusion"
    ),
    "Finance Analyst": (
        "financial analysis forecasting budgeting p&l balance sheet cash flow dcf valuation "
        "excel vba power bi tableau accounting gaap ifrs variance analysis cost reduction "
        "risk management investment portfolio mergers acquisitions "
        "financial modeling scenario planning kpi reporting"
    ),
    "Product Manager": (
        "product roadmap stakeholder management agile scrum user stories kpis okrs "
        "go-to-market competitive analysis user research wireframing jira confluence "
        "prioritisation launch strategy product analytics growth "
        "product-market fit feature definition sprint planning backlog grooming"
    ),
    "Cybersecurity Analyst": (
        "penetration testing siem soc vulnerability assessment incident response "
        "firewall ids ips wireshark nessus metasploit owasp iso 27001 gdpr "
        "threat modelling zero trust endpoint security "
        "forensics malware analysis threat intelligence red team blue team"
    ),
    "Backend Developer": (
        "backend api rest graphql node.js python django flask fastapi java spring "
        "database postgresql mysql mongodb redis caching authentication authorization "
        "jwt oauth2 microservices message queue rabbitmq kafka "
        "server performance load balancing horizontal scaling"
    ),
    "Cloud Architect": (
        "cloud architecture aws azure gcp solution design infrastructure "
        "multi-cloud hybrid cloud serverless lambda functions containers "
        "cost optimisation well-architected framework security compliance "
        "network vpc route53 cdn load balancer disaster recovery"
    ),
}

DATASET_PATH = Path(__file__).parent.parent.parent / "data" / "resume_dataset.csv"
MODEL_CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "role_classifier_v2.pkl"


# ── Dataset-aware training ────────────────────────────────────────────────────
def _load_dataset_texts() -> tuple[list[str], list[str]]:
    """Load texts and labels from CSV dataset if available."""
    if not DATASET_PATH.exists():
        logger.info("Dataset not found at %s — using corpus augmentation only.", DATASET_PATH)
        return [], []

    try:
        import pandas as pd
        df = pd.read_csv(DATASET_PATH)
        # Expected columns: resume_text, category
        if "resume_text" in df.columns and "category" in df.columns:
            df = df.dropna(subset=["resume_text", "category"])
            # Only keep roles we recognise
            known_roles = set(ROLE_CORPUS.keys())
            df = df[df["category"].isin(known_roles)]
            if len(df) > 0:
                logger.info("Loaded %d samples from dataset (%d roles).", len(df), df["category"].nunique())
                return df["resume_text"].tolist(), df["category"].tolist()
        logger.warning("Dataset missing expected columns (resume_text, category).")
    except Exception as exc:
        logger.warning("Failed to load dataset: %s", exc)
    return [], []


def _build_pipeline() -> tuple[Pipeline, LabelEncoder]:
    corpus_texts: list[str] = []
    corpus_labels: list[str] = []

    # 1. Real dataset (high weight — repeat 3× to emphasise)
    ds_texts, ds_labels = _load_dataset_texts()
    for t, l in zip(ds_texts, ds_labels):
        corpus_texts.extend([t] * 3)
        corpus_labels.extend([l] * 3)

    # 2. Keyword corpus augmentation (always included)
    rng = np.random.default_rng(42)
    for label, text in ROLE_CORPUS.items():
        words = text.split()
        for _ in range(10):
            size = max(len(words) // 2, min(len(words), 30))
            sampled = rng.choice(words, size=size, replace=False)
            corpus_texts.append(" ".join(sampled))
            corpus_labels.append(label)
        # Include full description
        corpus_texts.append(text)
        corpus_labels.append(label)

    le = LabelEncoder()
    y = le.fit_transform(corpus_labels)

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=8000,
            sublinear_tf=True,
            min_df=1,
        )),
        ("clf", RandomForestClassifier(
            n_estimators=400,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced",
        )),
    ])
    pipe.fit(corpus_texts, y)
    logger.info("Classifier trained on %d samples across %d roles.", len(corpus_texts), len(le.classes_))
    return pipe, le


def _load_or_train() -> tuple[Pipeline, LabelEncoder]:
    if MODEL_CACHE_PATH.exists():
        try:
            with open(MODEL_CACHE_PATH, "rb") as f:
                pipe, le = pickle.load(f)
            # Invalidate cache if dataset appeared since last train
            if DATASET_PATH.exists():
                cache_mtime = MODEL_CACHE_PATH.stat().st_mtime
                data_mtime  = DATASET_PATH.stat().st_mtime
                if data_mtime > cache_mtime:
                    logger.info("Dataset newer than cache — retraining …")
                    raise ValueError("stale")
            logger.info("Loaded cached role classifier.")
            return pipe, le
        except Exception:
            logger.warning("Cache invalid; retraining …")

    logger.info("Training role classifier …")
    pipe, le = _build_pipeline()
    with open(MODEL_CACHE_PATH, "wb") as f:
        pickle.dump((pipe, le), f)
    return pipe, le


# ── Public API ────────────────────────────────────────────────────────────────
class RoleClassifier:
    """Singleton wrapper — TF-IDF + Random Forest pipeline."""

    _instance: Optional["RoleClassifier"] = None

    def __new__(cls) -> "RoleClassifier":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._pipe, cls._instance._le = _load_or_train()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Force retrain (e.g. after new dataset uploaded)."""
        if MODEL_CACHE_PATH.exists():
            MODEL_CACHE_PATH.unlink()
        cls._instance = None

    def predict(self, text: str) -> dict:
        """
        Returns
        -------
        {
          "predicted_role": str,
          "confidence": float,
          "top3": [(role, prob), …],
        }
        """
        proba   = self._pipe.predict_proba([text])[0]
        top3_idx = np.argsort(proba)[-3:][::-1]
        top3    = [(self._le.inverse_transform([i])[0], float(proba[i])) for i in top3_idx]
        return {
            "predicted_role": top3[0][0],
            "confidence":     round(top3[0][1], 4),
            "top3":           top3,
        }

    def predict_batch(self, texts: list[str]) -> list[dict]:
        return [self.predict(t) for t in texts]

    @property
    def roles(self) -> list[str]:
        return list(self._le.classes_)


# ── Synthetic JD Generator ────────────────────────────────────────────────────
def generate_synthetic_jd(role: str) -> str:
    base = ROLE_CORPUS.get(role, "")
    if not base:
        return ""
    return (
        f"We are looking for a {role}. "
        f"Key requirements include: {base}. "
        f"The ideal candidate will have strong communication skills, "
        f"team collaboration experience, and a proven track record of delivering results."
    )

# ── Skill Gap Analyser ────────────────────────────────────────────────────────
def skill_gap_for_role(role: str, candidate_skills: list[str]) -> dict:
    """
    Compare candidate skills against the expected skill set for a role.

    Parameters
    ----------
    role             : Role name (must exist in ROLE_CORPUS).
    candidate_skills : Flat list of skills already extracted from the resume.

    Returns
    -------
    {
        "role":           str,
        "expected_skills":list[str],   # key skills for this role
        "present":        list[str],   # candidate has these
        "missing":        list[str],   # candidate lacks these
        "coverage_pct":   float,       # % of expected skills present
    }
    """
    corpus_text = ROLE_CORPUS.get(role, "")
    # Extract individual skill tokens from corpus string (2+ char words)
    raw_tokens = re.findall(r"[a-z][a-z0-9+#./\-]{1,30}", corpus_text.lower())
    # Filter to meaningful technical terms (skip common stop-words)
    _STOP = {"and", "the", "for", "with", "in", "of", "to", "on", "as",
              "or", "an", "is", "are", "be", "by", "at", "from", "that"}
    expected = [t for t in dict.fromkeys(raw_tokens) if t not in _STOP and len(t) > 2]
    expected = expected[:40]  # cap to top-40 most relevant

    cand_lower = {s.lower() for s in candidate_skills}

    present = [e for e in expected if e in cand_lower]
    missing = [e for e in expected if e not in cand_lower]
    coverage = round(len(present) / max(len(expected), 1) * 100, 1)

    return {
        "role":            role,
        "expected_skills": expected,
        "present":         present,
        "missing":         missing,
        "coverage_pct":    coverage,
    }