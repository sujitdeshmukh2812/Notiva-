import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort, jsonify, make_response, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from extensions import db
from models import User, Material, Course, Year, Semester, Subject, Rating, Bookmark, Notification, Doubt, Ad
import openai_helper

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
    total_downloads = db.session.query(db.func.sum(Material.download_count)).scalar() or 0

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
            
            if user and user.check_password(password):
                login_user(user)
                current_app.logger.info(f"Login successful for {email}")
                flash(f'Welcome back, {user.name}!', 'success')
                
                # Set a session variable to show the ad popup
                from flask import session
                session['show_ad_popup'] = True
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                
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
        
        if not name or not email or not password:
            flash('All fields are required.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
        else:
            new_user = User(name=name, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
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
            if 'file' not in request.files:
                flash('No file selected.', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected.', 'error')
                return redirect(request.url)
            
            course_id = request.form.get('course_id')
            year_id = request.form.get('year_id')
            semester_id = request.form.get('semester_id')
            subject_id = request.form.get('subject_id')
            description = request.form.get('description', '').strip()
            
            if not all([course_id, year_id, semester_id, subject_id]):
                flash('All fields are required.', 'error')
                return redirect(request.url)
            
            subject = Subject.query.get(subject_id)
            if not subject or subject.semester_id != int(semester_id):
                flash('Invalid subject selection.', 'error')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                try:
                    original_filename = secure_filename(file.filename)
                    file_extension = original_filename.rsplit('.', 1)[1].lower()
                    unique_filename = f"{uuid.uuid4()}.{file_extension}"
                    
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    
                    file_size = os.path.getsize(file_path)
                    
                    new_material = Material(
                        filename=unique_filename,
                        original_filename=original_filename,
                        description=description,
                        course_id=course_id,
                        year_id=year_id,
                        semester_id=semester_id,
                        subject_id=subject_id,
                        file_size=file_size,
                        file_type=file_extension,
                        uploader_id=current_user.id,
                        status='pending'
                    )
                    
                    db.session.add(new_material)
                    db.session.commit()
                    
                    flash('File uploaded successfully! It will be available after admin approval.', 'success')
                    return redirect(url_for('main.browse'))
                except Exception as e:
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
    
    try:
        courses = Course.query.order_by(Course.name).all()
        return render_template('upload.html', courses=courses)
    except Exception as e:
        current_app.logger.error(f"Error loading upload form: {str(e)}")
        flash('An error occurred while loading the upload form.', 'error')
        return redirect(url_for('main.index'))

@main.route('/browse')
def browse():
    subject_filter = request.args.get('subject', '')
    year_filter = request.args.get('year', '')
    semester_filter = request.args.get('semester', '')
    course_filter = request.args.get('course', '')
    
    query = Material.query.filter_by(status='approved')
    
    if subject_filter:
        query = query.filter(Material.subject.has(name=subject_filter))
    if year_filter:
        query = query.filter(Material.year.has(name=year_filter))
    if semester_filter:
        query = query.filter(Material.semester.has(name=semester_filter))
    if course_filter:
        query = query.filter(Material.course.has(name=course_filter))
    
    materials = query.order_by(Material.uploaded_at.desc()).all()
    
    subjects = sorted(list(set([m.subject.name for m in materials])))
    years = sorted(list(set([m.year.name for m in materials])))
    semesters = sorted(list(set([m.semester.name for m in materials])))
    courses = sorted(list(set([m.course.name for m in materials])))
    
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
    
    if material.status != 'approved':
        flash('This material is not available.', 'error')
        return redirect(url_for('main.browse'))
    
    material.view_count += 1
    db.session.commit()
    
    is_bookmarked = False
    user_rating = None
    if current_user.is_authenticated:
        is_bookmarked = Bookmark.query.filter_by(material_id=material_id, user_id=current_user.id).first() is not None
        user_rating = Rating.query.filter_by(material_id=material_id, user_id=current_user.id).first()
            
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
    
    if material.status != 'approved':
        flash('This file is not available for download.', 'error')
        return redirect(url_for('main.browse'))
    
    material.download_count += 1
    db.session.commit()
    
    return send_file(os.path.join(current_app.config['UPLOAD_FOLDER'], material.filename), as_attachment=True)

@main.route('/view/<int:material_id>')
@login_required
def view_material(material_id):
    material = Material.query.get_or_404(material_id)
    
    if material.status != 'approved' and not current_user.is_admin:
        flash('This file is not available for viewing.', 'error')
        return redirect(url_for('main.browse'))
    
    return send_file(os.path.join(current_app.config['UPLOAD_FOLDER'], material.filename))

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
        db.session.delete(bookmark)
        db.session.commit()
        flash('Removed from bookmarks.', 'info')
        is_bookmarked = False
    else:
        new_bookmark = Bookmark(material_id=material_id, user_id=current_user.id)
        db.session.add(new_bookmark)
        db.session.commit()
        flash('Added to bookmarks.', 'success')
        is_bookmarked = True
    
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
    
    rating = Rating.query.filter_by(material_id=material_id, user_id=current_user.id).first()
    
    if rating:
        rating.rating = rating_value
        rating.comment = comment
        flash('Your rating has been updated.', 'success')
    else:
        new_rating = Rating(
            material_id=material_id,
            user_id=current_user.id,
            rating=rating_value,
            comment=comment
        )
        db.session.add(new_rating)
        flash('Thank you for your rating!', 'success')
    
    db.session.commit()
    return redirect(url_for('main.material_detail', material_id=material_id))

@main.route('/doubts')
@login_required
def doubts():
    user_doubts = Doubt.query.filter_by(user_id=current_user.id).order_by(Doubt.created_at.desc()).all()
    subjects = Subject.query.order_by(Subject.name).all()
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
    
    subject = None
    if subject_id:
        subject = Subject.query.get(subject_id)
        
    ai_answer = openai_helper.answer_subject_doubt(question, subject.name if subject else None)
    
    new_doubt = Doubt(
        user_id=current_user.id,
        subject_id=subject_id,
        title=title,
        question=question,
        answer=ai_answer,
        is_answered=True,
        answered_at=datetime.utcnow()
    )
    
    db.session.add(new_doubt)
    db.session.commit()
    
    flash('Your doubt has been answered!', 'success')
    return redirect(url_for('main.doubts'))

@main.route('/notifications')
@login_required
def notifications():
    user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
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
    
    query = Material.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
        
    materials = query.order_by(Material.uploaded_at.desc()).all()
    
    return render_template('admin/notes_management.html', materials=materials, status_filter=status_filter)

@main.route('/admin/approve_material/<int:material_id>')
@login_required
def approve_material(material_id):
    if not current_user.is_admin:
        abort(403)
    
    material = Material.query.get_or_404(material_id)
    material.status = 'approved'
    material.reviewed_at = datetime.utcnow()
    
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
    
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], material.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    db.session.delete(material)
    db.session.commit()
    
    flash(f'Material "{material.original_filename}" deleted successfully!', 'success')
    return redirect(url_for('main.admin_notes'))

@main.route('/admin/doubts')
@login_required
def admin_doubts():
    if not current_user.is_admin:
        abort(403)
    
    doubts_ref = db.collection('doubts').order_by('created_at', direction='DESCENDING')
    doubts = [doc.to_dict() for doc in doubts_ref.stream()]
    
    return render_template('admin/doubts_management.html', doubts=doubts)

@main.route('/admin/respond_doubt/<string:doubt_id>', methods=['POST'])
@login_required
def respond_doubt(doubt_id):
    if not current_user.is_admin:
        abort(403)
    
    doubt_ref = db.collection('doubts').document(doubt_id)
    response = request.form.get('response', '').strip()
    
    if response:
        doubt_ref.update({
            'answer': response,
            'is_answered': True,
            'answered_at': datetime.utcnow()
        })
        
        doubt = doubt_ref.get().to_dict()
        
        notification_id = str(uuid.uuid4())
        notification = Notification(
            id=notification_id,
            user_id=doubt['user_id'],
            title='Doubt Answered',
            message=f'Your doubt "{doubt["title"]}" has been answered by an admin.',
            type='doubt_answered'
        )
        notification.save()
        
        flash('Response added successfully!', 'success')
    else:
        flash('Response cannot be empty.', 'error')
    
    return redirect(url_for('main.admin_doubts'))

@main.route('/admin/ads')
@login_required
def admin_ads():
    if not current_user.is_admin:
        abort(403)
    
    ads_ref = db.collection('ads').order_by('created_at', direction='DESCENDING')
    ads = [doc.to_dict() for doc in ads_ref.stream()]
    
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
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file.filename:
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                
                blob = bucket.blob(f"ads/{unique_filename}")
                blob.upload_from_file(file)
                
                image_url = blob.public_url
                image_filename = unique_filename
            else:
                flash('Invalid image file type.', 'error')
                return redirect(url_for('main.admin_ads'))

    ad_id = str(uuid.uuid4())
    ad = Ad(
        id=ad_id,
        title=title,
        content=content,
        image_filename=image_filename,
        image_url=image_url,
        link_url=link_url if link_url else None,
        placement=placement,
        created_by=current_user.id,
        is_active=True,
        start_date=None,
        end_date=None,
        click_count=0,
        view_count=0
    )
    
    ad.save()
    
    flash('Ad created successfully!', 'success')
    return redirect(url_for('main.admin_ads'))

@main.route('/admin/toggle_ad/<string:ad_id>')
@login_required
def toggle_ad(ad_id):
    if not current_user.is_admin:
        abort(403)
    
    ad_ref = db.collection('ads').document(ad_id)
    ad = ad_ref.get().to_dict()
    
    new_status = not ad.get('is_active', False)
    ad_ref.update({'is_active': new_status})
    
    status = 'activated' if new_status else 'deactivated'
    flash(f'Ad "{ad["title"]}" {status} successfully!', 'success')
    return redirect(url_for('main.admin_ads'))

@main.route('/admin/delete_ad/<string:ad_id>')
@login_required
def delete_ad(ad_id):
    if not current_user.is_admin:
        abort(403)
    
    ad_doc = db.collection('ads').document(ad_id).get()
    if not ad_doc.exists:
        abort(404)
        
    ad = ad_doc.to_dict()
    
    if ad.get('image_filename'):
        blob = bucket.blob(f"ads/{ad['image_filename']}")
        if blob.exists():
            blob.delete()
            
    db.collection('ads').document(ad_id).delete()
    
    flash(f'Ad "{ad["title"]}" deleted successfully!', 'success')
    return redirect(url_for('main.admin_ads'))

@main.route('/admin/academic')
@login_required
def admin_academic():
    if not current_user.is_admin:
        abort(403)
    try:
        courses_ref = db.collection('courses').order_by('name')
        courses = [doc.to_dict() for doc in courses_ref.stream()]
        
        total_years = len([doc.id for doc in db.collection('years').stream()])
        total_semesters = len([doc.id for doc in db.collection('semesters').stream()])
        total_subjects = len([doc.id for doc in db.collection('subjects').stream()])
        
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
        
        existing_course = db.collection('courses').where('name', '==', name).limit(1).stream()
        if len(list(existing_course)) > 0:
            flash('Course already exists.', 'error')
            return redirect(url_for('main.admin_academic'))
        
        course_id = str(uuid.uuid4())
        course = Course(id=course_id, name=name)
        course.save()
        
        flash(f'Course "{name}" created successfully!', 'success')
        return redirect(url_for('main.admin_academic'))
    except Exception as e:
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
        
        course_doc = db.collection('courses').document(course_id).get()
        if not course_doc.exists:
            flash('Invalid course selected.', 'error')
            return redirect(url_for('main.admin_academic'))
        
        existing_year = db.collection('years').where('name', '==', name).where('course_id', '==', course_id).limit(1).stream()
        if len(list(existing_year)) > 0:
            flash('Year already exists for this course.', 'error')
            return redirect(url_for('main.admin_academic'))
        
        year_id = str(uuid.uuid4())
        year = Year(id=year_id, name=name, course_id=course_id)
        year.save()
        
        flash(f'Year "{name}" created successfully!', 'success')
        return redirect(url_for('main.admin_academic'))
    except Exception as e:
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
    
    year_doc = db.collection('years').document(year_id).get()
    if not year_doc.exists:
        flash('Invalid year selected.', 'error')
        return redirect(url_for('main.admin_academic'))
    
    existing_semester = db.collection('semesters').where('name', '==', name).where('year_id', '==', year_id).limit(1).stream()
    if len(list(existing_semester)) > 0:
        flash('Semester already exists for this year.', 'error')
        return redirect(url_for('main.admin_academic'))
    
    semester_id = str(uuid.uuid4())
    semester = Semester(id=semester_id, name=name, year_id=year_id)
    semester.save()
    
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
    
    semester_doc = db.collection('semesters').document(semester_id).get()
    if not semester_doc.exists:
        flash('Invalid semester selected.', 'error')
        return redirect(url_for('main.admin_academic'))
    
    existing_subject = db.collection('subjects').where('name', '==', name).where('semester_id', '==', semester_id).limit(1).stream()
    if len(list(existing_subject)) > 0:
        flash('Subject already exists for this semester.', 'error')
        return redirect(url_for('main.admin_academic'))
    
    subject_id = str(uuid.uuid4())
    subject = Subject(id=subject_id, name=name, semester_id=semester_id)
    subject.save()
    
    flash(f'Subject "{name}" created successfully!', 'success')
    return redirect(url_for('main.admin_academic'))

@main.route('/admin/delete_course/<string:course_id>')
@login_required
def delete_course(course_id):
    if not current_user.is_admin:
        abort(403)
    
    course_doc = db.collection('courses').document(course_id).get()
    if not course_doc.exists:
        abort(404)
        
    course_name = course_doc.to_dict()['name']
    
    years_ref = db.collection('years').where('course_id', '==', course_id)
    for year_doc in years_ref.stream():
        delete_year(year_doc.id)
        
    db.collection('courses').document(course_id).delete()
    
    flash(f'Course "{course_name}" and all its associated data have been deleted.', 'success')
    return redirect(url_for('main.admin_academic'))

@main.route('/admin/delete_year/<string:year_id>')
@login_required
def delete_year(year_id):
    if not current_user.is_admin:
        abort(403)
    
    year_doc = db.collection('years').document(year_id).get()
    if not year_doc.exists:
        abort(404)
        
    year_name = year_doc.to_dict()['name']
    
    semesters_ref = db.collection('semesters').where('year_id', '==', year_id)
    for semester_doc in semesters_ref.stream():
        delete_semester(semester_doc.id)
        
    db.collection('years').document(year_id).delete()
    
    flash(f'Year "{year_name}" and its associated semesters, subjects, and materials have been deleted.', 'success')
    return redirect(url_for('main.admin_academic'))

@main.route('/admin/delete_semester/<string:semester_id>')
@login_required
def delete_semester(semester_id):
    if not current_user.is_admin:
        abort(403)
    
    semester_doc = db.collection('semesters').document(semester_id).get()
    if not semester_doc.exists:
        abort(404)
        
    semester_name = semester_doc.to_dict()['name']
    
    subjects_ref = db.collection('subjects').where('semester_id', '==', semester_id)
    for subject_doc in subjects_ref.stream():
        delete_subject(subject_doc.id)
        
    db.collection('semesters').document(semester_id).delete()
    
    flash(f'Semester "{semester_name}" and its associated subjects and materials have been deleted.', 'success')
    return redirect(url_for('main.admin_academic'))

@main.route('/admin/delete_subject/<string:subject_id>')
@login_required
def delete_subject(subject_id):
    if not current_user.is_admin:
        abort(403)
    
    subject_doc = db.collection('subjects').document(subject_id).get()
    if not subject_doc.exists:
        abort(404)
        
    subject_name = subject_doc.to_dict()['name']
    
    materials_ref = db.collection('materials').where('subject_id', '==', subject_id)
    for material_doc in materials_ref.stream():
        delete_material(material_doc.id)
        
    db.collection('subjects').document(subject_id).delete()
    
    flash(f'Subject "{subject_name}" and its associated materials have been deleted.', 'success')
    return redirect(url_for('main.admin_academic'))

@main.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        abort(403)
    
    users_ref = db.collection('users').order_by('created_at', direction='DESCENDING')
    users = [doc.to_dict() for doc in users_ref.stream()]
    
    return render_template('admin/user_management.html', users=users)

@main.route('/admin/toggle_admin/<string:user_id>')
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        abort(403)
    
    user_ref = db.collection('users').document(user_id)
    user = user_ref.get().to_dict()
    
    if user_id == current_user.id:
        flash('You cannot remove admin status from yourself.', 'error')
        return redirect(url_for('main.admin_users'))
    
    new_status = not user.get('is_admin', False)
    user_ref.update({'is_admin': new_status})
    
    status = 'granted' if new_status else 'revoked'
    flash(f'Admin access {status} for {user["name"]}.', 'success')
    return redirect(url_for('main.admin_users'))

@main.route('/admin/analytics')
@login_required
def admin_analytics():
    if not current_user.is_admin:
        abort(403)
    
    stats = {
        'users': {
            'total': len([doc.id for doc in db.collection('users').stream()]),
            'admins': len([doc.id for doc in db.collection('users').where('is_admin', '==', True).stream()]),
            'new_this_month': len([doc.id for doc in db.collection('users').where('created_at', '>=', datetime.now().replace(day=1)).stream()])
        },
        'materials': {
            'total': len([doc.id for doc in db.collection('materials').stream()]),
            'approved': len([doc.id for doc in db.collection('materials').where('status', '==', 'approved').stream()]),
            'pending': len([doc.id for doc in db.collection('materials').where('status', '==', 'pending').stream()]),
            'rejected': len([doc.id for doc in db.collection('materials').where('status', '==', 'rejected').stream()]),
            'total_downloads': sum([doc.to_dict().get('download_count', 0) for doc in db.collection('materials').stream()]),
            'total_views': sum([doc.to_dict().get('view_count', 0) for doc in db.collection('materials').stream()])
        },
        'doubts': {
            'total': len([doc.id for doc in db.collection('doubts').stream()]),
            'answered': len([doc.id for doc in db.collection('doubts').where('is_answered', '==', True).stream()]),
            'unanswered': len([doc.id for doc in db.collection('doubts').where('is_answered', '==', False).stream()])
        },
        'ads': {
            'total': len([doc.id for doc in db.collection('ads').stream()]),
            'active': len([doc.id for doc in db.collection('ads').where('is_active', '==', True).stream()]),
            'total_clicks': sum([doc.to_dict().get('click_count', 0) for doc in db.collection('ads').stream()]),
            'total_views': sum([doc.to_dict().get('view_count', 0) for doc in db.collection('ads').stream()])
        }
    }
    
    top_materials_ref = db.collection('materials').where('status', '==', 'approved').order_by('download_count', direction='DESCENDING').limit(10)
    top_materials = [doc.to_dict() for doc in top_materials_ref.stream()]
    
    # This is not efficient in Firestore, so we'll just get the latest users
    active_users_ref = db.collection('users').order_by('created_at', direction='DESCENDING').limit(10)
    active_users = [doc.to_dict() for doc in active_users_ref.stream()]
    
    subject_stats_ref = db.collection('subjects')
    subject_stats = []
    for subject_doc in subject_stats_ref.stream():
        subject = subject_doc.to_dict()
        materials_ref = db.collection('materials').where('subject_id', '==', subject_doc.id)
        material_count = len([doc.id for doc in materials_ref.stream()])
        total_downloads = sum([doc.to_dict().get('download_count', 0) for doc in materials_ref.stream()])
        subject_stats.append({
            'name': subject['name'],
            'material_count': material_count,
            'total_downloads': total_downloads
        })
        
    return render_template('admin/analytics.html', 
                         stats=stats,
                         top_materials=top_materials,
                         active_users=active_users,
                         subject_stats=subject_stats)

@main.route('/admin/edit_ad/<string:ad_id>', methods=['POST'])
@login_required
def edit_ad(ad_id):
    if not current_user.is_admin:
        abort(403)
    ad_ref = db.collection('ads').document(ad_id)
    
    ad_ref.update({
        'title': request.form.get('title', '').strip(),
        'content': request.form.get('content', '').strip(),
        'link_url': request.form.get('link_url', '').strip(),
        'placement': request.form.get('placement', 'sidebar')
    })

    if 'image' in request.files:
        file = request.files['image']
        if file.filename:
            if allowed_file(file.filename):
                ad = ad_ref.get().to_dict()
                if ad.get('image_filename'):
                    try:
                        old_blob = bucket.blob(f"ads/{ad['image_filename']}")
                        if old_blob.exists():
                            old_blob.delete()
                    except Exception as e:
                        current_app.logger.error(f"Error deleting old ad image: {e}")

                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                
                blob = bucket.blob(f"ads/{unique_filename}")
                blob.upload_from_file(file)
                
                ad_ref.update({
                    'image_url': blob.public_url,
                    'image_filename': unique_filename
                })
            else:
                flash('Invalid image file type.', 'error')
                return redirect(url_for('main.admin_ads'))

    flash('Ad updated successfully!', 'success')
    return redirect(url_for('main.admin_ads'))

@main.route('/admin/edit_subject/<string:subject_id>', methods=['POST'])
@login_required
def edit_subject(subject_id):
    if not current_user.is_admin:
        abort(403)
    subject_ref = db.collection('subjects').document(subject_id)
    new_name = request.form.get('name', '').strip()
    new_semester_id = request.form.get('semester_id')
    if not new_name or not new_semester_id:
        flash('Subject name and semester are required.', 'error')
        return redirect(url_for('main.admin_academic'))
    
    semester_doc = db.collection('semesters').document(new_semester_id).get()
    if not semester_doc.exists:
        flash('Invalid semester selected.', 'error')
        return redirect(url_for('main.admin_academic'))
        
    existing = db.collection('subjects').where('name', '==', new_name).where('semester_id', '==', new_semester_id).limit(1).stream()
    if len(list(existing)) > 0 and list(existing)[0].id != subject_id:
        flash('Subject name already exists in this semester.', 'error')
        return redirect(url_for('main.admin_academic'))
        
    subject_ref.update({
        'name': new_name,
        'semester_id': new_semester_id
    })
    flash('Subject updated successfully!', 'success')
    return redirect(url_for('main.admin_academic'))

@main.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        notifications_ref = db.collection('notifications').where('user_id', '==', current_user.id).where('is_read', '==', False)
        unread_count = len([doc.id for doc in notifications_ref.stream()])
        return {'unread_notifications': unread_count}
    return {'unread_notifications': 0}

@main.route('/get_popup_ad')
def get_popup_ad():
    popup_ad_ref = db.collection('ads').where('is_active', '==', True).where('placement', '==', 'popup').limit(1)
    popup_ad_docs = [doc.to_dict() for doc in popup_ad_ref.stream()]
    if popup_ad_docs:
        popup_ad = popup_ad_docs[0]
        return jsonify({
            'success': True,
            'ad': {
                'title': popup_ad['title'],
                'content': popup_ad['content'],
                'image_url': popup_ad.get('image_url'),
                'link_url': popup_ad.get('link_url')
            }
        })
    return jsonify({'success': False})

@main.route('/ad_popup_shown', methods=['POST'])
def ad_popup_shown():
    from flask import session
    session['show_ad_popup'] = False
    return jsonify({'success': True})
