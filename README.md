# CampusPulse

A reporting and resolution system for shared campus problems: a broken fan in Room
204, no Wi-Fi in the physics lab, an overflowing bin outside the canteen. Not for
personal grievances or complaints about people.

The system exists because of a specific failure mode. A student reports something,
it disappears into a WhatsApp group or a register at a desk, and nobody can say who
owns it or whether it was ever fixed. CampusPulse answers three questions at every
moment: **who owns this, what has happened to it, and is it actually fixed.**

---

## The four ideas the design rests on

**A report is not an issue.** A student submits a *report*. The problem itself is an
*issue*. When three students report the same broken fan, that is one issue with
three reports and three affected students, not three tickets in a queue. The
distinction is what lets the system show a handler how many people a problem affects
without anyone merging anything by hand.

**Routing is deterministic and configured, never inferred.** There is no model
guessing which department should fix something. An administrator writes rules, and
a report is matched against them in a fixed order:

| Order | Rule matches | Used when |
|-------|--------------|-----------|
| 1 | this issue type at this exact location | a rule was written for exactly this case |
| 2 | this issue type at an ancestor location | nearest ancestor wins, so a building rule covers its rooms |
| 3 | this issue type anywhere | a department owns this kind of problem campus-wide |
| 4 | any issue type at this location | one person owns everything in this place |
| 5 | any issue type at an ancestor location | as above, inherited down the hierarchy |
| 6 | the catch-all rule | miscellaneous issues nothing else claims |
| 7 | nothing matched | flagged for admin triage, administrators notified |

Ties inside a step break by priority, then by rule id. The same inputs always
produce the same handler, and an administrator can check any combination before a
student finds the gap, using **Configuration → Routing rules → Preview**.

Step 6 is the reason no report is ever silently orphaned. The catch-all rule is a
routing rule with both dropdowns left on "Any", and the API refuses to delete it
unless another one is configured to take its place.

**Escalation is a judgement, not a timer.** Nothing escalates because a clock ran
out. A handler escalates when the work is genuinely outside what they can authorise,
and must say why. The authority receives the complete case: every report, all
evidence, the full timeline, and the handler's stated reason. Nothing is summarised
away.

**Resolution requires evidence, and the students decide.** A handler cannot close an
issue by asserting it is done. They record what they did, optionally with a link to
a photo or work order. For issue types marked as requiring verification, the issue
then sits in *awaiting confirmation* until an affected student responds. Confirming
closes it. Disputing reopens it and sends it back, and the next resolution attempt
is tracked as a separate round, so a pattern of "fixed" and "still broken" is
visible rather than buried.

The first affected student to respond settles it for everyone. That is a deliberate
choice: waiting for unanimity means issues never close.

---

## What the seed data covers

`python -m scripts.seed` loads six categories, each owned by a named handler through
routing rules, plus the miscellaneous catch-all:

| Category | Typical sub-types | Why it is shaped this way |
|---|---|---|
| Physical Infrastructure | benches, fans, lights, sockets, Wi-Fi, walkways | high frequency, low severity: it adds up if ignored |
| Academic Resources | missing books, journal access, lab equipment | directly affects learning |
| Food & Health | canteen hygiene, drinking water, medical room | health-critical, so verification is required |
| Hostel & Accommodation | water or power outage, pests, overcrowding | quality of life; the warden owns anything inside a hostel block |
| Safety & Social Environment | unsafe or dark zones, broken safety equipment | **non-personal only**, see below |
| Extracurricular & Engagement | sports facilities, recreation equipment, event support | campus culture |

**Out of scope on purpose:** ragging, harassment and bullying. They are personal,
need anonymity and legal handling, and this platform shows handlers who reported an
issue. Direct those to your anti-ragging committee or Internal Complaints Committee,
not to a routing rule here.

## Who sees what

| | Their own issues | All campus issues | Reporter names | Reporter contact details |
|---|---|---|---|---|
| Student who reported it | yes | yes | yes | no |
| Student who did not | yes | yes | **no** | no |
| Assigned handler | — | their queue | yes | **yes** |
| Other handlers | — | — | yes | no |
| Higher authority | — | escalation queue | yes | yes |
| Administrator | — | everything | yes | yes |

Students can browse every issue on campus, which is the point of a shared board, but
a student who was not affected sees the reports without knowing who filed them.
Timeline entries are rewritten too, since a title like "Reported by Aarav Sharma"
would otherwise leak the name that the reporter field just hid.

Contact details go only to the staff member actually assigned to the issue, because
that is the person who may need to call someone. They are not in the general issue
payload at all.

---

## Stack

**Backend** — FastAPI, SQLAlchemy 2, Pydantic v2, Alembic, pytest. SQLite by
default, Postgres supported. Authentication is JWT bearer tokens; passwords are
bcrypt.

**Frontend** — Next.js App Router, TypeScript, Tailwind. No component library; the
UI is hand-written.

Dependencies are pinned exactly in `backend/requirements.txt` and
`frontend/package-lock.json`, and both are audited in CI.

---

## Running it

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"   # paste into SECRET_KEY
```

`SECRET_KEY` has no default. The application will not start without one, and it
refuses the key that used to be committed to this repository. See `SECURITY.md`.

```bash
alembic upgrade head            # create the schema
python -m scripts.seed          # optional: campus taxonomy, locations, routing rules
python -m scripts.create_admin --email you@campus.edu --name "Your Name"
uvicorn app.main:app --reload
```

`scripts/seed.py` generates a **different random password for every account** and
prints them once. There is no shared demo password and no seeding endpoint on the
API; reference data is an operator's job, not a request anyone can send.

Lost a password? There is no recovery, only reset:

```bash
python -m scripts.reset_password --email someone@campus.edu            # prompts
python -m scripts.reset_password --email someone@campus.edu --generate # random, printed once
```

API docs at `http://127.0.0.1:8000/docs` in development. They are disabled when
`ENVIRONMENT=production`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### Tests

```bash
cd backend && python -m pytest          # 108 tests, about 3 seconds
cd frontend && npx tsc --noEmit && npx eslint src
```

The test suite builds its schema by **running the real migrations**, so a model
change without a matching migration fails the suite instead of failing a deployment.

---

## Configuration

Everything lives in `backend/.env`. See `.env.example` for the full list.

| Setting | Notes |
|---|---|
| `SECRET_KEY` | Required, minimum 32 characters, no default |
| `ENVIRONMENT` | `development`, `staging` or `production` |
| `DATABASE_URL` | SQLite or Postgres |
| `CORS_ORIGINS` | Comma-separated. Rejected at startup if it contains `*` or `http://` when `ENVIRONMENT=production` |
| `BCRYPT_ROUNDS` | Defaults to 12; must be at least 12 in production, enforced at startup |
| `ALLOWED_ATTACHMENT_HOSTS` | Empty means any https host. Set it to restrict evidence links to your own domains |
| `LOGIN_RATE_LIMIT_PER_MINUTE` | Also `REGISTER_RATE_LIMIT_PER_HOUR` and `WRITE_RATE_LIMIT_PER_MINUTE` |

Production configuration is validated when settings load, not when something
eventually breaks.

---

## Operating it

**Logs** are structured JSON on stdout, one line per event, each carrying a
`request_id`. Every API response carries the same id in the `X-Request-ID` header
and inside any error body, so a student reporting "it did not work" hands you a
string that maps to exactly one request. Set `LOG_JSON=false` for readable local
output.

**Health** is at `/health` (process is up) and `/ready` (database reachable). Point
a load balancer at `/ready`.

**Errors** are always the same shape, and never contain a stack trace:

```json
{"error": {"code": "invalid_transition", "message": "…", "request_id": "a1b2c3d4"}}
```

**Database choice.** SQLite is the default and is appropriate for a single campus
deployment: the traffic is a few hundred reports a term, not a few hundred a second.
It has one writer at a time, so concurrent writes queue rather than run in parallel,
and it lives on one machine's disk, which makes backups a file copy and horizontal
scaling impossible. Switching to Postgres is a `DATABASE_URL` change and
`alembic upgrade head`. The code paths that differ between the two — row locking,
connection pragmas — are already branched on the driver.

**Known limits**, stated plainly:

- The rate limiter keeps counters in process memory. With more than one worker the
  effective limit multiplies by the worker count. Move the counters to Redis before
  running more than one.
- Notifications are in-app only. There is no email or SMS delivery.
- There is no password reset flow. An administrator updates the account.
- Evidence is a link to a file hosted elsewhere, not an upload.

---

## Layout

```
backend/
  app/
    api/v1/        auth, reports, issues, admin, notifications
    models/        SQLAlchemy tables
    schemas/       request and response models, with validation
    services/      routing, duplicate suggestion, issue state machine
    config.py      settings, validated at import
    errors.py      domain exceptions the API maps to status codes
    middleware.py  request ids, access logs, security headers
  alembic/         migrations
  scripts/         seed and admin bootstrap, run by an operator
  tests/           routing, authorization matrix, privacy, lifecycle, validation
frontend/
  src/app/         routes
  src/components/  shared UI
  src/lib/         api client, auth context, formatting
```

The state machine lives in exactly one place, `services/issue_state_machine.py`,
with the legal transitions written out as a table. Every action is checked against
it, so an illegal move fails the same way no matter which route attempted it.
