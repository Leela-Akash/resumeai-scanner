# Deployment Checklist

Run through every item before deploying to production.

---

## 1. Local Backend Tests

```bash
cd backend
python main.py
```

- [ ] Server starts with no errors in terminal
- [ ] `GET http://localhost:8000/health` returns `{"status":"healthy",...}`
- [ ] `services.groq` shows `"up"` in health response
- [ ] `services.firebase` shows `"up"` in health response

Test analyze endpoint via frontend:
- [ ] Upload a real PDF resume
- [ ] Paste a job description
- [ ] Click Analyze — result returns in under 15 seconds
- [ ] ATS score is between 0-100
- [ ] Matched + missing keywords are populated
- [ ] Weak bullets and improved bullets appear
- [ ] Overall feedback is 200+ words

Test history endpoint:
- [ ] After a scan, go to History page
- [ ] Past scan appears with correct job title, score, date
- [ ] Clicking "View Result" shows full result

---

## 2. Local Frontend Tests

```bash
cd frontend
npm run dev
```

Open http://localhost:5173

- [ ] Login page loads correctly
- [ ] Google login popup opens and completes
- [ ] After login, user photo and name appear in navbar
- [ ] Scan page loads with upload box and textarea
- [ ] PDF drag and drop works
- [ ] "Analyze Now" button triggers loading spinner
- [ ] Result page shows all sections
- [ ] History page shows past scans
- [ ] Pricing page shows 3 cards
- [ ] Logout works and returns to login page
- [ ] After 3 scans, upgrade modal appears

---

## 3. Build Verification

```bash
cd frontend
npm run build
```

- [ ] Build completes with no errors
- [ ] Only chunk size warnings are acceptable (not errors)
- [ ] `dist/` folder is created
- [ ] `dist/index.html` exists
- [ ] `dist/assets/` contains JS and CSS files

Preview the production build locally:
```bash
npm run preview
```
- [ ] App loads at http://localhost:4173
- [ ] Login works in preview mode
- [ ] No blank white screen

---

## 4. Console Error Checks

Open browser DevTools (F12) → Console tab

- [ ] No red errors on page load
- [ ] No CORS errors
- [ ] No Firebase initialization errors
- [ ] No "undefined" variable errors
- [ ] Network tab shows API calls returning 200

---

## 5. Mobile Responsive Checks

In DevTools → Toggle device toolbar (Ctrl+Shift+M)

Test on these sizes:
- [ ] iPhone SE (375px) — upload box visible, button clickable
- [ ] iPhone 12 (390px) — result card readable
- [ ] iPad (768px) — pricing cards layout correct
- [ ] Desktop (1280px) — full layout looks good

---

## 6. Pre-Deploy Final Checks

- [ ] `backend/.env` has all real values (not placeholders)
- [ ] `frontend/.env` has Render URL (not localhost)
- [ ] Firebase authorized domains includes `getshortlisted.me`
- [ ] Firestore composite index exists (userId ASC + createdAt DESC)
- [ ] All changes committed and pushed to GitHub

---

## Deploy Commands

```bash
# Backend — auto-deploys on Render when you push to main
git push origin main

# Frontend
cd frontend
npm run deploy
```
