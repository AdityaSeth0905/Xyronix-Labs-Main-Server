from django.http import JsonResponse, HttpResponseNotFound, HttpResponseServerError
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import os
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Load .env file
#env_path = Path(__file__).resolve().parent / ".env"
#load_dotenv(dotenv_path=env_path)
load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

#SUPABASE_URL = "https://lntonnxszoghefhapfuj.supabase.co"
#SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxudG9ubnhzem9naGVmaGFwZnVqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5MTcwNzQsImV4cCI6MjA2MTQ5MzA3NH0.licu--f0m4QPsEAyyg23iaEKXy54al56CY_n5g0yQm4"

#print("SUPABASE_URL:", SUPABASE_URL)
#print("SUPABASE_ANON_KEY:", SUPABASE_ANON_KEY)

HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json"
}
#print("HEADERS:", HEADERS)

TABLE = "scholarship_applications"

@method_decorator(csrf_exempt, name='dispatch')
class ApplicantsView(View):
    async def get(self, request):
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{SUPABASE_URL}/rest/v1/{TABLE}?select=*", headers=HEADERS)
            return JsonResponse(r.json(), safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class ApplicantDetailView(View):
    async def get(self, request, application_id):
        async with httpx.AsyncClient() as client:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE}?application_id=eq.{application_id}&select=*"
            r = await client.get(url, headers=HEADERS)
            data = r.json()
            if not data:
                return HttpResponseNotFound("Applicant not found")
            return JsonResponse(data[0], safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class ApplicantsRangeView(View):
    async def get(self, request):
        limit = request.GET.get("limit")
        offset = request.GET.get("offset", 0)
        async with httpx.AsyncClient() as client:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE}?select=*&limit={limit}&offset={offset}"
            r = await client.get(url, headers=HEADERS)
            return JsonResponse(r.json(), safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class ApplicantEmailView(View):
    async def get(self, request, email):
        async with httpx.AsyncClient() as client:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE}?student_email=eq.{email}&select=student_email"
            r = await client.get(url, headers=HEADERS)
            data = r.json()
            if not data:
                return HttpResponseNotFound("Email not found")
            return JsonResponse({"exists": True, "email": data[0]["student_email"]})

@method_decorator(csrf_exempt, name='dispatch')
class ApplicantAuthView(View):
    async def get(self, request, application_id):
        async with httpx.AsyncClient() as client:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE}?application_id=eq.{application_id}&select=username,password"
            r = await client.get(url, headers=HEADERS)
            data = r.json()
            if not data:
                return HttpResponseNotFound("Credentials not found")
            return JsonResponse(data[0])

@method_decorator(csrf_exempt, name='dispatch')
class PingDatabaseView(View):
    async def get(self, request):
        async with httpx.AsyncClient() as client:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE}?select=id&limit=1"
            try:
                r = await client.get(url, headers=HEADERS, timeout=5.0)
                if r.status_code == 200:
                    return JsonResponse({"status": "ok", "message": "Database connection successful"})
                else:
                    return HttpResponseServerError("Database unreachable")
            except httpx.RequestError as e:
                return HttpResponseServerError(f"Connection error: {str(e)}")

@method_decorator(csrf_exempt, name='dispatch')
class ApplicantExistsView(View):
    async def get(self, request, application_id):
        async with httpx.AsyncClient() as client:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE}?application_id=eq.{application_id}&select=application_id"
            r = await client.get(url, headers=HEADERS)
            data = r.json()
            if not data:
                return JsonResponse({"exists": False})
            return JsonResponse({"exists": True, "application_id": data[0]["application_id"]})
        
@method_decorator(csrf_exempt, name='dispatch')
class ApplicantCreateView(View):
    async def post(self, request):
        import json
        try:
            data = json.loads(request.body)
            email = data.get("student_email")
            username = data.get("username")
            password = data.get("password")
            if not email or not username or not password:
                return JsonResponse({"error": "Missing fields"}, status=400)

            async with httpx.AsyncClient() as client:
                # Check if email exists
                url = f"{SUPABASE_URL}/rest/v1/{TABLE}?student_email=eq.{email}&select=*"
                resp = await client.get(url, headers=HEADERS)
                applicants = resp.json()

                if not applicants:
                    # Email does not exist, create new applicant
                    payload = {
                        "student_email": email,
                        "username": username,
                        "password": password
                    }
                    create_resp = await client.post(
                        f"{SUPABASE_URL}/rest/v1/{TABLE}",
                        headers=HEADERS,
                        json=payload
                    )
                    if create_resp.status_code in (200, 201):
                        return JsonResponse({"success": True, "message": "Applicant created"})
                    else:
                        return JsonResponse({"error": "Failed to create applicant"}, status=500)
                else:
                    # Email exists, check if username/password are set
                    applicant = applicants[0]
                    if not applicant.get("username") and not applicant.get("password"):
                        # Update the existing applicant with username and password
                        update_payload = {
                            "username": username,
                            "password": password
                        }
                        update_url = f"{SUPABASE_URL}/rest/v1/{TABLE}?student_email=eq.{email}"
                        update_resp = await client.patch(
                            update_url,
                            headers=HEADERS,
                            json=update_payload
                        )
                        if update_resp.status_code in (200, 204):
                            return JsonResponse({"success": True, "message": "Username and password set for existing applicant"})
                        else:
                            return JsonResponse({"error": "Failed to update applicant"}, status=500)
                    else:
                        return JsonResponse({"error": "Applicant with this email already has username and password"}, status=409)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)