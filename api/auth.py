"""
Auth Router — Resume Ranker
============================
POST /auth/register         → Register with email + password
POST /auth/login            → Login with email + password  (returns JWT)
GET  /auth/google           → Redirect to Google OAuth consent screen
GET  /auth/google/callback  → Google OAuth callback  (returns JWT)
GET  /auth/me               → Return current user (requires JWT)
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient

# ── Config ─────────────────────────────────────────────────────────────────────
MONGO_URL          = os.getenv("MONGO_URL", "mongodb+srv://resume_ranker:Jaswanth939@cluster0.mtv0z8k.mongodb.net/?appName=Cluster0")
GOOGLE_CLIENT_ID   = os.getenv("GOOGLE_CLIENT_ID",   "647237772956-i7d79iftllabu88t4o06jb117q6tmvtp.apps.googleusercontent.com")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "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")
GOOGLE_REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI",  "http://localhost:8000/auth/google/callback")

SECRET_KEY   = os.getenv("JWT_SECRET", "resume-ranker-super-secret-key-change-in-prod")
ALGORITHM    = "HS256"
TOKEN_EXPIRE = 60 * 24  # minutes → 1 day

# ── DB ─────────────────────────────────────────────────────────────────────────
_client = MongoClient(MONGO_URL)
_db     = _client["resumeranker"]
users   = _db["users"]
users.create_index("email", unique=True)

# ── Helpers ────────────────────────────────────────────────────────────────────
pwd_ctx    = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2     = OAuth2PasswordBearer(tokenUrl="/auth/login/form", auto_error=False)
router     = APIRouter(prefix="/auth", tags=["auth"])


def _hash(password: str) -> str:
    return pwd_ctx.hash(password)


def _verify(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def _create_token(data: dict, expires_minutes: int = TOKEN_EXPIRE) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_current_user(token: str = Depends(oauth2)):
    """Dependency — inject into any protected endpoint."""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = _decode_token(token)
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = users.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ── Pydantic models ────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name:     str
    email:    EmailStr
    password: str


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         dict


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest):
    if users.find_one({"email": body.email}):
        raise HTTPException(status_code=409, detail="Email already registered")

    doc = {
        "name":       body.name,
        "email":      body.email,
        "password":   _hash(body.password),
        "provider":   "local",
        "created_at": datetime.utcnow().isoformat(),
    }
    users.insert_one(doc)

    token = _create_token({"sub": body.email})
    return TokenResponse(
        access_token=token,
        user={"name": body.name, "email": body.email},
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    user = users.find_one({"email": body.email})
    if not user or not _verify(body.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _create_token({"sub": body.email})
    return TokenResponse(
        access_token=token,
        user={"name": user["name"], "email": user["email"]},
    )


# OAuth2PasswordRequestForm support (for Swagger UI "Authorize" button)
@router.post("/login/form", response_model=TokenResponse, include_in_schema=False)
def login_form(form: OAuth2PasswordRequestForm = Depends()):
    user = users.find_one({"email": form.username})
    if not user or not _verify(form.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _create_token({"sub": form.username})
    return TokenResponse(
        access_token=token,
        user={"name": user["name"], "email": user["email"]},
    )


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return current_user


# ── Google OAuth ───────────────────────────────────────────────────────────────
GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL  = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.get("/google")
def google_login():
    """Redirect browser to Google's consent screen."""
    params = (
        f"client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&access_type=offline"
    )
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{params}")


@router.get("/google/callback")
async def google_callback(code: str):
    """Exchange code → token → user info → JWT."""
    async with httpx.AsyncClient() as client:
        # 1. Exchange code for tokens
        token_resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code":          code,
            "client_id":     GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri":  GOOGLE_REDIRECT_URI,
            "grant_type":    "authorization_code",
        })
        if token_resp.status_code != 200:
            raise HTTPException(500, f"Google token exchange failed: {token_resp.text}")

        access_token = token_resp.json()["access_token"]

        # 2. Fetch user info
        user_resp = await client.get(
            GOOGLE_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(500, "Could not fetch Google user info")

        g_user = user_resp.json()

    email = g_user.get("email")
    name  = g_user.get("name", email)

    if not email:
        raise HTTPException(400, "Google account has no email address")

    # 3. Upsert user in MongoDB
    existing = users.find_one({"email": email})
    if not existing:
        users.insert_one({
            "name":       name,
            "email":      email,
            "password":   "",           # no password for OAuth users
            "provider":   "google",
            "picture":    g_user.get("picture", ""),
            "created_at": datetime.utcnow().isoformat(),
        })
    else:
        # Update name/picture in case they changed
        users.update_one({"email": email}, {"$set": {"name": name, "picture": g_user.get("picture", "")}})

    # 4. Issue JWT and redirect to Streamlit with token in query param
    jwt_token = _create_token({"sub": email})
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
    return RedirectResponse(f"{frontend_url}/?token={jwt_token}&name={name}&email={email}")
