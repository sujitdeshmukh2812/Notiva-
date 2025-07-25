# Notiva - Academic Notes Management System

## 🎓 About
Notiva is a comprehensive academic notes management system that allows students to:
- Upload and share academic notes
- Browse notes by course, year, semester, and subject
- Ask and answer academic doubts
- Admin panel for complete academic structure management

## 🚀 Setup Instructions

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

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

### Step 4: Create Admin Account
```bash
python create_admin.py
```
Default admin credentials:
- Email: sujitdeshmukh2812@gmail.com
- Password: Sujit@2812

### Step 5: Run the Application
```bash
python main.py
```
The application will be available at: http://127.0.0.1:5000

## 📁 Project Structure
```
NotivaFlow/
├── app.py              # Application configuration
├── main.py            # Application entry point
├── models.py          # Database models
├── routes.py          # Application routes
├── static/            # Static files (CSS, JS)
├── templates/         # HTML templates
└── instance/         # Database and uploads
```

## 🔑 Features
1. **Academic Structure Management**
   - Manage courses, years, semesters, and subjects
   - Hierarchical organization of academic content

2. **Notes Management**
   - Upload notes with proper categorization
   - Browse and search notes
   - Download approved notes

3. **User Management**
   - User registration and authentication
   - Admin and regular user roles
   - Profile management

4. **Admin Features**
   - Complete academic structure management
   - Notes approval system
   - User management
   - Analytics dashboard

## 💡 Usage

### For Students
1. Register an account
2. Browse available notes
3. Upload your notes
4. Ask doubts

### For Admins
1. Log in with admin credentials
2. Access admin dashboard
3. Manage academic structure
4. Approve/reject notes
5. Manage users

## ⚙️ Environment Variables
Create a `.env` file with:
```env
DATABASE_URL=sqlite:///notiva.db
SESSION_SECRET=your-secret-key
```

## 📝 Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 🤝 Support
For support, email NOTIVA.OFFICIAL@GMAIL.COM 