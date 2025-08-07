from flask import Blueprint
from extensions import db
from flask_login import login_required
from flask import render_template,current_app, session, redirect, url_for,flash,request,send_file,send_from_directory
import os
from werkzeug.utils import secure_filename
from models import Student, Job,Application


student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('auth.login'))

    student_id = session['student_id']
    student = Student.query.get_or_404(student_id)
    
    applied_job_ids = [app.job_id for app in student.applied_jobs]
    recent_jobs = Job.query.order_by(Job.posted_on.desc()).limit(5).all()

    return render_template('student/dashboard.html', student=student,
                           recent_jobs=recent_jobs,
                           applied_job_ids=applied_job_ids)

@student_bp.route('/jobs')
def view_jobs():
    jobs = Job.query.order_by(Job.posted_on.desc()).all()
    student_id = session.get('student_id')
    applied_job_ids = []

    if student_id:
        student = Student.query.get(student_id)
        applied_job_ids = [app.job_id for app in student.applied_jobs] 

    return render_template('student/jobs.html', jobs=jobs, applied_job_ids=applied_job_ids)

@student_bp.route('/apply/<int:job_id>', methods=['POST'])
def apply_job(job_id):
    if 'student_id' not in session:
        return redirect(url_for('auth.login'))

    student_id = session['student_id']
    existing_app = Application.query.filter_by(student_id=student_id, job_id=job_id).first()

    if existing_app:
        flash('You have already applied for this job.', 'warning')
        return redirect(url_for('student.view_jobs'))

    application = Application(student_id=student_id, job_id=job_id)
    db.session.add(application)
    db.session.commit()
    flash('Application submitted successfully!', 'success')
    return redirect(url_for('student.view_applications'))

@student_bp.route('/applications')
def view_applications():
    if 'student_id' not in session:
        return redirect(url_for('auth.login'))

    student_id = session['student_id']
    student = Student.query.get_or_404(student_id)
    applications = student.applied_jobs

    return render_template('student/my_applications.html', applications=applications)

@student_bp.route('/resume/upload', methods=['GET', 'POST'])
def upload_resume():
    if 'student_id' not in session:
        return redirect(url_for('auth.login'))

    student = Student.query.get_or_404(session['student_id'])

    if request.method == 'POST':
        file = request.files['resume']
        if file and file.filename.endswith('.pdf'):
            filepath = os.path.join('static/resumes', secure_filename(file.filename))
            file.save(filepath)
            student.resume = filepath
            db.session.commit()
            flash('Resume uploaded successfully!', 'success')
            return redirect(url_for('student.student_dashboard'))
        else:
            flash('Please upload a PDF file.', 'danger')

    return render_template('student/upload_resume.html', student=student)

@student_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if 'student_id' not in session:
        return redirect(url_for('auth.login'))

    student = Student.query.get_or_404(session['student_id'])

    if request.method == 'POST':
        student.name = request.form['name']
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student.student_dashboard'))

    return render_template('student/edit_profile.html', student=student)



@student_bp.route('/resume/view')
def view_resume():
    if 'student_id' not in session:
        return redirect(url_for('auth.login'))

    student = Student.query.get_or_404(session['student_id'])

    if not student.resume:
        flash("No resume uploaded.", "warning")
        return redirect(url_for('student.student_dashboard'))

    # Make sure this path matches where you store resumes
    resume_folder = os.path.join(current_app.root_path, 'static', 'resumes')
    resume_filename = os.path.basename(student.resume)

    # Full safe path
    resume_path = os.path.join(resume_folder, resume_filename)

    if not os.path.exists(resume_path):
        flash("Resume file not found on server.", "danger")
        return redirect(url_for('student.student_dashboard'))

    return send_from_directory(directory=resume_folder, path=resume_filename, as_attachment=False)


@student_bp.route('/jobs/search', methods=['GET'])
def search_jobs():
    query = request.args.get('q', '')
    jobs = Job.query.filter(Job.title.ilike(f'%{query}%')).all()
    return render_template('student/jobs.html', jobs=jobs, query=query)

@student_bp.route('/applications/status/<status>')
def view_applications_by_status(status):
    if 'student_id' not in session:
        return redirect(url_for('auth.login'))

    apps = Application.query.filter_by(student_id=session['student_id'], status=status).all()
    return render_template('student/my_applications.html', applications=apps, filter_status=status)
@student_bp.route('/job/<int:job_id>')
def job_details(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('student/job_details.html', job=job)
