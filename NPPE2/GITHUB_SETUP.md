# GitHub Setup Guide

Complete guide to upload your project to GitHub from scratch.

## Step 1: Prepare Your Project

### 1.1 Check Current Status
```bash
# Navigate to project root
cd C:\Users\shrey\NPPE2

# Check if git is initialized
git status
```

If you see "not a git repository", proceed to Step 2.

### 1.2 Verify .gitignore
Make sure `.gitignore` exists and includes:
- `.env` files
- `node_modules/`
- `.next/`
- `venv/`
- `__pycache__/`
- `.vercel/`

## Step 2: Initialize Git Repository

```bash
# Initialize git repository
git init

# Check status
git status
```

## Step 3: Add All Files

```bash
# Add all files (respects .gitignore)
git add .

# Check what will be committed
git status
```

**Important:** Make sure `.env` files are NOT added (they should be in `.gitignore`)

## Step 4: Create Initial Commit

```bash
# Create first commit
git commit -m "Initial commit: Medical NLP Pipeline with Next.js frontend and FastAPI backend"

# Verify commit
git log
```

## Step 5: Create GitHub Repository

### Option A: Using GitHub Website

1. Go to https://github.com/new
2. **Repository name:** `medical-nlp-pipeline` (or your preferred name)
3. **Description:** "Medical transcription, NLP-based summarization, sentiment analysis, and SOAP note generation"
4. **Visibility:** Public or Private (your choice)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click **"Create repository"**

### Option B: Using GitHub CLI

```bash
# Install GitHub CLI if not installed
# Windows: winget install GitHub.cli

# Login
gh auth login

# Create repository
gh repo create medical-nlp-pipeline --public --source=. --remote=origin --push
```

## Step 6: Connect Local Repository to GitHub

```bash
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/medical-nlp-pipeline.git

# Verify remote
git remote -v
```

## Step 7: Push to GitHub

```bash
# Push to GitHub (first time)
git branch -M main
git push -u origin main
```

If prompted for credentials:
- **Username:** Your GitHub username
- **Password:** Use a Personal Access Token (not your password)
  - Create token: https://github.com/settings/tokens
  - Select scope: `repo`

## Step 8: Verify Upload

1. Go to your GitHub repository: `https://github.com/YOUR_USERNAME/medical-nlp-pipeline`
2. Check that all files are uploaded
3. Verify `.env` files are NOT visible (they should be ignored)

## Step 9: Update README (Optional)

Your README.md is already good, but you can add:
- Badges (build status, license)
- Screenshots
- Demo link (after deploying to Vercel)

## Step 10: Set Up Branch Protection (Optional)

1. Go to repository → Settings → Branches
2. Add rule for `main` branch
3. Require pull request reviews
4. Require status checks

## Quick Command Summary

```bash
# Complete setup in one go
cd C:\Users\shrey\NPPE2
git init
git add .
git commit -m "Initial commit: Medical NLP Pipeline"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/medical-nlp-pipeline.git
git push -u origin main
```

## Troubleshooting

### Issue: "fatal: not a git repository"
**Solution:** Run `git init` first

### Issue: "Permission denied"
**Solution:** 
- Use Personal Access Token instead of password
- Or set up SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

### Issue: "Large files detected"
**Solution:**
- Check `.gitignore` includes large files
- Use Git LFS for large files if needed

### Issue: ".env files are visible"
**Solution:**
- Check `.gitignore` includes `.env`
- Remove from git: `git rm --cached .env`
- Commit: `git commit -m "Remove .env files"`

## Next Steps After Upload

1. **Deploy Frontend to Vercel:**
   - Import from GitHub
   - Set `NEXT_PUBLIC_BACKEND_URL` environment variable
   - Deploy

2. **Deploy Backend:**
   - Railway, Render, or your own server
   - Set environment variables
   - Get public URL

3. **Update Vercel Environment Variable:**
   - Use backend URL from step 2

4. **Add GitHub Actions (Optional):**
   - Auto-deploy on push
   - Run tests
   - Lint code

## Repository Structure

Your GitHub repo should have:
```
medical-nlp-pipeline/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── app/
│   ├── package.json
│   ├── next.config.mjs
│   └── ...
├── .gitignore
├── README.md
└── env.example
```

**NOT included (in .gitignore):**
- `.env` files
- `node_modules/`
- `.next/`
- `venv/`
- `.vercel/`

