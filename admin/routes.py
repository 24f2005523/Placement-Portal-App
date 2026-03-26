from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Admin, Company, Student, PlacementDrive, Application, Placement
from functools import wraps

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.get_role() != 'admin':
            flash('Access denied. Admins only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# ─── Dashboard ───────────────────────────────────────────────

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()
    total_placements = Placement.query.count()

    pending_companies = Company.query.filter_by(approval_status='pending').count()
    pending_drives = PlacementDrive.query.filter_by(status='pending').count()

    recent_applications = Application.query.order_by(Application.applied_on.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_applications=total_applications,
        total_placements=total_placements,
        pending_companies=pending_companies,
        pending_drives=pending_drives,
        recent_applications=recent_applications
    )


# ─── Company Management ───────────────────────────────────────

@admin_bp.route('/companies')
@login_required
@admin_required
def companies():
    search = request.args.get('search', '')
    if search:
        company_list = Company.query.filter(
            Company.name.ilike(f'%{search}%') |
            Company.industry.ilike(f'%{search}%')
        ).all()
    else:
        company_list = Company.query.order_by(Company.created_at.desc()).all()
    return render_template('admin/companies.html', companies=company_list, search=search)


@admin_bp.route('/company/<int:company_id>/action', methods=['POST'])
@login_required
@admin_required
def company_action(company_id):
    company = Company.query.get_or_404(company_id)
    action = request.form.get('action')

    if action == 'approve':
        company.approval_status = 'approved'
        flash(f'{company.name} has been approved.', 'success')
    elif action == 'reject':
        company.approval_status = 'rejected'
        flash(f'{company.name} has been rejected.', 'warning')
    elif action == 'blacklist':
        company.status = 'blacklisted'
        flash(f'{company.name} has been blacklisted.', 'danger')
    elif action == 'activate':
        company.status = 'active'
        company.approval_status = 'approved'
        flash(f'{company.name} has been reactivated.', 'success')

    db.session.commit()
    return redirect(url_for('admin.companies'))


@admin_bp.route('/company/<int:company_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    flash('Company deleted successfully.', 'success')
    return redirect(url_for('admin.companies'))


# ─── Student Management ───────────────────────────────────────

@admin_bp.route('/students')
@login_required
@admin_required
def students():
    search = request.args.get('search', '')
    if search:
        student_list = Student.query.filter(
            Student.name.ilike(f'%{search}%') |
            Student.email.ilike(f'%{search}%') |
            Student.phone.ilike(f'%{search}%') |
            Student.id.in_(
                [s.id for s in Student.query.all() if str(s.id) == search]
            )
        ).all()
    else:
        student_list = Student.query.order_by(Student.created_at.desc()).all()
    return render_template('admin/students.html', students=student_list, search=search)


@admin_bp.route('/student/<int:student_id>/action', methods=['POST'])
@login_required
@admin_required
def student_action(student_id):
    student = Student.query.get_or_404(student_id)
    action = request.form.get('action')

    if action == 'blacklist':
        student.status = 'blacklisted'
        flash(f'{student.name} has been blacklisted.', 'danger')
    elif action == 'activate':
        student.status = 'active'
        flash(f'{student.name} has been reactivated.', 'success')

    db.session.commit()
    return redirect(url_for('admin.students'))


@admin_bp.route('/student/<int:student_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully.', 'success')
    return redirect(url_for('admin.students'))


# ─── Placement Drive Management ───────────────────────────────

@admin_bp.route('/drives')
@login_required
@admin_required
def drives():
    drive_list = PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).all()
    return render_template('admin/drives.html', drives=drive_list)


@admin_bp.route('/drive/<int:drive_id>/action', methods=['POST'])
@login_required
@admin_required
def drive_action(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    action = request.form.get('action')

    if action == 'approve':
        drive.status = 'approved'
        flash(f'Drive "{drive.job_title}" has been approved.', 'success')
    elif action == 'reject':
        drive.status = 'rejected'
        flash(f'Drive "{drive.job_title}" has been rejected.', 'warning')

    db.session.commit()
    return redirect(url_for('admin.drives'))


# ─── Applications ─────────────────────────────────────────────

@admin_bp.route('/applications')
@login_required
@admin_required
def applications():
    application_list = Application.query.order_by(Application.applied_on.desc()).all()
    return render_template('admin/applications.html', applications=application_list)


# ─── View Student Profile ─────────────────────────────────────

@admin_bp.route('/student/<int:student_id>/view')
@login_required
@admin_required
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    applications = Application.query.filter_by(student_id=student_id).all()
    return render_template('admin/view_student.html', student=student, applications=applications)


# ─── View Company Profile ─────────────────────────────────────

@admin_bp.route('/company/<int:company_id>/view')
@login_required
@admin_required
def view_company(company_id):
    company = Company.query.get_or_404(company_id)
    drives = PlacementDrive.query.filter_by(company_id=company_id).all()
    return render_template('admin/view_company.html', company=company, drives=drives)