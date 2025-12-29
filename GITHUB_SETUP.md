# Instructions to Push to GitHub

## Step 1: Install Git
Download and install Git from: https://git-scm.com/download/win

After installation, restart your terminal/PowerShell.

## Step 2: Initialize Git Repository
Open PowerShell in this directory and run:

```powershell
git init
```

## Step 3: Add All Files
```powershell
git add .
```

## Step 4: Create Initial Commit
```powershell
git commit -m "Initial commit: Activity Tracker"
```

## Step 5: Create GitHub Repository
1. Go to https://github.com and sign in
2. Click the "+" icon in the top right
3. Select "New repository"
4. Name your repository (e.g., "activity-tracker")
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 6: Add Remote and Push
After creating the repository, GitHub will show you commands. Use these:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your actual GitHub username and repository name.

## Alternative: Using GitHub CLI
If you have GitHub CLI installed, you can use:
```powershell
gh repo create activity-tracker --public --source=. --remote=origin --push
```

