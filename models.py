from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    materials = db.relationship('Material', backref='uploader', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    years = db.relationship('Year', backref='course', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.name}>'

class Year(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    semesters = db.relationship('Semester', backref='year', lazy=True, cascade='all, delete-orphan')
    
    # Unique constraint for name within a course
    __table_args__ = (db.UniqueConstraint('name', 'course_id'),)
    
    def __repr__(self):
        return f'<Year {self.name} - {self.course.name}>'

class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    year_id = db.Column(db.Integer, db.ForeignKey('year.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subjects = db.relationship('Subject', backref='semester', lazy=True, cascade='all, delete-orphan')
    
    # Unique constraint for name within a year
    __table_args__ = (db.UniqueConstraint('name', 'year_id'),)
    
    def __repr__(self):
        return f'<Semester {self.name} - {self.year.name}>'

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    materials = db.relationship('Material', backref='subject_ref', lazy=True)
    doubts = db.relationship('Doubt', backref='subject_ref', lazy=True)  # Add this line
    
    # Unique constraint for name within a semester
    __table_args__ = (db.UniqueConstraint('name', 'semester_id'),)
    
    def __repr__(self):
        return f'<Subject {self.name} - {self.semester.name}>'

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Foreign keys to the academic structure
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    year_id = db.Column(db.Integer, db.ForeignKey('year.id'), nullable=True)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    
    # Keep old fields for backward compatibility
    course = db.Column(db.String(100), nullable=True)
    year = db.Column(db.String(10), nullable=True)
    semester = db.Column(db.String(20), nullable=True)
    subject = db.Column(db.String(100), nullable=True)
    
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, rejected
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    download_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    
    # Relationships
    course_ref = db.relationship('Course', backref='materials')
    year_ref = db.relationship('Year', backref='materials')
    semester_ref = db.relationship('Semester', backref='materials')
    ratings = db.relationship('Rating', backref='material', lazy=True, cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='material', lazy=True, cascade='all, delete-orphan')
    
    @property
    def average_rating(self):
        if self.ratings:
            return sum(rating.rating for rating in self.ratings) / len(self.ratings)
        return 0
    
    @property
    def rating_count(self):
        return len(self.ratings)
    
    def __repr__(self):
        return f'<Material {self.original_filename}>'

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure one rating per user per material
    __table_args__ = (db.UniqueConstraint('material_id', 'user_id'),)
    
    def __repr__(self):
        return f'<Rating {self.rating} stars for {self.material.original_filename}>'

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure one bookmark per user per material
    __table_args__ = (db.UniqueConstraint('material_id', 'user_id'),)
    
    def __repr__(self):
        return f'<Bookmark {self.material.original_filename} by {self.user.name}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'upload_approved', 'new_material', etc.
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.title} for {self.user.name}>'

class Doubt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=True)
    is_answered = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answered_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Doubt {self.title} by {self.user.name}>'

class Ad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    link_url = db.Column(db.String(500), nullable=True)
    placement = db.Column(db.String(50), nullable=False, default='sidebar')  # sidebar, banner, popup
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    click_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    creator = db.relationship('User', backref='ads')
    
    def __repr__(self):
        return f'<Ad {self.title}>'

# Add relationships after all models are defined
User.ratings = db.relationship('Rating', backref='user', lazy=True)
User.bookmarks = db.relationship('Bookmark', backref='user', lazy=True)
User.notifications = db.relationship('Notification', backref='user', lazy=True)
User.doubts = db.relationship('Doubt', backref='user', lazy=True)
