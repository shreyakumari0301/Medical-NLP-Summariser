#!/bin/bash
# Complete GitHub upload commands - run these one by one

# Step 1: Initialize git repository
git init

# Step 2: Add all files (respects .gitignore)
git add .

# Step 3: Check what will be committed (optional - you can skip this)
git status

# Step 4: Create initial commit
git commit -m "Initial commit: Medical NLP Pipeline with Next.js frontend and FastAPI backend"

# Step 5: Rename branch to main (if on master)
git branch -M main

# Step 6: Add remote repository (replace YOUR_USERNAME with your GitHub username)
# You already have: https://github.com/shreyakumari0301/Medical-NLP-Summariser.git
git remote add origin https://github.com/shreyakumari0301/Medical-NLP-Summariser.git

# Step 7: Push to GitHub
git push -u origin main

