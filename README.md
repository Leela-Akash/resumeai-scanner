# ResumeAI Scanner

AI-powered resume scanner that gives you an ATS score in 10 seconds.
Live at: **https://getshortlisted.me**

---

## What It Does

- Upload your resume PDF + paste a job description
- AI analyzes both using a 5-stage pipeline
- Returns ATS score, matched/missing keywords, bullet improvements, hire probability
- Saves scan history per user
- Free tier: 3 scans/month. Pro: unlimited.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend | Python FastAPI |
| AI | Groq API (Llama 3.3 70B) |
| Auth | Firebase Authentication (Google) |
| Database | Firebase Firestore |
| Payments | Stripe |
| Frontend hosting | GitHub Pages |
| Backend hosting | Render.com |

---

## Local Development

### Prerequisites
- Node.js 18+
- Python 3.11+
- Git

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create `backend/.env` with all required variables (see `environment-variables.md`).

```bash
python main.py
# Running at http://localhost:8000
```

### Frontend Setup

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```
VITE_BACKEND_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=...
# (see environment-variables.md for full list)
```

```bash
npm run dev
# Running at http://localhost:5173
```

---

## Deployment

### Deploy Backend to Render

1. Push code to GitHub: `git push origin main`
2. Go to https://render.com → New → Web Service
3. Connect repo `Leela-Akash/resumeai-scanner`
4. Settings:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add all environment variables from `environment-variables.md`
6. Click Deploy

Render auto-deploys on every push to `main`.

### Deploy Frontend to GitHub Pages

```bash
cd frontend
npm run deploy
```

This builds the app and pushes to the `gh-pages` branch automatically.

### Set Environment Variables on Render

1. Render Dashboard → your service → Environment tab
2. Add each variable from `environment-variables.md` → Backend section
3. Click Save — service restarts automatically

### Verify Deployment

```bash
# Test backend health
curl https://resumeai-scanner.onrender.com/health

# Expected response:
# {"status":"healthy","timestamp":"...","services":{"groq":"up","firebase":"up"}}
```

Frontend: https://getshortlisted.me

---

## Rollback

See `rollback-guide.md` for step-by-step rollback instructions.

**Quick rollback:**
- Backend: Render Dashboard → Events tab → rollback to previous deploy
- Frontend: `git revert HEAD && git push && cd frontend && npm run deploy`

---

## Monitoring

| URL | Purpose |
|---|---|
| `https://resumeai-scanner.onrender.com/health` | Backend health check |
| `https://getshortlisted.me` | Frontend live site |
| https://render.com/dashboard | Backend logs and deploys |
| https://console.firebase.google.com | Auth and Firestore data |
| https://dashboard.stripe.com | Payment events |

---

## Project Structure

```
resumeai-scanner/
├── backend/
│   ├── middleware/        # Auth + subscription checks
│   ├── routes/            # API endpoints
│   ├── services/          # AI, PDF, Firebase logic
│   ├── main.py
│   ├── requirements.txt
│   └── render.yaml
├── frontend/
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── firebase/      # Auth + Firestore
│   │   ├── hooks/         # useAuth
│   │   ├── pages/         # Full page components
│   │   └── utils/         # API client
│   └── package.json
├── scripts/
│   ├── test-backend.sh
│   └── deploy-frontend.sh
├── deployment-checklist.md
├── rollback-guide.md
└── environment-variables.md
```
