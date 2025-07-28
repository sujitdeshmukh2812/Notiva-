import os
import uuid
import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort, jsonify, make_response, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from .app import db
from .models import User, Material, Course, Year, Semester, Subject, Rating, Bookmark, Notification, Doubt, Ad
from .openai_helper import answer_subject_doubt, generate_document_summary

main = Blueprint('main', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@main.route('/')
def index():
    # Get recent approved materials for homepage
    recent_materials = Material.query.filter_by(status='approved').order_by(Material.uploaded_at.desc()).limit(5).all()
    
    # Get statistics
    total_materials = Material.query.filter_by(status='approved').count()
    total_downloads = db.session.query(db.func.sum(Material.download_count)).filter_by(status='approved').scalar() or 0
    
    # Get active ads for homepage
    active_ads = Ad.query.filter_by(is_active=True, placement='banner').all()
    sidebar_ads = Ad.query.filter_by(is_active=True, placement='sidebar').limit(3).all()
    
    return render_template('index.html', 
                         recent_materials=recent_materials,
                         total_materials=total_materials,
                         total_downloads=total_downloads,
                         active_ads=active_ads,
                         sidebar_ads=sidebar_ads)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            current_app.logger.info(f"Login attempt for email: {email}")
            
            if not email or not password:
                flash('Email and password are required.', 'error')
                return render_template('login.html')
            
            user = User.query.filter_by(email=email).first()
            current_app.logger.info(f"User found: {user is not None}")
            
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                current_app.logger.info(f"Login successful for {email}")
                flash(f'Welcome back, {user.name}!', 'success')
                
                # Check if there's a next page in the request
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                
                # Redirect admin to admin dashboard, regular users to home
                if user.is_admin:
                    return redirect(url_for('main.admin_dashboard'))
                return redirect(url_for('main.index'))
            else:
                current_app.logger.warning(f"Failed login attempt for {email}")
                flash('Invalid email or password.', 'error')
        except Exception as e:
            current_app.logger.error(f"Error during login: {str(e)}")
            flash('An error occurred during login.', 'error')
    
    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
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
            
            flash('Welcome to Notiva! Registration successful! Please log in.', 'success')
            return redirect(url_for('main.login'))
    
    return render_template('register.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('main.index'))

@main.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'file' not in request.files:
                flash('No file selected.', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected.', 'error')
                return redirect(request.url)
            
            # Get and validate form data
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
                try:
                    # Generate unique filename
                    original_filename = secure_filename(file.filename)
                    file_extension = original_filename.rsplit('.', 1)[1].lower()
                    unique_filename = f"{uuid.uuid4()}.{file_extension}"
                    
                    # Save file
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    
                    # Get file size
                    file_size = os.path.getsize(file_path)
                    
                    # Create material record
                    material = Material(
                        filename=unique_filename,
                        original_filename=original_filename,
                        description=description if description else None,
                        course_id=int(course_id),
                        year_id=int(year_id),
                        semester_id=int(semester_id),
                        subject_id=int(subject_id),
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
                    return redirect(url_for('main.browse'))
                except Exception as e:
                    # If there was an error saving the file or creating the record,
                    # try to delete the file if it was saved
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    db.session.rollback()
                    current_app.logger.error(f"Error in file upload: {str(e)}")
                    flash('An error occurred while uploading the file.', 'error')
                    return redirect(request.url)
            else:
                allowed_types = ', '.join(current_app.config['ALLOWED_EXTENSIONS']).upper()
                flash(f'Invalid file type. Allowed types: {allowed_types}', 'error')
                return redirect(request.url)
        except Exception as e:
            current_app.logger.error(f"Error in upload route: {str(e)}")
            flash('An error occurred while processing your request.', 'error')
            return redirect(request.url)
    
    # GET request - show upload form
    try:
        courses = Course.query.order_by(Course.name).all()
        return render_template('upload.html', courses=courses)
    except Exception as e:
        current_app.logger.error(f"Error loading upload form: {str(e)}")
        flash('An error occurred while loading the upload form.', 'error')
        return redirect(url_for('main.index'))

@main.route('/browse')
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
    
    # Get sidebar ads
    sidebar_ads = Ad.query.filter_by(is_active=True, placement='sidebar').limit(2).all()
    
    return render_template('browse.html', 
                         materials=materials,
                         subjects=subjects,
                         years=years,
                         semesters=semesters,
                         courses=courses,
                         sidebar_ads=sidebar_ads,
                         current_filters={
                             'subject': subject_filter,
                             'year': year_filter,
                             'semester': semester_filter,
                             'course': course_filter
                         })

@main.route('/material/<int:material_id>')
def material_detail(material_id):
    material = Material.query.get_or_404(material_id)
    
    # Check if material is approved
    if material.status != 'approved':
        flash('This material is not available.', 'error')
        return redirect(url_for('main.browse'))
    
    # Increment view count
    material.view_count += 1
    db.session.commit()
    
    # Check if current user has bookmarked this material
    is_bookmarked = False
    user_rating = None
    if current_user.is_authenticated:
        bookmark = Bookmark.query.filter_by(material_id=material_id, user_id=current_user.id).first()
        is_bookmarked = bookmark is not None
        user_rating = Rating.query.filter_by(material_id=material_id, user_id=current_user.id).first()
    
    # Get all ratings for this material
    ratings = Rating.query.filter_by(material_id=material_id).order_by(Rating.created_at.desc()).all()
    
    return render_template('material_detail.html', 
                         material=material,
                         is_bookmarked=is_bookmarked,
                         user_rating=user_rating,
                         ratings=ratings)

@main.route('/download/<int:material_id>')
@login_required
def download(material_id):
    material = Material.query.get_or_404(material_id)
    
    # Check if material is approved
    if material.status != 'approved':
        flash('This file is not available for download.', 'error')
        return redirect(url_for('main.browse'))
    
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], material.filename)
    
    if not os.path.exists(file_path):
        flash('File not found.', 'error')
        return redirect(url_for('main.browse'))
    
    # Increment download count
    material.download_count += 1
    db.session.commit()
    
    return send_file(file_path, 
                    as_attachment=True, 
                    download_name=material.original_filename)

@main.route('/view/<int:material_id>')
@login_required
def view_material(material_id):
    material = Material.query.get_or_404(material_id)
    
    # Check if material is approved
    if material.status != 'approved' and not current_user.is_admin:
        flash('This file is not available for viewing.', 'error')
        return redirect(url_for('main.browse'))
    
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], material.filename)
    
    if not os.path.exists(file_path):
        flash('File not found.', 'error')
        return redirect(url_for('main.browse'))
    
    # For PDFs, display in browser
    if material.file_type.lower() == 'pdf':
        return send_file(
            file_path,
            mimetype='application/pdf'
        )
    
    # For other file types, download them
    return send_file(
        file_path,
        as_attachment=True,
        download_name=material.original_filename
    )

@main.route('/bookmarks')
@login_required
def bookmarks():
    user_bookmarks = Bookmark.query.filter_by(user_id=current_user.id).order_by(Bookmark.created_at.desc()).all()
    return render_template('bookmarks.html', bookmarks=user_bookmarks)

@main.route('/toggle_bookmark/<int:material_id>', methods=['POST'])
@login_required
def toggle_bookmark(material_id):
    material = Material.query.get_or_404(material_id)
    
    bookmark = Bookmark.query.filter_by(material_id=material_id, user_id=current_user.id).first()
    
    if bookmark:
        # Remove bookmark
        db.session.delete(bookmark)
        flash('Removed from bookmarks.', 'info')
        is_bookmarked = False
    else:
        # Add bookmark
        bookmark = Bookmark(material_id=material_id, user_id=current_user.id)
        db.session.add(bookmark)
        flash('Added to bookmarks.', 'success')
        is_bookmarked = True
    
    db.session.commit()
    
    # Return JSON for AJAX requests
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({'bookmarked': is_bookmarked})
    
    return redirect(request.referrer or url_for('main.browse'))

@main.route('/rate_material/<int:material_id>', methods=['POST'])
@login_required
def rate_material(material_id):
    material = Material.query.get_or_404(material_id)
    rating_value = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()
    
    if not rating_value or rating_value < 1 or rating_value > 5:
        flash('Invalid rating. Please select a rating between 1 and 5 stars.', 'error')
        return redirect(url_for('main.material_detail', material_id=material_id))
    
    # Check if user has already rated this material
    existing_rating = Rating.query.filter_by(material_id=material_id, user_id=current_user.id).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_value
        existing_rating.comment = comment if comment else None
        flash('Your rating has been updated.', 'success')
    else:
        # Create new rating
        new_rating = Rating(
            material_id=material_id,
            user_id=current_user.id,
            rating=rating_value,
            comment=comment if comment else None
        )
        db.session.add(new_rating)
        flash('Thank you for your rating!', 'success')
    
    db.session.commit()
    return redirect(url_for('main.material_detail', material_id=material_id))

@main.route('/doubts')
@login_required
def doubts():
    user_doubts = Doubt.query.filter_by(user_id=current_user.id).order_by(Doubt.created_at.desc()).all()
    subjects = Subject.query.all()
    return render_template('doubts.html', doubts=user_doubts, subjects=subjects)

@main.route('/ask_doubt', methods=['POST'])
@login_required
def ask_doubt():
    title = request.form.get('title', '').strip()
    question = request.form.get('question', '').strip()
    subject_id = request.form.get('subject_id')
    
    if not title or not question:
        flash('Title and question are required.', 'error')
        return redirect(url_for('main.doubts'))
    
    # Create new doubt
    doubt = Doubt(
        user_id=current_user.id,
        subject_id=int(subject_id) if subject_id else None,
        title=title,
        question=question
    )
    
    # Get AI answer
    subject_name = None
    if subject_id:
        subject = Subject.query.get(subject_id)
        if subject:
            subject_name = subject.name
    
    ai_answer = answer_subject_doubt(question, subject_name)
    doubt.answer = ai_answer
    doubt.is_answered = True
    doubt.answered_at = datetime.utcnow()
    
    db.session.add(doubt)
    db.session.commit()
    
    flash('Your doubt has been answered!', 'success')
    return redirect(url_for('main.doubts'))

@main.route('/notifications')
@login_required
def notifications():
    user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    # Mark all notifications as read
    for notification in user_notifications:
        if not notification.is_read:
            notification.is_read = True
    db.session.commit()
    
    return render_template('notifications.html', notifications=user_notifications)

@main.route('/get_years/<int:course_id>')
@login_required
def get_years(course_id):
    try:
        years = Year.query.filter_by(course_id=course_id).order_by(Year.name).all()
        return jsonify([{'id': year.id, 'name': year.name} for year in years])
    except Exception as e:
        current_app.logger.error(f"Error in get_years: {str(e)}")
        return jsonify({'error': 'Failed to fetch years'}), 500

@main.route('/get_semesters/<int:year_id>')
@login_required
def get_semesters(year_id):
    try:
        semesters = Semester.query.filter_by(year_id=year_id).order_by(Semester.name).all()
        return jsonify([{'id': semester.id, 'name': semester.name} for semester in semesters])
    except Exception as e:
        current_app.logger.error(f"Error in get_semesters: {str(e)}")
        return jsonify({'error': 'Failed to fetch semesters'}), 500

@main.route('/get_subjects/<int:semester_id>')
@login_required
def get_subjects(semester_id):
    try:
        subjects = Subject.query.filter_by(semester_id=semester_id).order_by(Subject.name).all()
        return jsonify([{'id': subject.id, 'name': subject.name} for subject in subjects])
    except Exception as e:
        current_app.logger.error(f"Error in get_subjects: {str(e)}")
        return jsonify({'error': 'Failed to fetch subjects'}), 500

@main.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

# Admin Routes
@main.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        # Get statistics for dashboard
        stats = {
            'total_users': User.query.count(),
            'total_materials': Material.query.count(),
            'pending_materials': Material.query.filter_by(status='pending').count(),
            'approved_materials': Material.query.filter_by(status='approved').count(),
            'total_doubts': Doubt.query.count(),
            'unanswered_doubts': Doubt.query.filter_by(is_answered=False).count(),
            'total_ads': Ad.query.count(),
            'active_ads': Ad.query.filter_by(is_active=True).count(),
            'total_downloads': db.session.query(db.func.sum(Material.download_count)).scalar() or 0
        }
        
        # Recent activities
        recent_materials = Material.query.order_by(Material.uploaded_at.desc()).limit(5).all()
        recent_doubts = Doubt.query.order_by(Doubt.created_at.desc()).limit(5).all()
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        
        return render_template('admin/dashboard.html', 
                            stats=stats,
                            recent_materials=recent_materials,
                            recent_doubts=recent_doubts,
                            recent_users=recent_users)
    except Exception as e:
        current_app.logger.error(f"Error in admin_dashboard: {str(e)}")
        flash('An error occurred while loading the dashboard.', 'error')
        return redirect(url_for('main.index'))

@main.route('/admin/notes')
@login_required
def admin_notes():
    if not current_user.is_admin:
        abort(403)
    
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        materials = Material.query.order_by(Material.uploaded_at.desc()).all()
    else:
        materials = Material.query.filter_by(status=status_filter).order_by(Material.uploaded_at.desc()).all()
    
    return render_template('admin/notes_management.html', materials=materials, status_filter=status_filter)

@main.route('/admin/approve_material/<int:material_id>')
@login_required
def approve_material(material_id):
    if not current_user.is_admin:
        abort(403)
    
    material = Material.query.get_or_404(material_id)
    material.status = 'approved'
    material.reviewed_at = datetime.utcnow()
    db.session.commit()
    
    # Create notification for uploader
    notification = Notification(
        user_id=material.uploader_id,
        title='Material Approved',
        message=f'Your uploaded material "{material.original_filename}" has been approved and is now available.',
        type='upload_approved'
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f'Material "{material.original_filename}" approved successfully!', 'success')
    return redirect(url_for('main.admin_notes'))

@main.route('/admin/reject_material/<int:material_id>')
@login_required
def reject_material(material_id):
    if not current_user.is_admin:
        abort(403)
    
    material = Material.query.get_or_404(material_id)
    material.status = 'rejected'
    material.reviewed_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Material "{material.original_filename}" rejected.', 'warning')
    return redirect(url_for('main.admin_notes'))

@main.route('/admin/delete_material/<int:material_id>')
@login_required
def delete_material(material_id):
    if not current_user.is_admin:
        abort(403)
    
    material = Material.query.get_or_404(material_id)
    
    # Delete the file
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], material.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete from database
    db.session.delete(material)
    db.session.commit()
    
    flash(f'Material "{material.original_filename}" deleted successfully!', 'success')
    return redirect(url_for('main.admin_notes'))

@main.route('/admin/doubts')
@login_required
def admin_doubts():
    if not current_user.is_admin:
        abort(403)
    
    doubts = Doubt.query.order_by(Doubt.created_at.desc()).all()
    return render_template('admin/doubts_management.html', doubts=doubts)

@main.route('/admin/respond_doubt/<int:doubt_id>', methods=['POST'])
@login_required
def respond_doubt(doubt_id):
    if not current_user.is_admin:
        abort(403)
    
    doubt = Doubt.query.get_or_404(doubt_id)
    response = request.form.get('response', '').strip()
    
    if response:
        doubt.answer = response
        doubt.is_answered = True
        doubt.answered_at = datetime.utcnow()
        db.session.commit()
        
        # Create notification for user
        notification = Notification(
            user_id=doubt.user_id,
            title='Doubt Answered',
            message=f'Your doubt "{doubt.title}" has been answered by an admin.',
            type='doubt_answered'
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Response added successfully!', 'success')
    else:
        flash('Response cannot be empty.', 'error')
    
    return redirect(url_for('main.admin_doubts'))

@main.route('/admin/ads')
@login_required
def admin_ads():
    if not current_user.is_admin:
        abort(403)
    
    ads = Ad.query.order_by(Ad.created_at.desc()).all()
    return render_template('admin/ads_management.html', ads=ads)

@main.route('/admin/create_ad', methods=['POST'])
@login_required
def create_ad():
    if not current_user.is_admin:
        abort(403)
    
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    link_url = request.form.get('link_url', '').strip()
    placement = request.form.get('placement', 'sidebar')
    
    if not title or not content:
        flash('Title and content are required.', 'error')
        return redirect(url_for('main.admin_ads'))
    
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
            image_url = url_for('static', filename=f'uploads/{unique_filename}')

    ad = Ad(
        title=title,
        content=content,
        image_url=image_url,
        link_url=link_url if link_url else None,
        placement=placement,
        created_by=current_user.id
    )
    
    db.session.add(ad)
    db.session.commit()
    
    flash('Ad created successfully!', 'success')
    return redirect(url_for('main.admin_ads'))

@main.route('/admin/toggle_ad/<int:ad_id>')
@login_required
def toggle_ad(ad_id):
    if not current_user.is_admin:
        abort(403)
    
    ad = Ad.query.get_or_404(ad_id)
    ad.is_active = not ad.is_active
    db.session.commit()
    
    status = 'activated' if ad.is_active else 'deactivated'
    flash(f'Ad "{ad.title}" {status} successfully!', 'success')
    return redirect(url_for('main.admin_ads'))

@main.route('/admin/delete_ad/<int:ad_id>')
@login_required
def delete_ad(ad_id):
    if not current_user.is_admin:
        abort(403)
    
    ad = Ad.query.get_or_404(ad_id)
    
    # Delete the associated image file if it exists
    if ad.image_url:
        try:
            # Extract filename from URL path
            filename = os.path.basename(ad.image_url)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                current_app.logger.info(f"Deleted ad image: {file_path}")
        except Exception as e:
            current_app.logger.error(f"Error deleting ad image file {ad.image_url}: {e}")

    db.session.delete(ad)
    db.session.commit()
    
    flash(f'Ad "{ad.title}" deleted successfully!', 'success')
    return redirect(url_for('main.admin_ads'))

@main.route('/admin/academic')
@login_required
def admin_academic():
    if not current_user.is_admin:
        abort(403)
    try:
        courses = Course.query.order_by(Course.name).all()
        total_years = Year.query.count()
        total_semesters = Semester.query.count()
        total_subjects = Subject.query.count()
        
        return render_template('admin/academic_management.html',
                            courses=courses,
                            total_years=total_years,
                            total_semesters=total_semesters,
                            total_subjects=total_subjects)
    except Exception as e:
        current_app.logger.error(f"Error in admin_academic: {str(e)}")
        flash('An error occurred while loading academic management.', 'error')
        return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/create_course', methods=['POST'])
@login_required
def create_course():
    if not current_user.is_admin:
        abort(403)
    try:
        name = request.form.get('name', '').strip()
        if not name:
            flash('Course name is required.', 'error')
            return redirect(url_for('main.admin_academic'))
        
        if Course.query.filter_by(name=name).first():
            flash('Course already exists.', 'error')
            return redirect(url_for('main.admin_academic'))
        
        course = Course(name=name)
        db.session.add(course)
        db.session.commit()
        
        flash(f'Course "{name}" created successfully!', 'success')
        return redirect(url_for('main.admin_academic'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in create_course: {str(e)}")
        flash('An error occurred while creating the course.', 'error')
        return redirect(url_for('main.admin_academic'))

@main.route('/admin/create_year', methods=['POST'])
@login_required
def create_year():
    if not current_user.is_admin:
        abort(403)
    try:
        name = request.form.get('name', '').strip()
        course_id = request.form.get('course_id')
        
        if not name or not course_id:
            flash('Year name and course are required.', 'error')
            return redirect(url_for('main.admin_academic'))
        
        course = Course.query.get(course_id)
        if not course:
            flash('Invalid course selected.', 'error')
            return redirect(url_for('main.admin_academic'))
        
        if Year.query.filter_by(name=name, course_id=course_id).first():
            flash('Year already exists for this course.', 'error')
            return redirect(url_for('main.admin_academic'))
        
        year = Year(name=name, course_id=course_id)
        db.session.add(year)
        db.session.commit()
        
        flash(f'Year "{name}" created successfully!', 'success')
        return redirect(url_for('main.admin_academic'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in create_year: {str(e)}")
        flash('An error occurred while creating the year.', 'error')
        return redirect(url_for('main.admin_academic'))

@main.route('/admin/create_semester', methods=['POST'])
@login_required
def create_semester():
    if not current_user.is_admin:
        abort(403)
    
    name = request.form.get('name', '').strip()
    year_id = request.form.get('year_id')
    
    if not name or not year_id:
        flash('Semester name and year are required.', 'error')
        return redirect(url_for('main.admin_academic'))
    
    year = Year.query.get(year_id)
    if not year:
        flash('Invalid year selected.', 'error')
        return redirect(url_for('main.admin_academic'))
    
    if Semester.query.filter_by(name=name, year_id=year_id).first():
        flash('Semester already exists for this year.', 'error')
        return redirect(url_for('main.admin_academic'))
    
    semester = Semester(name=name, year_id=year_id)
    db.session.add(semester)
    db.session.commit()
    
    flash(f'Semester "{name}" created successfully!', 'success')
    return redirect(url_for('main.admin_academic'))

@main.route('/admin/create_subject', methods=['POST'])
@login_required
def create_subject():
    if not current_user.is_admin:
        abort(403)
    
    name = request.form.get('name', '').strip()
    semester_id = request.form.get('semester_id')
    
    if not name or not semester_id:
        flash('Subject name and semester are required.', 'error')
        return redirect(url_for('main.admin_academic'))
    
    semester = Semester.query.get(semester_id)
    if not semester:
        flash('Invalid semester selected.', 'error')
        return redirect(url_for('main.admin_academic'))
    
    if Subject.query.filter_by(name=name, semester_id=semester_id).first():
        flash('Subject already exists for this semester.', 'error')
        return redirect(url_for('main.admin_academic'))
    
    subject = Subject(name=name, semester_id=semester_id)
    db.session.add(subject)
    db.session.commit()
    
    flash(f'Subject "{name}" created successfully!', 'success')
    return redirect(url_for('main.admin_academic'))

# DELETE routes for academic CRUD
@main.route('/admin/delete_course/<int:course_id>')
@login_required
def delete_course(course_id):
    if not current_user.is_admin:
        abort(403)
    
    course = Course.query.get_or_404(course_id)
    
    # Find and delete associated years, semesters, subjects, and materials
    years_to_delete = Year.query.filter_by(course_id=course_id).all()
    for year in years_to_delete:
        semesters_to_delete = Semester.query.filter_by(year_id=year.id).all()
        for semester in semesters_to_delete:
            subjects_to_delete = Subject.query.filter_by(semester_id=semester.id).all()
            for subject in subjects_to_delete:
                materials_to_delete = Material.query.filter_by(subject_id=subject.id).all()
                for material in materials_to_delete:
                    # Delete the file
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], material.filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    # Delete from database
                    db.session.delete(material)
                db.session.delete(subject)
            db.session.delete(semester)
        db.session.delete(year)

    db.session.delete(course)
    db.session.commit()
    
    flash(f'Course "{course.name}" and all its associated data have been deleted.', 'success')
    return redirect(url_for('main.admin_academic'))

@main.route('/admin/delete_year/<int:year_id>')
@login_required
def delete_year(year_id):
    if not current_user.is_admin:
        abort(403)
    
    year = Year.query.get_or_404(year_id)
    
    # Find and delete associated semesters, subjects, and materials
    semesters_to_delete = Semester.query.filter_by(year_id=year_id).all()
    for semester in semesters_to_delete:
        subjects_to_delete = Subject.query.filter_by(semester_id=semester.id).all()
        for subject in subjects_to_delete:
            materials_to_delete = Material.query.filter_by(subject_id=subject.id).all()
            for material in materials_to_delete:
                # Delete the file
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], material.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                # Delete from database
                db.session.delete(material)
            db.session.delete(subject)
        db.session.delete(semester)

    db.session.delete(year)
    db.session.commit()
    
    flash(f'Year "{year.name}" and its associated semesters, subjects, and materials have been deleted.', 'success')
    return redirect(url_for('main.admin_academic'))

@main.route('/admin/delete_semester/<int:semester_id>')
@login_required
def delete_semester(semester_id):
    if not current_user.is_admin:
        abort(403)
    
    semester = Semester.query.get_or_404(semester_id)
    
    # Find and delete associated subjects and their materials
    subjects_to_delete = Subject.query.filter_by(semester_id=semester_id).all()
    for subject in subjects_to_delete:
        materials_to_delete = Material.query.filter_by(subject_id=subject.id).all()
        for material in materials_to_delete:
            # Delete the file
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], material.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            # Delete from database
            db.session.delete(material)
        db.session.delete(subject)

    db.session.delete(semester)
    db.session.commit()
    
    flash(f'Semester "{semester.name}" and its associated subjects and materials have been deleted.', 'success')
    return redirect(url_for('main.admin_academic'))

@main.route('/admin/delete_subject/<int:subject_id>')
@login_required
def delete_subject(subject_id):
    if not current_user.is_admin:
        abort(403)
    
    subject = Subject.query.get_or_404(subject_id)
    
    # Find and delete associated materials and their files
    materials_to_delete = Material.query.filter_by(subject_id=subject_id).all()
    for material in materials_to_delete:
        # Delete the file
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], material.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        # Delete from database
        db.session.delete(material)

    db.session.delete(subject)
    db.session.commit()
    
    flash(f'Subject "{subject.name}" and its associated materials have been deleted.', 'success')
    return redirect(url_for('main.admin_academic'))

@main.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        abort(403)
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/user_management.html', users=users)

@main.route('/admin/toggle_admin/<int:user_id>')
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        abort(403)
    
    user = User.query.get_or_404(user_id)
    
    # Prevent removing admin status from yourself
    if user.id == current_user.id:
        flash('You cannot remove admin status from yourself.', 'error')
        return redirect(url_for('main.admin_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'granted' if user.is_admin else 'revoked'
    flash(f'Admin access {status} for {user.name}.', 'success')
    return redirect(url_for('main.admin_users'))

@main.route('/admin/analytics')
@login_required
def admin_analytics():
    if not current_user.is_admin:
        abort(403)
    
    # Comprehensive analytics data
    stats = {
        'users': {
            'total': User.query.count(),
            'admins': User.query.filter_by(is_admin=True).count(),
            'new_this_month': User.query.filter(User.created_at >= datetime.now().replace(day=1)).count()
        },
        'materials': {
            'total': Material.query.count(),
            'approved': Material.query.filter_by(status='approved').count(),
            'pending': Material.query.filter_by(status='pending').count(),
            'rejected': Material.query.filter_by(status='rejected').count(),
            'total_downloads': db.session.query(db.func.sum(Material.download_count)).scalar() or 0,
            'total_views': db.session.query(db.func.sum(Material.view_count)).scalar() or 0
        },
        'doubts': {
            'total': Doubt.query.count(),
            'answered': Doubt.query.filter_by(is_answered=True).count(),
            'unanswered': Doubt.query.filter_by(is_answered=False).count()
        },
        'ads': {
            'total': Ad.query.count(),
            'active': Ad.query.filter_by(is_active=True).count(),
            'total_clicks': db.session.query(db.func.sum(Ad.click_count)).scalar() or 0,
            'total_views': db.session.query(db.func.sum(Ad.view_count)).scalar() or 0
        }
    }
    
    # Top materials by downloads
    top_materials = Material.query.filter_by(status='approved').order_by(Material.download_count.desc()).limit(10).all()
    
    # Most active users
    active_users = User.query.join(Material).group_by(User.id).order_by(db.func.count(Material.id).desc()).limit(10).all()
    
    # Subject-wise statistics
    subject_stats = db.session.query(
        Subject.name,
        db.func.count(Material.id).label('material_count'),
        db.func.sum(Material.download_count).label('total_downloads')
    ).join(Material, Material.subject_id == Subject.id).group_by(Subject.id).all()
    
    return render_template('admin/analytics.html', 
                         stats=stats,
                         top_materials=top_materials,
                         active_users=active_users,
                         subject_stats=subject_stats)

@main.route('/admin/edit_ad/<int:ad_id>', methods=['POST'])
@login_required
def edit_ad(ad_id):
    if not current_user.is_admin:
        abort(403)
    ad = Ad.query.get_or_404(ad_id)
    
    ad.title = request.form.get('title', '').strip()
    ad.content = request.form.get('content', '').strip()
    ad.link_url = request.form.get('link_url', '').strip()
    ad.placement = request.form.get('placement', 'sidebar')

    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            # Delete old image if it exists
            if ad.image_url:
                try:
                    old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], ad.image_url.split('/')[-1])
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                except Exception as e:
                    current_app.logger.error(f"Error deleting old ad image: {e}")

            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
            ad.image_url = url_for('static', filename=f'uploads/{unique_filename}')

    db.session.commit()
    flash('Ad updated successfully!', 'success')
    return redirect(url_for('main.admin_ads'))

@main.route('/admin/edit_subject/<int:subject_id>', methods=['POST'])
@login_required
def edit_subject(subject_id):
    if not current_user.is_admin:
        abort(403)
    subject = Subject.query.get_or_404(subject_id)
    new_name = request.form.get('name', '').strip()
    new_semester_id = request.form.get('semester_id')
    if not new_name or not new_semester_id:
        flash('Subject name and semester are required.', 'error')
        return redirect(url_for('main.admin_academic'))
    semester = Semester.query.get(new_semester_id)
    if not semester:
        flash('Invalid semester selected.', 'error')
        return redirect(url_for('main.admin_academic'))
    # Check for duplicates within the semester (excluding current subject)
    existing = Subject.query.filter(Subject.name == new_name, Subject.semester_id == new_semester_id, Subject.id != subject_id).first()
    if existing:
        flash('Subject name already exists in this semester.', 'error')
        return redirect(url_for('main.admin_academic'))
    subject.name = new_name
    subject.semester_id = new_semester_id
    db.session.commit()
    flash('Subject updated successfully!', 'success')
    return redirect(url_for('main.admin_academic'))

# Context processor to inject unread notification count
@main.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return {'unread_notifications': unread_count}
    return {'unread_notifications': 0}

@main.route('/get_popup_ad')
def get_popup_ad():
    popup_ad = Ad.query.filter_by(is_active=True, placement='popup').first()
    if popup_ad:
        return jsonify({
            'success': True,
            'ad': {
                'title': popup_ad.title,
                'content': popup_ad.content,
                'image_url': popup_ad.image_url,
                'link_url': popup_ad.link_url
            }
        })
    return jsonify({'success': False})
