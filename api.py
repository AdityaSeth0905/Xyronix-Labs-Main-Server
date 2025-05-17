from fastapi import FastAPI, HTTPException, Query
from typing import Optional
import httpx
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment from .env.gsef
#env_path = Path(__file__).resolve().parent.parent / ".env.gsef"
#load_dotenv(dotenv_path=env_path)

SUPABASE_URL = "https://lntonnxszoghefhapfuj.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxudG9ubnhzem9naGVmaGFwZnVqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5MTcwNzQsImV4cCI6MjA2MTQ5MzA3NH0.licu--f0m4QPsEAyyg23iaEKXy54al56CY_n5g0yQm4"

HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json"
}

TABLE = "scholarship_applications"
app = FastAPI()


@app.get("/applicants")
async def get_all_applicants():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{SUPABASE_URL}/rest/v1/{TABLE}?select=*", headers=HEADERS)
        return r.json()


@app.get("/applicant/{application_id}")
async def get_applicant(application_id: str):
    async with httpx.AsyncClient() as client:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE}?application_id=eq.{application_id}&select=*"
        r = await client.get(url, headers=HEADERS)
        data = r.json()
        if not data:
            raise HTTPException(status_code=404, detail="Applicant not found")
        return data[0]


@app.get("/applicants/range")
async def get_applicants_range(limit: int = Query(...), offset: int = Query(0)):
    async with httpx.AsyncClient() as client:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE}?select=*&limit={limit}&offset={offset}"
        r = await client.get(url, headers=HEADERS)
        return r.json()


@app.get("/applicant/email/{email}")
async def get_applicant_by_email(email: str):
    async with httpx.AsyncClient() as client:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE}?student_email=eq.{email}&select=student_email"
        r = await client.get(url, headers=HEADERS)
        data = r.json()
        if not data:
            raise HTTPException(status_code=404, detail="Email not found")
        return {"exists": True, "email": data[0]["student_email"]}


@app.get("/applicant/auth/{application_id}")
async def get_username_password(application_id: str):
    async with httpx.AsyncClient() as client:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE}?application_id=eq.{application_id}&select=username,password"
        r = await client.get(url, headers=HEADERS)
        data = r.json()
        if not data:
            raise HTTPException(status_code=404, detail="Credentials not found")
        return data[0]


@app.get("/ping")
async def ping_database():
    async with httpx.AsyncClient() as client:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE}?select=id&limit=1"
        try:
            r = await client.get(url, headers=HEADERS, timeout=5.0)
            if r.status_code == 200:
                return {"status": "ok", "message": "Database connection successful"}
            else:
                raise HTTPException(status_code=503, detail="Database unreachable")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Connection error: {str(e)}")

@app.get("/applicant/exists/{application_id}")
async def check_applicant_exists(application_id: str):
    async with httpx.AsyncClient() as client:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE}?application_id=eq.{application_id}&select=application_id"
        r = await client.get(url, headers=HEADERS)
        data = r.json()
        if not data:
            return {"exists": False}
        return {"exists": True, "application_id": data[0]["application_id"]}