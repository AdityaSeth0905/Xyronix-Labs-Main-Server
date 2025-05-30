from django.http import JsonResponse, HttpResponseNotFound, HttpResponseServerError
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import os
import httpx
from dotenv import load_dotenv
from pathlib import Path
from django.contrib.auth import login as django_login
from .models import User
from django.contrib.auth.hashers import make_password, check_password
import time
from django.http import FileResponse, HttpResponse, Http404

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
        




@method_decorator(csrf_exempt, name='dispatch')
class CustomLoginView(View):
    async def post(self, request):
        import json
        data = json.loads(request.body)
        login_type = data.get("login_type")  # "application_id" or "username"
        username = data.get("username")
        password = data.get("password")
        application_id = data.get("application_id")

        if login_type == "application_id":
            # Check applicant in Supabase
            async with httpx.AsyncClient() as client:
                url = f"{SUPABASE_URL}/rest/v1/{TABLE}?application_id=eq.{application_id}&select=*"
                r = await client.get(url, headers=HEADERS)
                applicants = r.json()
                if not applicants:
                    return JsonResponse({"error": "Invalid application ID"}, status=404)
            # Check if user exists in Users table
            try:
                user = User.objects.get(applicant_id=application_id)
                return JsonResponse({"success": True, "user_id": user.id})
            except User.DoesNotExist:
                # Prompt to create username and password
                return JsonResponse({"prompt": "create_username_password", "application_id": application_id})

        elif login_type == "username":
            # Authenticate against Users table
            try:
                user = User.objects.get(username=username)
                if check_password(password, user.password_hash):
                    return JsonResponse({"success": True, "user_id": user.id})
                else:
                    return JsonResponse({"error": "Invalid username or password"}, status=401)
            except User.DoesNotExist:
                return JsonResponse({"error": "Invalid username or password"}, status=401)

        else:
            return JsonResponse({"error": "Invalid login type"}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class RegisterUserView(View):
    async def post(self, request):
        import json
        data = json.loads(request.body)
        application_id = data.get("application_id")
        username = data.get("username")
        password = data.get("password")

        if not application_id or not username or not password:
            return JsonResponse({"error": "Missing fields"}, status=400)

        # Check applicant exists in Supabase
        async with httpx.AsyncClient() as client:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE}?application_id=eq.{application_id}&select=*"
            r = await client.get(url, headers=HEADERS)
            applicants = r.json()
            if not applicants:
                return JsonResponse({"error": "Invalid application ID"}, status=404)

        # Check if username is already taken
        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username already taken"}, status=409)

        # Create user in Users table
        user = User.objects.create(
            applicant_id=application_id,
            username=username,
            password_hash=make_password(password)
        )
        return JsonResponse({"success": True, "user_id": user.id})
    
@method_decorator(csrf_exempt, name='dispatch')
class UpdateApplicationStatusView(View):
    async def post(self, request, application_id=None, status_code=None):
        import json

        # Prefer URL params if present, else use JSON body
        if application_id and status_code:
            app_id = application_id
            status = status_code
        else:
            try:
                data = json.loads(request.body)
            except Exception:
                return JsonResponse({"error": "Invalid JSON"}, status=400)
            app_id = data.get("application_id")
            status = data.get("status_code")

        if not app_id or not status:
            return JsonResponse({"error": "Missing application_id or status_code"}, status=400)

        # Check applicant exists in Supabase
        async with httpx.AsyncClient() as client:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE}?application_id=eq.{app_id}&select=*"
            r = await client.get(url, headers=HEADERS)
            applicants = r.json()
            if not applicants:
                return JsonResponse({"error": "Invalid application ID"}, status=404)

            # Update application status
            update_url = f"{SUPABASE_URL}/rest/v1/{TABLE}?application_id=eq.{app_id}"
            update_payload = {"application_status": status}
            update_resp = await client.patch(
                update_url,
                headers=HEADERS,
                json=update_payload
            )
            if update_resp.status_code in (200, 204):
                return JsonResponse({"success": True, "message": "Application status updated"})
            else:
                return JsonResponse({"error": "Failed to update status"}, status=500)
            
@method_decorator(csrf_exempt, name='dispatch')
class ApplicationsAfterIDView(View):
    async def get(self, request):
        async with httpx.AsyncClient() as client:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE}?select=id,application_id"
            r = await client.get(url, headers=HEADERS)
            data = r.json()
            filtered = [app for app in data if isinstance(app.get("id"), int) and app["id"] > 27]
            return JsonResponse({
                "total": len(filtered),
                "application_ids": [app["application_id"] for app in filtered]
            })

@method_decorator(csrf_exempt, name='dispatch')
class AcceptedApplicationsView(View):
    async def get(self, request):
        async with httpx.AsyncClient() as client:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE}?select=application_id,application_status"
            r = await client.get(url, headers=HEADERS)
            data = r.json()
            accepted = [app for app in data if app.get("application_status") == "A100"]
            return JsonResponse({
                "total_accepted": len(accepted),
                "application_ids": [app["application_id"] for app in accepted]
            })

@method_decorator(csrf_exempt, name='dispatch')
class PendingApplicationsView(View):
    async def get(self, request):
        async with httpx.AsyncClient() as client:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE}?select=application_id,application_status"
            r = await client.get(url, headers=HEADERS)
            data = r.json()
            pending = [app for app in data if app.get("application_status") == "pending"]
            return JsonResponse({
                "total_pending": len(pending),
                "application_ids": [app["application_id"] for app in pending]
            })

@method_decorator(csrf_exempt, name='dispatch')
class PendingApplicationsDataView(View):
    async def get(self, request):
        async with httpx.AsyncClient() as client:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE}?select=*"
            r = await client.get(url, headers=HEADERS)
            data = r.json()
            pending = [app for app in data if app.get("application_status") == "pending"]
            return JsonResponse({
                "total_pending": len(pending),
                "pending_applications": pending
            }, safe=False)
        
@method_decorator(csrf_exempt, name='dispatch')
class ApplicantDeleteView(View):
    async def post(self, request, application_id=None):
        import json

        # Prefer URL param if present, else use JSON body
        app_id = application_id
        if not app_id:
            try:
                data = json.loads(request.body)
                app_id = data.get("application_id")
            except Exception:
                return JsonResponse({"error": "Invalid JSON"}, status=400)

        if not app_id:
            return JsonResponse({"error": "Missing application_id"}, status=400)

        # Check applicant exists in Supabase
        async with httpx.AsyncClient() as client:
            url = f"{SUPABASE_URL}/rest/v1/{TABLE}?application_id=eq.{app_id}"
            # First, check existence
            check_url = f"{url}&select=application_id"
            r = await client.get(check_url, headers=HEADERS)
            applicants = r.json()
            if not applicants:
                return JsonResponse({"error": "Invalid application ID"}, status=404)

            # Delete applicant
            delete_resp = await client.delete(url, headers=HEADERS)
            if delete_resp.status_code in (200, 204):
                return JsonResponse({"success": True, "message": f"Application {app_id} deleted"})
            else:
                return JsonResponse({"error": "Failed to delete application"}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class APIDeepHealthCheckView(View):
    async def get(self, request):
        base_url = "https://server.xyronixlabs.com/gsef"
        endpoints_report = []
        overall_healthy = True

        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            # 1. Get all applicants (real data)
            start = time.time()
            try:
                applicants_resp = await client.get(f"{base_url}/applicants/")
                applicants_latency = round((time.time() - start) * 1000, 2)
                applicants_healthy = applicants_resp.status_code == 200
                applicants_data = applicants_resp.json() if applicants_healthy else []
                endpoints_report.append({
                    "endpoint": "/applicants/",
                    "method": "GET",
                    "status": "healthy" if applicants_healthy else f"unhealthy ({applicants_resp.status_code})",
                    "latency_ms": applicants_latency,
                    "sample_response": applicants_data[:1] if applicants_data else None
                })
                if not applicants_healthy:
                    overall_healthy = False
            except Exception as e:
                endpoints_report.append({
                    "endpoint": "/applicants/",
                    "method": "GET",
                    "status": f"unhealthy ({str(e)})",
                    "latency_ms": None,
                    "sample_response": None
                })
                overall_healthy = False
                applicants_data = []

            # Use applicant with id == 28 for further checks if available
            sample_app = next((app for app in applicants_data if app.get("id") == 28), None)
            if not sample_app:
                endpoints_report.append({
                    "endpoint": "ALL",
                    "method": "N/A",
                    "status": "unhealthy (No applicant with id 28 found)",
                    "latency_ms": None,
                    "sample_response": None
                })
                return JsonResponse({
                    "overall_status": "unhealthy",
                    "endpoints": endpoints_report,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })

            application_id = sample_app.get("application_id", "SAMPLE_ID")
            email = sample_app.get("student_email", "sample@email.com")

            # 2. Applicant Detail
            start = time.time()
            try:
                resp = await client.get(f"{base_url}/applicant/{application_id}/")
                latency = round((time.time() - start) * 1000, 2)
                healthy = resp.status_code == 200
                endpoints_report.append({
                    "endpoint": f"/applicant/{application_id}/",
                    "method": "GET",
                    "status": "healthy" if healthy else f"unhealthy ({resp.status_code})",
                    "latency_ms": latency,
                    "sample_response": resp.json() if healthy else None
                })
                if not healthy:
                    overall_healthy = False
            except Exception as e:
                endpoints_report.append({
                    "endpoint": f"/applicant/{application_id}/",
                    "method": "GET",
                    "status": f"unhealthy ({str(e)})",
                    "latency_ms": None,
                    "sample_response": None
                })
                overall_healthy = False

            # 3. Applicant Exists
            start = time.time()
            try:
                resp = await client.get(f"{base_url}/applicant/exists/{application_id}/")
                latency = round((time.time() - start) * 1000, 2)
                healthy = resp.status_code == 200
                endpoints_report.append({
                    "endpoint": f"/applicant/exists/{application_id}/",
                    "method": "GET",
                    "status": "healthy" if healthy else f"unhealthy ({resp.status_code})",
                    "latency_ms": latency,
                    "sample_response": resp.json() if healthy else None
                })
                if not healthy:
                    overall_healthy = False
            except Exception as e:
                endpoints_report.append({
                    "endpoint": f"/applicant/exists/{application_id}/",
                    "method": "GET",
                    "status": f"unhealthy ({str(e)})",
                    "latency_ms": None,
                    "sample_response": None
                })
                overall_healthy = False

            # 4. Applicant by Email
            start = time.time()
            try:
                resp = await client.get(f"{base_url}/applicant/email/{email}/")
                latency = round((time.time() - start) * 1000, 2)
                healthy = resp.status_code == 200
                endpoints_report.append({
                    "endpoint": f"/applicant/email/{email}/",
                    "method": "GET",
                    "status": "healthy" if healthy else f"unhealthy ({resp.status_code})",
                    "latency_ms": latency,
                    "sample_response": resp.json() if healthy else None
                })
                if not healthy:
                    overall_healthy = False
            except Exception as e:
                endpoints_report.append({
                    "endpoint": f"/applicant/email/{email}/",
                    "method": "GET",
                    "status": f"unhealthy ({str(e)})",
                    "latency_ms": None,
                    "sample_response": None
                })
                overall_healthy = False

            # 5. Applicants Range
            start = time.time()
            try:
                resp = await client.get(f"{base_url}/applicants/range/")
                latency = round((time.time() - start) * 1000, 2)
                healthy = resp.status_code == 200
                endpoints_report.append({
                    "endpoint": "/applicants/range/",
                    "method": "GET",
                    "status": "healthy" if healthy else f"unhealthy ({resp.status_code})",
                    "latency_ms": latency,
                    "sample_response": resp.json() if healthy else None
                })
                if not healthy:
                    overall_healthy = False
            except Exception as e:
                endpoints_report.append({
                    "endpoint": "/applicants/range/",
                    "method": "GET",
                    "status": f"unhealthy ({str(e)})",
                    "latency_ms": None,
                    "sample_response": None
                })
                overall_healthy = False

            # 6. Analytics endpoints
            analytics_endpoints = [
                ("/applications/new/", "GET"),
                ("/applications/accepted/", "GET"),
                ("/applications/pending/", "GET"),
                ("/applications/pending-data/", "GET"),
            ]
            for url, method in analytics_endpoints:
                start = time.time()
                try:
                    resp = await client.get(f"{base_url}{url}")
                    latency = round((time.time() - start) * 1000, 2)
                    healthy = resp.status_code == 200
                    endpoints_report.append({
                        "endpoint": url,
                        "method": method,
                        "status": "healthy" if healthy else f"unhealthy ({resp.status_code})",
                        "latency_ms": latency,
                        "sample_response": resp.json() if healthy else None
                    })
                    if not healthy:
                        overall_healthy = False
                except Exception as e:
                    endpoints_report.append({
                        "endpoint": url,
                        "method": method,
                        "status": f"unhealthy ({str(e)})",
                        "latency_ms": None,
                        "sample_response": None
                    })
                    overall_healthy = False

            # 7. Ping
            start = time.time()
            try:
                resp = await client.get(f"{base_url}/ping/")
                latency = round((time.time() - start) * 1000, 2)
                healthy = resp.status_code == 200
                endpoints_report.append({
                    "endpoint": "/ping/",
                    "method": "GET",
                    "status": "healthy" if healthy else f"unhealthy ({resp.status_code})",
                    "latency_ms": latency,
                    "sample_response": resp.json() if healthy else None
                })
                if not healthy:
                    overall_healthy = False
            except Exception as e:
                endpoints_report.append({
                    "endpoint": "/ping/",
                    "method": "GET",
                    "status": f"unhealthy ({str(e)})",
                    "latency_ms": None,
                    "sample_response": None
                })
                overall_healthy = False

        return JsonResponse({
            "overall_status": "healthy" if overall_healthy else "unhealthy",
            "endpoints": endpoints_report,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })

@method_decorator(csrf_exempt, name='dispatch')
class APIDocumentationDownloadView(View):
    def get(self, request):
        import os
        doc_path = os.path.join(os.path.dirname(__file__), "APImanual.md")
        if not os.path.exists(doc_path):
            return Http404("API manual not found.")
        response = FileResponse(open(doc_path, "rb"), as_attachment=True, filename="APImanual.md")
        response['Content-Type'] = 'text/markdown'
        return response

@method_decorator(csrf_exempt, name='dispatch')
class ApplicantTimestampsView(View):
    async def get(self, request, application_id):
        async with httpx.AsyncClient() as client:
            # Adjust the select fields as per your Supabase schema
            url = (
                f"{SUPABASE_URL}/rest/v1/{TABLE}"
                f"?application_id=eq.{application_id}"
                f"&select=application_id,created_at,updated_at,application_status,status_updated_at"
            )
            r = await client.get(url, headers=HEADERS)
            data = r.json()
            if not data:
                return JsonResponse({"error": "Applicant not found"}, status=404)
            applicant = data[0]
            return JsonResponse({
                "application_id": applicant.get("application_id"),
                "submitted_at": applicant.get("created_at"),
                "last_updated_at": applicant.get("updated_at"),
                "application_status": applicant.get("application_status"),
                "status_updated_at": applicant.get("status_updated_at"),
            })
        
@method_decorator(csrf_exempt, name='dispatch')
class APISelfDocView(View):
    def get(self, request):
        api_list = [
            {
                "name": "List All Applicants",
                "method": "GET",
                "path": "/gsef/applicants/",
                "description": "Returns a list of all applicants.",
                "example": "curl https://server.xyronixlabs.com/gsef/applicants/"
            },
            {
                "name": "Get Applicant Details",
                "method": "GET",
                "path": "/gsef/applicant/<application_id>/",
                "description": "Returns details for a specific applicant.",
                "example": "curl https://server.xyronixlabs.com/gsef/applicant/IAF-2025-54357/"
            },
            {
                "name": "Check Applicant Exists",
                "method": "GET",
                "path": "/gsef/applicant/exists/<application_id>/",
                "description": "Checks if an applicant exists.",
                "example": "curl https://server.xyronixlabs.com/gsef/applicant/exists/IAF-2025-54357/"
            },
            {
                "name": "Get Applicant by Email",
                "method": "GET",
                "path": "/gsef/applicant/email/<email>/",
                "description": "Checks if an applicant with the given email exists.",
                "example": "curl https://server.xyronixlabs.com/gsef/applicant/email/test@email.com/"
            },
            {
                "name": "Applicants Range (Pagination)",
                "method": "GET",
                "path": "/gsef/applicants/range/?limit=10&offset=0",
                "description": "Returns applicants with pagination.",
                "example": "curl 'https://server.xyronixlabs.com/gsef/applicants/range/?limit=10&offset=0'"
            },
            {
                "name": "Create Applicant",
                "method": "POST",
                "path": "/gsef/applicant/create/",
                "description": "Creates a new applicant.",
                "example": "curl -X POST https://server.xyronixlabs.com/gsef/applicant/create/ -H 'Content-Type: application/json' -d '{\"student_email\": \"test@email.com\", \"username\": \"user\", \"password\": \"pass\"}'"
            },
            {
                "name": "Delete Applicant (API/Manual)",
                "method": "POST",
                "path": "/gsef/applicant/delete/ or /gsef/applicant/delete/<application_id>/",
                "description": "Deletes an applicant by application_id.",
                "example": "curl -X POST https://server.xyronixlabs.com/gsef/applicant/delete/IAF-2025-54357/"
            },
            {
                "name": "Login (by application_id or username/password)",
                "method": "POST",
                "path": "/gsef/auth/login/",
                "description": "Login using application_id or username/password.",
                "example": "curl -X POST https://server.xyronixlabs.com/gsef/auth/login/ -H 'Content-Type: application/json' -d '{\"login_type\": \"application_id\", \"application_id\": \"IAF-2025-54357\"}'"
            },
            {
                "name": "Register User",
                "method": "POST",
                "path": "/gsef/auth/register/",
                "description": "Register a new user with username and password.",
                "example": "curl -X POST https://server.xyronixlabs.com/gsef/auth/register/ -H 'Content-Type: application/json' -d '{\"application_id\": \"IAF-2025-54357\", \"username\": \"user\", \"password\": \"pass\"}'"
            },
            {
                "name": "Update Application Status (API/Manual)",
                "method": "POST",
                "path": "/gsef/auth/update-status/ or /gsef/auth/update-status/<application_id>/<status_code>/",
                "description": "Update the status of an application.",
                "example": "curl -X POST https://server.xyronixlabs.com/gsef/auth/update-status/IAF-2025-54357/A100/"
            },
            {
                "name": "New Applications After ID 27",
                "method": "GET",
                "path": "/gsef/applications/new/",
                "description": "Get applications with ID > 27.",
                "example": "curl https://server.xyronixlabs.com/gsef/applications/new/"
            },
            {
                "name": "Accepted Applications",
                "method": "GET",
                "path": "/gsef/applications/accepted/",
                "description": "Get all accepted applications.",
                "example": "curl https://server.xyronixlabs.com/gsef/applications/accepted/"
            },
            {
                "name": "Pending Applications",
                "method": "GET",
                "path": "/gsef/applications/pending/",
                "description": "Get all pending applications.",
                "example": "curl https://server.xyronixlabs.com/gsef/applications/pending/"
            },
            {
                "name": "Pending Applications Data",
                "method": "GET",
                "path": "/gsef/applications/pending-data/",
                "description": "Get full data for all pending applications.",
                "example": "curl https://server.xyronixlabs.com/gsef/applications/pending-data/"
            },
            {
                "name": "Ping Database",
                "method": "GET",
                "path": "/gsef/ping/",
                "description": "Check database connectivity.",
                "example": "curl https://server.xyronixlabs.com/gsef/ping/"
            },
            {
                "name": "API Health Report",
                "method": "GET",
                "path": "/gsef/health/report/",
                "description": "Get a health report for all APIs.",
                "example": "curl https://server.xyronixlabs.com/gsef/health/report/"
            },
            {
                "name": "API Manual Download",
                "method": "GET",
                "path": "/gsef/docs/manual/",
                "description": "Download the API manual as a Markdown file.",
                "example": "curl -O https://server.xyronixlabs.com/gsef/docs/manual/"
            },
            {
                "name": "Applicant Timestamps",
                "method": "GET",
                "path": "/gsef/applicant/timestamps/<application_id>/",
                "description": "Get submission, update, and status change times for an applicant.",
                "example": "curl https://server.xyronixlabs.com/gsef/applicant/timestamps/IAF-2025-54357/"
            },
        ]
        return JsonResponse({"apis": api_list})