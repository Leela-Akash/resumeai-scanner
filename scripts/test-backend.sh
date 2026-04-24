#!/bin/bash
# Test backend health and critical endpoints
# Run from project root: bash scripts/test-backend.sh

BACKEND_URL=${1:-http://localhost:8000}
PASS=0
FAIL=0

green() { echo -e "\033[32m✓ $1\033[0m"; }
red()   { echo -e "\033[31m✗ $1\033[0m"; }

echo ""
echo "Testing backend at: $BACKEND_URL"
echo "─────────────────────────────────"

# Health check
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health")
if [ "$HEALTH" = "200" ]; then
  green "Health check passed (200)"
  PASS=$((PASS+1))
else
  red "Health check failed (got $HEALTH, expected 200)"
  FAIL=$((FAIL+1))
fi

# Health response has groq status
GROQ_STATUS=$(curl -s "$BACKEND_URL/health" | grep -o '"groq":"[^"]*"')
if echo "$GROQ_STATUS" | grep -q "up"; then
  green "Groq API key present"
  PASS=$((PASS+1))
else
  red "Groq API key missing — check GROQ_API_KEY env var"
  FAIL=$((FAIL+1))
fi

# Firebase status
FIREBASE_STATUS=$(curl -s "$BACKEND_URL/health" | grep -o '"firebase":"[^"]*"')
if echo "$FIREBASE_STATUS" | grep -q "up"; then
  green "Firebase credentials present"
  PASS=$((PASS+1))
else
  red "Firebase credentials missing — check FIREBASE_* env vars"
  FAIL=$((FAIL+1))
fi

# Analyze endpoint exists (should return 401 without token, not 404)
ANALYZE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND_URL/api/analyze")
if [ "$ANALYZE" = "401" ] || [ "$ANALYZE" = "422" ]; then
  green "Analyze endpoint reachable (returns $ANALYZE as expected)"
  PASS=$((PASS+1))
else
  red "Analyze endpoint issue (got $ANALYZE)"
  FAIL=$((FAIL+1))
fi

# History endpoint exists (should return 401 without token)
HISTORY=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/history")
if [ "$HISTORY" = "401" ]; then
  green "History endpoint reachable (returns 401 as expected)"
  PASS=$((PASS+1))
else
  red "History endpoint issue (got $HISTORY)"
  FAIL=$((FAIL+1))
fi

echo "─────────────────────────────────"
echo "Results: $PASS passed, $FAIL failed"
echo ""

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
