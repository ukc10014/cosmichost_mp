# Git Setup Instructions

## ⚠️ CRITICAL: Security First!

Your `.env` file contains **LIVE API KEYS** for:
- OpenAI
- Anthropic (Claude)
- Google (Gemini)
- OpenRouter
- Tinker

**These keys MUST NEVER be committed to git or pushed to GitHub!**

## ✅ Safety Measures Already in Place

I've created the following files to protect your API keys:

1. **`.gitignore`** - Prevents sensitive files from being tracked:
   - `.env` (your actual API keys)
   - `.venv/` (404MB virtual environment)
   - `__pycache__/` and `*.pyc`
   - `.ipynb_checkpoints/`
   - `*_key.json` files
   - Large log files

2. **`.env.example`** - Template file (safe to commit):
   - Shows what keys are needed
   - Contains placeholder values
   - Users can copy to `.env` and fill in their own keys

3. **`check_before_push.sh`** - Safety verification script:
   - Run this BEFORE your first push
   - Checks for sensitive files that might be accidentally tracked
   - Provides clear pass/fail status

## 🚀 Safe Git Workflow

### Step 1: Verify Safety
```bash
./check_before_push.sh
```

You should see:
```
✅ SAFE TO PUSH
No sensitive files detected in git staging
```

### Step 2: Initialize Repository
```bash
git init
```

### Step 3: Run Safety Check Again
```bash
./check_before_push.sh
```

This time it will check if any sensitive files are actually being tracked.

### Step 4: Stage Files
```bash
git add .
```

### Step 5: Verify What's Staged
```bash
git status
```

**IMPORTANT:** Verify that you DO NOT see:
- `.env`
- `.venv/`
- `*_key.json`
- `google_cloud_key/`

### Step 6: Commit
```bash
git commit -m "Initial commit: Cosmic Host moral parliament experiment"
```

### Step 7: Add Remote and Push
```bash
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git branch -M main
git push -u origin main
```

## 🆘 If You Accidentally Commit Sensitive Data

**DO NOT** just delete the file and commit again - it's still in git history!

### If you haven't pushed yet:
```bash
# Remove from git (but keep local file)
git rm --cached .env

# Amend the commit
git commit --amend -m "Initial commit"
```

### If you've already pushed to GitHub:

**IMMEDIATE ACTIONS:**

1. **Rotate ALL API keys immediately:**
   - OpenAI: https://platform.openai.com/api-keys
   - Anthropic: https://console.anthropic.com/settings/keys
   - Google Cloud: https://console.cloud.google.com/apis/credentials
   - OpenRouter: https://openrouter.ai/keys

2. **Remove from git history:**
   ```bash
   # Using BFG Repo-Cleaner (recommended)
   brew install bfg  # macOS
   bfg --delete-files .env
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   git push --force
   ```

   OR

   ```bash
   # Using git filter-branch
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   git push --force --all
   ```

3. **Verify removal:**
   - Check git history: `git log --all --full-history -- .env`
   - Should return nothing

## 📋 What Gets Committed vs. Ignored

### ✅ Committed to Git:
- Python source files (`*.py`)
- Jupyter notebooks (`*.ipynb`)
- Configuration templates (`.env.example`)
- Static assets (`static/`)
- Documentation (`*.md`)
- Safety scripts (`check_before_push.sh`)
- `CLAUDE.md` (Claude Code guidance)

### ❌ NOT Committed (in `.gitignore`):
- `.env` - **API keys**
- `.venv/` - Virtual environment (404MB)
- `__pycache__/` - Python cache
- `.ipynb_checkpoints/` - Jupyter checkpoints
- `logs/*.json`, `logs/*.jsonl` - Experiment logs
- `*_key.json` - Google Cloud keys
- Large output files (>1MB)
- Temporary files (`tmp_*`)

## 🔍 Regular Security Checks

Run the safety check periodically:
```bash
./check_before_push.sh
```

Especially:
- Before pushing new commits
- After adding new files
- If you modify `.gitignore`

## 📚 Additional Resources

- GitHub: [Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- Git: [gitignore documentation](https://git-scm.com/docs/gitignore)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)

## ✅ Verification Checklist

Before pushing:
- [ ] `.gitignore` exists
- [ ] `.env` is in `.gitignore`
- [ ] `.venv/` is in `.gitignore`
- [ ] Ran `./check_before_push.sh` - passed
- [ ] Ran `git status` - no `.env` or `.venv/` shown
- [ ] Verified commit doesn't contain API keys: `git show | grep -i "api.*key"`

**Only push when all items are checked!**
