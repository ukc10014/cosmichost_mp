#!/bin/bash
# Safety check before pushing to GitHub
# Run this before your first git push

echo "🔍 Checking for sensitive files before git push..."
echo ""

ISSUES=0
GIT_INITIALIZED=false

# Check if git is initialized
if [ -d ".git" ]; then
    GIT_INITIALIZED=true
    echo "✅ Git repository initialized"
else
    echo "⚠️  Git not initialized yet (run 'git init' first)"
fi

echo ""

# Check if .gitignore exists
if [ ! -f ".gitignore" ]; then
    echo "❌ ERROR: .gitignore file not found!"
    ISSUES=$((ISSUES + 1))
else
    echo "✅ .gitignore exists"
fi

# Check if .env is in .gitignore
if grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo "✅ .env is in .gitignore"
else
    echo "❌ ERROR: .env is NOT in .gitignore!"
    ISSUES=$((ISSUES + 1))
fi

# Check if .env exists (it should, but shouldn't be tracked)
if [ -f ".env" ]; then
    echo "⚠️  .env file exists (this is OK if it's in .gitignore)"

    # Check if it would be staged (only if git is initialized)
    if [ "$GIT_INITIALIZED" = true ]; then
        if git ls-files --error-unmatch .env 2>/dev/null; then
            echo "❌ CRITICAL: .env is tracked by git!"
            ISSUES=$((ISSUES + 1))
        else
            echo "✅ .env is NOT tracked by git"
        fi
    fi
fi

# Check for other sensitive patterns
echo ""
echo "🔍 Checking for other sensitive files..."

# Check if .venv would be committed (only if git is initialized)
if [ "$GIT_INITIALIZED" = true ]; then
    if git ls-files --error-unmatch .venv 2>/dev/null | head -1 >/dev/null 2>&1; then
        echo "❌ ERROR: .venv directory is tracked! (404MB - should be in .gitignore)"
        ISSUES=$((ISSUES + 1))
    else
        echo "✅ .venv is not tracked"
    fi
else
    if grep -q "^\.venv/$" .gitignore 2>/dev/null; then
        echo "✅ .venv/ is in .gitignore (will not be tracked)"
    fi
fi

# Check for key files
if ls *_key.json 2>/dev/null | head -1 >/dev/null; then
    echo "⚠️  Found *_key.json files"
    if [ "$GIT_INITIALIZED" = true ]; then
        for keyfile in *_key.json; do
            if git ls-files --error-unmatch "$keyfile" 2>/dev/null; then
                echo "❌ CRITICAL: $keyfile is tracked!"
                ISSUES=$((ISSUES + 1))
            fi
        done
    else
        echo "   (Will check if tracked after 'git init')"
    fi
fi

# Summary
echo ""
echo "================================"
if [ $ISSUES -eq 0 ]; then
    echo "✅ SAFE TO PUSH"
    echo "No sensitive files detected in git staging"
    echo ""
    echo "Next steps:"
    echo "1. git init (if not already done)"
    echo "2. git add ."
    echo "3. git commit -m 'Initial commit'"
    echo "4. git remote add origin <your-repo-url>"
    echo "5. git push -u origin main"
else
    echo "❌ NOT SAFE TO PUSH"
    echo "Found $ISSUES issue(s) - FIX BEFORE PUSHING!"
    echo ""
    echo "Actions needed:"
    echo "1. Ensure .gitignore includes all sensitive files"
    echo "2. Run: git rm --cached <file> (to untrack files)"
    echo "3. Run this script again"
fi
echo "================================"

exit $ISSUES
