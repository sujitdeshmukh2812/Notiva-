# Notiva - Educational Study Materials Platform

## Overview

Notiva is a modern Flask-based web application designed for educational institutions to facilitate the sharing, browsing, and downloading of study materials among students. The platform features a comprehensive admin system, user authentication, file management, AI-powered Q&A capabilities, and advertising management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 with Flask
- **UI Framework**: Bootstrap 5 with dark theme
- **Icons**: Font Awesome 6.4.0
- **Styling**: Custom CSS with CSS variables for theming
- **JavaScript**: Vanilla JavaScript with Bootstrap components
- **Responsive Design**: Mobile-first approach with responsive grid system

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Architecture Pattern**: MVC (Model-View-Controller)
- **ORM**: SQLAlchemy with declarative base
- **Authentication**: Flask-Login for session management
- **Password Security**: Werkzeug security for password hashing
- **File Handling**: Secure file upload system with validation

### Data Storage
- **Database**: SQLite (development) with PostgreSQL support via environment variables
- **ORM**: SQLAlchemy with relationship mapping
- **File Storage**: Local filesystem in `static/uploads/` directory
- **Connection Management**: Pool recycling and pre-ping for reliability

## Key Components

### User Management System
- **Authentication**: Email/password login with secure hashing
- **User Roles**: Regular users and administrators (is_admin flag)
- **Session Management**: Flask-Login integration with secure sessions
- **Registration**: User account creation with validation

### Academic Hierarchy Management
- **Structure**: Course → Year → Semester → Subject hierarchy
- **Dynamic Management**: Admin-controlled creation and editing
- **Relationships**: Proper foreign key constraints and cascade operations
- **Validation**: Prevents duplicate entries within scope
- **Material Tracking**: Count materials per academic component

### Material Management System
- **File Upload**: Multi-format support (PDF, DOC, DOCX, TXT, images)
- **File Validation**: Extension and size limits (16MB max)
- **Status System**: Pending/approved/rejected workflow
- **Metadata**: Title, description, academic categorization
- **Download Tracking**: Usage statistics and analytics

### AI Integration
- **OpenAI GPT-4o**: Question answering system
- **Doubt Resolution**: Student Q&A with AI responses
- **Document Summarization**: Automatic content summaries
- **Subject-specific**: Context-aware responses based on subjects

### Admin Dashboard
- **Material Moderation**: Approve/reject uploaded materials
- **User Management**: Monitor and manage user accounts
- **Academic Structure**: Manage courses, years, semesters, subjects
- **Analytics**: Usage statistics and platform metrics
- **Advertising**: Banner and sidebar ad management

### Additional Features
- **Bookmarks**: Save materials for later access
- **Ratings**: 5-star rating system for materials
- **Notifications**: Real-time updates for user activities
- **Search & Filter**: Advanced filtering by academic hierarchy
- **Export**: CSV export functionality for academic data

## Data Flow

### User Registration/Authentication
1. User submits registration form
2. Password hashed using Werkzeug security
3. User record created in database
4. Session established via Flask-Login

### Material Upload Process
1. User selects academic hierarchy (course/year/semester/subject)
2. File uploaded with metadata
3. Server validates file type and size
4. Material saved with "pending" status
5. Admin reviews and approves/rejects
6. User notified of status change

### AI-Powered Q&A
1. User submits question with optional subject context
2. Question sent to OpenAI GPT-4o API
3. AI generates educational response
4. Response stored and displayed to user
5. Conversation history maintained

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **Flask-Login**: User session management
- **Werkzeug**: Security utilities and WSGI

### Frontend Dependencies
- **Bootstrap 5**: UI framework and responsive design
- **Font Awesome**: Icon library
- **jQuery**: JavaScript utilities (implied by Bootstrap)

### AI Integration
- **OpenAI API**: GPT-4o model for educational assistance
- **API Key**: Environment variable configuration required

### Development Tools
- **ProxyFix**: WSGI middleware for deployment
- **Logging**: Python logging for debugging and monitoring

## Deployment Strategy

### Environment Configuration
- **Database URL**: Configurable via `DATABASE_URL` environment variable
- **Session Secret**: Configurable via `SESSION_SECRET` environment variable
- **OpenAI API Key**: Required via `OPENAI_API_KEY` environment variable

### File System Requirements
- **Upload Directory**: `static/uploads/` with write permissions
- **Static Assets**: CSS, JavaScript, and image files in `static/`
- **Templates**: Jinja2 templates in `templates/` directory

### Database Setup
- **Development**: SQLite database (`notiva.db`)
- **Production**: PostgreSQL support via DATABASE_URL
- **Migrations**: Manual table creation via app context
- **Admin Account**: Script provided for initial admin user creation

### Security Considerations
- **File Upload Validation**: Extension whitelist and size limits
- **Password Security**: Werkzeug hashing with salt
- **Session Security**: Configurable secret key
- **Admin Protection**: Role-based access control
- **WSGI Security**: ProxyFix for header handling

### Scalability Notes
- **Database Pooling**: Connection pool with recycling
- **File Storage**: Local filesystem (can be extended to cloud storage)
- **API Rate Limiting**: Consider implementing for OpenAI API calls
- **Caching**: No current implementation (opportunity for optimization)

## Deployment Information

### Recent Changes (July 29, 2025)
- **Migration Complete**: Successfully migrated from Replit Agent to standard Replit environment
- **Database**: PostgreSQL integration with proper SSL configuration and connection pooling
- **Authentication Fix**: Resolved session secret key configuration
- **URL Routing Fixed**: Resolved all Flask blueprint URL routing issues in templates
- **Admin Account**: Created admin user (sujitdeshmukh2812@gmail.com / Sujit@2812)
- **Full Functionality**: All pages now load correctly - homepage, admin dashboard, user features
- **Ads System Fixed**: Database relationships resolved, ad creation and management working
- **Complete Testing**: All core features verified working - authentication, user management, file system
- **Deployment Ready**: Application successfully running on Replit with PostgreSQL database
- **Migration Success**: Replit Agent to Replit migration completed with all features working

### Render Deployment Setup
- **Platform**: Render.com web service
- **Database**: Neon PostgreSQL (serverless)
- **Build Script**: `build.sh` - installs dependencies and creates database tables
- **Start Command**: `gunicorn main:app --bind 0.0.0.0:$PORT`
- **Python Version**: 3.11.9 (specified in runtime.txt)

### Environment Variables for Render
- `DATABASE_URL`: postgresql://neondb_owner:npg_AkeGQ5IBMNy4dep-withered-hill-aing4uwt-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
- `SESSION_SECRET`: Auto-generated secure key
- `OPENAI_API_KEY`: Required for AI-powered Q&A features
- `FLASK_ENV`: production

### Admin Access
- **Email**: sujitdeshmukh2812@gmail.com
- **Password**: Sujit@2812
- **Dashboard**: Accessible after login at /admin_dashboard