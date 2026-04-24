#!/bin/bash
# Build and deploy frontend to GitHub Pages
# Run from project root: bash scripts/deploy-frontend.sh

set -e

green() { echo -e "\033[32m✓ $1\033[0m"; }
red()   { echo -e "\033[31m✗ $1\033[0m"; }

echo ""
echo "Deploying frontend to GitHub Pages"
echo "─────────────────────────────────"

cd frontend

# Check .env exists
if [ ! -f ".env" ]; then
  red ".env file not found in frontend/"
  exit 1
fi
green ".env file found"

# Check VITE_BACKEND_URL is not localhost
BACKEND_URL=$(grep VITE_BACKEND_URL .env | cut -d '=' -f2)
if echo "$BACKEND_URL" | grep -q "localhost"; then
  red "VITE_BACKEND_URL is still localhost — update .env to Render URL before deploying"
  exit 1
fi
green "VITE_BACKEND_URL points to: $BACKEND_URL"

# Install dependencies
echo "Installing dependencies..."
npm install --silent
green "Dependencies installed"

# Build
echo "Building production bundle..."
npm run build
green "Build successful"

# Check dist exists
if [ ! -d "dist" ]; then
  red "dist/ folder not found after build"
  exit 1
fi
green "dist/ folder created"

# Deploy
echo "Deploying to GitHub Pages..."
npm run deploy
green "Deployed to GitHub Pages"

echo "─────────────────────────────────"
echo "Done! Site will be live at https://getshortlisted.me in 1-2 minutes"
echo ""
