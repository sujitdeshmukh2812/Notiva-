# Notiva - Educational Study Materials Platform

A modern Flask-based web application designed for educational institutions to facilitate the sharing, browsing, and downloading of study materials among students.

## Features

### 🎓 Academic Management
- **Hierarchical Structure**: Course → Year → Semester → Subject organization
- **Dynamic Content**: Admin-controlled academic structure management
- **Material Categorization**: Organized study materials by academic hierarchy

### 👥 User Management
- **Authentication**: Secure email/password login system
- **User Roles**: Regular users and administrators
- **Profile Management**: User account creation and management

### 📚 Material Management
- **File Upload**: Support for PDF, DOC, DOCX, PPT, images, and more
- **Status Workflow**: Pending → Approved → Published material flow
- **Download Tracking**: Usage statistics and analytics
- **File Validation**: Size limits (16MB) and extension filtering

### 🤖 AI Integration
- **OpenAI GPT-4o**: AI-powered question answering system
- **Doubt Resolution**: Student Q&A with intelligent responses
- **Subject Context**: Context-aware educational assistance

### 🎯 Additional Features
- **Bookmarks**: Save materials for later access
- **Rating System**: 5-star rating for materials
- **Notifications**: Real-time updates for users
- **Search & Filter**: Advanced filtering by academic structure
- **Admin Dashboard**: Comprehensive administration panel
- **Advertisement System**: Banner and sidebar ad management

## Technology Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **Security**: Werkzeug password hashing
- **AI**: OpenAI GPT-4o API

### Frontend
- **Template Engine**: Jinja2
- **UI Framework**: Bootstrap 5 (Dark Theme)
- **Icons**: Font Awesome 6.4.0
- **JavaScript**: Vanilla JavaScript with Bootstrap components

### Deployment
- **Platform**: Replit / Render.com
- **Database**: Neon PostgreSQL (Serverless)
- **Server**: Gunicorn WSGI server

## Installation & Setup

### Prerequisites
- Python 3.11+
- PostgreSQL database
- OpenAI API key (optional, for AI features)

### Environment Variables
```bash
DATABASE_URL=postgresql://username:password@host:port/database
SESSION_SECRET=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

### Local Development
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Run database migrations: `python create_admin.py`
5. Start the application: `gunicorn --bind 0.0.0.0:5000 main:app`

## Admin Access

Default admin credentials:
- **Email**: sujitdeshmukh2812@gmail.com
- **Password**: Sujit@2812

## Project Structure

```
├── app.py              # Flask application factory
├── models.py           # Database models
├── routes.py           # Application routes
├── main.py             # Application entry point
├── create_admin.py     # Admin user creation script
├── openai_helper.py    # AI integration helper
├── templates/          # Jinja2 templates
├── static/            # Static assets (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── uploads/       # User uploaded files
└── requirements.txt   # Python dependencies
```

## Key Components

### Database Models
- **User**: User accounts and authentication
- **Course/Year/Semester/Subject**: Academic hierarchy
- **Material**: Study materials and files
- **Rating/Bookmark**: User interactions
- **Notification**: System notifications
- **Doubt**: AI-powered Q&A system
- **Ad**: Advertisement management

### Security Features
- Password hashing with Werkzeug
- File upload validation and size limits
- Role-based access control
- CSRF protection
- SSL/TLS database connections

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is developed for educational purposes.

## Support

For support and questions, please contact the development team or create an issue in the repository.

---

**Notiva** - Empowering Education Through Technology 🎓