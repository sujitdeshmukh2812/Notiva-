from firebase_config import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin):
    def __init__(self, id, name, email, password_hash, is_admin=False, created_at=None):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            'name': self.name,
            'email': self.email,
            'password_hash': self.password_hash,
            'is_admin': self.is_admin,
            'created_at': self.created_at
        }

    @staticmethod
    def get(user_id):
        user_data = db.collection('users').document(user_id).get()
        if user_data.exists:
            data = user_data.to_dict()
            return User(user_id, data['name'], data['email'], data['password_hash'], data.get('is_admin', False), data.get('created_at'))
        return None

    @staticmethod
    def get_by_email(email):
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1)
        results = query.stream()
        for user_doc in results:
            user_data = user_doc.to_dict()
            return User(user_doc.id, user_data['name'], user_data['email'], user_data['password_hash'], user_data.get('is_admin', False), user_data.get('created_at'))
        return None

    def save(self):
        db.collection('users').document(self.id).set(self.to_dict())

class Course:
    def __init__(self, id, name, created_at=None):
        self.id = id
        self.name = name
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            'name': self.name,
            'created_at': self.created_at
        }

    @staticmethod
    def get(course_id):
        course_data = db.collection('courses').document(course_id).get()
        if course_data.exists:
            data = course_data.to_dict()
            return Course(course_id, data['name'], data.get('created_at'))
        return None

    def save(self):
        db.collection('courses').document(self.id).set(self.to_dict())

class Year:
    def __init__(self, id, name, course_id, created_at=None):
        self.id = id
        self.name = name
        self.course_id = course_id
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            'name': self.name,
            'course_id': self.course_id,
            'created_at': self.created_at
        }

    @staticmethod
    def get(year_id):
        year_data = db.collection('years').document(year_id).get()
        if year_data.exists:
            data = year_data.to_dict()
            return Year(year_id, data['name'], data['course_id'], data.get('created_at'))
        return None

    def save(self):
        db.collection('years').document(self.id).set(self.to_dict())

class Semester:
    def __init__(self, id, name, year_id, created_at=None):
        self.id = id
        self.name = name
        self.year_id = year_id
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            'name': self.name,
            'year_id': self.year_id,
            'created_at': self.created_at
        }

    @staticmethod
    def get(semester_id):
        semester_data = db.collection('semesters').document(semester_id).get()
        if semester_data.exists:
            data = semester_data.to_dict()
            return Semester(semester_id, data['name'], data['year_id'], data.get('created_at'))
        return None

    def save(self):
        db.collection('semesters').document(self.id).set(self.to_dict())

class Subject:
    def __init__(self, id, name, semester_id, created_at=None):
        self.id = id
        self.name = name
        self.semester_id = semester_id
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            'name': self.name,
            'semester_id': self.semester_id,
            'created_at': self.created_at
        }

    @staticmethod
    def get(subject_id):
        subject_data = db.collection('subjects').document(subject_id).get()
        if subject_data.exists:
            data = subject_data.to_dict()
            return Subject(subject_id, data['name'], data['semester_id'], data.get('created_at'))
        return None

    def save(self):
        db.collection('subjects').document(self.id).set(self.to_dict())

class Material:
    def __init__(self, id, filename, original_filename, description, course_id, year_id, semester_id, subject_id, file_size, file_type, status, uploader_id, uploaded_at=None, reviewed_at=None, download_count=0, view_count=0):
        self.id = id
        self.filename = filename
        self.original_filename = original_filename
        self.description = description
        self.course_id = course_id
        self.year_id = year_id
        self.semester_id = semester_id
        self.subject_id = subject_id
        self.file_size = file_size
        self.file_type = file_type
        self.status = status
        self.uploader_id = uploader_id
        self.uploaded_at = uploaded_at or datetime.utcnow()
        self.reviewed_at = reviewed_at
        self.download_count = download_count
        self.view_count = view_count

    def to_dict(self):
        return {
            'filename': self.filename,
            'original_filename': self.original_filename,
            'description': self.description,
            'course_id': self.course_id,
            'year_id': self.year_id,
            'semester_id': self.semester_id,
            'subject_id': self.subject_id,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'status': self.status,
            'uploader_id': self.uploader_id,
            'uploaded_at': self.uploaded_at,
            'reviewed_at': self.reviewed_at,
            'download_count': self.download_count,
            'view_count': self.view_count
        }

    @staticmethod
    def get(material_id):
        material_data = db.collection('materials').document(material_id).get()
        if material_data.exists:
            data = material_data.to_dict()
            return Material(material_id, data['filename'], data['original_filename'], data['description'], data['course_id'], data['year_id'], data['semester_id'], data['subject_id'], data['file_size'], data['file_type'], data['status'], data['uploader_id'], data.get('uploaded_at'), data.get('reviewed_at'), data.get('download_count', 0), data.get('view_count', 0))
        return None

    def save(self):
        db.collection('materials').document(self.id).set(self.to_dict())

class Rating:
    def __init__(self, id, material_id, user_id, rating, comment, created_at=None):
        self.id = id
        self.material_id = material_id
        self.user_id = user_id
        self.rating = rating
        self.comment = comment
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            'material_id': self.material_id,
            'user_id': self.user_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at
        }

    def save(self):
        db.collection('ratings').document(self.id).set(self.to_dict())

class Bookmark:
    def __init__(self, id, material_id, user_id, created_at=None):
        self.id = id
        self.material_id = material_id
        self.user_id = user_id
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            'material_id': self.material_id,
            'user_id': self.user_id,
            'created_at': self.created_at
        }

    def save(self):
        db.collection('bookmarks').document(self.id).set(self.to_dict())

class Notification:
    def __init__(self, id, user_id, title, message, type, is_read=False, created_at=None):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.message = message
        self.type = type
        self.is_read = is_read
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at
        }

    def save(self):
        db.collection('notifications').document(self.id).set(self.to_dict())

class Doubt:
    def __init__(self, id, user_id, subject_id, title, question, answer=None, is_answered=False, created_at=None, answered_at=None):
        self.id = id
        self.user_id = user_id
        self.subject_id = subject_id
        self.title = title
        self.question = question
        self.answer = answer
        self.is_answered = is_answered
        self.created_at = created_at or datetime.utcnow()
        self.answered_at = answered_at

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'subject_id': self.subject_id,
            'title': self.title,
            'question': self.question,
            'answer': self.answer,
            'is_answered': self.is_answered,
            'created_at': self.created_at,
            'answered_at': self.answered_at
        }

    def save(self):
        db.collection('doubts').document(self.id).set(self.to_dict())

class Ad:
    def __init__(self, id, title, content, image_filename, image_url, link_url, placement, is_active, start_date, end_date, click_count, view_count, created_by, created_at=None):
        self.id = id
        self.title = title
        self.content = content
        self.image_filename = image_filename
        self.image_url = image_url
        self.link_url = link_url
        self.placement = placement
        self.is_active = is_active
        self.start_date = start_date
        self.end_date = end_date
        self.click_count = click_count
        self.view_count = view_count
        self.created_by = created_by
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            'title': self.title,
            'content': self.content,
            'image_filename': self.image_filename,
            'image_url': self.image_url,
            'link_url': self.link_url,
            'placement': self.placement,
            'is_active': self.is_active,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'click_count': self.click_count,
            'view_count': self.view_count,
            'created_by': self.created_by,
            'created_at': self.created_at
        }

    def save(self):
        db.collection('ads').document(self.id).set(self.to_dict())
