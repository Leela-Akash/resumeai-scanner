# Environment Variables Reference

Complete list of all environment variables needed to run ResumeAI Scanner.

---

## Backend — Render.com Environment Variables

Set these in Render Dashboard → your service → Environment tab.

| Variable | Description | Where to get it |
|---|---|---|
| `GROQ_API_KEY` | Groq API key for AI analysis | https://console.groq.com → API Keys |
| `FIREBASE_PROJECT_ID` | Firebase project ID | Firebase Console → Project Settings |
| `FIREBASE_CLIENT_EMAIL` | Firebase service account email | Firebase Console → Project Settings → Service Accounts → Generate Key |
| `FIREBASE_PRIVATE_KEY` | Firebase private key (with `\n` newlines) | Same JSON file as above |
| `FRONTEND_URL` | Your frontend domain | `https://getshortlisted.me` |
| `FREE_SCAN_LIMIT` | Optional. Scans allowed per free user. `0` or unset = unlimited | Leave unset until paid plans exist |
| `GROQ_MODEL` | Optional. Groq model id | Defaults to `llama-3.3-70b-versatile` |

### FIREBASE_PRIVATE_KEY format on Render
Paste the key exactly as it appears in the JSON file.
Render handles the `\n` newlines correctly.
Do NOT wrap in quotes on Render.

---

## Frontend — .env (Production)

File: `frontend/.env` — committed to git, used in production builds.

| Variable | Value |
|---|---|
| `VITE_BACKEND_URL` | `https://resumeai-scanner.onrender.com` |
| `VITE_FIREBASE_API_KEY` | From Firebase Console → Project Settings → Web App |
| `VITE_FIREBASE_AUTH_DOMAIN` | `your-project.firebaseapp.com` |
| `VITE_FIREBASE_PROJECT_ID` | `your-project-id` |
| `VITE_FIREBASE_STORAGE_BUCKET` | `your-project.appspot.com` |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Numeric ID from Firebase config |
| `VITE_FIREBASE_APP_ID` | From Firebase config object |

## Frontend — .env.local (Local Development)

File: `frontend/.env.local` — NOT committed to git.

Same as above but with:
```
VITE_BACKEND_URL=http://localhost:8000
```

---

## Firebase Setup Steps

1. Go to https://console.firebase.google.com
2. Create project → name it `resumeai-scanner`
3. Enable Google Authentication:
   - Authentication → Sign-in method → Google → Enable
4. Create Firestore database:
   - Firestore Database → Create database → Start in production mode → Mumbai region
   - Rules tab → paste the contents of `firestore.rules` from this repo → Publish (denies all browser access; the backend uses the Admin SDK)
     (test mode lets anyone read and write every document, and expires after 30 days)
5. Get web app config:
   - Project Settings → Your apps → Web → Register app → copy firebaseConfig
6. Get service account key (for backend):
   - Project Settings → Service accounts → Generate new private key → download JSON
   - Copy `project_id`, `client_email`, `private_key` to backend env vars
7. Add authorized domains:
   - Authentication → Settings → Authorized domains → Add `getshortlisted.me`
8. Create Firestore index:
   - Firestore → Indexes → Add index
   - Collection: `scans`, Fields: `userId` ASC + `createdAt` DESC

---

## GitHub Actions Secrets

For the CI build workflow to work, add these in:
GitHub repo → Settings → Secrets and variables → Actions → New repository secret

- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`
