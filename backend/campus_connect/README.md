# 🌐 Campus Connect Backend (Django)

This Django REST API powers **Campus Connect**, a platform to manage:

- ✅ User registration and login
- ✅ Email verification with codes
- ✅ Profile visibility & token-based authentication
- ✅ Blood donation registration and tracking

---

## 🧭 Table of Contents

1. [Installation](#installation)
2. [Authentication](#authentication)
3. [Accounts API](#accounts-api)
4. [Bloodbank API](#bloodbank-api)
5. [Testing](#testing)
6. [Requirements](#requirements)
7. [Git Best Practices](#gitignore-suggestions)
8. [License](#license)

---

Certainly! Here’s how your **original setup code snippet** should be embedded in your `README.md` under the **Installation** section:

---

## 📦 Installation

```bash
git clone https://github.com/SaifullahMnsur-Again/campus_connect-undergrad_swe_project.git
cd campus_connect-undergrad_swe_project/backend/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd campus_connect
python manage.py migrate

# Load initial blood groups into the database
python manage.py load_bloodgroups

python manage.py runserver
```

---

## 🔐 Authentication

Token-based authentication is used.

After login, include this in headers:

```http
Authorization: Token <your_token>
```

---

## 🧑‍💼 Accounts API

**Base URL**: `/api/accounts/`

| Endpoint         | Method | Description                             | Auth Required |
| ---------------- | ------ | --------------------------------------- | ------------- |
| `/register/`     | POST   | Register a new user                     | ❌ No          |
| `/verify-email/` | POST   | Verify email with 6-digit code          | ❌ No          |
| `/login/`        | POST   | Log in and receive authentication token | ❌ No          |
| `/logout/`       | POST   | Log out (deletes token)                 | ✅ Yes         |
| `/profile/`      | GET    | Get current user's profile              | ✅ Yes         |
| `/profile/`      | PATCH  | Update current user's profile           | ✅ Yes         |
| `/`              | GET    | Public paginated user list              | ❌ No          |
| `/<int:pk>/`     | GET    | Public profile of a user by ID          | ❌ No          |

---

### 🔹 Register a User

**POST** `/api/accounts/register/`

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password123",
  "confirm_password": "password123",
  "blood_group": "A+"
}
```

---

### 🔹 Verify Email

**POST** `/api/accounts/verify-email/`

```json
{
  "email": "john@example.com",
  "code": "123456"
}
```

> ⚠️ Code is sent (printed/logged for dev); expires in 15 mins.

---

### 🔹 Login

**POST** `/api/accounts/login/`

```json
{
  "email": "john@example.com",
  "password": "password123"
}
```

**Response**:

```json
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

---

### 🔹 Logout

**POST** `/api/accounts/logout/`
**Headers**: `Authorization: Token <token>`

Logs out the user by deleting the token.

---

### 🔹 View Own Profile

**GET** `/api/accounts/profile/`

Returns your user info (respects contact visibility settings).

---

### 🔹 Update Profile

**PATCH** `/api/accounts/profile/`

```json
{
  "phone": "+1234567890",
  "contact_visibility": "email"
}
```

---

### 🔹 List Users

**GET** `/api/accounts/`

Query Parameters:

* `limit=20`
* `offset=0`

Returns:

```json
{
  "count": 100,
  "results": [
    {
      "id": 1,
      "name": "Jane Doe",
      "detail_url": "http://.../api/accounts/1/"
    }
  ]
}
```

---

### 🔹 View Public Profile by ID

**GET** `/api/accounts/<user_id>/`

Returns filtered info depending on the user’s visibility settings.

---

## 🩸 Bloodbank API

**Base URL**: `/api/bloodbank/`

---

### 🔬 Blood Groups

| Endpoint                 | Method | Description                     | Auth Required |
| ------------------------ | ------ | ------------------------------- | ------------- |
| `/bloodgroups/`          | GET    | List all available blood groups | ❌ No          |
| `/bloodgroups/<int:pk>/` | GET    | Get single blood group detail   | ❌ No          |

**Example response**:

```json
["A+", "B+", "O-", "AB-"]
```

---

### 🩺 Donor Management

| Endpoint           | Method | Description                         | Auth Required |
| ------------------ | ------ | ----------------------------------- | ------------- |
| `/donor/register/` | POST   | Register current user as donor      | ✅ Yes         |
| `/donor/`          | GET    | View current user's donor profile   | ✅ Yes         |
| `/donor/`          | PATCH  | Update current user's donor profile | ✅ Yes         |
| `/donor/profile/`  | GET    | Alias for `/donor/`                 | ✅ Yes         |
| `/donor/profile/`  | PATCH  | Alias for `/donor/`                 | ✅ Yes         |
| `/donor/withdraw/` | POST   | Delete donor profile (withdraw)     | ✅ Yes         |
| `/donor/<int:pk>/` | GET    | View another donor's public profile | ❌ No          |

---

### 🔹 Register as Donor

**POST** `/api/bloodbank/donor/register/`

```json
{
  "emergency_contact": "+1234567890",
  "preferred_location": "City Hospital",
  "last_donated": "2025-01-01",
  "consent": true
}
```

---

### 🔹 Update Donor Profile

**PATCH** `/api/bloodbank/donor/`

```json
{
  "preferred_location": "Updated Clinic",
  "consent": false
}
```

---

### 🔹 Withdraw from Donor Program

**POST** `/api/bloodbank/donor/withdraw/`

**Response**:

```json
{
  "message": "Donor profile withdrawn successfully."
}
```

---

### 🔹 View Public Donor Profile by ID

**GET** `/api/bloodbank/donor/<id>/`

Returns donor info (no edit privileges).

---

## 🧪 Testing

Run the full test suite using:

```bash
python manage.py test accounts
python manage.py test bloodbank
```

Covers:

* Registration + verification
* Login/logout
* Donor profile management
* Public/private access controls
* Load testing with 100+ users

---

## ⚙️ Requirements

```txt
Django>=3.2
djangorestframework>=3.12
djangorestframework-authtoken
Faker>=8.0
```

Generate:

```bash
pip freeze > requirements.txt
```

---

## 📁 .gitignore Suggestions

Avoid committing these:

```txt
*.pyc
__pycache__/
*.sqlite3
*.log
.env
media/
venv/
staticfiles/
.DS_Store
.idea/
.vscode/
```

---

## 📝 License