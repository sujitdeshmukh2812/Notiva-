import os
import uuid
import csv
import io
from flask import render_template, request, redirect, url_for, flash, send_file, abort, jsonify, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from app import app, db, allowed_file
from models import User, Material, Course, Year, Semester, Subject, Rating, Bookmark, Notification, Doubt
from openai_helper import answer_subject_doubt, generate_document_summary

@app.route('/')
def index():
    # Get recent approved materials for homepage
    recent_materials = Material.query.filter_by(status='approved').order_by(Material.uploaded_at.desc()).limit(5).all()
    
    # Get statistics
    total_materials = Material.query.filter_by(status='approved').count()
    total_downloads = db.session.query(db.func.sum(Material.download_count)).filter_by(status='approved').scalar() or 0
    
    return render_template('index.html', 
                         recent_materials=recent_materials,
                         total_materials=total_materials,
                         total_downloads=total_downloads)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if not name or not email or not password:
            flash('All fields are required.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
        else:
            # Create new user
            user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        # Get form data
        course_id = request.form.get('course_id')
        year_id = request.form.get('year_id')
        semester_id = request.form.get('semester_id')
        subject_id = request.form.get('subject_id')
        description = request.form.get('description', '').strip()
        
        # Validation
        if not all([course_id, year_id, semester_id, subject_id]):
            flash('All fields are required.', 'error')
            return redirect(request.url)
        
        # Verify the selected academic structure exists
        subject = Subject.query.get(subject_id)
        if not subject or subject.semester_id != int(semester_id):
            flash('Invalid subject selection.', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            original_filename = secure_filename(file.filename) if file.filename else 'unknown'
            file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'unknown'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Save file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create material record with new structure
            material = Material(
                filename=unique_filename,
                original_filename=original_filename,
                description=description if description else None,
                course_id=int(course_id),
                year_id=int(year_id),
                semester_id=int(semester_id),
                subject_id=int(subject_id),
                # Keep old fields for backward compatibility
                course=subject.semester.year.course.name,
                year=subject.semester.year.name,
                semester=subject.semester.name,
                subject=subject.name,
                file_size=file_size,
                file_type=file_extension,
                uploader_id=current_user.id
            )
            
            db.session.add(material)
            db.session.commit()
            
            flash('File uploaded successfully! It will be available after admin approval.', 'success')
            return redirect(url_for('browse'))
        else:
            flash('Invalid file type. Allowed types: PDF, DOC, DOCX, TXT, JPG, JPEG, PNG, GIF', 'error')
    
    # Get courses for the upload form
    courses = Course.query.all()
    return render_template('upload.html', courses=courses)

@app.route('/browse')
def browse():
    # Get filter parameters
    subject_filter = request.args.get('subject', '')
    year_filter = request.args.get('year', '')
    semester_filter = request.args.get('semester', '')
    course_filter = request.args.get('course', '')
    
    # Build query for approved materials
    query = Material.query.filter_by(status='approved')
    
    # Apply filters using both new and old structures for backward compatibility
    if subject_filter:
        query = query.filter(
            db.or_(
                Material.subject.ilike(f'%{subject_filter}%'),
                Material.subject_ref.has(Subject.name.ilike(f'%{subject_filter}%'))
            )
        )
    if year_filter:
        query = query.filter(
            db.or_(
                Material.year.ilike(f'%{year_filter}%'),
                Material.year_ref.has(Year.name.ilike(f'%{year_filter}%'))
            )
        )
    if semester_filter:
        query = query.filter(
            db.or_(
                Material.semester.ilike(f'%{semester_filter}%'),
                Material.semester_ref.has(Semester.name.ilike(f'%{semester_filter}%'))
            )
        )
    if course_filter:
        query = query.filter(
            db.or_(
                Material.course.ilike(f'%{course_filter}%'),
                Material.course_ref.has(Course.name.ilike(f'%{course_filter}%'))
            )
        )
    
    materials = query.order_by(Material.uploaded_at.desc()).all()
    
    # Get unique values for filter dropdowns from both old and new structures
    # Old structure values
    old_subjects = db.session.query(Material.subject).filter(
        Material.status == 'approved', 
        Material.subject.isnot(None)
    ).distinct().all()
    old_years = db.session.query(Material.year).filter(
        Material.status == 'approved',
        Material.year.isnot(None)
    ).distinct().all()
    old_semesters = db.session.query(Material.semester).filter(
        Material.status == 'approved',
        Material.semester.isnot(None)
    ).distinct().all()
    old_courses = db.session.query(Material.course).filter(
        Material.status == 'approved',
        Material.course.isnot(None)
    ).distinct().all()
    
    # New structure values
    new_subjects = db.session.query(Subject.name).join(Material, Material.subject_id == Subject.id).filter(
        Material.status == 'approved'
    ).distinct().all()
    new_years = db.session.query(Year.name).join(Material, Material.year_id == Year.id).filter(
        Material.status == 'approved'
    ).distinct().all()
    new_semesters = db.session.query(Semester.name).join(Material, Material.semester_id == Semester.id).filter(
        Material.status == 'approved'
    ).distinct().all()
    new_courses = db.session.query(Course.name).join(Material, Material.course_id == Course.id).filter(
        Material.status == 'approved'
    ).distinct().all()
    
    # Combine and deduplicate
    subjects = list(set([s[0] for s in old_subjects if s[0]] + [s[0] for s in new_subjects]))
    years = list(set([y[0] for y in old_years if y[0]] + [y[0] for y in new_years]))
    semesters = list(set([s[0] for s in old_semesters if s[0]] + [s[0] for s in new_semesters]))
    courses = list(set([c[0] for c in old_courses if c[0]] + [c[0] for c in new_courses]))
    
    # Sort the lists
    subjects.sort()
    years.sort()
    semesters.sort()
    courses.sort()
    
    return render_template('browse.html', 
                         materials=materials,
                         subjects=subjects,
                         years=years,
                         semesters=semesters,
                         courses=courses,
                         current_filters={
                             'subject': subject_filter,
                             'year': year_filter,
                             'semester': semester_filter,
                             'course': course_filter
                         })

@app.route('/download/<int:material_id>')
@login_required
def download(material_id):
    material = Material.query.get_or_404(material_id)
    
    # Check if material is approved
    if material.status != 'approved':
        flash('This file is not available for download.', 'error')
        return redirect(url_for('browse'))
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], material.filename)
    
    if not os.path.exists(file_path):
        flash('File not found.', 'error')
        return redirect(url_for('browse'))
    
    # Increment download count
    material.download_count += 1
    db.session.commit()
    
    return send_file(file_path, 
                    as_attachment=True, 
                    download_name=material.original_filename)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    # Get all materials and users
    pending_materials = Material.query.filter_by(status='pending').order_by(Material.uploaded_at.desc()).all()
    approved_materials = Material.query.filter_by(status='approved').order_by(Material.uploaded_at.desc()).all()
    rejected_materials = Material.query.filter_by(status='rejected').order_by(Material.uploaded_at.desc()).all()
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Statistics
    total_users = User.query.count()
    total_uploads = Material.query.count()
    pending_count = Material.query.filter_by(status='pending').count()
    
    return render_template('admin.html', 
                         pending_materials=pending_materials,
                         approved_materials=approved_materials,
                         rejected_materials=rejected_materials,
                         users=users,
                         total_users=total_users,
                         total_uploads=total_uploads,
                         pending_count=pending_count)

@app.route('/admin/approve/<int:material_id>')
@login_required
def approve_material(material_id):
    if not current_user.is_admin:
        abort(403)
    
    material = Material.query.get_or_404(material_id)
    material.status = 'approved'
    material.reviewed_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Material "{material.original_filename}" approved successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/reject/<int:material_id>')
@login_required
def reject_material(material_id):
    if not current_user.is_admin:
        abort(403)
    
    material = Material.query.get_or_404(material_id)
    material.status = 'rejected'
    material.reviewed_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Material "{material.original_filename}" rejected.', 'warning')
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:material_id>')
@login_required
def delete_material(material_id):
    if not current_user.is_admin:
        abort(403)
    
    material = Material.query.get_or_404(material_id)
    
    # Delete file from filesystem
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], material.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete from database
    db.session.delete(material)
    db.session.commit()
    
    flash(f'Material "{material.original_filename}" deleted permanently.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/toggle_admin/<int:user_id>')
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        abort(403)
    
    user = User.query.get_or_404(user_id)
    
    # Prevent removing admin rights from yourself
    if user.id == current_user.id:
        flash('You cannot modify your own admin status.', 'error')
        return redirect(url_for('admin'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'granted' if user.is_admin else 'revoked'
    flash(f'Admin privileges {status} for {user.name}.', 'success')
    return redirect(url_for('admin'))

# API Routes for Dynamic Dropdowns
@app.route('/api/years/<int:course_id>')
def get_years(course_id):
    years = Year.query.filter_by(course_id=course_id).order_by(Year.name).all()
    return jsonify([{'id': year.id, 'name': year.name} for year in years])

@app.route('/api/semesters/<int:year_id>')
def get_semesters(year_id):
    semesters = Semester.query.filter_by(year_id=year_id).order_by(Semester.name).all()
    return jsonify([{'id': semester.id, 'name': semester.name} for semester in semesters])

@app.route('/api/subjects/<int:semester_id>')
def get_subjects(semester_id):
    subjects = Subject.query.filter_by(semester_id=semester_id).order_by(Subject.name).all()
    return jsonify([{'id': subject.id, 'name': subject.name} for subject in subjects])

# Academic Structure Management Routes
@app.route('/admin/academic')
@login_required
def academic_management():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    courses = Course.query.order_by(Course.name).all()
    return render_template('admin_academic.html', courses=courses)

# Course Management
@app.route('/admin/academic/course/add', methods=['POST'])
@login_required
def add_course():
    if not current_user.is_admin:
        abort(403)
    
    name = request.form.get('name', '').strip()
    if not name:
        flash('Course name is required.', 'error')
        return redirect(url_for('academic_management'))
    
    # Check for duplicates
    existing = Course.query.filter_by(name=name).first()
    if existing:
        flash('Course already exists.', 'error')
        return redirect(url_for('academic_management'))
    
    course = Course(name=name)
    db.session.add(course)
    db.session.commit()
    
    flash(f'Course "{name}" added successfully!', 'success')
    return redirect(url_for('academic_management'))

@app.route('/admin/academic/course/edit/<int:course_id>', methods=['POST'])
@login_required
def edit_course(course_id):
    if not current_user.is_admin:
        abort(403)
    
    course = Course.query.get_or_404(course_id)
    new_name = request.form.get('name', '').strip()
    
    if not new_name:
        flash('Course name is required.', 'error')
        return redirect(url_for('academic_management'))
    
    # Check for duplicates (excluding current course)
    existing = Course.query.filter(Course.name == new_name, Course.id != course_id).first()
    if existing:
        flash('Course name already exists.', 'error')
        return redirect(url_for('academic_management'))
    
    course.name = new_name
    db.session.commit()
    
    flash(f'Course updated successfully!', 'success')
    return redirect(url_for('academic_management'))

@app.route('/admin/academic/course/delete/<int:course_id>')
@login_required
def delete_course(course_id):
    if not current_user.is_admin:
        abort(403)
    
    course = Course.query.get_or_404(course_id)
    
    # Check if course has materials
    material_count = Material.query.filter_by(course_id=course_id).count()
    if material_count > 0:
        flash(f'Cannot delete course "{course.name}". It has {material_count} materials associated with it.', 'error')
        return redirect(url_for('academic_management'))
    
    db.session.delete(course)
    db.session.commit()
    
    flash(f'Course "{course.name}" deleted successfully!', 'success')
    return redirect(url_for('academic_management'))

# Year Management
@app.route('/admin/academic/year/add', methods=['POST'])
@login_required
def add_year():
    if not current_user.is_admin:
        abort(403)
    
    name = request.form.get('name', '').strip()
    course_id = request.form.get('course_id')
    
    if not name or not course_id:
        flash('All fields are required.', 'error')
        return redirect(url_for('academic_management'))
    
    # Check for duplicates within the course
    existing = Year.query.filter_by(name=name, course_id=course_id).first()
    if existing:
        flash('Year already exists in this course.', 'error')
        return redirect(url_for('academic_management'))
    
    year = Year(name=name, course_id=course_id)
    db.session.add(year)
    db.session.commit()
    
    flash(f'Year "{name}" added successfully!', 'success')
    return redirect(url_for('academic_management'))

@app.route('/admin/academic/year/edit/<int:year_id>', methods=['POST'])
@login_required
def edit_year(year_id):
    if not current_user.is_admin:
        abort(403)
    
    year = Year.query.get_or_404(year_id)
    new_name = request.form.get('name', '').strip()
    
    if not new_name:
        flash('Year name is required.', 'error')
        return redirect(url_for('academic_management'))
    
    # Check for duplicates within the course (excluding current year)
    existing = Year.query.filter(Year.name == new_name, Year.course_id == year.course_id, Year.id != year_id).first()
    if existing:
        flash('Year name already exists in this course.', 'error')
        return redirect(url_for('academic_management'))
    
    year.name = new_name
    db.session.commit()
    
    flash(f'Year updated successfully!', 'success')
    return redirect(url_for('academic_management'))

@app.route('/admin/academic/year/delete/<int:year_id>')
@login_required
def delete_year(year_id):
    if not current_user.is_admin:
        abort(403)
    
    year = Year.query.get_or_404(year_id)
    
    # Check if year has materials
    material_count = Material.query.filter_by(year_id=year_id).count()
    if material_count > 0:
        flash(f'Cannot delete year "{year.name}". It has {material_count} materials associated with it.', 'error')
        return redirect(url_for('academic_management'))
    
    db.session.delete(year)
    db.session.commit()
    
    flash(f'Year "{year.name}" deleted successfully!', 'success')
    return redirect(url_for('academic_management'))

# Semester Management
@app.route('/admin/academic/semester/add', methods=['POST'])
@login_required
def add_semester():
    if not current_user.is_admin:
        abort(403)
    
    name = request.form.get('name', '').strip()
    year_id = request.form.get('year_id')
    
    if not name or not year_id:
        flash('All fields are required.', 'error')
        return redirect(url_for('academic_management'))
    
    # Check for duplicates within the year
    existing = Semester.query.filter_by(name=name, year_id=year_id).first()
    if existing:
        flash('Semester already exists in this year.', 'error')
        return redirect(url_for('academic_management'))
    
    semester = Semester(name=name, year_id=year_id)
    db.session.add(semester)
    db.session.commit()
    
    flash(f'Semester "{name}" added successfully!', 'success')
    return redirect(url_for('academic_management'))

@app.route('/admin/academic/semester/edit/<int:semester_id>', methods=['POST'])
@login_required
def edit_semester(semester_id):
    if not current_user.is_admin:
        abort(403)
    
    semester = Semester.query.get_or_404(semester_id)
    new_name = request.form.get('name', '').strip()
    
    if not new_name:
        flash('Semester name is required.', 'error')
        return redirect(url_for('academic_management'))
    
    # Check for duplicates within the year (excluding current semester)
    existing = Semester.query.filter(Semester.name == new_name, Semester.year_id == semester.year_id, Semester.id != semester_id).first()
    if existing:
        flash('Semester name already exists in this year.', 'error')
        return redirect(url_for('academic_management'))
    
    semester.name = new_name
    db.session.commit()
    
    flash(f'Semester updated successfully!', 'success')
    return redirect(url_for('academic_management'))

@app.route('/admin/academic/semester/delete/<int:semester_id>')
@login_required
def delete_semester(semester_id):
    if not current_user.is_admin:
        abort(403)
    
    semester = Semester.query.get_or_404(semester_id)
    
    # Check if semester has materials
    material_count = Material.query.filter_by(semester_id=semester_id).count()
    if material_count > 0:
        flash(f'Cannot delete semester "{semester.name}". It has {material_count} materials associated with it.', 'error')
        return redirect(url_for('academic_management'))
    
    db.session.delete(semester)
    db.session.commit()
    
    flash(f'Semester "{semester.name}" deleted successfully!', 'success')
    return redirect(url_for('academic_management'))

# Subject Management
@app.route('/admin/academic/subject/add', methods=['POST'])
@login_required
def add_subject():
    if not current_user.is_admin:
        abort(403)
    
    name = request.form.get('name', '').strip()
    semester_id = request.form.get('semester_id')
    
    if not name or not semester_id:
        flash('All fields are required.', 'error')
        return redirect(url_for('academic_management'))
    
    # Check for duplicates within the semester
    existing = Subject.query.filter_by(name=name, semester_id=semester_id).first()
    if existing:
        flash('Subject already exists in this semester.', 'error')
        return redirect(url_for('academic_management'))
    
    subject = Subject(name=name, semester_id=semester_id)
    db.session.add(subject)
    db.session.commit()
    
    flash(f'Subject "{name}" added successfully!', 'success')
    return redirect(url_for('academic_management'))

@app.route('/admin/academic/subject/edit/<int:subject_id>', methods=['POST'])
@login_required
def edit_subject(subject_id):
    if not current_user.is_admin:
        abort(403)
    
    subject = Subject.query.get_or_404(subject_id)
    new_name = request.form.get('name', '').strip()
    
    if not new_name:
        flash('Subject name is required.', 'error')
        return redirect(url_for('academic_management'))
    
    # Check for duplicates within the semester (excluding current subject)
    existing = Subject.query.filter(Subject.name == new_name, Subject.semester_id == subject.semester_id, Subject.id != subject_id).first()
    if existing:
        flash('Subject name already exists in this semester.', 'error')
        return redirect(url_for('academic_management'))
    
    subject.name = new_name
    db.session.commit()
    
    flash(f'Subject updated successfully!', 'success')
    return redirect(url_for('academic_management'))

@app.route('/admin/academic/subject/delete/<int:subject_id>')
@login_required
def delete_subject(subject_id):
    if not current_user.is_admin:
        abort(403)
    
    subject = Subject.query.get_or_404(subject_id)
    
    # Check if subject has materials
    material_count = Material.query.filter_by(subject_id=subject_id).count()
    if material_count > 0:
        flash(f'Cannot delete subject "{subject.name}". It has {material_count} materials associated with it.', 'error')
        return redirect(url_for('academic_management'))
    
    db.session.delete(subject)
    db.session.commit()
    
    flash(f'Subject "{subject.name}" deleted successfully!', 'success')
    return redirect(url_for('academic_management'))

# Export academic structure to CSV
@app.route('/admin/academic/export')
@login_required
def export_academic_structure():
    if not current_user.is_admin:
        abort(403)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Course', 'Year', 'Semester', 'Subject', 'Material Count'])
    
    # Write data
    courses = Course.query.all()
    for course in courses:
        for year in course.years:
            for semester in year.semesters:
                for subject in semester.subjects:
                    material_count = Material.query.filter_by(subject_id=subject.id).count()
                    writer.writerow([course.name, year.name, semester.name, subject.name, material_count])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=academic_structure_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

# Material Preview Route
@app.route('/admin/preview/<int:material_id>')
@login_required
def preview_material(material_id):
    if not current_user.is_admin:
        abort(403)
    
    material = Material.query.get_or_404(material_id)
    
    # Determine file type for proper display
    file_extension = material.file_type.lower()
    is_image = file_extension in ['jpg', 'jpeg', 'png', 'gif']
    is_pdf = file_extension == 'pdf'
    is_viewable = is_image or is_pdf
    
    return render_template('admin_preview.html', 
                         material=material, 
                         is_image=is_image, 
                         is_pdf=is_pdf, 
                         is_viewable=is_viewable)

# Password Change Routes
@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([current_password, new_password, confirm_password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('change_password'))
        
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect(url_for('change_password'))
        
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long.', 'error')
            return redirect(url_for('change_password'))
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('change_password.html')

# ===============================
# NEW FEATURES IMPLEMENTATION
# ===============================

# Document Rating System
@app.route('/rate_material/<int:material_id>', methods=['POST'])
@login_required
def rate_material(material_id):
    material = Material.query.get_or_404(material_id)
    rating_value = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()
    
    if not rating_value or rating_value < 1 or rating_value > 5:
        flash('Please provide a valid rating (1-5 stars).', 'error')
        return redirect(url_for('browse'))
    
    # Check if user already rated this material
    existing_rating = Rating.query.filter_by(material_id=material_id, user_id=current_user.id).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_value
        existing_rating.comment = comment if comment else None
        existing_rating.created_at = datetime.utcnow()
    else:
        # Create new rating
        new_rating = Rating(
            material_id=material_id,
            user_id=current_user.id,
            rating=rating_value,
            comment=comment if comment else None
        )
        db.session.add(new_rating)
    
    db.session.commit()
    flash('Rating submitted successfully!', 'success')
    return redirect(url_for('browse'))

# Bookmark System
@app.route('/toggle_bookmark/<int:material_id>', methods=['POST'])
@login_required
def toggle_bookmark(material_id):
    material = Material.query.get_or_404(material_id)
    existing_bookmark = Bookmark.query.filter_by(material_id=material_id, user_id=current_user.id).first()
    
    if existing_bookmark:
        # Remove bookmark
        db.session.delete(existing_bookmark)
        db.session.commit()
        flash('Document removed from bookmarks.', 'info')
    else:
        # Add bookmark
        new_bookmark = Bookmark(material_id=material_id, user_id=current_user.id)
        db.session.add(new_bookmark)
        db.session.commit()
        flash('Document bookmarked successfully!', 'success')
    
    return redirect(url_for('browse'))

@app.route('/my_bookmarks')
@login_required
def my_bookmarks():
    bookmarked_materials = db.session.query(Material).join(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Material.status == 'approved'
    ).order_by(Bookmark.created_at.desc()).all()
    
    return render_template('bookmarks.html', materials=bookmarked_materials)

# Notification System
@app.route('/notifications')
@login_required
def notifications():
    user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).all()
    
    # Mark notifications as read
    for notification in user_notifications:
        if not notification.is_read:
            notification.is_read = True
    db.session.commit()
    
    return render_template('notifications.html', notifications=user_notifications)

@app.route('/get_unread_notifications')
@login_required
def get_unread_notifications():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    recent = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(
        Notification.created_at.desc()
    ).limit(5).all()
    
    return jsonify({
        'count': count,
        'notifications': [{
            'title': n.title,
            'message': n.message,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M')
        } for n in recent]
    })

# Doubt Chat System
@app.route('/doubts')
@login_required
def doubts():
    user_doubts = Doubt.query.filter_by(user_id=current_user.id).order_by(
        Doubt.created_at.desc()
    ).all()
    subjects = Subject.query.all()
    
    return render_template('doubts.html', doubts=user_doubts, subjects=subjects)

@app.route('/ask_doubt', methods=['POST'])
@login_required
def ask_doubt():
    title = request.form.get('title', '').strip()
    question = request.form.get('question', '').strip()
    subject_id = request.form.get('subject_id')
    
    if not title or not question:
        flash('Title and question are required.', 'error')
        return redirect(url_for('doubts'))
    
    # Get subject name for AI context
    subject_name = None
    if subject_id and subject_id.isdigit():
        subject = Subject.query.get(int(subject_id))
        subject_name = subject.name if subject else None
    
    # Create doubt record
    doubt = Doubt(
        user_id=current_user.id,
        subject_id=int(subject_id) if subject_id and subject_id.isdigit() else None,
        title=title,
        question=question
    )
    db.session.add(doubt)
    db.session.flush()  # Get the doubt ID
    
    # Try to get AI answer
    try:
        ai_answer = answer_subject_doubt(question, subject_name)
        doubt.answer = ai_answer
        doubt.is_answered = True
        doubt.answered_at = datetime.utcnow()
        flash('Your doubt has been answered by AI!', 'success')
    except Exception as e:
        flash('Your doubt has been submitted. An answer will be provided soon.', 'info')
    
    db.session.commit()
    return redirect(url_for('doubts'))

# Enhanced Browse with Ratings Display
@app.route('/material_details/<int:material_id>')
def material_details(material_id):
    material = Material.query.get_or_404(material_id)
    if material.status != 'approved':
        abort(404)
    
    # Increment view count
    material.view_count += 1
    db.session.commit()
    
    # Get ratings and comments
    ratings = Rating.query.filter_by(material_id=material_id).order_by(Rating.created_at.desc()).all()
    user_rating = None
    user_bookmark = None
    
    if current_user.is_authenticated:
        user_rating = Rating.query.filter_by(material_id=material_id, user_id=current_user.id).first()
        user_bookmark = Bookmark.query.filter_by(material_id=material_id, user_id=current_user.id).first()
    
    return render_template('material_details.html', 
                         material=material, 
                         ratings=ratings,
                         user_rating=user_rating,
                         user_bookmark=user_bookmark)

# Enhanced Download with Tracking
@app.route('/download/<int:material_id>')
@login_required
def download_material(material_id):
    material = Material.query.get_or_404(material_id)
    
    if material.status != 'approved':
        flash('This file is not available for download.', 'error')
        return redirect(url_for('browse'))
    
    # Increment download count
    material.download_count += 1
    db.session.commit()
    
    # Create notification for uploader
    create_notification(
        material.uploader_id,
        'Document Downloaded',
        f'Your document "{material.original_filename}" was downloaded by {current_user.name}.',
        'download'
    )
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], material.filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=material.original_filename)
    else:
        flash('File not found.', 'error')
        return redirect(url_for('browse'))

# Admin Analytics Dashboard  
@app.route('/admin/analytics')
@login_required
def admin_analytics():
    if not current_user.is_admin:
        abort(403)
    
    # Basic statistics
    total_users = User.query.count()
    total_materials = Material.query.count()
    approved_materials = Material.query.filter_by(status='approved').count()
    pending_materials = Material.query.filter_by(status='pending').count()
    
    total_downloads = db.session.query(db.func.sum(Material.download_count)).scalar() or 0
    total_views = db.session.query(db.func.sum(Material.view_count)).scalar() or 0
    
    # Most downloaded materials
    top_downloads = Material.query.filter_by(status='approved').order_by(
        Material.download_count.desc()
    ).limit(10).all()
    
    # Most viewed materials
    top_views = Material.query.filter_by(status='approved').order_by(
        Material.view_count.desc()
    ).limit(10).all()
    
    # Most active uploaders
    top_uploaders = db.session.query(
        User.name, db.func.count(Material.id).label('upload_count')
    ).join(Material).filter(
        Material.status == 'approved'
    ).group_by(User.id, User.name).order_by(
        db.func.count(Material.id).desc()
    ).limit(10).all()
    
    # Subject-wise statistics
    subject_stats = db.session.query(
        Subject.name, 
        db.func.count(Material.id).label('material_count'),
        db.func.sum(Material.download_count).label('total_downloads')
    ).join(Material, Material.subject_id == Subject.id).filter(
        Material.status == 'approved'
    ).group_by(Subject.id, Subject.name).order_by(
        db.func.count(Material.id).desc()
    ).all()
    
    return render_template('admin_analytics.html',
                         total_users=total_users,
                         total_materials=total_materials,
                         approved_materials=approved_materials,
                         pending_materials=pending_materials,
                         total_downloads=total_downloads,
                         total_views=total_views,
                         top_downloads=top_downloads,
                         top_views=top_views,
                         top_uploaders=top_uploaders,
                         subject_stats=subject_stats)

# Helper function to create notifications
def create_notification(user_id, title, message, notification_type):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type
    )
    db.session.add(notification)
    db.session.commit()

# Enhanced admin approve function with notifications
@app.route('/admin/approve/<int:material_id>')
@login_required
def admin_approve_material(material_id):
    if not current_user.is_admin:
        abort(403)
    
    material = Material.query.get_or_404(material_id)
    material.status = 'approved'
    material.reviewed_at = datetime.utcnow()
    db.session.commit()
    
    # Create notification for uploader
    create_notification(
        material.uploader_id,
        'Document Approved!',
        f'Your document "{material.original_filename}" has been approved and is now available for download.',
        'upload_approved'
    )
    
    # Notify users interested in this subject about new material
    if material.subject_id:
        # Get users who have bookmarked materials from the same subject
        interested_users = db.session.query(User.id).join(Bookmark).join(Material).filter(
            Material.subject_id == material.subject_id,
            User.id != material.uploader_id  # Don't notify the uploader
        ).distinct().all()
        
        for user_tuple in interested_users:
            user_id = user_tuple[0]
            create_notification(
                user_id,
                'New Material Available',
                f'New study material "{material.original_filename}" is available in {material.subject_ref.name if material.subject_ref else material.subject}.',
                'new_material'
            )
    
    flash('Material approved successfully and notifications sent!', 'success')
    return redirect(url_for('admin'))
