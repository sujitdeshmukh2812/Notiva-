# Notiva - Academic Notes Management System

## 🎓 About
Notiva is a comprehensive academic notes management system that allows students to:
- Upload and share academic notes
- Browse notes by course, year, semester, and subject
- Ask and answer academic doubts
- Admin panel for complete academic structure management

## 🚀 Local Development Setup

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- PostgreSQL (for production) or SQLite (for development)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd NotivaFlow
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables
```bash
cp .env.example .env
# Edit .env file with your configuration
```

### Step 5: Initialize Database
```bash
python init_db.py
```

### Step 6: Run the Application
```bash
python main.py
```
The application will be available at: http://127.0.0.1:5000

## 🚀 Production Deployment (Render)

### Prerequisites
- Render account
- Neon database (PostgreSQL)
- OpenAI API key (optional, for AI features)

### Step 1: Set Up Neon Database
1. Create a Neon database account
2. Create a new database
3. Copy the connection string

### Step 2: Deploy to Render
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set the following environment variables:
   - `DATABASE_URL`: Your Neon database connection string
   - `SECRET_KEY`: A secure random string
   - `OPENAI_API_KEY`: Your OpenAI API key (optional)
   - `FLASK_ENV`: production
   - `FLASK_CONFIG`: production

### Step 3: Access Your Application
After deployment, your application will be available at your Render URL.

## 🔑 Default Admin Credentials
- Email: sujitdeshmukh2812@gmail.com
- Password: Sujit@2812

## 🌍 Environment Variables

### Required for Production
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Flask secret key for sessions
- `FLASK_ENV`: Set to 'production'
- `FLASK_CONFIG`: Set to 'production'

### Optional
- `OPENAI_API_KEY`: For AI-powered doubt resolution
- `LOG_TO_STDOUT`: Set to 'true' for production logging

## 📁 Project Structure
```
NotivaFlow/
├── app.py              # Application configuration
├── main.py            # Application entry point
├── wsgi.py            # WSGI entry point for production
├── models.py          # Database models
├── routes.py          # Application routes
├── config.py          # Configuration settings
├── extensions.py      # Flask extensions
├── init_db.py         # Database initialization script
├── static/            # Static files (CSS, JS)
├── templates/         # HTML templates
├── requirements.txt   # Python dependencies
├── render.yaml        # Render deployment configuration
├── Procfile          # Process file for deployment
└── runtime.txt       # Python version specification
```

## 🔑 Features
1. **Academic Structure Management**
   - Manage courses, years, semesters, and subjects
   - Hierarchical organization of academic content

2. **Notes Management**
   - Upload notes with proper categorization
   - Browse and search notes
   - Download approved notes
   - Rating and review system
   - Bookmark functionality

3. **User Management**
   - User registration and authentication
   - Admin and regular user roles
   - Profile management
   - Notification system

4. **Admin Features**
   - Complete academic structure management
   - Notes approval system
   - User management
   - Analytics dashboard
   - Advertisement management

5. **AI Features**
   - AI-powered doubt resolution
   - Automatic document summarization
   - Subject-specific question answering

## 💡 Usage

### For Students
1. Register an account
2. Browse available notes
3. Upload your notes
4. Ask doubts and get AI-powered answers
5. Rate and bookmark materials

### For Admins
1. Log in with admin credentials
2. Access admin dashboard
3. Manage academic structure
4. Approve/reject notes
5. Manage users
6. View analytics and manage advertisements

## 🔧 Database Schema
The application uses a relational database with the following main entities:
- Users (with admin roles)
- Academic structure (Courses → Years → Semesters → Subjects)
- Materials (linked to academic structure)
- Ratings, Bookmarks, Notifications
- Doubts (with AI-powered answers)
- Advertisements

## 🛡️ Security Features
- Password hashing with Werkzeug
- Session management with Flask-Login
- CSRF protection
- File upload validation
- SQL injection prevention with SQLAlchemy ORM
- SSL/TLS support for production

## 📝 Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 🐛 Troubleshooting

### Common Issues
1. **Database Connection Error**: Ensure DATABASE_URL is correctly set
2. **File Upload Issues**: Check UPLOAD_FOLDER permissions
3. **AI Features Not Working**: Verify OPENAI_API_KEY is set
4. **Admin Access Denied**: Run `python create_admin.py` to create admin user

### Logs
- Development: Check console output
- Production: Check Render logs or application logs

## 🤝 Support
For support, email NOTIVA.OFFICIAL@GMAIL.COM

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments
- Flask framework and its extensions
- Bootstrap for UI components
- OpenAI for AI capabilities
- Neon for database hosting
- Render for application hosting