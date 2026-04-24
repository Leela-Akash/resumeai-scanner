# Rollback Guide

Step-by-step instructions to revert to a working version if something breaks in production.

---

## Rollback Backend on Render

1. Go to https://render.com → Dashboard → click `resumeai-scanner`
2. Click the **Events** tab on the left
3. Find the last working deploy (green checkmark)
4. Click the 3-dot menu next to it → **Rollback to this deploy**
5. Wait 2-3 minutes for deploy to complete
6. Test: `https://resumeai-scanner.onrender.com/health`

---

## Rollback Frontend on GitHub Pages

### Option A — Revert last commit

```bash
cd e:\ResumeScanner

# See recent commits
git log --oneline -10

# Revert the last commit (creates a new revert commit)
git revert HEAD

# Push the revert
git push origin main

# Redeploy frontend
cd frontend
npm run deploy
```

### Option B — Go back to specific commit

```bash
# Find the commit hash you want to go back to
git log --oneline -10

# Reset to that commit (replace abc1234 with actual hash)
git reset --hard abc1234

# Force push (careful — this rewrites history)
git push origin main --force

# Redeploy
cd frontend
npm run deploy
```

---

## Check Render Logs for Errors

1. Go to https://render.com → Dashboard → `resumeai-scanner`
2. Click **Logs** tab
3. Look for lines starting with `ERROR` or `CRITICAL`
4. Common errors and fixes:

| Error | Fix |
|---|---|
| `GROQ_API_KEY is not set` | Add env var on Render dashboard |
| `firebase_admin` credential error | Check FIREBASE_PRIVATE_KEY format |
| `ModuleNotFoundError` | Check requirements.txt has the package |
| `Port already in use` | Render handles this automatically |
| `CORS error` | Add domain to allowed_origins in main.py |

---

## Check GitHub Pages Deployment

1. Go to https://github.com/Leela-Akash/resumeai-scanner
2. Click **Actions** tab
3. Check if the latest workflow run is green
4. If red, click it to see the error

Or check Pages status:
- Repo → Settings → Pages → should show "Your site is live at https://getshortlisted.me"

---

## Emergency Resources

- Render status page: https://status.render.com
- Firebase status: https://status.firebase.google.com
- Groq API status: https://groqstatus.com
- GitHub status: https://githubstatus.com
