# Notiva Deployment Guide - Render + Neon Database

## Prerequisites
1. **Render Account**: Sign up at [render.com](https://render.com)
2. **Neon Database**: Already configured with connection string
3. **GitHub Repository**: Push your code to a GitHub repository

## Step 1: Prepare Your Repository
Make sure these files are in your repository root:
- `render.yaml` - Render service configuration
- `build.sh` - Build script for dependencies and database setup
- `deployment_requirements.txt` - Python dependencies
- `runtime.txt` - Python version specification
- `main.py` - Application entry point

## Step 2: Deploy to Render

### Option A: Using render.yaml (Recommended)
1. Connect your GitHub repository to Render
2. Render will automatically detect the `render.yaml` file
3. The service will be configured with:
   - Build command: `./build.sh`
   - Start command: `gunicorn main:app --bind 0.0.0.0:$PORT`
   - Environment variables from the YAML file

### Option B: Manual Setup
1. Create new Web Service on Render
2. Connect your GitHub repository
3. Configure settings:
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn main:app --bind 0.0.0.0:$PORT`
   - **Python Version**: 3.11.9

## Step 3: Environment Variables
Set these environment variables in Render:

### Required Variables
- `DATABASE_URL`: 
  ```
  postgresql://neondb_owner:npg_AkeGQ5IBMNy4dep-withered-hill-aing4uwt-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
  ```
- `SESSION_SECRET`: Generate a secure random string
- `FLASK_ENV`: `production`

### Optional Variables
- `OPENAI_API_KEY`: Required for AI-powered Q&A features

## Step 4: Verify Deployment
1. Wait for the build to complete
2. Visit your Render service URL
3. Test admin login:
   - Email: `sujitdeshmukh2812@gmail.com`
   - Password: `admin123`

## Step 5: Post-Deployment Setup
1. **Create Admin Account**: The build script automatically creates tables
2. **Upload Test Materials**: Test the file upload functionality
3. **Configure OpenAI**: Add your OpenAI API key for Q&A features

## Troubleshooting

### Build Failures
- Check that `build.sh` has execute permissions
- Verify all dependencies are in `deployment_requirements.txt`
- Check Python version in `runtime.txt`

### Database Connection Issues
- Verify the Neon database connection string
- Ensure SSL mode is set to 'require'
- Check that the database is not paused

### Application Errors
- Check Render logs for detailed error messages
- Verify environment variables are set correctly
- Test the application locally first

## Security Notes
- Change the default admin password after deployment
- Set a strong SESSION_SECRET
- Keep your Neon database credentials secure
- Enable Neon's IP restrictions if needed

## Performance Optimization
- Enable Neon connection pooling
- Configure Gunicorn workers: `gunicorn main:app --workers 2`
- Add Redis for session storage (optional)
- Implement CDN for static files (optional)