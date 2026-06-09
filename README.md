# Resume Ranker Pro — v2.2

AI-powered resume screening and ranking system with hybrid NLP scoring, project extraction, and skill-gap analysis.

## Architecture

```
proj_final/
├── backend/
│   ├── api/main.py              # FastAPI — rank, health, roles endpoints
│   └── core/
│       ├── parser.py            # Multi-format parser + skill & project extractor
│       ├── scoring_engine.py    # Hybrid SBERT + TF-IDF + Experience scorer
│       └── classifier.py        # Role classifier + skill_gap_for_role()
├── frontend/dashboard.py        # Streamlit recruiter dashboard
├── data/
│   ├── resume_dataset.csv       # Training data (Kaggle resume dataset)
│   └── role_classifier_v2.pkl   # Pre-trained classifier model
├── tests/test_scoring.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
└── requirements.txt
```

## Scoring Formula

```
Score (1–10) = (0.50 × Semantic) + (0.30 × Keyword Match) + (0.20 × Experience)
```

| Component | Method | Purpose |
|-----------|--------|---------|
| Semantic | SBERT `all-mpnet-base-v2` cosine | Context understanding, immune to keyword stuffing |
| Keyword | TF-IDF bigram overlap | Ensures must-have terms (AWS, Java) are present |
| Experience | Regex year extraction | Penalises seniority mismatches |

## Features

### Scoring & Ranking
- Uploads PDF, DOCX, and TXT resumes in batch
- Three ranking modes: Custom JD · Standard Role · Auto-Classify (no JD)
- Per-candidate score breakdown with radar chart
- PII anonymisation via spaCy NER before scoring (bias mitigation)

### 🗂 Project Extraction *(v2.2)*
- Automatically detects project sections using header patterns (`Projects`, `Portfolio`, `Key Projects`, etc.)
- Extracts project title, description, and skills mentioned per project
- Displayed in a dedicated **Projects tab** per candidate
- Project count and titles included in CSV export

### 🔍 Skill Gap Analysis *(v2.2)*
- Compares each candidate's detected skills against the expected skill set for their predicted role
- Shows **% coverage**, **Skills Present** (green), and **Skills Missing** (red) side by side
- Coverage gauge changes colour: green ≥ 60% · amber ≥ 35% · red < 35%
- Missing skills and coverage % included in CSV export

### Dashboard Tabs (per candidate)
| Tab | Content |
|-----|---------|
| 📈 Scores | Bar charts + radar chart of score breakdown |
| 🛠 Skills | Categorised skill tags extracted from resume |
| 🗂 Projects | Detected projects with title, description, skills |
| 🔍 Skill Gap | Coverage gauge + present/missing skill tags |
| 🔑 Keywords | JD-matched keywords |
| 📝 Explanation | Full scoring explanation text |

## Quickstart

```bash
# Install
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Terminal 1 — API
$env:PYTHONPATH = "D:\path\to\proj_final"   # PowerShell
uvicorn backend.api.main:app --reload --port 8000

# Terminal 2 — Dashboard
$env:PYTHONPATH = "D:\path\to\proj_final"
streamlit run frontend/dashboard.py
```

**Docker:**
```bash
cd docker && docker compose up --build
# API  → http://localhost:8000/docs
# UI   → http://localhost:8501
```

## API v2.2 — /api/rank Response (new fields)

```json
{
  "ranked": [{
    "projects": [
      {
        "title": "Real-Time Fraud Detection System",
        "description": "Built an ML pipeline using Python and Kafka...",
        "skills_mentioned": ["python", "kafka", "machine learning"]
      }
    ],
    "skill_gap": {
      "role": "Data Scientist",
      "expected_skills": ["python", "tensorflow", "pandas", ...],
      "present": ["python", "pandas", "scikit-learn"],
      "missing": ["tensorflow", "spark", "airflow"],
      "coverage_pct": 62.5
    }
  }]
}
```

## Dataset

- **Kaggle Resume Dataset** (`gauravduttakiit/resume-dataset`)
- 2,484 real resumes across 25 job categories
- Used to train the role classifier (`role_classifier_v2.pkl`)