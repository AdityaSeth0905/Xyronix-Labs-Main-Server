# Developer Manual for Scholarship Application APIs

This document provides an in-depth, industry-standard guide to the API endpoints exposed by the Django server. These endpoints are primarily used for managing and authenticating scholarship applicants via Supabase.

---

## Base URL

```
https://server.xyronixlabs.com/gsef/
```

All endpoints below are relative to this base URL.

---

## 📋 Endpoints Overview

### 1. `GET /applicants/` — **List All Applicants**

* **Description:** Fetch all scholarship applicants.
* **Returns:** JSON list of all entries in `scholarship_applications`.

### 2. `GET /applicant/<application_id>/` — **Get Applicant Details**

* **Description:** Fetch details for a specific applicant.
* **Params:** `application_id` (string)
* **Returns:** Applicant record or 404.

### 3. `GET /applicants/range/?limit=<int>&offset=<int>` — **Paginated Applicant List**

* **Description:** Fetch paginated list of applicants.
* **Returns:** Paginated JSON array.

### 4. `GET /applicant/email/<email>/` — **Check Email Existence**

* **Description:** Check if an email exists in the system.
* **Returns:** `{ exists: true/false, email: <email> }`

### 5. `GET /applicant/auth/<application_id>/` — **Get Auth Info by Application ID**

* **Description:** Fetch username and password for an applicant.

### 6. `GET /ping/` — **Health Check**

* **Description:** Health check for Supabase connection.
* **Returns:** Status message.

### 7. `GET /applicant/exists/<application_id>/` — **Check Applicant Existence**

* **Description:** Check if applicant exists.
* **Returns:** `{ exists: true/false }`

### 8. `POST /applicant/create/` — **Create or Update Applicant**

* **Description:** Create new or update existing applicant record.
* **Body (JSON):**

```json
{
  "student_email": "email@example.com",
  "username": "user",
  "password": "pass"
}
```

### 9. `POST /auth/login/` — **Login**

* **Description:** Login via username or application\_id.
* **Body (JSON):**

```json
{
  "login_type": "username" | "application_id",
  "username": "user",
  "password": "pass",
  "application_id": "app_id"
}
```

### 10. `POST /auth/register/` — **Register User**

* **Description:** Register a new user.
* **Body (JSON):**

```json
{
  "application_id": "app_id",
  "username": "new_user",
  "password": "pass"
}
```

### 11. `POST /auth/update-status/` or `POST /auth/update-status/<application_id>/<status_code>/` — **Update Application Status**

* **Description:** Update application status.
* **Body (JSON):**

```json
{
  "application_id": "app_id",
  "status_code": "A100"
}
```

### 12. `GET /applications/new/` — **New Applications (ID > 27)**

* **Description:** Get applications with ID > 27.
* **Returns:** Count and list of application IDs.

### 13. `GET /applications/after/<after_id>/` — **New Applications After Given ID**

* **Description:** Same as above, but customizable threshold.

### 14. `GET /applications/accepted/` — **Accepted Applications**

* **Description:** List of applications with status `A100`.

### 15. `GET /applications/accepted/<status_code>/` — **Accepted Applications by Status Code**

* **Description:** Filter accepted by custom status.

### 16. `GET /applications/pending/` — **Pending Applications**

* **Description:** List all applications with status `pending`.

### 17. `GET /applications/pending/<status_code>/` — **Pending Applications by Status Code**

* **Description:** Filter pending by given status code.

### 18. `GET /applications/pending-data/` — **Full Pending Applications**

* **Description:** Return complete records of all pending applications.

### 19. `GET /applications/pending-data/<status_code>/` — **Full Pending Data by Status**

* **Description:** Same as above, with filtered status.

### 20. `POST /applicant/delete/` — **Delete Applicant (JSON)**

* **Description:** Delete applicant by passing JSON body.
* **Body (JSON):**

```json
{ "application_id": "app_id" }
```

### 21. `POST /applicant/delete/<application_id>/` — **Delete Applicant (Manual)**

* **Description:** Delete applicant using URL param.

### 22. `GET /health/report/` — **Comprehensive Health Report**

* **Description:** Runs in-depth checks on multiple core endpoints and returns health, latency, and a sample response for each.
* **Returns:**

```json
{
  "overall_status": "healthy" | "unhealthy",
  "endpoints": [
    {
      "endpoint": "/applicants/",
      "method": "GET",
      "status": "healthy",
      "latency_ms": 132.5,
      "sample_response": [{ "id": 1, ... }]
    },
    ...
  ],
  "timestamp": "2025-05-30 12:30:00"
}
```

### 23. `GET /applicant/timestamps/<application_id>/` — **Fetch Applicant Timestamps**

* **Description:** Retrieve creation, update, and status update timestamps of a specific applicant.
* **Returns:**

```json
{
  "application_id": "app_id",
  "submitted_at": "2025-05-01T10:20:30Z",
  "last_updated_at": "2025-05-10T14:12:45Z",
  "application_status": "pending",
  "status_updated_at": "2025-05-10T14:12:45Z"
}
```

---

## ⚙️ Supabase Integration

* **Base API URL:** Loaded from `.env` as `SUPABASE_URL`
* **Headers:**

```http
Authorization: Bearer <SUPABASE_ANON_KEY>
Content-Type: application/json
```

* **Target Table:** `scholarship_applications`

---

## 🛡️ Authentication & Security

* Username-password login is securely checked using Django's `check_password`.
* Passwords are hashed using `make_password()` before storing.
* CSRF is exempted as it's an API-only backend.

---

## 📌 Notes for Developers

* Use async clients (`httpx.AsyncClient`) for all DB calls.
* Follow status codes for handling errors:

  * `200/201`: Success
  * `400`: Bad request (missing or invalid data)
  * `404`: Resource not found
  * `409`: Conflict (e.g., duplicate username)
  * `500`: Internal server error
* Supabase constraints (e.g., field types) must be respected client-side.

---

## 🔚 Summary

This document is the reference guide for using and extending the scholarship application's backend API. Each endpoint is designed for Supabase-first integration, offering a scalable and decoupled data layer.
