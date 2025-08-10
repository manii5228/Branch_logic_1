from flask import Blueprint, render_template, redirect, url_for, flash, request,session
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

from models import User,Student
from auth.forms import RegistrationForm, LoginForm
from config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        # ✅ Handle admin login separately
        if email == Config.ADMIN_EMAIL and password == Config.ADMIN_PASSWORD:
            admin_user = User.query.filter_by(email=email).first()

            if not admin_user:
                # Create admin user in database on first login
                admin_user = User(email=email, password=generate_password_hash('admin'), role='admin')
                db.session.add(admin_user)
                db.session.commit()

            login_user(admin_user)
            session['role'] = 'admin'
            return redirect(url_for('admin.dashboard'))

        # ✅ Student login
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            session['role'] = 'student'
            # ✅ Fetch the student profile and store ID in session
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                session['student_id'] = student.id
                return redirect(url_for('student.student_dashboard'))
        
        flash('Invalid credentials', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('auth/login.html', form=form)

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("Admin access only", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already registered. Please log in.", "danger")
            return redirect(url_for('auth.login'))

        # Properly hash the password
        hashed_password = generate_password_hash(form.password.data)

        new_user = User(email=form.email.data, password=hashed_password, role='student')
        db.session.add(new_user)
        db.session.commit()

        # Create student profile
        student = Student(name=form.name.data, user_id=new_user.id)
        db.session.add(student)
        db.session.commit()
        
        # Log the new user in and redirect to the dashboard
        login_user(new_user)
        session['role'] = 'student'
        session['student_id'] = student.id
        flash("Registration successful! You are now logged in.", "success")
        return redirect(url_for('student.student_dashboard'))

    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))