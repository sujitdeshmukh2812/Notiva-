# GitHub Authentication Setup for Notiva Project

## The Issue
GitHub no longer accepts password authentication for Git operations. You need a Personal Access Token (PAT).

## Solution Steps:

### 1. Create a Personal Access Token on GitHub
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name like "Notiva Project"
4. Select expiration (recommend 90 days or No expiration)
5. Select these scopes:
   - ✅ repo (Full control of private repositories)
   - ✅ workflow (Update GitHub Action workflows)
6. Click "Generate token"
7. **COPY THE TOKEN** - you won't see it again!

### 2. Configure Git Authentication in Replit
Run these commands in the Shell:

```bash
# Set your GitHub username and email
git config --global user.name "sujitdeshmukh2812"
git config --global user.email "sujitdeshmukh2812@gmail.com"

# Update the remote URL to use token authentication
git remote set-url origin https://YOUR_TOKEN@github.com/sujitdeshmukh2812/Notiva-.git
```

Replace `YOUR_TOKEN` with the token you copied from GitHub.

### Alternative Method - Use Username:Token Format
If the above doesn't work, try:
```bash
git remote set-url origin https://sujitdeshmukh2812:YOUR_TOKEN@github.com/sujitdeshmukh2812/Notiva-.git
```

### Troubleshooting Invalid Authentication
If you're still getting "invalid" errors:

1. **Check token permissions**: Your token needs "repo" scope
2. **Token expiry**: Make sure your token hasn't expired
3. **Remove cached credentials**:
```bash
git config --global --unset credential.helper
```
4. **Try fresh token**: Generate a new token from GitHub

### 3. Push to GitHub
```bash
git push origin main
```

## Alternative: Use SSH Keys
If you prefer SSH (more secure):

1. Generate SSH key in Replit Shell:
```bash
ssh-keygen -t ed25519 -C "sujitdeshmukh2812@gmail.com"
```

2. Add the public key to GitHub:
```bash
cat ~/.ssh/id_ed25519.pub
```
Copy the output and add it to GitHub → Settings → SSH and GPG keys

3. Update remote URL:
```bash
git remote set-url origin git@github.com:sujitdeshmukh2812/Notiva-.git
```

## Current Repository Status
✅ Repository: https://github.com/sujitdeshmukh2812/Notiva-
✅ 5 commits ready to push
✅ All files prepared with proper documentation
✅ .gitignore configured to exclude sensitive data

Your Notiva educational platform is ready for GitHub once authentication is set up!