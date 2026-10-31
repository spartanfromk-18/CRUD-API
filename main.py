import os
from typing import Optional
from fastapi import FastAPI, Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv
from supabase import create_client, Client
from src.routes.enrich import router as enrich_router

# 1. Load environment variables first
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
security = HTTPBearer()

# 2. Initialize FastAPI app ONCE with full metadata
app = FastAPI(
    title="Task & Auth API - Supabase Backend",
    version="4.0",
    description="Secure REST API with Supabase Auth, JWT verification, and LLM Enrichment."
)

# 3. Include all application routers
app.include_router(enrich_router)

# --- Pydantic Models ---
class AuthCredentials(BaseModel):
    email: EmailStr = Field(examples=["test@example.com"])
    password: str = Field(examples=["password123"])

# --- Public Endpoints ---
@app.get("/", summary="API Info")
def get_api_info():
    return {"name": "Auth & LLM API", "version": "4.0", "auth_provider": "Supabase"}

@app.get("/public/info", summary="Public lobby info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}

# --- Authentication Endpoints ---
@app.post("/auth/signup", status_code=201, summary="Register a new user")
def sign_up(credentials: AuthCredentials):
    try:
        response = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password
        })
        return {"message": "User created successfully", "user": response.user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", status_code=200, summary="Authenticate and get JWT")
def log_in(credentials: AuthCredentials):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        return JSONResponse(status_code=401, content={"error": "Invalid login credentials"})

# --- Security Dependency Guard ---
async def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})
        return user_response.user
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})

# --- Protected Endpoints ---
@app.get("/protected/profile", summary="Get authenticated user profile")
def protected_profile(user = Depends(verify_bearer_token)):
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
        "role": user.role
    }

@app.get("/protected/dashboard", summary="Second protected route using same guard")
def protected_dashboard(user = Depends(verify_bearer_token)):
    return {"message": f"Welcome to your secure dashboard, {user.email}!"}

@app.post("/auth/logout", status_code=204, summary="End user session")
def log_out(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        supabase.auth.sign_out(token)
        return
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))