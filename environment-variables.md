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
| `STRIPE_SECRET_KEY` | Stripe secret key | https://dashboard.stripe.com → Developers → API Keys |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | Stripe Dashboard → Webhooks → your endpoint → Signing secret |
| `STRIPE_PRO_PRICE_ID` | Stripe price ID for Pro plan ($9/mo) | Stripe Dashboard → Products → Pro → Price ID |
| `STRIPE_PREMIUM_PRICE_ID` | Stripe price ID for Premium plan ($19/mo) | Stripe Dashboard → Products → Premium → Price ID |
| `FRONTEND_URL` | Your frontend domain | `https://getshortlisted.me` |

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
   - Firestore Database → Create database → Start in test mode → Mumbai region
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

## Stripe Setup Steps

1. Go to https://stripe.com → create account
2. Create Pro product:
   - Products → Add product → Name: "Pro Plan" → Price: $9/month recurring
   - Copy the Price ID (starts with `price_`)
3. Create Premium product:
   - Same steps → Name: "Premium Plan" → Price: $19/month recurring
4. Get API keys:
   - Developers → API Keys → copy Secret key (starts with `sk_live_`)
5. Set up webhook:
   - Developers → Webhooks → Add endpoint
   - URL: `https://resumeai-scanner.onrender.com/api/stripe-webhook`
   - Events: `checkout.session.completed`
   - Copy Signing secret (starts with `whsec_`)

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
