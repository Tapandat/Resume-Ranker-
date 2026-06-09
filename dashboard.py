"""
Resume Ranker Pro — Streamlit Dashboard v2.2
=============================================
• Adaptive light/dark theme using Streamlit's native theming
• Professional recruiter UI with glassmorphism cards
• Skill extraction breakdown per candidate
• Score radar + stacked bar charts
• CSV export
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE = "http://localhost:8000/api"
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# ── Auth guard — redirect to login if not authenticated ───────────────────────
if "token" not in st.session_state or not st.session_state["token"]:
    st.session_state.clear()
    st.switch_page("login.py")

# ── Logo (optional — won't crash if missing) ──────────────────────────────────
_LOGO_PATH = Path("frontend/Logo.jpg")
_logo_img  = None
if _LOGO_PATH.exists():
    from PIL import Image
    _logo_img = Image.open(_LOGO_PATH)

st.set_page_config(
    page_title  = "Resume Ranker Pro",
    page_icon   = _logo_img or "🎯",
    layout      = "wide",
    initial_sidebar_state = "expanded",
)

# ── Adaptive CSS — works with both Streamlit light AND dark themes ─────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Override Streamlit font globally ───────────────────────────────── */
html, body, [class*="css"], .stApp {
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── Hide auto-generated multipage nav links in sidebar ─────────────── */
[data-testid="stSidebarNav"]     { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* ── Force text colours to inherit from Streamlit theme ─────────────── */
h1, h2, h3, h4 {
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    color: var(--text-color) !important;
}

p, li, .stMarkdown p, .stMarkdown li {
    color: var(--text-color) !important;
}

/* Metric cards */
[data-testid="metric-container"] {
    border: 1px solid rgba(128,128,128,0.2) !important;
    border-radius: 14px !important;
    padding: 1.1rem 1.2rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
    background: var(--secondary-background-color) !important;
}
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
}
[data-testid="stMetricLabel"] {
    font-size: .8rem !important;
    font-weight: 500 !important;
    opacity: .7 !important;
}

/* Buttons */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    letter-spacing: .01em !important;
    transition: opacity .15s, transform .1s !important;
}
.stButton > button:hover {
    opacity: .88 !important;
    transform: translateY(-1px) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    border-radius: 12px !important;
}

/* Expander */
[data-testid="stExpander"] {
    border-radius: 10px !important;
}

/* Tabs — increase contrast */
[data-testid="stTabs"] button[role="tab"] {
    font-weight: 500 !important;
    font-size: .85rem !important;
}

/* ── Custom card component ─────────────────────────────────────────── */
.rank-card {
    background: var(--secondary-background-color);
    border: 1px solid rgba(128,128,128,0.18);
    border-radius: 16px;
    padding: 1.3rem 1.6rem 1.1rem;
    margin-bottom: 1.1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    transition: border-color .2s, box-shadow .2s;
}
.rank-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 4px 16px rgba(59,130,246,0.15);
}

/* Score badge */
.score-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.55rem;
    font-weight: 700;
    width: 68px;
    height: 68px;
    border-radius: 14px;
    flex-shrink: 0;
}
.score-high { background: rgba(16,185,129,0.12); color: #10b981; border: 2px solid #10b981; }
.score-mid  { background: rgba(245,158,11,0.12); color: #f59e0b; border: 2px solid #f59e0b; }
.score-low  { background: rgba(239,68,68,0.12);  color: #ef4444; border: 2px solid #ef4444; }

/* Candidate header row */
.cand-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: .9rem;
}
.cand-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-color);
    margin: 0;
}
.cand-meta {
    font-size: .8rem;
    color: var(--text-color);
    opacity: .65;
    margin: 0;
}
.cand-role {
    font-size: .76rem;
    font-weight: 600;
    background: rgba(59,130,246,0.12);
    color: #3b82f6;
    border: 1px solid rgba(59,130,246,0.35);
    border-radius: 20px;
    padding: 2px 10px;
    display: inline-block;
}

/* Rank badge */
.rank-num {
    font-size: .68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: var(--text-color);
    opacity: .5;
    background: rgba(128,128,128,0.1);
    border: 1px solid rgba(128,128,128,0.2);
    border-radius: 6px;
    padding: 2px 8px;
}

/* Progress bars */
.bar-group { margin-bottom: .4rem; }
.bar-row   { display: flex; align-items: center; gap: .5rem; margin-bottom: .22rem; }
.bar-lbl   { font-size: .73rem; color: var(--text-color); opacity: .75; width: 145px; flex-shrink: 0; }
.bar-track { flex: 1; background: rgba(128,128,128,0.15); border-radius: 4px; height: 7px; }
.bar-fill  { height: 7px; border-radius: 4px; }
.bar-pct   { font-size: .7rem; font-family: 'JetBrains Mono', monospace;
             color: var(--text-color); opacity: .65; width: 36px; text-align: right; flex-shrink: 0; }

/* Skill tags */
.skill-section { margin-top: .6rem; }
.skill-cat  { font-size: .67rem; font-weight: 700; text-transform: uppercase;
              letter-spacing: .09em; color: var(--text-color); opacity: .5;
              margin: .55rem 0 .28rem; }
.tag {
    display: inline-block;
    font-size: .7rem;
    font-family: 'JetBrains Mono', monospace;
    border-radius: 6px;
    padding: 2px 9px;
    margin: 2px 3px;
}
.tag-kw    { background: rgba(59,130,246,0.12);  color: #3b82f6;
             border: 1px solid rgba(59,130,246,0.3); }
.tag-skill { background: rgba(128,128,128,0.1);  color: var(--text-color);
             opacity: .85; border: 1px solid rgba(128,128,128,0.2); }

/* Stat card for hero section */
.hero-stat {
    background: var(--secondary-background-color);
    border: 1px solid rgba(128,128,128,0.18);
    border-radius: 14px;
    padding: 1.3rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.hero-stat .v {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #3b82f6;
}
.hero-stat .l {
    font-size: .78rem;
    color: var(--text-color);
    opacity: .6;
    margin-top: .3rem;
}

/* Mode badge */
.mode-badge {
    display: inline-flex;
    align-items: center;
    gap: .45rem;
    background: rgba(59,130,246,0.1);
    color: #3b82f6;
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 8px;
    padding: .32rem .85rem;
    font-size: .82rem;
    font-weight: 600;
    margin-bottom: 1.1rem;
}

/* Section divider */
hr { border-color: rgba(128,128,128,0.15) !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    border-right: 1px solid rgba(128,128,128,0.15) !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

/* Skill-gap project card */
.proj-card {
    background: var(--secondary-background-color);
    border: 1px solid rgba(128,128,128,0.18);
    border-radius: 12px;
    padding: .95rem 1.1rem;
    margin-bottom: .75rem;
}
.proj-title {
    font-weight: 700;
    font-size: .95rem;
    color: #3b82f6;
    margin-bottom: .28rem;
}
.proj-desc {
    font-size: .84rem;
    color: var(--text-color);
    opacity: .75;
    margin-bottom: .45rem;
}
</style>
""", unsafe_allow_html=True)


# ── Chart helpers — adaptive Plotly colours ────────────────────────────────────
def _plotly_theme() -> dict:
    """Transparent background so Streamlit's theme shows through."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", size=12),
        margin=dict(l=10, r=10, t=36, b=10),
    )


def score_breakdown_chart(data: list[dict]) -> go.Figure:
    names = [d["filename"][:22] for d in data]
    fig   = go.Figure()
    fig.add_bar(name="Semantic (50%)",   x=names, y=[d["semantic_score"]   for d in data],
                marker_color="#3b82f6", marker_line_width=0)
    fig.add_bar(name="Keyword (30%)",    x=names, y=[d["keyword_score"]    for d in data],
                marker_color="#8b5cf6", marker_line_width=0)
    fig.add_bar(name="Experience (20%)", x=names, y=[d["experience_score"] for d in data],
                marker_color="#10b981", marker_line_width=0)
    fig.update_layout(
        barmode="stack",
        height=290,
        legend=dict(orientation="h", y=1.14, x=0),
        yaxis=dict(title="Component Score (0–1)", gridcolor="rgba(128,128,128,0.12)"),
        xaxis=dict(gridcolor="rgba(128,128,128,0.08)"),
        **_plotly_theme(),
    )
    return fig


def radar_chart(cand: dict) -> go.Figure:
    kw_breadth    = min(len(cand["matched_keywords"]) / 15, 1.0)
    skill_breadth = min(len(cand["all_skills"]) / 20, 1.0)
    categories    = ["Semantic", "Keywords", "Experience", "Skill Breadth", "Overall"]
    values        = [
        cand["semantic_score"],
        cand["keyword_score"],
        cand["experience_score"],
        skill_breadth,
        (cand["final_score"] - 1) / 9,
    ]
    values     += [values[0]]
    categories += [categories[0]]

    fig = go.Figure(go.Scatterpolar(
        r=values, theta=categories,
        fill="toself",
        line=dict(color="#3b82f6", width=2),
        fillcolor="rgba(59,130,246,0.12)",
        name=cand["filename"][:18],
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 1],
                            gridcolor="rgba(128,128,128,0.2)",
                            tickfont=dict(size=9)),
            angularaxis=dict(gridcolor="rgba(128,128,128,0.2)"),
        ),
        showlegend=False,
        height=270,
        **_plotly_theme(),
    )
    return fig


# ── HTML helpers ──────────────────────────────────────────────────────────────
def score_cls(s: float) -> str:
    return "score-high" if s >= 7.5 else "score-mid" if s >= 5.0 else "score-low"


def bar_row(label: str, val: float, color: str) -> str:
    pct = int(val * 100)
    return (
        f'<div class="bar-row">'
        f'<span class="bar-lbl">{label}</span>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{color}"></div></div>'
        f'<span class="bar-pct">{pct}%</span>'
        f'</div>'
    )


def tags_html(items: list[str], cls: str = "tag-skill") -> str:
    return "".join(f'<span class="tag {cls}">{t}</span>' for t in items)


def skills_section_html(skills: dict[str, list[str]]) -> str:
    if not skills:
        return '<p style="font-size:.78rem;opacity:.5">No skills extracted.</p>'
    parts = ['<div class="skill-section">']
    for cat, ss in skills.items():
        parts.append(f'<div class="skill-cat">{cat}</div>')
        parts.append(tags_html(ss, "tag-skill"))
    parts.append("</div>")
    return "".join(parts)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    if _logo_img:
        st.image(_logo_img, use_column_width=True)
    else:
        st.markdown("## 🎯 Resume Ranker")

    # ── User info + logout ─────────────────────────────────────────────────────
    user = st.session_state.get("user", {})
    if user:
        st.markdown(
            f'<div style="background:var(--secondary-background-color);border:1px solid rgba(128,128,128,0.2);'
            f'border-radius:10px;padding:.65rem .9rem;margin-bottom:.5rem;">'
            f'<div style="font-size:.78rem;opacity:.55">Signed in as</div>'
            f'<div style="font-weight:600;font-size:.9rem">{user.get("name","")}</div>'
            f'<div style="font-size:.75rem;opacity:.55">{user.get("email","")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.clear()
            st.switch_page("login.py")

    st.markdown("---")

    uploaded = st.file_uploader(
        "📄 Upload Resumes",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="PDF, DOCX, and plain text supported.",
    )

    st.markdown("---")
    st.markdown("### 📋 Job Description")

    jd_mode_choice = st.radio(
        "JD Source",
        ["Paste JD text", "🤖 Auto-detect role (ML)"],
        index=0,
        help="Without a JD, ML classifier predicts the role.",
    )

    jd_text = job_title = ""
    if jd_mode_choice == "Paste JD text":
        job_title = st.text_input("Job Title (optional)", placeholder="e.g. Senior Data Scientist")
        jd_text   = st.text_area("Job Description", height=180, placeholder="Paste full JD here …")
    else:
        st.caption("ML will predict the role from resume content and generate a synthetic JD for scoring.")

    st.markdown("---")
    required_years = st.slider("Min. Years of Experience", 0, 15, 3)
    anonymize      = st.toggle("Anonymise PII", value=True,
                               help="Strips names, emails, phone numbers via regex + spaCy NER.")

    rank_btn = st.button("🚀 Rank Resumes", type="primary", use_container_width=True)

    st.markdown("---")
    st.caption("Resume Ranker Pro v2.2 · SBERT + TF-IDF + Random Forest")


# ── Landing page ───────────────────────────────────────────────────────────────
st.markdown("# 🎯 Resume Ranker Pro")
st.markdown(
    '<p style="opacity:.6;margin-top:-.5rem;margin-bottom:1.5rem;font-size:.95rem">'
    'Hybrid NLP scoring · ML role classification · Skill extraction</p>',
    unsafe_allow_html=True,
)

if not rank_btn:
    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, "3",    "Scoring Signals"),
        (c2, "12",   "Detectable Roles"),
        (c3, "1–10", "Score Range"),
        (c4, "50+",  "Skill Categories"),
    ]:
        col.markdown(
            f'<div class="hero-stat"><div class="v">{val}</div><div class="l">{lbl}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.markdown("""
### How it works
1. **Upload** resumes (PDF, DOCX, TXT) in the sidebar
2. **Provide a JD** — or choose ML auto-detection
3. **Click Rank** — results in seconds

#### Scoring Formula

| Signal | Weight | Method |
|--------|--------|--------|
| Semantic alignment | **50%** | SBERT `all-mpnet-base-v2` cosine (or TF-IDF fallback) |
| Keyword overlap | **30%** | TF-IDF bigram cosine vs JD |
| Experience factor | **20%** | Regex extraction → normalised curve |

#### No-JD ML Pipeline
TF-IDF + Random Forest classifier (trained on 288+ labelled resumes, 12 roles)
predicts the best-fit role → synthetic JD is generated → normal scoring runs.
        """)
    with col_r:
        st.markdown("""
#### Extracted Skills
The parser detects 50+ skill categories including:
- Programming Languages
- ML / AI frameworks
- Cloud & DevOps tools
- Databases
- Frontend / Backend
- Soft skills & more
        """)
    st.stop()

# ── API call ───────────────────────────────────────────────────────────────────
if not uploaded:
    st.error("⚠️ Upload at least one resume file to continue.")
    st.stop()

with st.spinner("Parsing, extracting skills and scoring resumes …"):
    try:
        files_payload = [
            ("files", (f.name, f.getvalue(), "application/octet-stream"))
            for f in uploaded
        ]
        data_payload = {
            "jd_text":        jd_text if jd_mode_choice == "Paste JD text" else "",
            "job_title":      job_title,
            "required_years": required_years,
            "anonymize":      str(anonymize).lower(),
        }
        resp = requests.post(f"{API_BASE}/rank", files=files_payload, data=data_payload, timeout=120)
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.ConnectionError:
        st.error(
            "❌ Cannot reach API at `http://localhost:8000`.\n\n"
            "Start the backend:\n```\nuvicorn backend.api.main:app --reload --port 8000\n```"
        )
        st.stop()
    except Exception as exc:
        st.error(f"API error: {exc}")
        if hasattr(exc, "response") and exc.response is not None:
            st.code(exc.response.text)
        st.stop()

ranked = result.get("ranked", [])
if not ranked:
    st.warning("No resumes could be scored.")
    st.stop()

# ── Mode + summary ─────────────────────────────────────────────────────────────
detected  = result.get("detected_role")
jd_mode   = result["jd_mode"]
mode_icon = "🤖" if jd_mode == "classifier" else "📋"
mode_txt  = (
    f"Auto-detected role: <b>{detected}</b>" if jd_mode == "classifier"
    else f"JD provided · Job title: <b>{result.get('job_title') or 'N/A'}</b>"
)
st.markdown(
    f'<div class="mode-badge">{mode_icon} {mode_txt}</div>',
    unsafe_allow_html=True,
)

scores_list = [r["final_score"] for r in ranked]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Candidates Ranked", result["total_resumes"])
c2.metric("Top Score",         f"{max(scores_list):.1f}/10")
c3.metric("Avg Score",         f"{sum(scores_list)/len(scores_list):.1f}/10")
c4.metric("Mode",              jd_mode.title())

st.markdown("---")

# ── Score breakdown chart ─────────────────────────────────────────────────────
st.markdown("### 📊 Score Breakdown")
st.plotly_chart(score_breakdown_chart(ranked), use_container_width=True)

st.markdown("---")
st.markdown("### 🏆 Ranked Candidates")

for cand in ranked:
    medal    = {1: "🥇", 2: "🥈", 3: "🥉"}.get(cand["rank"], "")
    sc_cls   = score_cls(cand["final_score"])
    conf_str = f" · {cand['role_confidence']*100:.0f}% conf" if cand.get("role_confidence") else ""

    st.markdown(
        f'<div class="rank-card">'
        f'<div class="cand-header">'
        f'<div class="score-badge {sc_cls}">{cand["final_score"]}</div>'
        f'<div style="flex:1;min-width:0">'
        f'<div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap">'
        f'<span class="rank-num">#{cand["rank"]} {medal}</span>'
        f'<span class="cand-role">{cand.get("predicted_role","N/A")}{conf_str}</span>'
        f'</div>'
        f'<p class="cand-title" style="margin-top:.3rem">{cand["filename"]}</p>'
        f'<p class="cand-meta">'
        f'Experience: <b>{cand["years_of_experience"]} yrs</b> &nbsp;·&nbsp; '
        f'Words: <b>{cand["word_count"]}</b> &nbsp;·&nbsp; '
        f'Skills found: <b>{len(cand["all_skills"])}</b>'
        f'</p>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    tab_scores, tab_skills, tab_proj, tab_gap, tab_kw, tab_exp = st.tabs([
        "📈 Scores", "🛠 Skills", "🗂 Projects", "🔍 Skill Gap", "🔑 Keywords", "📝 Explanation"
    ])

    with tab_scores:
        col_bars, col_radar = st.columns([3, 2])
        with col_bars:
            st.markdown(
                '<div class="bar-group">'
                + bar_row("Semantic Alignment", cand["semantic_score"], "#3b82f6")
                + bar_row("Keyword Match",      cand["keyword_score"],  "#8b5cf6")
                + bar_row("Experience Factor",  cand["experience_score"], "#10b981")
                + "</div>",
                unsafe_allow_html=True,
            )
        with col_radar:
            st.plotly_chart(radar_chart(cand), use_container_width=True)

    with tab_skills:
        skills = cand.get("skills", {})
        if skills:
            st.markdown(skills_section_html(skills), unsafe_allow_html=True)
        else:
            st.info("No structured skills extracted from this resume.")

    with tab_proj:
        projects = cand.get("projects", [])
        if projects:
            for idx, proj in enumerate(projects, 1):
                title       = proj.get("title", f"Project {idx}")
                desc        = proj.get("description", "")
                proj_skills = proj.get("skills_mentioned", [])
                st.markdown(
                    f'<div class="proj-card">'
                    f'<div class="proj-title">🗂 {title}</div>'
                    f'<div class="proj-desc">{desc}</div>'
                    + (
                        f'<div style="font-size:.74rem;opacity:.5;margin-bottom:.25rem">Skills detected:</div>'
                        + tags_html(proj_skills, "tag-kw")
                        if proj_skills else ""
                    )
                    + "</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No projects detected in this resume. Projects section may be absent or uses an unrecognised format.")

    with tab_gap:
        gap = cand.get("skill_gap")
        if gap:
            role_for_gap = gap.get("role", "")
            coverage     = gap.get("coverage_pct", 0)
            present      = gap.get("present", [])
            missing      = gap.get("missing", [])

            gauge_color = "#10b981" if coverage >= 60 else ("#f59e0b" if coverage >= 35 else "#ef4444")
            st.markdown(
                f'<div class="proj-card">'
                f'<div style="font-size:.8rem;opacity:.55;margin-bottom:.2rem">'
                f'Skill coverage vs <b style="opacity:1">{role_for_gap}</b> role</div>'
                f'<div style="font-size:2rem;font-weight:800;color:{gauge_color}">{coverage}%</div>'
                f'<div style="background:rgba(128,128,128,0.15);border-radius:5px;height:8px;margin-top:.4rem">'
                f'<div style="width:{min(coverage,100)}%;height:8px;border-radius:5px;background:{gauge_color}"></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            col_have, col_miss = st.columns(2)
            with col_have:
                st.markdown('<div style="font-weight:700;color:#10b981;margin-bottom:.4rem">✅ Skills Present</div>', unsafe_allow_html=True)
                if present:
                    st.markdown(tags_html(present, "tag-kw"), unsafe_allow_html=True)
                else:
                    st.caption("None matched")

            with col_miss:
                st.markdown('<div style="font-weight:700;color:#ef4444;margin-bottom:.4rem">❌ Skills Missing</div>', unsafe_allow_html=True)
                if missing:
                    missing_html = " ".join(
                        f'<span style="display:inline-block;background:rgba(239,68,68,0.10);'
                        f'color:#ef4444;border:1px solid rgba(239,68,68,0.3);'
                        f'border-radius:20px;font-size:.72rem;padding:2px 10px;margin:2px 3px">'
                        f'{s}</span>'
                        for s in missing
                    )
                    st.markdown(missing_html, unsafe_allow_html=True)
                else:
                    st.caption("All expected skills found!")
        else:
            st.info("Skill gap analysis not available — role not in standard corpus.")

    with tab_kw:
        kws = cand.get("matched_keywords", [])
        if kws:
            st.markdown(
                '<div style="margin-top:.3rem">' + tags_html(kws, "tag-kw") + "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("No keyword matches found.")

    with tab_exp:
        st.code(cand["explanation"], language="")

    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)


# ── Download CSV ───────────────────────────────────────────────────────────────
st.markdown("---")
df_export = pd.DataFrame([{
    "Rank":             r["rank"],
    "Filename":         r["filename"],
    "Final Score":      r["final_score"],
    "Semantic Score":   r["semantic_score"],
    "Keyword Score":    r["keyword_score"],
    "Experience Score": r["experience_score"],
    "Years Experience": r["years_of_experience"],
    "Predicted Role":   r.get("predicted_role", ""),
    "Role Confidence":  r.get("role_confidence", ""),
    "Skills Count":     len(r.get("all_skills", [])),
    "All Skills":       ", ".join(r.get("all_skills", [])),
    "Projects Count":   len(r.get("projects", [])),
    "Project Titles":   " | ".join(p.get("title","") for p in r.get("projects", [])),
    "Skill Gap %":      r["skill_gap"]["coverage_pct"] if r.get("skill_gap") else "",
    "Missing Skills":   ", ".join(r["skill_gap"]["missing"]) if r.get("skill_gap") else "",
    "Matched Keywords": ", ".join(r.get("matched_keywords", [])),
    "Word Count":       r.get("word_count", 0),
} for r in ranked])

st.download_button(
    "⬇️ Download Results CSV",
    df_export.to_csv(index=False).encode(),
    "resume_rankings.csv",
    "text/csv",
    use_container_width=True,
)