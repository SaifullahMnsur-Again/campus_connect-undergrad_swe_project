# Campus Connect API Documentation

This document outlines the API endpoints for the **Campus Connect** platform, a Django-based RESTful API designed to facilitate university campus services such as campus exploration, blood bank management, lost and found, and user account management. The API supports various user roles (students, teachers, officers, staff) with specific requirements for registration and interaction.

- **Base URL**: `/api/`
- **Authentication**: Most endpoints require authentication via a token obtained through the `/api/accounts/login/` endpoint. Include the token in the `Authorization` header as `Token <token>`.
- **Content Type**: Unless specified (e.g., multipart for file uploads), use `application/json`.
- **Roles and Permissions**:
  - **Students/Teachers**: Must specify university and academic unit; teachers require a teacher designation.
  - **Officers/Staff**: Must specify designation and workplace.
  - **Admins**: University admins (`admin_level='university'`) or app-wide admins (`admin_level='app'`) have elevated permissions.
- **Response Format**: Responses typically include a `message` field and, where applicable, `data` or `redirect` fields.

## Table of Contents

1. [Accounts](#accounts)
   - [Register User](#register-user)
   - [Verify Email](#verify-email)
   - [Login](#login)
   - [Logout](#logout)
   - [User List](#user-list)
   - [User Profile](#user-profile)
   - [User Detail](#user-detail)
2. [Blood Bank](#blood-bank)
   - [Blood Group List](#blood-group-list)
   - [Blood Group Detail](#blood-group-detail)
   - [Donor Register](#donor-register)
   - [Donor Profile](#donor-profile)
   - [Donor Withdraw](#donor-withdraw)
   - [Donor Detail](#donor-detail)
   - [Donor List](#donor-list)
   - [Blood Request List/Create](#blood-request-listcreate)
   - [Blood Request Detail](#blood-request-detail)
   - [Blood Request Delete](#blood-request-delete)
   - [Blood Request Donor Register](#blood-request-donor-register)
   - [Blood Request Donor List](#blood-request-donor-list)
3. [Places](#places)
   - [Place List/Create](#place-listcreate)
   - [University Places](#university-places)
   - [Place Detail](#place-detail)
   - [Place Update](#place-update)
   - [Place Delete](#place-delete)
   - [Place Recursive Delete](#place-recursive-delete)
   - [Place Search](#place-search)
   - [Place Type List](#place-type-list)
   - [Media Access](#media-access)
   - [Pending Place Updates](#pending-place-updates)
   - [Place Update Detail](#place-update-detail)
   - [Place Update Approval](#place-update-approval)
4. [Lost and Found](#lost-and-found)
   - [Lost Item List/Create](#lost-item-listcreate)
   - [Lost Item Detail](#lost-item-detail)
   - [Lost Item Claim](#lost-item-claim)
   - [Lost Item Resolve](#lost-item-resolve)
   - [Lost Item Approve](#lost-item-approve)
   - [My Claims List](#my-claims-list)
   - [My Posts List](#my-posts-list)
   - [Lost Item Claims List](#lost-item-claims-list)
   - [History](#history)
   - [Media Access](#media-access-lost-and-found)

## Accounts

### Register User
- **Endpoint**: `POST /api/accounts/register/`
- **Permission**: AllowAny
- **Description**: Registers a new user and sends a verification code to their email.
- **Request Body**:
  ```json
  {
    "name": "string",
    "email": "string",
    "password": "string (min 8 chars)",
    "confirm_password": "string",
    "role": "string (student|teacher|officer|staff)",
    "contact_visibility": "string (none|email|phone|both)",
    "phone": "string (optional)",
    "blood_group": "string (optional, e.g., A+)",
    "university": "integer (required for student/teacher)",
    "academic_unit": "integer (required for student/teacher)",
    "teacher_designation": "integer (required for teacher)",
    "designation": "string (required for officer/staff)",
    "workplace": "string (required for officer/staff)",
    "admin_level": "string (none|university|app, default: none)"
  }
  ```
- **Responses**:
  - **201 Created**:
    ```json
    {
      "message": "User registered, please verify your email.",
      "redirect": "/api/accounts/verify-email/"
    }
    ```
  - **400 Bad Request** (e.g., invalid data, duplicate email, mismatched passwords):
    ```json
    {
      "message": {
        "email": ["This email is already registered."],
        "confirm_password": ["Passwords do not match."],
        "academic_unit": ["Must select an academic unit if a university is chosen."]
      },
      "redirect": null
    }
    ```

### Verify Email
- **Endpoint**: `POST /api/accounts/verify-email/`
- **Permission**: AllowAny
- **Description**: Verifies a user's email using a 6-digit code sent during registration.
- **Request Body**:
  ```json
  {
    "email": "string",
    "code": "string (6 digits)"
  }
  ```
- **Responses**:
  - **200 OK**:
    ```json
    {
      "message": "Email verified successfully.",
      "redirect": "/api/accounts/login/"
    }
    ```
  - **400 Bad Request** (invalid/expired code):
    ```json
    {
      "message": "Invalid or expired code.",
      "redirect": null
    }
    ```
  - **404 Not Found** (user not found):
    ```json
    {
      "message": "User not found.",
      "redirect": null
    }
    ```

### Login
- **Endpoint**: `POST /api/accounts/login/`
- **Permission**: AllowAny
- **Description**: Authenticates a user and returns an authentication token.
- **Request Body**:
  ```json
  {
    "email": "string",
    "password": "string"
  }
  ```
- **Responses**:
  - **200 OK**:
    ```json
    {
      "token": "string",
      "user": {
        "id": "integer",
        "name": "string",
        "email": "string",
        "phone": "string|null",
        "blood_group": "string|null",
        "contact_visibility": "string",
        "role": "string",
        "admin_level": "string",
        "university": {"name": "string", "short_name": "string|null"}|null,
        "academic_unit": {"name": "string", "short_name": "string|null", "unit_type": "string"}|null,
        "teacher_designation": "string|null",
        "designation": "string|null",
        "workplace": "string|null"
      },
      "profile_url": "string",
      "redirect": null
    }
    ```
  - **400 Bad Request** (invalid credentials, inactive account):
    ```json
    {
      "message": "Invalid credentials." | "Account is inactive or unverified.",
      "redirect": null
    }
    ```

### Logout
- **Endpoint**: `POST /api/accounts/logout/`
- **Permission**: IsAuthenticated
- **Description**: Logs out the user by deleting their authentication token.
- **Request Body**: None
- **Responses**:
  - **200 OK**:
    ```json
    {
      "message": "Logged out successfully.",
      "redirect": null
    }
    ```
  - **400 Bad Request** (unexpected error):
    ```json
    {
      "message": "Error message",
      "redirect": null
    }
    ```

### User List
- **Endpoint**: `GET /api/accounts/`
- **Permission**: IsAuthenticated
- **Description**: Lists all users with pagination, showing basic details.
- **Query Parameters**:
  - `limit`: Number of results per page
  - `offset`: Starting point for pagination
- **Responses**:
  - **200 OK**:
    ```json
    {
      "count": "integer",
      "next": "string|null",
      "previous": "string|null",
      "results": [
        {
          "id": "integer",
          "name": "string",
          "role": "string",
          "admin_level": "string",
          "university": {"name": "string", "short_name": "string|null"}|null,
          "academic_unit": {"name": "string", "short_name": "string|null", "unit_type": "string"}|null,
          "detail_url": "string"
        }
      ]
    }
    ```

### User Profile
- **Endpoint**: `GET /api/accounts/profile/` | `PATCH /api/accounts/profile/`
- **Permission**: IsAuthenticated
- **Description**: Retrieves or updates the authenticated user's profile.
- **Request Body (PATCH)**:
  ```json
  {
    "name": "string",
    "phone": "string|null",
    "blood_group": "string|null",
    "contact_visibility": "string",
    "university": "integer|null",
    "academic_unit": "integer|null",
    "teacher_designation": "integer|null",
    "designation": "string|null",
    "workplace": "string|null"
  }
  ```
- **Responses**:
  - **GET 200 OK**:
    ```json
    {
      "id": "integer",
      "name": "string",
      "email": "string",
      "phone": "string|null",
      "blood_group": "string|null",
      "contact_visibility": "string",
      "role": "string",
      "admin_level": "string",
      "university": {"name": "string", "short_name": "string|null"}|null,
      "academic_unit": {"name": "string", "short_name": "string|null", "unit_type": "string"}|null,
      "teacher_designation": "string|null",
      "designation": "string|null",
      "workplace": "string|null"
    }
    ```
  - **PATCH 200 OK**:
    ```json
    {
      "message": "Profile updated successfully.",
      "data": { /* Updated user data as above */ }
    }
    ```
  - **PATCH 400 Bad Request** (validation errors):
    ```json
    {
      "message": {
        "blood_group": ["Blood group 'X' does not exist."],
        "academic_unit": ["Academic unit must belong to the selected university."]
      }
    }
    ```

### User Detail
- **Endpoint**: `GET /api/accounts/<int:pk>/`
- **Permission**: AllowAny
- **Description**: Retrieves a user's details by ID, respecting contact visibility settings.
- **Responses**:
  - **200 OK**:
    ```json
    {
      "id": "integer",
      "name": "string",
      "email": "string|null",
      "phone": "string|null",
      "blood_group": "string|null",
      "contact_visibility": "string",
      "role": "string",
      "admin_level": "string",
      "university": {"name": "string", "short_name": "string|null"}|null,
      "academic_unit": {"name": "string", "short_name": "string|null", "unit_type": "string"}|null,
      "teacher_designation": "string|null",
      "designation": "string|null",
      "workplace": "string|null"
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "message": "User not found."
    }
    ```

## Blood Bank

### Blood Group List
- **Endpoint**: `GET /api/bloodbank/blood-groups/`
- **Permission**: AllowAny
- **Description**: Lists all blood groups.
- **Responses**:
  - **200 OK**:
    ```json
    ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    ```

### Blood Group Detail
- **Endpoint**: `GET /api/bloodbank/blood-groups/<str:pk>/`
- **Permission**: AllowAny
- **Description**: Retrieves details of a specific blood group.
- **Responses**:
  - **200 OK**:
    ```json
    {
      "name": "A+"
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "message": "Blood group not found."
    }
    ```

### Donor Register
- **Endpoint**: `POST /api/bloodbank/donor-register/`
- **Permission**: IsAuthenticated
- **Description**: Registers the authenticated user as a blood donor.
- **Request Body**:
  ```json
  {
    "emergency_contact": "string (+1234567890)",
    "preferred_location": "string",
    "last_donated": "string (YYYY-MM-DD, optional)",
    "consent": "boolean"
  }
  ```
- **Responses**:
  - **201 Created**:
    ```json
    {
      "emergency_contact": "string",
      "preferred_location": "string",
      "last_donated": "string|null",
      "consent": "boolean",
      "name": "string",
      "blood_group": "string|null",
      "user": "integer",
      "detail_url": "string"
    }
    ```
  - **400 Bad Request** (already registered, invalid data):
    ```json
    {
      "message": "User is already registered as a donor." | {
        "emergency_contact": ["Phone number must be in international format (e.g., +1234567890)."]
      }
    }
    ```

### Donor Profile
- **Endpoint**: `GET /api/bloodbank/donor-profile/` | `PATCH /api/bloodbank/donor-profile/`
- **Permission**: IsAuthenticated
- **Description**: Retrieves or updates the authenticated user's donor profile.
- **Request Body (PATCH)**:
  ```json
  {
    "emergency_contact": "string",
    "preferred_location": "string",
    "last_donated": "string|null",
    "consent": "boolean"
  }
  ```
- **Responses**:
  - **GET 200 OK**:
    ```json
    {
      "emergency_contact": "string",
      "preferred_location": "string",
      "last_donated": "string|null",
      "consent": "boolean",
      "name": "string",
      "blood_group": "string|null",
      "user": "integer",
      "detail_url": "string"
    }
    ```
  - **PATCH 200 OK**:
    ```json
    {
      "message": "Donor profile updated successfully.",
      "data": { /* Updated donor data as above */ }
    }
    ```
  - **404 Not Found** (no donor profile):
    ```json
    {
      "message": "No donor profile found. To register as a donor use the url below.",
      "redirect": "/api/bloodbank/donor-register/"
    }
    ```
  - **400 Bad Request** (validation errors):
    ```json
    {
      "last_donated": ["Last donated date cannot be in the future."]
    }
    ```

### Donor Withdraw
- **Endpoint**: `POST /api/bloodbank/donor-withdraw/`
- **Permission**: IsAuthenticated
- **Description**: Removes the authenticated user's donor profile.
- **Request Body**: None
- **Responses**:
  - **204 No Content**:
    ```json
    {
      "message": "Donor profile withdrawn successfully."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "message": "No donor profile found."
    }
    ```

### Donor Detail
- **Endpoint**: `GET /api/bloodbank/donors/<int:pk>/`
- **Permission**: AllowAny
- **Description**: Retrieves a donor's details by ID.
- **Responses**:
  - **200 OK**:
    ```json
    {
      "emergency_contact": "string",
      "preferred_location": "string",
      "last_donated": "string|null",
      "consent": "boolean",
      "name": "string",
      "blood_group": "string|null",
      "user": "integer",
      "detail_url": "string"
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "message": "Donor profile not found."
    }
    ```

### Donor List
- **Endpoint**: `GET /api/bloodbank/donors/`
- **Permission**: AllowAny
- **Description**: Lists donors with optional filters and pagination.
- **Query Parameters**:
  - `blood_group`: Filter by blood group (e.g., A+)
  - `location`: Filter by preferred location (case-insensitive)
  - `last_donated_before`: Filter by last donated date (YYYY-MM-DD)
  - `last_donated_after`: Filter by last donated date (YYYY-MM-DD)
  - `limit`: Number of results per page
  - `offset`: Starting point for pagination
- **Responses**:
  - **200 OK**:
    ```json
    {
      "count": "integer",
      "next": "string|null",
      "previous": "string|null",
      "results": [
        {
          "emergency_contact": "string",
          "preferred_location": "string",
          "last_donated": "string|null",
          "consent": "boolean",
          "name": "string",
          "blood_group": "string|null",
          "user": "integer",
          "detail_url": "string"
        }
      ]
    }
    ```
  - **400 Bad Request** (invalid date format):
    ```json
    {
      "message": "Invalid date format for last_donated_before. Use YYYY-MM-DD."
    }
    ```

### Blood Request List/Create
- **Endpoint**: `GET /api/bloodbank/requests/` | `POST /api/bloodbank/requests/`
- **Permission**: GET: AllowAny, POST: IsAuthenticated
- **Description**: Lists open blood requests (or all for the authenticated user) or creates a new blood request.
- **Request Body (POST)**:
  ```json
  {
    "title": "string",
    "description": "string",
    "blood_group": "string",
    "university": "integer",
    "request_date": "string (YYYY-MM-DD)",
    "urgent": "boolean",
    "location": "string"
  }
  ```
- **Responses**:
  - **GET 200 OK**:
    ```json
    {
      "count": "integer",
      "next": "string|null",
      "previous": "string|null",
      "results": [
        {
          "id": "integer",
          "title": "string",
          "description": "string",
          "user": {"id": "integer", "name": "string", "detail_url": "string"},
          "blood_group": {"name": "string"},
          "university": {"id": "integer", "name": "string"},
          "request_date": "string",
          "urgent": "boolean",
          "location": "string",
          "status": "string",
          "created_at": "string",
          "updated_at": "string",
          "resolved_by": {"id": "integer", "name": "string", "detail_url": "string"}|null
        }
      ]
    }
    ```
  - **POST 201 Created**:
    ```json
    {
      "id": "integer",
      "title": "string",
      /* Other fields as above */
    }
    ```
  - **POST 400 Bad Request** (validation errors):
    ```json
    {
      "blood_group": ["This field is required."]
    }
    ```

### Blood Request Detail
- **Endpoint**: `GET /api/bloodbank/requests/<int:pk>/`
- **Permission**: AllowAny
- **Description**: Retrieves details of an open blood request.
- **Responses**:
  - **200 OK**:
    ```json
    {
      "id": "integer",
      "title": "string",
      /* Other fields as in list response */
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Blood request not found, not approved, or resolved."
    }
    ```

### Blood Request Delete
- **Endpoint**: `DELETE /api/bloodbank/requests/<int:pk>/`
- **Permission**: IsAuthenticated
- **Description**: Deletes a blood request if the user is the owner or a university admin.
- **Responses**:
  - **204 No Content**:
    ```json
    {
      "message": "Blood request deleted successfully."
    }
    ```
  - **403 Forbidden** (no permission):
    ```json
    {
      "error": "You do not have permission to delete this request."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Blood request not found."
    }
    ```

### Blood Request Donor Register
- **Endpoint**: `POST /api/bloodbank/request-donor-register/`
- **Permission**: IsAuthenticated
- **Description**: Registers the authenticated user (must be a donor) for a blood request.
- **Request Body**:
  ```json
  {
    "blood_request": "integer",
    "message": "string (10-1000 chars)",
    "contact_info": "string (+1234567890)"
  }
  ```
- **Responses**:
  - **201 Created**:
    ```json
    {
      "id": "integer",
      "blood_request": "integer",
      "donor": {
        "id": "integer",
        "name": "string",
        "blood_group": "string|null",
        "emergency_contact": "string",
        "preferred_location": "string",
        "detail_url": "string"
      },
      "message": "string",
      "contact_info": "string",
      "created_at": "string"
    }
    ```
  - **400 Bad Request** (not a donor, invalid data):
    ```json
    {
      "message": "You must be registered as a donor to volunteer for a blood request.",
      "redirect": "/api/bloodbank/donor-register/"
    }
    ```
  - **400 Bad Request** (validation errors):
    ```json
    {
      "error": {
        "message": ["Ensure this field has at least 10 characters."]
      }
    }
    ```

### Blood Request Donor List
- **Endpoint**: `GET /api/bloodbank/requests/<int:pk>/donors/`
- **Permission**: IsAuthenticated
- **Description**: Lists donors registered for a blood request (accessible to the request owner or admins).
- **Responses**:
  - **200 OK**:
    ```json
    {
      "count": "integer",
      "next": "string|null",
      "previous": "string|null",
      "results": [
        {
          "id": "integer",
          "blood_request": "integer",
          "donor": {
            "id": "integer",
            "name": "string",
            "blood_group": "string|null",
            "emergency_contact": "string",
            "preferred_location": "string",
            "detail_url": "string"
          },
          "message": "string",
          "contact_info": "string",
          "created_at": "string"
        }
      ]
    }
    ```
  - **403 Forbidden** (no permission):
    ```json
    {
      "error": "You do not have permission to view registered donors for this request."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Blood request not found, not approved, or resolved."
    }
    ```

## Places

### Place List/Create
- **Endpoint**: `GET /api/places/` | `POST /api/places/`
- **Permission**: GET: AllowAny, POST: IsAuthenticated
- **Description**: Lists approved places with pagination or creates a new place (multipart for media uploads).
- **Request Body (POST)**:
  ```json
  {
    "name": "string",
    "university": "integer",
    "academic_unit": "integer|null",
    "place_type": "string",
    "parent": "integer|null",
    "description": "string",
    "history": "string",
    "establishment_year": "integer|null",
    "relative_location": "string",
    "latitude": "float|null",
    "longitude": "float|null",
    "maps_link": "string",
    "university_root": "boolean",
    "academic_unit_root": "boolean",
    "media_files": ["file (jpg, jpeg, png, mp4, mov, max 10MB)"]
  }
  ```
- **Responses**:
  - **GET 200 OK**:
    ```json
    {
      "count": "integer",
      "next": "string|null",
      "previous": "string|null",
      "results": [
        {
          "id": "integer",
          "university": "integer",
          "academic_unit": "integer|null",
          "parent": "integer|null",
          "parent_data": {"id": "integer", "name": "string", "detail_url": "string"}|null,
          "children": [{"id": "integer", "name": "string", "detail_url": "string"}],
          "name": "string",
          "description": "string",
          "history": "string",
          "establishment_year": "integer|null",
          "place_type": "string",
          "relative_location": "string",
          "latitude": "float|null",
          "longitude": "float|null",
          "maps_link": "string",
          "created_at": "string",
          "updated_at": "string",
          "created_by": {"id": "integer", "name": "string", "detail_url": "string"},
          "media": [{"id": "integer", "file_url": "string", "uploaded_at": "string", "next_media_url": "string|null", "previous_media_url": "string|null"}],
          "approval_status": "string",
          "university_root": "boolean",
          "academic_unit_root": "boolean"
        }
      ]
    }
    ```
  - **POST 201 Created**:
    ```json
    {
      "id": "integer",
      /* Other fields as above */
    }
    ```
  - **POST 400 Bad Request** (validation errors):
    ```json
    {
      "academic_unit": ["Academic unit must belong to the selected university."],
      "media_files": ["File test.jpg exceeds maximum size of 10MB."]
    }
    ```

### University Places
- **Endpoint**: `GET /api/places/universities/`
- **Permission**: AllowAny
- **Description**: Lists all root places (parent=null) that are approved.
- **Responses**:
  - **200 OK**:
    ```json
    [
      {
        "id": "integer",
        /* Other fields as in Place List response */
      }
    ]
    ```

### Place Detail
- **Endpoint**: `GET /api/places/<int:pk>/`
- **Permission**: AllowAny
- **Description**: Retrieves details of an approved place.
- **Responses**:
  - **200 OK**:
    ```json
    {
      "id": "integer",
      /* Other fields as in Place List response */
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Place not found or awaiting approval. Contact an admin to check status."
    }
    ```

### Place Update
- **Endpoint**: `POST /api/places/<int:pk>/update/`
- **Permission**: IsAuthenticated
- **Description**: Submits an update for an approved place (multipart for media uploads). Non-admins can only update media.
- **Request Body**:
  ```json
  {
    "university": "integer|null",
    "academic_unit": "integer|null",
    "parent": "integer|null",
    "name": "string",
    "description": "string",
    "history": "string",
    "establishment_year": "integer|null",
    "place_type": "string",
    "relative_location": "string",
    "latitude": "float|null",
    "longitude": "float|null",
    "maps_link": "string",
    "university_root": "boolean",
    "academic_unit_root": "boolean",
    "media_files": ["file (jpg, jpeg, png, mp4, mov, max 10MB)"]
  }
  ```
- **Responses**:
  - **201 Created**:
    ```json
    {
      "message": "Place update submitted for approval.",
      "data": {
        "id": "integer",
        "place": "integer",
        "university": "integer|null",
        "academic_unit": "integer|null",
        "parent": "integer|null",
        "name": "string",
        "description": "string",
        "history": "string",
        "establishment_year": "integer|null",
        "place_type": "string",
        "relative_location": "string",
        "latitude": "float|null",
        "longitude": "float|null",
        "maps_link": "string",
        "created_at": "string",
        "updated_at": "string",
        "updated_by": {"id": "integer", "name": "string", "detail_url": "string"},
        "media": [{"id": "integer", "file_url": "string", "uploaded_at": "string", "next_media_url": "string|null", "previous_media_url": "string|null"}],
        "approval_status": "string",
        "university_root": "boolean",
        "academic_unit_root": "boolean",
        "detail_url": "string",
        "approval_url": "string"
      }
    }
    ```
  - **400 Bad Request** (validation errors, non-admin updating non-media fields):
    ```json
    {
      "error": {
        "name": ["Only media updates are allowed for non-admin users."]
      }
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Place not found or not approved."
    }
    ```

### Place Delete
- **Endpoint**: `DELETE /api/places/<int:pk>/delete/`
- **Permission**: IsAuthenticated, PlaceOwnerOrAdminPermission
- **Description**: Deletes a place if the user is the owner or an admin, and there are no child places.
- **Responses**:
  - **204 No Content**:
    ```json
    {
      "message": "Place deleted successfully."
    }
    ```
  - **400 Bad Request** (has child places):
    ```json
    {
      "error": "Cannot delete place with child places. Delete all child places first or use recursive deletion."
    }
    ```
  - **403 Forbidden** (no permission):
    ```json
    {
      "error": "You do not have permission to delete this place."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Place not found."
    }
    ```

### Place Recursive Delete
- **Endpoint**: `DELETE /api/places/<int:pk>/recursive-delete/`
- **Permission**: IsAuthenticated, UniversityAdminPermission
- **Description**: Deletes a place and all its child places recursively.
- **Responses**:
  - **204 No Content**:
    ```json
    {
      "message": "Place and all child places deleted successfully."
    }
    ```
  - **403 Forbidden** (no permission):
    ```json
    {
      "error": "You do not have permission to perform recursive deletion."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Place not found."
    }
    ```

### Place Search
- **Endpoint**: `GET /api/places/search/`
- **Permission**: AllowAny
- **Description**: Searches approved places by various criteria with pagination.
- **Query Parameters**:
  - `university`: University name
  - `place_type`: Place type name
  - `name`: Place name or university/academic unit short name
  - `relative_location`: Location string
  - `academic_unit`: Academic unit name
  - `raw_query`: General search term (cannot combine with specific fields)
  - `limit`: Number of results per page
  - `offset`: Starting point for pagination
- **Responses**:
  - **200 OK**:
    ```json
    {
      "count": "integer",
      "next": "string|null",
      "previous": "string|null",
      "results": [
        {
          "id": "integer",
          /* Other fields as in Place List response */
        }
      ]
    }
    ```
  - **400 Bad Request** (invalid query):
    ```json
    {
      "error": {
        "non_field_errors": ["Cannot use general search with specific fields (university, place_type, name, relative_location, academic_unit)."]
      }
    }
    ```
  - **404 Not Found** (university/academic unit/place type not found):
    ```json
    {
      "error": "University not found."
    }
    ```

### Place Type List
- **Endpoint**: `GET /api/places/place-types/`
- **Permission**: AllowAny
- **Description**: Lists all place types.
- **Responses**:
  - **200 OK**:
    ```json
    [
      {
        "id": "integer",
        "name": "string"
      }
    ]
    ```

### Media Access
- **Endpoint**: `GET /api/places/media/<int:pk>/`
- **Permission**: AllowAny
- **Description**: Retrieves a media file for a place or place update, respecting approval status.
- **Responses**:
  - **200 OK**: Returns the file (content types: image/jpeg, image/png, video/mp4, video/quicktime)
  - **403 Forbidden** (unapproved place/update, unauthorized access):
    ```json
    {
      "error": "Media not accessible; place is not approved."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Media not found." | "Media file not found on server."
    }
    ```

### Pending Place Updates
- **Endpoint**: `GET /api/places/pending/`
- **Permission**: IsAuthenticated, UniversityAdminPermission
- **Description**: Lists pending place updates for the user's university (or all for app admins) with pagination.
- **Responses**:
  - **200 OK**:
    ```json
    {
      "count": "integer",
      "next": "string|null",
      "previous": "string|null",
      "results": [
        {
          "id": "integer",
          "place": "integer",
          "university": "integer|null",
          "academic_unit": "integer|null",
          "parent": "integer|null",
          "name": "string",
          "description": "string",
          "history": "string",
          "establishment_year": "integer|null",
          "place_type": "string",
          "relative_location": "string",
          "latitude": "float|null",
          "longitude": "float|null",
          "maps_link": "string",
          "created_at": "string",
          "updated_at": "string",
          "updated_by": {"id": "integer", "name": "string", "detail_url": "string"},
          "media": [{"id": "integer", "file_url": "string", "uploaded_at": "string", "next_media_url": "string|null", "previous_media_url": "string|null"}],
          "approval_status": "string",
          "university_root": "boolean",
          "academic_unit_root": "boolean",
          "detail_url": "string",
          "approval_url": "string"
        }
      ]
    }
    ```

### Place Update Detail
- **Endpoint**: `GET /api/places/updates/<int:pk>/`
- **Permission**: IsAuthenticated
- **Description**: Retrieves details of a place update (accessible to the submitter or admins).
- **Responses**:
  - **200 OK**:
    ```json
    {
      "original": { /* Place data as in Place List response */ },
      "update": { /* Place update data as in Pending Place Updates response */ }
    }
    ```
  - **403 Forbidden** (no permission):
    ```json
    {
      "error": "You do not have permission to view this update."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Place update not found."
    }
    ```

### Place Update Approval
- **Endpoint**: `POST /api/places/updates/<int:pk>/approve/`
- **Permission**: IsAuthenticated, UniversityAdminPermission
- **Description**: Approves or rejects a place update, applying changes if approved.
- **Request Body**:
  ```json
  {
    "approval_status": "string (approved|rejected)"
  }
  ```
- **Responses**:
  - **200 OK**:
    ```json
    {
      "message": "Place update 'Place Name' approved." | "Place update 'Place Name' rejected."
    }
    ```
  - **400 Bad Request** (invalid status):
    ```json
    {
      "error": "Invalid approval_status. Use 'approved' or 'rejected'."
    }
    ```
  - **403 Forbidden** (no permission):
    ```json
    {
      "error": "You do not have permission to approve this update."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Place update not found."
    }
    ```

## Lost and Found

### Lost Item List/Create
- **Endpoint**: `GET /api/lostandfound/lost/` | `POST /api/lostandfound/lost/`
- **Permission**: GET: AllowAny, POST: IsAuthenticated
- **Description**: Lists approved lost/found items or creates a new item (multipart for media uploads).
- **Query Parameters (GET)**:
  - `status`: Filter by status (lost|found|resolved)
  - `limit`: Number of results per page
  - `offset`: Starting point for pagination
- **Request Body (POST)**:
  ```json
  {
    "title": "string",
    "description": "string",
    "university": "integer",
    "lost_date": "string (YYYY-MM-DD)",
    "location": "string",
    "status": "string (lost|found)",
    "media_files": ["file (jpg, jpeg, png, max 10MB)"]
  }
  ```
- **Responses**:
  - **GET 200 OK**:
    ```json
    {
      "count": "integer",
      "next": "string|null",
      "previous": "string|null",
      "results": [
        {
          "id": "integer",
          "title": "string",
          "description": "string",
          "user": {"id": "integer", "name": "string", "detail_url": "string"},
          "university": {"id": "integer", "name": "string"},
          "lost_date": "string",
          "location": "string",
          "status": "string",
          "approval_status": "string",
          "created_at": "string",
          "updated_at": "string",
          "resolved_by": {"id": "integer", "name": "string", "detail_url": "string"}|null,
          "media": [{"id": "integer", "file_url": "string", "uploaded_at": "string"}]
        }
      ]
    }
    ```
  - **POST 201 Created**:
    ```json
    {
      "id": "integer",
      /* Other fields as above */
    }
    ```
  - **POST 400 Bad Request** (validation errors):
    ```json
    {
      "lost_date": ["Lost date cannot be in the future."]
    }
    ```

### Lost Item Detail
- **Endpoint**: `GET /api/lostandfound/lost/<int:pk>/`
- **Permission**: AllowAny
- **Description**: Retrieves details of an approved lost/found item.
- **Responses**:
  - **200 OK**:
    ```json
    {
      "id": "integer",
      /* Other fields as in Lost Item List response */
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Item not found, not approved, or resolved."
    }
    ```

### Lost Item Claim
- **Endpoint**: `POST /api/lostandfound/lost/<int:pk>/claim/`
- **Permission**: IsAuthenticated
- **Description**: Allows a user to claim a lost item (cannot claim own item).
- **Request Body**:
  ```json
  {
    "message": "string"
  }
  ```
- **Responses**:
  - **201 Created**:
    ```json
    {
      "id": "integer",
      "lost_item": "integer",
      "claimant": {"id": "integer", "name": "string", "detail_url": "string"},
      "message": "string",
      "created_at": "string"
    }
    ```
  - **400 Bad Request** (claiming own item, invalid data):
    ```json
    {
      "error": "You cannot claim your own item."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Item not found, not approved, or resolved."
    }
    ```

### Lost Item Resolve
- **Endpoint**: `POST /api/lostandfound/lost/<int:pk>/resolve/`
- **Permission**: IsAuthenticated, UniversityAdminPermission
- **Description**: Resolves a lost item by linking it to a claim.
- **Request Body**:
  ```json
  {
    "claim_id": "integer"
  }
  ```
- **Responses**:
  - **200 OK**:
    ```json
    {
      "message": "Item resolved successfully."
    }
    ```
  - **400 Bad Request** (invalid claim):
    ```json
    {
      "error": "Invalid claim ID."
    }
    ```
  - **403 Forbidden** (no permission):
    ```json
    {
      "error": "You do not have permission to resolve this item."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Item not found."
    }
    ```

### Lost Item Approve
- **Endpoint**: `POST /api/lostandfound/lost/<int:pk>/approve/`
- **Permission**: IsAuthenticated, UniversityAdminPermission
- **Description**: Approves a pending lost/found item.
- **Responses**:
  - **200 OK**:
    ```json
    {
      "message": "Item approved successfully."
    }
    ```
  - **403 Forbidden** (no permission):
    ```json
    {
      "error": "You do not have permission to approve this item."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Item not found."
    }
    ```

### My Claims List
- **Endpoint**: `GET /api/lostandfound/my-claims/`
- **Permission**: IsAuthenticated
- **Description**: Lists claims made by the authenticated user with pagination.
- **Responses**:
  - **200 OK**:
    ```json
    {
      "count": "integer",
      "next": "string|null",
      "previous": "string|null",
      "results": [
        {
          "id": "integer",
          "lost_item": {
            "id": "integer",
            "title": "string",
            /* Other item fields */
          },
          "claimant": {"id": "integer", "name": "string", "detail_url": "string"},
          "message": "string",
          "created_at": "string"
        }
      ]
    }
    ```

### My Posts List
- **Endpoint**: `GET /api/lostandfound/my-posts/`
- **Permission**: IsAuthenticated
- **Description**: Lists items posted by the authenticated user with pagination.
- **Responses**:
  - **200 OK**:
    ```json
    {
      "count": "integer",
      "next": "string|null",
      "previous": "string|null",
      "results": [
        {
          "id": "integer",
          /* Other fields as in Lost Item List response */
        }
      ]
    }
    ```

### Lost Item Claims List
- **Endpoint**: `GET /api/lostandfound/lost/<int:pk>/claims/`
- **Permission**: IsAuthenticated
- **Description**: Lists claims for a lost item (accessible to the item owner or admins).
- **Responses**:
  - **200 OK**:
    ```json
    [
      {
        "id": "integer",
        "lost_item": "integer",
        "claimant": {"id": "integer", "name": "string", "detail_url": "string"},
        "message": "string",
        "created_at": "string"
      }
    ]
    ```
  - **403 Forbidden** (no permission):
    ```json
    {
      "error": "You do not have permission to view claims for this item."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Item not found, not approved, or resolved."
    }
    ```

### History
- **Endpoint**: `GET /api/lostandfound/history/`
- **Permission**: IsAuthenticated
- **Description**: Lists the authenticated user's claims and posts with pagination.
- **Responses**:
  - **200 OK**:
    ```json
    {
      "count": "integer",
      "next": "string|null",
      "previous": "string|null",
      "results": [
        {
          "id": "integer",
          "title": "string",
          /* Other item fields */
          "claim": {
            "id": "integer",
            "message": "string",
            "created_at": "string"
          }|null
        }
      ]
    }
    ```

### Media Access (Lost and Found)
- **Endpoint**: `GET /api/lostandfound/media/<int:pk>/`
- **Permission**: AllowAny
- **Description**: Retrieves a media file for a lost/found item, accessible to the owner, admins, or if the item is approved.
- **Responses**:
  - **200 OK**: Returns the file (content types: image/jpeg, image/png)
  - **403 Forbidden** (unapproved item, unauthorized access):
    ```json
    {
      "error": "Media not accessible; item is not approved or you lack permission."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Media not found."
    }
    ```

## Notes
- **Validation**: The API enforces strict validation (e.g., academic unit must belong to the selected university, dates cannot be in the future).
- **Media Uploads**: Supported file types are jpg, jpeg, png (for lost and found, places) and mp4, mov (for places). Maximum file size is 10MB.
- **Pagination**: Used in list endpoints with `limit` and `offset` parameters.
- **Permissions**: Admin-level permissions (`university` or `app`) are required for actions like approving updates or resolving items.
- **Error Handling**: Detailed error messages are provided for validation failures, permission issues, and resource not found cases.

This documentation covers all endpoints and cases based on the provided code. For further clarification or additional endpoints, please provide details.