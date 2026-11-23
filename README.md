# GetShortlisted — ResumeAI Scanner

Upload a resume PDF, paste a job description, and get an ATS-style score with the exact
keywords you're missing and a review of every bullet point.

**Live:** https://getshortlisted.me

---

## How the analysis works

```
PDF ──► text extraction (PyMuPDF, page/size/scan checks)
          │
          ├─► Stage 1  Keyword extraction ─ LLM, JD + resume in parallel, JSON mode
          │            Keyword matching ─── deterministic: aliases + whole-word fuzzy match
          ├─► Stage 2  Bullet review ────── one batched LLM call: score 0–10, issues, rewrite
          ├─► Stage 3  Experience ───────── date ranges from the Experience section only
          ├─► Stage 4  ATS score ────────── deterministic weighted formula
          └─► Stage 5  Feedback ─────────── LLM text, falls back to a template on failure
```

**Score** = keyword match × 0.40 + bullet quality × 0.30 + experience × 0.20 + format × 0.10

Design decisions:

- **LLM output is untrusted input.** Every response is requested in JSON mode and validated
  with Pydantic (`services/schemas.py`) before it reaches scoring. Invalid output is retried
  once; if it's still invalid the request fails with a clear error instead of returning a
  made-up score.
- **The LLM extracts, code decides.** The model only pulls skills out of text and reviews
  bullets. Matching and scoring are plain, unit-tested Python, so the same inputs give the
  same score.
- **Matching that understands skills.** `Java` doesn't match `JavaScript`, `SQL` doesn't
  match `NoSQL`, but `Node.js`/`NodeJS` and `Postgres`/`PostgreSQL` do (`services/matching.py`).
- **No invented achievements.** Bullet rewrites keep the candidate's facts and use
  `[placeholders]` for metrics they didn't give, rather than inventing "10K users".
- **Resilient AI calls.** One pooled HTTP client, retries with backoff on 429/5xx/network
  errors, no retries on 4xx, and user-facing errors that don't leak provider details
  (`services/llm.py`).

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | Python 3.11, FastAPI, Pydantic v2 |
| AI | Groq API (Llama 3.3 70B) |
| Matching | RapidFuzz |
| PDF | PyMuPDF |
| Auth | Firebase Authentication (Google) |
| Database | Cloud Firestore, accessed only by the backend (rules deny browser access) |
| Hosting | GitHub Pages (frontend), Render (backend, Docker) |
| CI | GitHub Actions: backend tests + frontend build |

Paid plans aren't built yet. The free-scan limit is controlled by `FREE_SCAN_LIMIT`
(unset = unlimited).

---

## API

All `/api` routes need a Firebase ID token: `Authorization: Bearer <token>`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness + whether Groq/Firebase are configured |
| `POST` | `/api/analyze` | `multipart/form-data`: `resume` (PDF ≤ 5MB, ≤ 5 pages), `job_description` (50–8,000 chars). Rate limit 10/min per IP |
| `GET` | `/api/history?limit=50` | The signed-in user's past scans, newest first |

Errors: `400` bad input · `401` bad token · `403 FREE_LIMIT_REACHED` · `413` file too large ·
`422` unreadable/scanned PDF · `429` rate limited · `503` AI provider unavailable.

---

## Local development

### Backend
```bash
cd backend
python3.11 -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env    # fill in values, see environment-variables.md
python main.py          # http://localhost:8000
```

### Tests
```bash
cd backend
python -m pytest -q
```
Tests replace Firebase and Groq with fakes, so they need no credentials or network.

### Frontend
```bash
cd frontend
npm install
# frontend/.env.local -> VITE_BACKEND_URL=http://localhost:8000 plus Firebase web config
npm run dev             # http://localhost:5173
```

---

## Deployment

- **Backend:** Render web service, root `backend`, uses `render.yaml`. Auto-deploys on push to `main`.
- **Frontend:** `cd frontend && npm run deploy` (builds and pushes to `gh-pages`).
- **Firestore rules:** paste `firestore.rules` into Firebase Console → Firestore → Rules.
- Full variable list: `environment-variables.md`. Rollback steps: `rollback-guide.md`.

Render's free tier sleeps when idle, so the first request after a while takes ~50s.

---

## Project structure

```
backend/
  main.py                    FastAPI app, CORS, rate limiting, health
  routes/analyze.py          upload validation -> pipeline -> save
  routes/history.py          paginated scan history
  middleware/                Firebase token verification, free-plan limit
  services/grok_service.py   pipeline orchestrator (stages 1–5)
  services/llm.py            Groq client: JSON mode, validation, retries
  services/schemas.py        Pydantic models for LLM output
  services/matching.py       keyword normalisation + matching
  services/experience.py     experience-section parsing
  services/pdf_service.py    PDF text extraction + checks
  tests/                     pytest suite (no network)
frontend/src/
  components/                upload, results, score UI
  firebase/                  auth config; history via the backend API
  hooks/useAuth.js
firestore.rules              Firestore security rules
```
