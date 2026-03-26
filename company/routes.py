from flask import Blueprint, render_template
from flask_login import login_required

company_bp = Blueprint('company', __name__)

@company_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('company/dashboard.html')