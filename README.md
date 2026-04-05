# Zorvyn Finance Backend

A Finance Data Processing and Access Control Backend built with **FastAPI**, **SQLAlchemy**, and **SQLite**.

Supports role-based access control, financial record management, and aggregated dashboard analytics.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Framework | FastAPI | Fast, modern, auto-generates `/docs` |
| Database | SQLite via SQLAlchemy ORM | Simple setup, no external DB required |
| Auth | JWT (python-jose) + bcrypt (passlib) | Stateless, industry standard |
| Validation | Pydantic v2 | Built into FastAPI, clear error messages |

---

## Project Structure

```
zorvyn-finance-backend/
├── main.py              # App entry point, router registration
├── database.py          # SQLAlchemy engine + session + get_db()
├── models.py            # ORM models: User, FinancialRecord
├── schemas.py           # Pydantic request/response models
├── auth.py              # JWT creation/decoding, password hashing
├── dependencies.py      # Reusable FastAPI deps: get_current_user,
│                        #   require_analyst_or_above, require_admin
├── routers/
│   ├── auth.py          # POST /auth/register, /auth/login
│   ├── users.py         # GET/PATCH /users (admin only)
│   ├── records.py       # CRUD /records with filters
│   └── dashboard.py     # GET /dashboard/summary, /by-category, /trends
└── requirements.txt
```

---

## Setup and Run

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Start the server**
```bash
uvicorn main:app --reload
```

**3. Open the interactive API docs**
```
http://localhost:8000/docs
```

The SQLite database (`finance.db`) is created automatically on first run. No external database setup needed.

---

## Roles and Permissions

| Action | Viewer | Analyst | Admin |
|---|:---:|:---:|:---:|
| Register / Login | ✅ | ✅ | ✅ |
| View own profile | ✅ | ✅ | ✅ |
| View financial records | ✅ | ✅ | ✅ |
| View dashboard / analytics | ✅ | ✅ | ✅ |
| Create financial records | ❌ | ✅ | ✅ |
| Update financial records | ❌ | Own only | ✅ Any |
| Delete financial records (soft) | ❌ | ❌ | ✅ |
| List all users | ❌ | ❌ | ✅ |
| Change user roles | ❌ | ❌ | ✅ |
| Activate / deactivate users | ❌ | ❌ | ✅ |

**Note:** The first user to register is automatically assigned the `admin` role. All subsequent registrations default to `viewer`.

---

## API Overview

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and receive JWT token |

### Users
| Method | Endpoint | Access |
|---|---|---|
| GET | `/users/me` | Any authenticated user |
| GET | `/users` | Admin |
| GET | `/users/{id}` | Admin |
| PATCH | `/users/{id}/role` | Admin |
| PATCH | `/users/{id}/status` | Admin |

### Financial Records
| Method | Endpoint | Access |
|---|---|---|
| POST | `/records` | Analyst, Admin |
| GET | `/records` | All authenticated |
| GET | `/records/{id}` | All authenticated |
| PATCH | `/records/{id}` | Analyst (own), Admin (any) |
| DELETE | `/records/{id}` | Admin (soft delete) |

**Supported filters on `GET /records`:**
- `record_type` — `income` or `expense`
- `category` — partial match
- `date_from` / `date_to` — ISO 8601 datetime
- `limit` / `offset` — pagination (default limit: 50)

### Dashboard
| Method | Endpoint | Access |
|---|---|---|
| GET | `/dashboard/summary` | All authenticated |
| GET | `/dashboard/by-category` | All authenticated |
| GET | `/dashboard/trends` | All authenticated |

---

## Sample API Flow

```bash
# 1. Register (first user = admin automatically)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"secret123"}'

# 2. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"secret123"}'
# → returns {"access_token": "eyJ...", "token_type": "bearer"}

# 3. Create a record (use the token from step 2)
curl -X POST http://localhost:8000/records \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"amount":5000,"type":"income","category":"Salary","date":"2026-04-01T00:00:00"}'

# 4. Get dashboard summary
curl http://localhost:8000/dashboard/summary \
  -H "Authorization: Bearer eyJ..."
```

---

## Assumptions and Design Decisions

1. **First-user admin:** The first registered user is made admin automatically. This avoids the chicken-and-egg problem of needing an admin to create the first admin.

2. **Soft deletes:** Records are never permanently deleted. `is_deleted = True` hides them from all queries while preserving data integrity. Only admins can soft-delete.

3. **Analyst record ownership:** Analysts can update only the records they created. Admins can update any record.

4. **SQLite:** Used for simplicity and zero-setup deployment. Can be swapped for PostgreSQL/MySQL by changing `DATABASE_URL` in `database.py` — the SQLAlchemy abstraction handles the rest.

5. **JWT expiry:** Tokens expire after 24 hours. The `SECRET_KEY` in `auth.py` should be replaced with a strong environment variable in production.

6. **No hard delete endpoint:** Permanent deletion is intentionally omitted. In a finance system, record history is important for auditing.

7. **Category as string:** Categories are free-form text rather than an enum/FK table. This allows flexibility without requiring a separate category management API. Can be normalized in a future iteration.

---

## Possible Enhancements (not implemented)

- Environment variable config (`python-dotenv`)
- Pagination headers (`X-Total-Count`)
- Full-text search on notes/category
- Rate limiting per user
- Unit and integration tests
- Deployed API (e.g. Render or Railway)
