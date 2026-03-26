import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Admin, Company, Student

auth_bp = Blueprint('auth', __name__)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        role = current_user.get_role()
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'company':
            return redirect(url_for('company.dashboard'))
        elif role == 'student':
            return redirect(url_for('student.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email')
        password = request.form.get('password')

        if role == 'admin':
            user = Admin.query.filter_by(username=email).first()
            if user and user.check_password(password):
                login_user(user)
                flash('Welcome back, Admin!', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                flash('Invalid admin credentials.', 'danger')

        elif role == 'company':
            user = Company.query.filter_by(email=email).first()
            if user and user.check_password(password):
                if user.status == 'blacklisted':
                    flash('Your account has been blacklisted. Contact admin.', 'danger')
                elif user.approval_status == 'pending':
                    flash('Your account is pending admin approval.', 'warning')
                elif user.approval_status == 'rejected':
                    flash('Your registration was rejected. Contact admin.', 'danger')
                else:
                    login_user(user)
                    flash(f'Welcome, {user.name}!', 'success')
                    return redirect(url_for('company.dashboard'))
            else:
                flash('Invalid company credentials.', 'danger')

        elif role == 'student':
            user = Student.query.filter_by(email=email).first()
            if user and user.check_password(password):
                if user.status == 'blacklisted':
                    flash('Your account has been blacklisted. Contact admin.', 'danger')
                else:
                    login_user(user)
                    flash(f'Welcome, {user.name}!', 'success')
                    return redirect(url_for('student.dashboard'))
            else:
                flash('Invalid student credentials.', 'danger')

        else:
            flash('Please select a role.', 'warning')

    return render_template('auth/login.html')


@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        branch = request.form.get('branch')
        cgpa = request.form.get('cgpa')
        graduation_year = request.form.get('graduation_year')
        skills = request.form.get('skills')

        # Check if email already exists
        if Student.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('auth.register_student'))

        # Validate password length
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.register_student'))

        # Handle resume upload
        resume_path = None
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"resume_{email}_{file.filename}")
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                resume_path = filename

        student = Student(
            name=name,
            email=email,
            phone=phone,
            branch=branch,
            cgpa=float(cgpa) if cgpa else None,
            graduation_year=int(graduation_year) if graduation_year else None,
            skills=skills,
            resume_path=resume_path
        )
        student.set_password(password)
        db.session.add(student)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_student.html')


@auth_bp.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        hr_contact = request.form.get('hr_contact')
        industry = request.form.get('industry')
        website = request.form.get('website')
        description = request.form.get('description')

        # Check if email already exists
        if Company.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register_company'))

        # Validate password length
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.register_company'))

        company = Company(
            name=name,
            email=email,
            hr_contact=hr_contact,
            industry=industry,
            website=website,
            description=description
        )
        company.set_password(password)
        db.session.add(company)
        db.session.commit()

        flash('Registration successful! Please wait for admin approval.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_company.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

