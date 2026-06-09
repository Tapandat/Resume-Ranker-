"""
Resume Ranker Pro — Login / Register Page
==========================================
Handles:
  • Email + password login
  • Email + password registration
  • Google OAuth (redirects through FastAPI → Google → back here)
  • JWT stored in st.session_state; persisted via query params on OAuth return
"""

from __future__ import annotations

import requests
import streamlit as st
from pathlib import Path
from urllib.parse import urlencode

API_BASE     = "http://localhost:8000"
GOOGLE_LOGIN = f"{API_BASE}/auth/google"

# ── Page config ────────────────────────────────────────────────────────────────
_LOGO_PATH = Path("frontend/Logo.jpg")
_logo_img  = None
if _LOGO_PATH.exists():
    from PIL import Image
    _logo_img = Image.open(_LOGO_PATH)

st.set_page_config(
    page_title="Resume Ranker — Login",
    page_icon=_logo_img or "🎯",
    layout="centered",
)

# ── Hide Streamlit's auto-generated multipage nav sidebar ──────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'DM Sans', sans-serif !important;
}
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

.auth-card {
    background: var(--secondary-background-color);
    border: 1px solid rgba(128,128,128,0.18);
    border-radius: 20px;
    padding: 2.2rem 2.4rem 2rem;
    max-width: 440px;
    margin: 2rem auto;
    box-shadow: 0 4px 24px rgba(0,0,0,0.07);
}
.auth-title {
    font-size: 1.6rem;
    font-weight: 700;
    margin-bottom: .2rem;
    text-align: center;
}
.auth-sub {
    font-size: .88rem;
    opacity: .55;
    text-align: center;
    margin-bottom: 1.6rem;
}
.divider {
    display: flex;
    align-items: center;
    gap: .75rem;
    margin: 1.1rem 0;
    color: rgba(128,128,128,0.6);
    font-size: .78rem;
}
.divider::before, .divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(128,128,128,0.2);
}
.google-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: .65rem;
    width: 100%;
    padding: .65rem 1rem;
    border: 1px solid rgba(128,128,128,0.3);
    border-radius: 10px;
    background: var(--secondary-background-color);
    color: var(--text-color);
    font-family: 'DM Sans', sans-serif;
    font-size: .9rem;
    font-weight: 600;
    cursor: pointer;
    transition: border-color .2s, box-shadow .2s;
    text-decoration: none;
}
.google-btn:hover {
    border-color: #4285F4;
    box-shadow: 0 2px 8px rgba(66,133,244,0.18);
}
</style>
""", unsafe_allow_html=True)


# ── Handle OAuth return (token in URL query param) ────────────────────────────
params = st.query_params
if "token" in params and "token" not in st.session_state:
    st.session_state["token"] = params["token"]
    st.session_state["user"]  = {
        "name":  params.get("name",  "User"),
        "email": params.get("email", ""),
    }
    st.query_params.clear()
    st.switch_page("pages/dashboard.py")


# ── Already logged in — redirect straight to dashboard ───────────────────────
if st.session_state.get("token"):
    st.switch_page("pages/dashboard.py")


# ── UI ─────────────────────────────────────────────────────────────────────────
col = st.columns([1, 2, 1])[1]

with col:
    if _logo_img:
        st.image(_logo_img, width=80)
    st.markdown('<div class="auth-title">🎯 Resume Ranker Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-sub">Sign in to start ranking resumes</div>', unsafe_allow_html=True)

    # ── Google OAuth button ────────────────────────────────────────────────────
    st.markdown(
        f'<a class="google-btn" href="{GOOGLE_LOGIN}" target="_self">'
        f'<svg width="18" height="18" viewBox="0 0 48 48">'
        f'<path fill="#FFC107" d="M43.6 20H24v8h11.3C33.6 33.1 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.8 1.1 7.9 3l5.7-5.7C34.1 6.5 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20c11 0 19.7-8 19.7-20 0-1.3-.1-2.7-.1-4z"/>'
        f'<path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.5 15.1 18.9 12 24 12c3 0 5.8 1.1 7.9 3l5.7-5.7C34.1 6.5 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/>'
        f'<path fill="#4CAF50" d="M24 44c5.2 0 9.9-1.9 13.5-5L31.8 33.5C29.9 34.9 27.1 36 24 36c-5.3 0-9.6-2.9-11.3-7.1l-6.5 5C9.6 39.7 16.3 44 24 44z"/>'
        f'<path fill="#1976D2" d="M43.6 20H24v8h11.3c-.9 2.4-2.5 4.4-4.5 5.8l5.7 4.5C40.3 35.1 44 30 44 24c0-1.3-.1-2.7-.4-4z"/>'
        f'</svg>'
        f'Continue with Google</a>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="divider">or</div>', unsafe_allow_html=True)

    # ── Tabs: Login / Register ─────────────────────────────────────────────────
    tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

    with tab_login:
        email    = st.text_input("Email",    key="li_email",    placeholder="you@example.com")
        password = st.text_input("Password", key="li_password", type="password", placeholder="Your password")
        err_box  = st.empty()

        if st.button("Sign In", type="primary", use_container_width=True, key="btn_login"):
            if not email or not password:
                err_box.error("Please fill in all fields.")
            else:
                with st.spinner("Signing in…"):
                    try:
                        resp = requests.post(
                            f"{API_BASE}/auth/login",
                            json={"email": email, "password": password},
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state["token"] = data["access_token"]
                            st.session_state["user"]  = data["user"]
                            st.switch_page("pages/dashboard.py")
                        else:
                            try:
                                detail = resp.json().get("detail", "Login failed.")
                            except Exception:
                                detail = resp.text
                            err_box.error(detail)
                    except requests.exceptions.ConnectionError:
                        err_box.error("❌ Cannot reach API. Make sure the backend is running.")

    with tab_register:
        r_name     = st.text_input("Full Name",        key="reg_name",  placeholder="Jane Doe")
        r_email    = st.text_input("Email",             key="reg_email", placeholder="you@example.com")
        r_password = st.text_input("Password",          key="reg_pass",  type="password", placeholder="Min 6 characters")
        r_confirm  = st.text_input("Confirm Password",  key="reg_conf",  type="password", placeholder="Repeat password")
        r_err      = st.empty()

        if st.button("Create Account", type="primary", use_container_width=True, key="btn_register"):
            if not r_name or not r_email or not r_password:
                r_err.error("Please fill in all fields.")
            elif r_password != r_confirm:
                r_err.error("Passwords do not match.")
            elif len(r_password) < 6:
                r_err.error("Password must be at least 6 characters.")
            else:
                with st.spinner("Creating account…"):
                    try:
                        resp = requests.post(
                            f"{API_BASE}/auth/register",
                            json={"name": r_name, "email": r_email, "password": r_password},
                            timeout=10,
                        )
                        if resp.status_code == 201:
                            data = resp.json()
                            st.session_state["token"] = data["access_token"]
                            st.session_state["user"]  = data["user"]
                            st.switch_page("pages/dashboard.py")
                        else:
                            try:
                                detail = resp.json().get("detail", "Registration failed.")
                            except Exception:
                                detail = resp.text
                            r_err.error(detail)
                    except requests.exceptions.ConnectionError:
                        r_err.error("❌ Cannot reach API. Make sure the backend is running.")
