
# Lost and Found App

The **Lost and Found App** is a Django-based RESTful API designed to help university students and staff report, claim, and resolve lost and found items within their campus community. Built with Django REST Framework, it provides a secure, user-friendly platform for managing item posts, uploading media, and tracking resolutions.

## Features
- **Post Lost/Found Items**: Users can report lost or found items with details like title, description, date, approximate time, and location.
- **Media Uploads**: Attach images or videos (jpg, jpeg, png, mp4, mov) to posts and claims, with randomized media IDs for enhanced security.
- **Claim System**: Users can submit claims for lost or found items, including supporting media.
- **Resolution**: Item owners can mark items as resolved (e.g., found, returned).
- **Simplified API Responses**: Lightweight responses for listing lost items, including essential fields and links.
- **Secure Media Access**: Media access is restricted to authorized users (item owners or claimants) via tokenized URLs.
- **Approximate Time**: Specify the approximate time of loss or discovery for better context.
- **Pagination**: Paginated responses for listing items, with `limit` and `offset` support.
- **Public and Authenticated Endpoints**: Public access for viewing items, token authentication for creating, claiming, and resolving.

## Requirements
- Python 3.8+
- Django 4.2+
- Django REST Framework 3.14+
- PostgreSQL (recommended) or SQLite
- Dependencies (see `requirements.txt`):
  - `django`
  - `djangorestframework`
  - `python-decouple` (for environment variables)
  - `pillow` (for image processing)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd campus_connect
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your_django_secret_key
   DEBUG=True
   DATABASE_URL=sqlite:///db.sqlite3  # Or PostgreSQL URL
   ```
   Generate a `SECRET_KEY` using a secure method (e.g., `python -c "import secrets; print(secrets.token_urlsafe(50))"`).

5. **Apply Migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser** (optional, for admin access):
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the Development Server**:
   ```bash
   python manage.py runserver
   ```
   The API will be available at `http://localhost:8000/api/lostandfound/`.

## Usage

### Authentication
- Most `POST` endpoints require token authentication. Obtain a token via the accounts app (e.g., `POST /api/accounts/login/`).
- Include the token in requests:
  ```
  Authorization: Token <your_token>
  ```

### Example: Create a Lost Item
```bash
curl -X POST http://localhost:8000/api/lostandfound/lost/ \
     -H "Authorization: Token <your_token>" \
     -F "university=1" \
     -F "title=Lost Wallet" \
     -F "description=Black leather wallet with ID cards" \
     -F "lost_date=2025-05-01" \
     -F "approximate_time=14:30" \
     -F "location=Library" \
     -F "media_files=@/path/to/wallet.jpg"
```

**Response**:
```json
{
  "id": 4,
  "user": {
    "id": 1,
    "name": "ICE",
    "detail_url": "http://localhost:8000/api/accounts/1/"
  },
  "university": 1,
  "title": "Lost Wallet",
  "description": "Black leather wallet with ID cards",
  "lost_date": "2025-05-01",
  "approximate_time": "14:30:00",
  "location": "Library",
  "status": "open",
  "created_at": "2025-05-16T02:07:00.123456Z",
  "media": [
    {
      "id": "xYz123456789AbCd",
      "file_url": "http://localhost:8000/api/lostandfound/media/xYz123456789AbCd/"
    }
  ]
}
```

### Example: List Lost Items
```bash
curl http://localhost:8000/api/lostandfound/lost/
```

**Response**:
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 3,
      "user": {
        "id": 1,
        "name": "ICE",
        "detail_url": "http://localhost:8000/api/accounts/1/"
      },
      "title": "Lost my wallet",
      "description": "Lost my wallet around tukitaki",
      "lost_date": "2025-04-29",
      "approximate_time": "14:30:00",
      "location": "tukitaki",
      "status": "open",
      "created_at": "2025-05-15T19:47:50.044833Z",
      "media": [
        {
          "id": "aBcDeFgHiJkLmNoP",
          "file_url": "http://localhost:8000/api/lostandfound/media/aBcDeFgHiJkLmNoP/"
        }
      ],
      "detail_url": "http://localhost:8000/api/lostandfound/lost/3/"
    }
  ]
}
```

## API Documentation
For detailed endpoint information, including request/response formats and error handling, see [lostandfound_api.md](lostandfound/docs/lostandfound_api.md). Key endpoints include:
- `GET/POST /lost/`: List or create lost items.
- `GET/POST /found/`: List or create found items.
- `POST /lost/claim/`, `POST /found/claim/`: Submit claims.
- `POST /lost/<pk>/resolve/`, `POST /found/<pk>/resolve/`: Resolve items.
- `GET /media/<pk>/`: Access media securely.

## Project Structure
```
campus_connect/
├── lostandfound/
│   ├── migrations/
│   ├── tests.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── docs/
│       └── lostandfound_api.md
├── accounts/
├── universities/
├── manage.py
├── requirements.txt
└── .env
```

## Contributing
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

Please follow the coding style (PEP 8) and include tests for new features.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For issues or questions, open an issue on the repository or contact the project maintainer.