# Render Deployment Fix for Admin Login

## Problem
After deploying to Render, you get "Invalid email or password" when trying to login as admin because Render uses a fresh PostgreSQL database that doesn't have any users.

## Root Cause
- **Replit**: Uses local SQLite database with existing admin account
- **Render**: Uses fresh PostgreSQL database without any users
- Your admin credentials work locally but not on Render

## Solution
Updated `build.sh` script that:
1. Forces creation of admin account during deployment
2. Deletes any existing conflicting accounts
3. Verifies the login credentials work
4. Shows clear success/failure messages

## Render Configuration

### Build Command:
```
./build.sh
```

### Start Command:
```
gunicorn main:app --bind 0.0.0.0:$PORT
```

### Environment Variables (REQUIRED):
```
DATABASE_URL=your-neon-postgresql-connection-string
SESSION_SECRET=mBFhjBTsx8d-KIYKTkNUjNhH8QLT9hsoNAwAqAiOlPc
OPENAI_API_KEY=your-openai-api-key
FLASK_ENV=production
```

## Admin Credentials (After Deployment):
- **Email:** sujitdeshmukh2812@gmail.com
- **Password:** Sujit@2812

## Deployment Steps:
1. **Push to GitHub:** Make sure latest build.sh is in your repository
2. **Redeploy on Render:** Trigger a new deployment
3. **Check Build Logs:** Look for "🎉 Admin setup completed successfully!" message
4. **Test Login:** Use the credentials above

## Troubleshooting:
If you still can't login after deployment:

1. **Check Render Build Logs** for error messages
2. **Verify Environment Variables** are set correctly
3. **Database Connection** - ensure DATABASE_URL is correct
4. **Manual Admin Creation** - Run this in Render console if needed:
```python
from app import app, db
from models import User

with app.app_context():
    admin = User(name='Sujit Deshmukh', email='sujitdeshmukh2812@gmail.com', is_admin=True)
    admin.set_password('Sujit@2812')
    db.session.add(admin)
    db.session.commit()
```

## Success Indicators:
- Build logs show "🎉 Admin setup completed successfully!"
- Login credentials work immediately after deployment
- No "Invalid email or password" errors