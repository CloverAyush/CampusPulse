# CampusPulse: Student Institutional Issues Reporting & Resolution Platform

CampusPulse is a production-grade full-stack web platform for colleges and universities to report, deterministically route, resolve with evidence, and verify non-personal institutional problems (electrical, plumbing, cleanliness, Wi-Fi, water supply, library facilities, etc.).

---

## 🏛️ Core Principles & Architecture

### 1. REPORT vs ISSUE (First-Class Distinction)
- **`REPORT`**: An individual student's submission.
- **`ISSUE`**: The underlying campus institutional problem that $\ge 1$ reports point to.
- *Example:* Three students in Room 204 report "fan broken" independently $\to$ Resolves to **1 Issue** with **3 linked Reports** and 3 affected students.

### 2. Deterministic Existing-Issue Matching (No AI/ML or Silent Merges)
- When a student begins a report, deterministic matching checks active issues matching `(IssueType + Location + Asset)`.
- If a match is found, the system presents the existing issue and lets the student choose:
  - **"Yes, link my report to this existing issue"**
  - **"No, submit as a distinct new issue"**
- The system **never** silently auto-merges reports.

### 3. Deterministic Routing Rules
- The institution configures deterministic lookup rules `(IssueType [+ Location]) -> Handler`.
- Specific room/building rules take precedence over general campus-wide rules, with a global fallback.

### 4. Verified Resolution vs Student Verification
- **Institutional Resolution**: The assigned handler must attach verifiable proof (photo, action description, maintenance slip, or screenshot).
- **Student Verification**: Affected students confirm or dispute that the problem is fixed. If disputed, the issue reopens automatically.
- Verification requirement is configurable per issue type (e.g. Cleanliness auto-closes, Electrical requires verification).

### 5. Audit-Grade Escalation
- Handlers escalate issues with a stated reason (e.g., budget sanction $> 10,000$ INR or external vendor contract needed).
- Higher authorities (Deans/Directors) receive the complete case history snapshot (original reports, photos, handler attempts, reasons) with zero summarization.

---

## 📦 Tech Stack

- **Backend**: FastAPI, SQLAlchemy ORM, Pydantic v2, SQLite (PostgreSQL-compatible portable schema), Alembic migrations, Pytest, PyJWT, bcrypt.
- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, Lucide Icons.

---

## 🚀 Getting Started

### 1. Backend Setup & Run

```bash
# Navigate to backend
cd backend

# Create virtual environment (if not created)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations & seed realistic campus dataset
python seeds.py

# Start FastAPI server (runs on http://127.0.0.1:8000)
uvicorn app.main:app --reload --port 8000
```

FastAPI Interactive API Documentation:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### 2. Running Automated Tests

```bash
# In the backend directory with venv activated:
pytest -v tests
```

The test suite validates:
1. Deterministic routing resolution with specificity precedence (`test_routing.py`)
2. Deterministic duplicate suggestion and report linking (`test_duplicate_check.py`)
3. Complete happy path: Report $\to$ In Progress $\to$ Resolve with Evidence $\to$ Student Confirm $\to$ Close (`test_report_resolve_verify.py`)
4. Dispute/reopen path and auto-close policies (`test_report_resolve_verify.py`)
5. Escalation flow with full history snapshot preservation (`test_escalation.py`)

### 3. Frontend Setup & Run

```bash
# Navigate to frontend
cd frontend

# Install packages
npm install

# Start Next.js development server (runs on http://localhost:3000)
npm run dev
```

---

## 👥 Demo Personas (1-Click Switcher Available in UI)

| Persona | Name | Role | Scope |
| :--- | :--- | :--- | :--- |
| **Student** | Aarav Sharma | `student` | Reports issues, tracks submitted reports, verifies resolutions |
| **Facilities Handler** | Rajesh Sharma | `handler` | Receives Electrical & Facilities issues, starts work, resolves with evidence, escalates |
| **IT Handler** | Amit Deshmukh | `handler` | Receives Wi-Fi & Network issues |
| **Higher Authority** | Dr. K. Verma | `higher_authority` | Dean of Infrastructure; reviews escalated issues with full audit snapshots |
| **Admin** | Administrator | `admin` | Manages issue types, locations, and deterministic routing lookup table |

---

## 🌐 API Resource Endpoints

- `POST /api/v1/auth/login`, `POST /api/v1/auth/demo-login`, `GET /api/v1/auth/me`
- `POST /api/v1/reports/check-duplicate` — Deterministic duplicate check
- `POST /api/v1/reports` — Submit report (or link to existing issue)
- `GET /api/v1/reports/my` — Student submitted reports
- `GET /api/v1/issues` — Issues list filtered by role & status
- `GET /api/v1/issues/{id}` — Full issue details with linked reports
- `GET /api/v1/issues/{id}/history` — Chronological audit timeline
- `POST /api/v1/issues/{id}/progress` — Handler starts progress
- `POST /api/v1/issues/{id}/resolve` — Resolve with evidence
- `POST /api/v1/issues/{id}/escalate` — Escalate with stated reason
- `POST /api/v1/issues/{id}/verify` — Student confirms or disputes
- `GET /api/v1/admin/taxonomies` — Available issue types, locations, handlers
- `GET / POST / PUT /api/v1/admin/routing-rules` — Deterministic routing table
- `POST /api/v1/admin/seed-data` — Reset database with demo data

