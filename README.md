# Campus Connect API Documentation

This document outlines the API endpoints for the **Campus Connect** application, which includes user management, blood bank services, lost and found functionality, and university-related data. All endpoints are prefixed with `/api/`.

---

## Table of Contents

1. [Accounts API](#accounts-api)
   - [Register User](#register-user)
   - [Verify Email](#verify-email)
   - [Login](#login)
   - [Logout](#logout)
   - [User List](#user-list)
   - [User Profile](#user-profile)
   - [User Detail](#user-detail)
2. [Bloodbank API](#bloodbank-api)
   - [Blood Group List/Detail](#blood-group-listdetail)
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
3. [Lost and Found API](#lost-and-found-api)
   - [All Items List](#all-items-list)
   - [Pending Items List](#pending-items-list)
   - [Resolved Items List](#resolved-items-list)
   - [Lost Item List/Create](#lost-item-listcreate)
   - [Found Item List/Create](#found-item-listcreate)
   - [Lost Item Detail](#lost-item-detail)
   - [Found Item Detail](#found-item-detail)
   - [Lost Item Claim](#lost-item-claim)
   - [Found Item Claim](#found-item-claim)
   - [Lost Item Resolve](#lost-item-resolve)
   - [Found Item Resolve](#found-item-resolve)
   - [Lost Item Approve](#lost-item-approve)
   - [Found Item Approve](#found-item-approve)
   - [My Claims List](#my-claims-list)
   - [My Posts List](#my-posts-list)
   - [Lost Item Claims List](#lost-item-claims-list)
   - [Found Item Claims List](#found-item-claims-list)
   - [History](#history)
   - [Media Access](#media-access)
4. [Universities API](#universities-api)
   - [University List](#university-list)
   - [Department List](#department-list)
   - [Institute List](#institute-list)
   - [Teacher Designation List](#teacher-designation-list)
   - [Department and Institute List](#department-and-institute-list)
   - [University Users](#university-users)

---

## Accounts API

### Register User
- **Endpoint**: `/api/accounts/register/`
- **Method**: POST
- **Permissions**: AllowAny
- **Description**: Registers a new user and sends a verification code to the provided email.
- **Request Body**:
  ```json
  {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "password": "securepassword123",
    "confirm_password": "securepassword123",
    "phone": "+1234567890",
    "blood_group": "A+",
    "contact_visibility": "email",
    "role": "student",
    "admin_level": "none",
    "university": 1,
    "academic_unit": 1,
    "teacher_designation": null,
    "designation": "",
    "workplace": ""
  }
  ```
- **Response**:
  - **201 Created**:
    ```json
    {
      "message": "User registered, please verify your email.",
      "redirect": "/api/accounts/verify-email/"
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "message": {
        "email": ["This email is already registered."]
      },
      "redirect": null
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "password": "securepassword123",
    "confirm_password": "securepassword123",
    "phone": "+1234567890",
    "blood_group": "A+",
    "contact_visibility": "email",
    "role": "student",
    "admin_level": "none",
    "university": 1,
    "academic_unit": 1
  }'
  ```

### Verify Email
- **Endpoint**: `/api/accounts/verify-email/`
- **Method**: POST
- **Permissions**: AllowAny
- **Description**: Verifies a user's email using a 6-digit code sent during registration.
- **Request Body**:
  ```json
  {
    "email": "john.doe@example.com",
    "code": "123456"
  }
  ```
- **Response**:
  - **200 OK**:
    ```json
    {
      "message": "Email verified successfully.",
      "redirect": "/api/accounts/login/"
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "message": "Invalid or expired code.",
      "redirect": null
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/accounts/verify-email/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "code": "123456"
  }'
  ```

### Login
- **Endpoint**: `/api/accounts/login/`
- **Method**: POST
- **Permissions**: AllowAny
- **Description**: Authenticates a user and returns an authentication token.
- **Request Body**:
  ```json
  {
    "email": "john.doe@example.com",
    "password": "securepassword123"
  }
  ```
- **Response**:
  - **200 OK**:
    ```json
    {
      "token": "abc123token",
      "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "blood_group": "A+",
        "contact_visibility": "email",
        "role": "student",
        "admin_level": "none",
        "university": {
          "name": "Example University",
          "short_name": "EU"
        },
        "academic_unit": {
          "name": "Department of Computer Science",
          "short_name": "CS",
          "unit_type": "department"
        }
      },
      "profile_url": "http://localhost:8000/api/accounts/profile/",
      "redirect": null
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "message": "Invalid credentials.",
      "redirect": null
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "securepassword123"
  }'
  ```

### Logout
- **Endpoint**: `/api/accounts/logout/`
- **Method**: POST
- **Permissions**: IsAuthenticated
- **Description**: Logs out a user by deleting their authentication token.
- **Request Body**: None
- **Response**:
  - **200 OK**:
    ```json
    {
      "message": "Logged out successfully.",
      "redirect": null
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "message": "An error occurred.",
      "redirect": null
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/accounts/logout/ \
  -H "Authorization: Token abc123token"
  ```

### User List
- **Endpoint**: `/api/accounts/`
- **Method**: GET
- **Permissions**: IsAuthenticated
- **Description**: Retrieves a paginated list of all users.
- **Query Parameters**:
  - `limit`: Number of results per page
  - `offset`: Starting point for pagination
- **Response**:
  - **200 OK**:
    ```json
    {
      "count": 2,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "name": "John Doe",
          "role": "student",
          "admin_level": "none",
          "university": {
            "name": "Example University",
            "short_name": "EU"
          },
          "academic_unit": {
            "name": "Department of Computer Science",
            "short_name": "CS",
            "unit_type": "department"
          },
          "detail_url": "http://localhost:8000/api/accounts/1/"
        }
      ]
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/accounts/?limit=10&offset=0 \
  -H "Authorization: Token abc123token"
  ```

### User Profile
- **Endpoint**: `/api/accounts/profile/`
- **Method**: GET, PATCH
- **Permissions**: IsAuthenticated
- **Description**: Retrieves or updates the authenticated user's profile.
- **Request Body (PATCH)**:
  ```json
  {
    "phone": "+0987654321",
    "contact_visibility": "phone",
    "blood_group": "B+"
  }
  ```
- **Response**:
  - **GET (200 OK)**:
    ```json
    {
      "id": 1,
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "+1234567890",
      "blood_group": "A+",
      "contact_visibility": "email",
      "role": "student",
      "admin_level": "none",
      "university": {
        "name": "Example University",
        "short_name": "EU"
      },
      "academic_unit": {
        "name": "Department of Computer Science",
        "short_name": "CS",
        "unit_type": "department"
      }
    }
    ```
  - **PATCH (200 OK)**:
    ```json
    {
      "message": "Profile updated successfully.",
      "data": {
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+0987654321",
        "blood_group": "B+",
        "contact_visibility": "phone",
        "role": "student",
        "admin_level": "none",
        "university": {
          "name": "Example University",
          "short_name": "EU"
        },
        "academic_unit": {
          "name": "Department of Computer Science",
          "short_name": "CS",
          "unit_type": "department"
        }
      }
    }
    ```
  - **PATCH (400 Bad Request)**:
    ```json
    {
      "message": {
        "blood_group": ["Blood group 'X+' does not exist."]
      }
    }
    ```
- **Example**:
  ```bash
  curl -X PATCH http://localhost:8000/api/accounts/profile/ \
  -H "Authorization: Token abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+0987654321",
    "contact_visibility": "phone",
    "blood_group": "B+"
  }'
  ```

### User Detail
- **Endpoint**: `/api/accounts/<int:pk>/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Retrieves details of a specific user by ID, respecting contact visibility settings.
- **Response**:
  - **200 OK**:
    ```json
    {
      "id": 1,
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "+1234567890",
      "blood_group": "A+",
      "contact_visibility": "email",
      "role": "student",
      "admin_level": "none",
      "university": {
        "name": "Example University",
        "short_name": "EU"
      },
      "academic_unit": {
        "name": "Department of Computer Science",
        "short_name": "CS",
        "unit_type": "department"
      }
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "message": "User not found."
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/accounts/1/
  ```

---

## Bloodbank API

### Blood Group List/Detail
- **Endpoint**: `/api/bloodbank/bloodgroups/` or `/api/bloodbank/bloodgroups/<str:pk>/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Retrieves a list of all blood groups or details of a specific blood group by name.
- **Response**:
  - **List (200 OK)**:
    ```json
    ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    ```
  - **Detail (200 OK)**:
    ```json
    {
      "name": "A+"
    }
    ```
  - **Detail (404 Not Found)**:
    ```json
    {
      "message": "Blood group not found."
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/bloodbank/bloodgroups/
  ```

### Donor Register
- **Endpoint**: `/api/bloodbank/donor/register/`
- **Method**: POST
- **Permissions**: IsAuthenticated
- **Description**: Registers the authenticated user as a blood donor.
- **Request Body**:
  ```json
  {
    "emergency_contact": "+1234567890",
    "preferred_location": "City Hospital",
    "last_donated": "2025-01-01",
    "consent": true
  }
  ```
- **Response**:
  - **201 Created**:
    ```json
    {
      "emergency_contact": "+1234567890",
      "preferred_location": "City Hospital",
      "last_donated": "2025-01-01",
      "consent": true,
      "name": "John Doe",
      "blood_group": "A+",
      "user": 1,
      "detail_url": "http://localhost:8000/api/bloodbank/donor/1/"
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "message": "User is already registered as a donor."
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/bloodbank/donor/register/ \
  -H "Authorization: Token abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "emergency_contact": "+1234567890",
    "preferred_location": "City Hospital",
    "last_donated": "2025-01-01",
    "consent": true
  }'
  ```

### Donor Profile
- **Endpoint**: `/api/bloodbank/donor/` or `/api/bloodbank/donor/profile/`
- **Method**: GET, PATCH
- **Permissions**: IsAuthenticated
- **Description**: Retrieves or updates the authenticated user's donor profile.
- **Request Body (PATCH)**:
  ```json
  {
    "preferred_location": "General Hospital"
  }
  ```
- **Response**:
  - **GET (200 OK)**:
    ```json
    {
      "emergency_contact": "+1234567890",
      "preferred_location": "City Hospital",
      "last_donated": "2025-01-01",
      "consent": true,
      "name": "John Doe",
      "blood_group": "A+",
      "user": 1,
      "detail_url": "http://localhost:8000/api/bloodbank/donor/1/"
    }
    ```
  - **PATCH (200 OK)**:
    ```json
    {
      "message": "Donor profile updated successfully.",
      "data": {
        "emergency_contact": "+1234567890",
        "preferred_location": "General Hospital",
        "last_donated": "2025-01-01",
        "consent": true,
        "name": "John Doe",
        "blood_group": "A+",
        "user": 1,
        "detail_url": "http://localhost:8000/api/bloodbank/donor/1/"
      }
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "message": "No donor profile found. To register as a donor use the url below.",
      "redirect": "http://localhost:8000/api/bloodbank/donor/register/"
    }
    ```
- **Example**:
  ```bash
  curl -X PATCH http://localhost:8000/api/bloodbank/donor/ \
  -H "Authorization: Token abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "preferred_location": "General Hospital"
  }'
  ```

### Donor Withdraw
- **Endpoint**: `/api/bloodbank/donor/withdraw/`
- **Method**: POST
- **Permissions**: IsAuthenticated
- **Description**: Removes the authenticated user's donor profile.
- **Request Body**: None
- **Response**:
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
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/bloodbank/donor/withdraw/ \
  -H "Authorization: Token abc123token"
  ```

### Donor Detail
- **Endpoint**: `/api/bloodbank/donor/<int:pk>/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Retrieves details of a specific donor by ID.
- **Response**:
  - **200 OK**:
    ```json
    {
      "emergency_contact": "+1234567890",
      "preferred_location": "City Hospital",
      "last_donated": "2025-01-01",
      "consent": true,
      "name": "John Doe",
      "blood_group": "A+",
      "user": 1,
      "detail_url": "http://localhost:8000/api/bloodbank/donor/1/"
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "message": "Donor profile not found."
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/bloodbank/donor/1/
  ```

### Donor List
- **Endpoint**: `/api/bloodbank/donors/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Retrieves a paginated list of donors, with optional filters.
- **Query Parameters**:
  - `blood_group`: Filter by blood group (e.g., `A+`)
  - `location`: Filter by preferred location (case-insensitive)
  - `last_donated_before`: Filter by last donated date before (YYYY-MM-DD)
  - `last_donated_after`: Filter by last donated date after (YYYY-MM-DD)
- **Response**:
  - **200 OK**:
    ```json
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "emergency_contact": "+1234567890",
          "preferred_location": "City Hospital",
          "last_donated": "2025-01-01",
          "consent": true,
          "name": "John Doe",
          "blood_group": "A+",
          "user": 1,
          "detail_url": "http://localhost:8000/api/bloodbank/donor/1/"
        }
      ]
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "message": "Invalid date format for last_donated_before. Use YYYY-MM-DD."
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/bloodbank/donors/?blood_group=A+&limit=10
  ```

### Blood Request List/Create
- **Endpoint**: `/api/bloodbank/requests/`
- **Method**: GET, POST
- **Permissions**: GET (AllowAny), POST (IsAuthenticated)
- **Description**: Lists open blood requests or creates a new blood request.
- **Request Body (POST)**:
  ```json
  {
    "blood_group": "A+",
    "university": 1,
    "title": "Urgent Blood Needed",
    "description": "Need A+ blood for surgery.",
    "request_date": "2025-05-20",
    "urgent": true,
    "location": "City Hospital"
  }
  ```
- **Response**:
  - **GET (200 OK)**:
    ```json
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "user": {
            "id": 1,
            "name": "John Doe",
            "detail_url": "http://localhost:8000/api/accounts/1/"
          },
          "blood_group": "A+",
          "university": 1,
          "title": "Urgent Blood Needed",
          "description": "Need A+ blood for surgery.",
          "request_date": "2025-05-20",
          "urgent": true,
          "location": "City Hospital",
          "status": "open",
          "created_at": "2025-05-17T01:27:00Z",
          "updated_at": "2025-05-17T01:27:00Z",
          "resolved_by": null,
          "media": [],
          "registered_donors": []
        }
      ]
    }
    ```
  - **POST (201 Created)**:
    ```json
    {
      "id": 1,
      "user": {
        "id": 1,
        "name": "John Doe",
        "detail_url": "http://localhost:8000/api/accounts/1/"
      },
      "blood_group": "A+",
      "university": 1,
      "title": "Urgent Blood Needed",
      "description": "Need A+ blood for surgery.",
      "request_date": "2025-05-20",
      "urgent": true,
      "location": "City Hospital",
      "status": "open",
      "created_at": "2025-05-17T01:27:00Z",
      "updated_at": "2025-05-17T01:27:00Z",
      "resolved_by": null,
      "media": [],
      "registered_donors": []
    }
    ```
  - **POST (400 Bad Request)**:
    ```json
    {
      "error": {
        "blood_group": ["Blood group 'X+' does not exist."]
      }
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/bloodbank/requests/ \
  -H "Authorization: Token abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "blood_group": "A+",
    "university": 1,
    "title": "Urgent Blood Needed",
    "description": "Need A+ blood for surgery.",
    "request_date": "2025-05-20",
    "urgent": true,
    "location": "City Hospital"
  }'
  ```

### Blood Request Detail
- **Endpoint**: `/api/bloodbank/requests/<int:pk>/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Retrieves details of a specific open blood request.
- **Response**:
  - **200 OK**:
    ```json
    {
      "id": 1,
      "user": {
        "id": 1,
        "name": "John Doe",
        "detail_url": "http://localhost:8000/api/accounts/1/"
      },
      "blood_group": "A+",
      "university": 1,
      "title": "Urgent Blood Needed",
      "description": "Need A+ blood for surgery.",
      "request_date": "2025-05-20",
      "urgent": true,
      "location": "City Hospital",
      "status": "open",
      "created_at": "2025-05-17T01:27:00Z",
      "updated_at": "2025-05-17T01:27:00Z",
      "resolved_by": null,
      "media": [],
      "registered_donors": []
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Blood request not found, not approved, or resolved."
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/bloodbank/requests/1/
  ```

### Blood Request Delete
- **Endpoint**: `/api/bloodbank/requests/<int:pk>/delete/`
- **Method**: DELETE
- **Permissions**: IsAuthenticated
- **Description**: Deletes a blood request if the user is the owner or a university admin.
- **Response**:
  - **204 No Content**:
    ```json
    {
      "message": "Blood request deleted successfully."
    }
    ```
  - **403 Forbidden**:
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
- **Example**:
  ```bash
  curl -X DELETE http://localhost:8000/api/bloodbank/requests/1/delete/ \
  -H "Authorization: Token abc123token"
  ```

### Blood Request Donor Register
- **Endpoint**: `/api/bloodbank/requests/donor/register/`
- **Method**: POST
- **Permissions**: IsAuthenticated
- **Description**: Registers the authenticated user (who must be a donor) to donate for a blood request.
- **Request Body**:
  ```json
  {
    "blood_request": 1,
    "message": "I am available to donate on May 20.",
    "contact_info": "+1234567890"
  }
  ```
- **Response**:
  - **201 Created**:
    ```json
    {
      "id": 1,
      "blood_request": 1,
      "donor": {
        "id": 1,
        "name": "John Doe",
        "blood_group": "A+",
        "emergency_contact": "+1234567890",
        "preferred_location": "City Hospital",
        "detail_url": "http://localhost:8000/api/bloodbank/donor/1/"
      },
      "message": "I am available to donate on May 20.",
      "contact_info": "+1234567890",
      "created_at": "2025-05-17T01:27:00Z"
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "error": {
        "non_field_errors": ["You have already registered to donate for this request."]
      }
    }
    ```
  - **400 Bad Request (Not a Donor)**:
    ```json
    {
      "message": "You must be registered as a donor to volunteer for a blood request.",
      "redirect": "http://localhost:8000/api/bloodbank/donor/register/"
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/bloodbank/requests d/ \
  -H "Authorization: Token abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "blood_request": 1,
    "message": "I am available to donate on May 20.",
    "contact_info": "+1234567890"
  }'
  ```

### Blood Request Donor List
- **Endpoint**: `/api/bloodbank/requests/<int:pk>/donors/`
- **Method**: GET
- **Permissions**: IsAuthenticated
- **Description**: Lists registered donors for a specific open blood request, accessible to the request owner or admins.
- **Response**:
  - **200 OK**:
    ```json
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "blood_request": 1,
          "donor": {
            "id": 1,
            "name": "John Doe",
            "blood_group": "A+",
            "emergency_contact": "+1234567890",
            "preferred_location": "City Hospital",
            "detail_url": "http://localhost:8000/api/bloodbank/donor/1/"
          },
          "message": "I am available to donate on May 20.",
          "contact_info": "+1234567890",
          "created_at": "2025-05-17T01:27:00Z"
        }
      ]
    }
    ```
  - **403 Forbidden**:
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
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/bloodbank/requests/1/donors/ \
  -H "Authorization: Token abc123token"
  ```

---

## Lost and Found API

### All Items List
- **Endpoint**: `/api/lostandfound/all/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Lists all approved, unresolved lost and found items.
- **Response**:
  - **200 OK**:
    ```json
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "user": {
            "id": 1,
            "name": "John Doe",
            "detail_url": "http://localhost:8000/api/accounts/1/"
          },
          "title": "Lost Wallet",
          "description": "Black leather wallet lost in library.",
          "lost_date": "2025-05-15",
          "approximate_time": "14:30:00",
          "location": "Main Library",
          "status": "open",
          "approval_status": "approved",
          "created_at": "2025-05-17T01:27:00Z",
          "updated_at": "2025-05-17T01:27:00Z",
          "media": [],
          "post_type": "lost",
          "is_admin": false,
          "detail_url": "http://localhost:8000/api/lostandfound/lost/1/",
          "claims_url": "http://localhost:8000/api/lostandfound/lost/1/claims/",
          "resolve_url": null,
          "approve_url": null
        }
      ]
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/lostandfound/all/
  ```

### Pending Items List
- **Endpoint**: `/api/lostandfound/pending/`
- **Method**: GET
- **Permissions**: IsAuthenticated, AdminPermission
- **Description**: Lists pending lost and found items for admins.
- **Response**:
  - **200 OK**:
    ```json
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "user": {
            "id": 1,
            "name": "John Doe",
            "detail_url": "http://localhost:8000/api/accounts/1/"
          },
          "title": "Lost Wallet",
          "description": "Black leather wallet lost in library.",
          "lost_date": "2025-05-15",
          "approximate_time": "14:30:00",
          "location": "Main Library",
          "status": "open",
          "approval_status": "pending",
          "created_at": "2025-05-17T01:27:00Z",
          "updated_at": "2025-05-17T01:27:00Z",
          "media": [],
          "post_type": "lost",
          "is_admin": true,
          "detail_url": "http://localhost:8000/api/lostandfound/lost/1/",
          "claims_url": "http://localhost:8000/api/lostandfound/lost/1/claims/",
          "resolve_url": null,
          "approve_url": "http://localhost:8000/api/lostandfound/lost/1/approve/"
        }
      ]
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/lostandfound/pending/ \
  -H "Authorization: Token abc123token"
  ```

### Resolved Items List
- **Endpoint**: `/api/lostandfound/resolved/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Lists approved, resolved lost and found items.
- **Response**:
  - **200 OK**:
    ```json
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "user": {
            "id": 1,
            "name": "John Doe",
            "detail_url": "http://localhost:8000/api/accounts/1/"
          },
          "title": "Lost Wallet",
          "description": "Black leather wallet lost in library.",
          "lost_date": "2025-05-15",
          "approximate_time": "14:30:00",
          "location": "Main Library",
          "status": "found",
          "approval_status": "approved",
          "created_at": "2025-05-17T01:27:00Z",
          "updated_at": "2025-05-17T01:27:00Z",
          "media": [],
          "post_type": "lost",
          "is_admin": false,
          "detail_url": "http://localhost:8000/api/lostandfound/lost/1/",
          "claims_url": "http://localhost:8000/api/lostandfound/lost/1/claims/",
          "resolve_url": null,
          "approve_url": null
        }
      ]
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/lostandfound/resolved/
  ```

### Lost Item List/Create
- **Endpoint**: `/api/lostandfound/lost/`
- **Method**: GET, POST
- **Permissions**: GET (AllowAny), POST (IsAuthenticated)
- **Description**: Lists approved, unresolved lost items or creates a new lost item (pending approval).
- **Request Body (POST)**:
  ```json
  {
    "university": 1,
    "title": "Lost Wallet",
    "description": "Black leather wallet lost in library.",
    "lost_date": "2025-05-15",
    "approximate_time": "14:30:00",
    "location": "Main Library",
    "media_files": []
  }
  ```
- **Response**:
  - **GET (200 OK)**:
    ```json
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "user": {
            "id": 1,
            "name": "John Doe",
            "detail_url": "http://localhost:8000/api/accounts/1/"
          },
          "title": "Lost Wallet",
          "description": "Black leather wallet lost in library.",
          "lost_date": "2025-05-15",
          "approximate_time": "14:30:00",
          "location": "Main Library",
          "status": "open",
          "approval_status": "approved",
          "created_at": "2025-05-17T01:27:00Z",
          "updated_at": "2025-05-17T01:27:00Z",
          "media": [],
          "post_type": "lost",
          "is_admin": false,
          "detail_url": "http://localhost:8000/api/lostandfound/lost/1/",
          "claims_url": "http://localhost:8000/api/lostandfound/lost/1/claims/",
          "resolve_url": null,
          "approve_url": null
        }
      ]
    }
    ```
  - **POST (201 Created)**:
    ```json
    {
      "id": 1,
      "user": {
        "id": 1,
        "name": "John Doe",
        "detail_url": "http://localhost:8000/api/accounts/1/"
      },
      "university": 1,
      "title": "Lost Wallet",
      "description": "Black leather wallet lost in library.",
      "lost_date": "2025-05-15",
      "approximate_time": "14:30:00",
      "location": "Main Library",
      "status": "open",
      "approval_status": "pending",
      "created_at": "2025-05-17T01:27:00Z",
      "updated_at": "2025-05-17T01:27:00Z",
      "media": [],
      "post_type": "lost",
      "is_admin": false,
      "detail_url": "http://localhost:8000/api/lostandfound/lost/1/",
      "claims_url": "http://localhost:8000/api/lostandfound/lost/1/claims/",
      "resolve_url": "http://localhost:8000/api/lostandfound/lost/1/resolve/",
      "approve_url": null
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/lostandfound/lost/ \
  -H "Authorization: Token abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "university": 1,
    "title": "Lost Wallet",
    "description": "Black leather wallet lost in library.",
    "lost_date": "2025-05-15",
    "approximate_time": "14:30:00",
    "location": "Main Library"
  }'
  ```

### Found Item List/Create
- **Endpoint**: `/api/lostandfound/found/`
- **Method**: GET, POST
- **Permissions**: GET (AllowAny), POST (IsAuthenticated)
- **Description**: Lists approved, unresolved found items or creates a new found item (pending approval).
- **Request Body (POST)**:
  ```json
  {
    "university": 1,
    "title": "Found Wallet",
    "description": "Found a black leather wallet in library.",
    "found_date": "2025-05-15",
    "approximate_time": "14:30:00",
    "location": "Main Library",
    "media_files": []
  }
  ```
- **Response**:
  - **GET (200 OK)**:
    ```json
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "user": {
            "id": 1,
            "name": "John Doe",
            "detail_url": "http://localhost:8000/api/accounts/1/"
          },
          "title": "Found Wallet",
          "description": "Found a black leather wallet in library.",
          "found_date": "2025-05-15",
          "approximate_time": "14:30:00",
          "location": "Main Library",
          "status": "open",
          "approval_status": "approved",
          "created_at": "2025-05-17T01:27:00Z",
          "updated_at": "2025-05-17T01:27:00Z",
          "media": [],
          "post_type": "found",
          "is_admin": false,
          "detail_url": "http://localhost:8000/api/lostandfound/found/1/",
          "claims_url": "http://localhost:8000/api/lostandfound/found/1/claims/",
          "resolve_url": null,
          "approve_url": null
        }
      ]
    }
    ```
  - **POST (201 Created)**:
    ```json
    {
      "id": 1,
      "user": {
        "id": 1,
        "name": "John Doe",
        "detail_url": "http://localhost:8000/api/accounts/1/"
      },
      "university": 1,
      "title": "Found Wallet",
      "description": "Found a black leather wallet in library.",
      "found_date": "2025-05-15",
      "approximate_time": "14:30:00",
      "location": "Main Library",
      "status": "open",
      "approval_status": "pending",
      "created_at": "2025-05-17T01:27:00Z",
      "updated_at": "2025-05-17T01:27:00Z",
      "media": [],
      "post_type": "found",
      "is_admin": false,
      "detail_url": "http://localhost:8000/api/lostandfound/found/1/",
      "claims_url": "http://localhost:8000/api/lostandfound/found/1/claims/",
      "resolve_url": "http://localhost:8000/api/lostandfound/found/1/resolve/",
      "approve_url": null
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/lostandfound/found/ \
  -H "Authorization: Token abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "university": 1,
    "title": "Found Wallet",
    "description": "Found a black leather wallet in library.",
    "found_date": "2025-05-15",
    "approximate_time": "14:30:00",
    "location": "Main Library"
  }'
  ```

### Lost Item Detail
- **Endpoint**: `/api/lostandfound/lost/<int:pk>/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Retrieves details of a specific approved, unresolved lost item.
- **Response**:
  - **200 OK**:
    ```json
    {
      "id": 1,
      "user": {
        "id": 1,
        "name": "John Doe",
        "detail_url": "http://localhost:8000/api/accounts/1/"
      },
      "title": "Lost Wallet",
      "description": "Black leather wallet lost in library.",
      "lost_date": "2025-05-15",
      "approximate_time": "14:30:00",
      "location": "Main Library",
      "status": "open",
      "approval_status": "approved",
      "created_at": "2025-05-17T01:27:00Z",
      "updated_at": "2025-05-17T01:27:00Z",
      "media": [],
      "post_type": "lost",
      "is_admin": false,
      "detail_url": "http://localhost:8000/api/lostandfound/lost/1/",
      "claims_url": "http://localhost:8000/api/lostandfound/lost/1/claims/",
      "resolve_url": null,
      "approve_url": null
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Lost item not found, not approved, or resolved."
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/lostandfound/lost/1/
  ```

### Found Item Detail
- **Endpoint**: `/api/lostandfound/found/<int:pk>/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Retrieves details of a specific approved, unresolved found item.
- **Response**:
  - **200 OK**:
    ```json
    {
      "id": 1,
      "user": {
        "id": 1,
        "name": "John Doe",
        "detail_url": "http://localhost:8000/api/accounts/1/"
      },
      "title": "Found Wallet",
      "description": "Found a black leather wallet in library.",
      "found_date": "2025-05-15",
      "approximate_time": "14:30:00",
      "location": "Main Library",
      "status": "open",
      "approval_status": "approved",
      "created_at": "2025-05-17T01:27:00Z",
      "updated_at": "2025-05-17T01:27:00Z",
      "media": [],
      "post_type": "found",
      "is_admin": false,
      "detail_url": "http://localhost:8000/api/lostandfound/found/1/",
      "claims_url": "http://localhost:8000/api/lostandfound/found/1/claims/",
      "resolve_url": null,
      "approve_url": null
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Found item not found, not approved, or resolved."
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/lostandfound/found/1/
  ```

### Lost Item Claim
- **Endpoint**: `/api/lostandfound/lost/claim/`
- **Method**: POST
- **Permissions**: IsAuthenticated
- **Description**: Creates a claim for an approved, open lost item.
- **Request Body**:
  ```json
  {
    "lost_item": 1,
    "description": "I believe this is my wallet, lost on May 15.",
    "media_files": []
  }
  ```
- **Response**:
  - **201 Created**:
    ```json
    {
      "id": 1,
      "lost_item": 1,
      "claimant": {
        "id": 2,
        "name": "Jane Doe",
        "detail_url": "http://localhost:8000/api/accounts/2/"
      },
      "description": "I believe this is my wallet, lost on May 15.",
      "created_at": "2025-05-17T01:27:00Z",
      "media": []
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "error": {
        "non_field_errors": ["You cannot claim your own lost item."]
      }
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/lostandfound/lost/claim/ \
  -H "Authorization: Token abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "lost_item": 1,
    "description": "I believe this is my wallet, lost on May 15."
  }'
  ```

### Found Item Claim
- **Endpoint**: `/api/lostandfound/found/claim/`
- **Method**: POST
- **Permissions**: IsAuthenticated
- **Description**: Creates a claim for an approved, open found item.
- **Request Body**:
  ```json
  {
    "found_item": 1,
    "description": "I lost a wallet matching this description.",
    "media_files": []
  }
  ```
- **Response**:
  - **201 Created**:
    ```json
    {
      "id": 1,
      "found_item": 1,
      "claimant": {
        "id": 2,
        "name": "Jane Doe",
        "detail_url": "http://localhost:8000/api/accounts/2/"
      },
      "description": "I lost a wallet matching this description.",
      "created_at": "2025-05-17T01:27:00Z",
      "media": []
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "error": {
        "non_field_errors": ["You cannot claim your own found item."]
      }
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/lostandfound/found/claim/ \
  -H "Authorization: Token abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "foundAXIS": 1,
    "description": "I lost a wallet matching this description."
  }'
  ```

### Lost Item Resolve
- **Endpoint**: `/api/lostandfound/lost/<int:pk>/resolve/`
- **Method**: POST
- **Permissions**: IsAuthenticated
- **Description**: Resolves an approved, unresolved lost item (only by the owner).
- **Request Body**:
  ```json
  {
    "status": "found",
    "resolved_by": 2
  }
  ```
- **Response**:
  - **200 OK**:
    ```json
    {
      "message": "Lost item resolved as 'found'."
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "error": {
        "non_field_errors": ["Resolved_by must be one of the claimants."]
      }
    }
    ```
  - **403 Forbidden**:
    ```json
    {
      "error": "Only the item owner can resolve this item."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Lost item not found, not approved, or already resolved."
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/lostandfound/lost/1/resolve/ \
  -H "Authorization: Token abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "found",
    "resolved_by": 2
  }'
  ```

### Found Item Resolve
- **Endpoint**: `/api/lostandfound/found/<int:pk>/resolve/`
- **Method**: POST
- **Permissions**: IsAuthenticated
- **Description**: Resolves an approved, unresolved found item (only by the owner).
- **Request Body**:
  ```json
  {
    "status": "returned",
    "resolved_by": 2
  }
  ```
- **Response**:
  - **200 OK**:
    ```json
    {
      "message": "Found item resolved as 'returned'."
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "error": {
        "non_field_errors": ["Resolved_by must be one of the claimants."]
      }
    }
    ```
  - **403 Forbidden**:
    ```json
    {
      "error": "Only the item owner can resolve this item."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Found item not found, not approved, or already resolved."
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/lostandfound/found/1/resolve/ \
  -H "Authorization: Token abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "returned",
    "resolved_by": 2
  }'
  ```

### Lost Item Approve
- **Endpoint**: `/api/lostandfound/lost/<int:pk>/approve/`
- **Method**: POST
- **Permissions**: IsAuthenticated, UniversityAdminPermission
- **Description**: Approves or rejects a lost item (only by authorized admins).
- **Request Body**:
  ```json
  {
    "approval_status": "approved"
  }
  ```
- **Response**:
  - **200 OK**:
    ```json
    {
      "message": "Lost item 'Lost Wallet' approved."
    }
    ```
  - **403 Forbidden**:
    ```json
    {
      "error": "You do not have permission to approve this item."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Lost item not found."
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/lostandfound/lost/1/approve/ \
  -H "Authorization: Token abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "approval_status": "approved"
  }'
  ```

### Found Item Approve
- **Endpoint**: `/api/lostandfound/found/<int:pk>/approve/`
- **Method**: POST
- **Permissions**: IsAuthenticated, UniversityAdminPermission
- **Description**: Approves or rejects a found item (only by authorized admins).
- **Request Body**:
  ```json
  {
    "approval_status": "approved"
  }
  ```
- **Response**:
  - **200 OK**:
    ```json
    {
      "message": "Found item 'Found Wallet' approved."
    }
    ```
  - **403 Forbidden**:
    ```json
    {
      "error": "You do not have permission to approve this item."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Found item not found."
    }
    ```
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/lostandfound/found/1/approve/ \
  -H "Authorization: Token abc123token" \
  -H "Content-Type: application/json" \
  -d '{
    "approval_status": "approved"
  }'
  ```

### My Claims List
- **Endpoint**: `/api/lostandfound/my-claims/`
- **Method**: GET
- **Permissions**: IsAuthenticated
- **Description**: Lists all claims made by the authenticated user.
- **Response**:
  - **200 OK**:
    ```json
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "lost_item": 1,
          "claimant": {
            "id": 2,
            "name": "Jane Doe",
            "detail_url": "http://localhost:8000/api/accounts/2/"
          },
          "description": "I believe this is my wallet, lost on May 15.",
          "created_at": "2025-05-17T01:27:00Z",
          "media": []
        }
      ]
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/lostandfound/my-claims/ \
  -H "Authorization: Token abc123token"
  ```

### My Posts List
- **Endpoint**: `/api/lostandfound/my-posts/`
- **Method**: GET
- **Permissions**: IsAuthenticated
- **Description**: Lists all lost and found posts created by the authenticated user.
- **Response**:
  - **200 OK**:
    ```json
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "user": {
            "id": 1,
            "name": "John Doe",
            "detail_url": "http://localhost:8000/api/accounts/1/"
          },
          "title": "Lost Wallet",
          "description": "Black leather wallet lost in library.",
          "lost_date": "2025-05-15",
          "approximate_time": "14:30:00",
          "location": "Main Library",
          "status": "open",
          "approval_status": "approved",
          "created_at": "2025-05-17T01:27:00Z",
          "updated_at": "2025-05-17T01:27:00Z",
          "media": [],
          "post_type": "lost",
          "is_admin": false,
          "detail_url": "http://localhost:8000/api/lostandfound/lost/1/",
          "claims_url": "http://localhost:8000/api/lostandfound/lost/1/claims/",
          "resolve_url": "http://localhost:8000/api/lostandfound/lost/1/resolve/",
          "approve_url": null
        }
      ]
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/lostandfound/my-posts/ \
  -H "Authorization: Token abc123token"
  ```

### Lost Item Claims List
- **Endpoint**: `/api/lostandfound/lost/<int:pk>/claims/`
- **Method**: GET
- **Permissions**: IsAuthenticated, PostOwnerOrAdminPermission
- **Description**: Lists all claims on a specific approved, unresolved lost item.
- **Response**:
  - **200 OK**:
    ```json
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "lost_item": 1,
          "claimant": {
            "id": 2,
            "name": "Jane Doe",
            "detail_url": "http://localhost:8000/api/accounts/2/"
          },
          "description": "I believe this is my wallet, lost on May 15.",
          "created_at": "2025-05-17T01:27:00Z",
          "media": []
        }
      ]
    }
    ```
  - **403 Forbidden**:
    ```json
    {
      "error": "You do not have permission to view claims for this item."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Lost item not found, not approved, or resolved."
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/lostandfound/lost/1/claims/ \
  -H "Authorization: Token abc123token"
  ```

### Found Item Claims List
- **Endpoint**: `/api/lostandfound/found/<int:pk>/claims/`
- **Method**: GET
- **Permissions**: IsAuthenticated, PostOwnerOrAdminPermission
- **Description**: Lists all claims on a specific approved, unresolved found item.
- **Response**:
  - **200 OK**:
    ```json
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 1,
          "found_item": 1,
          "claimant": {
            "id": 2,
            "name": "Jane Doe",
            "detail_url": "http://localhost:8000/api/accounts/2/"
          },
          "description": "I lost a wallet matching this description.",
          "created_at": "2025-05-17T01:27:00Z",
          "media": []
        }
      ]
    }
    ```
  - **403 Forbidden**:
    ```json
    {
      "error": "You do not have permission to view claims for this item."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Found item not found, not approved, or resolved."
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/lostandfound/found/1/claims/ \
  -H "Authorization: Token abc123token"
  ```

### History
- **Endpoint**: `/api/lostandfound/history/`
- **Method**: GET
- **Permissions**: IsAuthenticated
- **Description**: Retrieves the authenticated user's activity history (posts, claims made, claims received).
- **Response**:
  - **200 OK**:
    ```json
    {
      "posts": [
        {
          "id": 1,
          "user": {
            "id": 1,
            "name": "John Doe",
            "detail_url": "http://localhost:8000/api/accounts/1/"
          },
          "title": "Lost Wallet",
          "description": "Black leather wallet lost in library.",
          "lost_date": "2025-05-15",
          "approximate_time": "14:30:00",
          "location": "Main Library",
          "status": "open",
          "approval_status": "approved",
          "created_at": "2025-05-17T01:27:00Z",
          "updated_at": "2025-05-17T01:27:00Z",
          "media": [],
          "post_type": "lost",
          "is_admin": false,
          "detail_url": "http://localhost:8000/api/lostandfound/lost/1/",
          "claims_url": "http://localhost:8000/api/lostandfound/lost/1/claims/",
          "resolve_url": "http://localhost:8000/api/lostandfound/lost/1/resolve/",
          "approve_url": null
        }
      ],
      "claims_made": [
        {
          "id": 1,
          "found_item": 1,
          "claimant": {
            "id": 1,
            "name": "John Doe",
            "detail_url": "http://localhost:8000/api/accounts/1/"
          },
          "description": "I lost a wallet matching this description.",
          "created_at": "2025-05-17T01:27:00Z",
          "media": []
        }
      ],
      "claims_received": [
        {
          "id": 1,
          "lost_item": 1,
          "claimant": {
            "id": 2,
            "name": "Jane Doe",
            "detail_url": "http://localhost:8000/api/accounts/2/"
          },
          "description": "I believe this is my wallet, lost on May 15.",
          "created_at": "2025-05-17T01:27:00Z",
          "media": []
        }
      ]
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/lostandfound/history/ \
  -H "Authorization: Token abc123token"
  ```

### Media Access
- **Endpoint**: `/api/lostandfound/media/<str:pk>/`
- **Method**: GET
- **Permissions**: IsAuthenticated
- **Description**: Provides access to media files for authorized users (owners, claimants, or admins).
- **Response**:
  - **200 OK**: Returns the media file (e.g., image or video) with appropriate content type.
  - **403 Forbidden**:
    ```json
    {
      "error": "You do not have permission to access this media."
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "error": "Media not found."
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/lostandfound/media/abc123media/ \
  -H "Authorization: Token abc123token"
  ```

---

## Universities API

### University List
- **Endpoint**: `/api/universities/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Retrieves a list of all universities.
- **Response**:
  - **200 OK**:
    ```json
    [
      {
        "id": 1,
        "name": "Example University",
        "short_name": "EU"
      }
    ]
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/universities/
  ```

### Department List
- **Endpoint**: `/api/universities/departments/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Retrieves a list of all departments.
- **Response**:
  - **200 OK**:
    ```json
    [
      {
        "id": 1,
        "name": "Department of Computer Science",
        "short_name": "CS",
        "unit_type": "department",
        "university": {
          "id": 1,
          "name": "Example University",
          "short_name": "EU"
        }
      }
    ]
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/universities/departments/
  ```

### Institute List
- **Endpoint**: `/api/universities/institutes/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Retrieves a list of all institutes.
- **Response**:
  - **200 OK**:
    ```json
    [
      {
        "id": 2,
        "name": "Institute of Technology",
        "short_name": "IT",
        "unit_type": "institute",
        "university": {
          "id": 1,
          "name": "Example University",
          "short_name": "EU"
        }
      }
    ]
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/universities/institutes/
  ```

### Teacher Designation List
- **Endpoint**: `/api/universities/teacher-designations/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Retrieves a list of all teacher designations.
- **Response**:
  - **200 OK**:
    ```json
    [
      {
        "id": 1,
        "name": "Professor"
      },
      {
        "id": 2,
        "name": "Associate Professor"
      }
    ]
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/universities/teacher-designations/
  ```

### Department and Institute List
- **Endpoint**: `/api/universities/departments-institutes/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Retrieves departments and institutes, optionally filtered by university short name.
- **Query Parameters**:
  - `name`: University short name (e.g., `EU`)
- **Response**:
  - **200 OK**:
    ```json
    {
      "departments": [
        {
          "id": 1,
          "name": "Department of Computer Science",
          "short_name": "CS",
          "unit_type": "department",
          "university": {
            "id": 1,
            "name": "Example University",
            "short_name": "EU"
          }
        }
      ],
      "institutes": [
        {
          "id": 2,
          "name": "Institute of Technology",
          "short_name": "IT",
          "unit_type": "institute",
          "university": {
            "id": 1,
            "name": "Example University",
            "short_name": "EU"
          }
        }
      ]
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "message": "University not found."
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/universities/departments-institutes/?name=EU
  ```

### University Users
- **Endpoint**: `/api/universities/<str:university_short_name>/users/`
- **Method**: GET
- **Permissions**: AllowAny
- **Description**: Retrieves users associated with a specific university, categorized by role.
- **Response**:
  - **200 OK**:
    ```json
    {
      "students": [
        {
          "id": 1,
          "name": "John Doe",
          "role": "student",
          "admin_level": "none",
          "university": {
            "name": "Example University",
            "short_name": "EU"
          },
          "academic_unit": {
            "name": "Department of Computer Science",
            "short_name": "CS",
            "unit_type": "department"
          },
          "detail_url": "http://localhost:8000/api/accounts/1/"
        }
      ],
      "teachers": [],
      "officers": [],
      "staff": []
    }
    ```
  - **404 Not Found**:
    ```json
    {
      "message": "University not found."
    }
    ```
- **Example**:
  ```bash
  curl -X GET http://localhost:8000/api/universities/EU/users/
  ```

---

## Authentication

- **Token Authentication**: Most endpoints requiring `IsAuthenticated` permission expect an `Authorization` header with a token obtained from the `/api/accounts/login/` endpoint.
  - Format: `Authorization: Token <token>`
- **Permissions**:
  - `AllowAny`: Accessible to all users, including unauthenticated ones.
  - `IsAuthenticated`: Requires a valid token.
  - `AdminPermission`: Requires the user to have `university` or `app` admin level.
  - `UniversityAdminPermission`: Requires the user to be an admin for the specific university associated with the resource.
  - `PostOwnerOrAdminPermission`: Requires the user to be the resource owner or an authorized admin.

## Notes

- All dates and times are in ISO 8601 format (e.g., `2025-05-17T01:27:00Z` for datetimes, `2025-05-15` for dates, `14:30:00` for times).
- Media files (for lost and found items/claims) are uploaded via multipart form data and accessed via the `/api/lostandfound/media/<str:pk>/` endpoint.
- Pagination is supported for list endpoints using `limit` and `offset` query parameters.
- Error responses typically include a `message` or `error` field with details.