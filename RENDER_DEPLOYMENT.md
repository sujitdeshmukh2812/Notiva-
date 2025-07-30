# Render Deployment Fix for Admin Login

## Problem
After deploying to Render, you get "Invalid email or password" when trying to login as admin because Render creates a fresh database without any users.

## Solution
The updated `build.sh` script automatically creates the admin account during deployment.

## Render Configuration

### Build Command:
```
./build.sh
```

### Start Command:
```
gunicorn main:app --bind 0.0.0.0:$PORT
```

### Environment Variables:
```
DATABASE_URL=your-postgresql-connection-string
SESSION_SECRET=mBFhjBTsx8d-KIYKTkNUjNhH8QLT9hsoNAwAqAiOlPc
OPENAI_API_KEY=your-openai-api-key
FLASK_ENV=production
```

## Admin Credentials (After Deployment):
- **Email:** sujitdeshmukh2812@gmail.com
- **Password:** Sujit@2812

## Deployment Steps:
1. Push updated code to GitHub (with the new build.sh)
2. Redeploy on Render
3. The build script will create the admin account automatically
4. Login with the credentials above

## What the Build Script Does:
- Installs Python dependencies
- Creates database tables
- Creates admin user with correct credentials
- Verifies setup completion

Your admin login will work after redeployment with this fix!