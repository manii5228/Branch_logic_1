from flask import Blueprint, render_template, redirect, url_for, flash, request, session, send_from_directory, current_app, send_file
import os
from werkzeug.utils import secure_filename
from models import Student, Job, Application, Category
from extensions import db
from flask_login import login_required, current_user
from sqlalchemy import or_,func,and_
from sqlalchemy.orm import joinedload
from flask import jsonify

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard', methods=['GET'])
@login_required
def student_dashboard():
    from models import Job, Application, Category
    from sqlalchemy import or_

    # Get filter/search parameters
    query = request.args.get('q', '').strip()
    min_salary = request.args.get('min_salary', type=int)
    category_id = request.args.get('category_id', type=int)

    jobs = Job.query

    if query:
        jobs = jobs.filter(
            or_(
                Job.title.ilike(f"%{query}%"),
                Job.company.ilike(f"%{query}%"),
                Job.tags.ilike(f"%{query}%"),
                Job.description.ilike(f"%{query}%"),
                Job.location.ilike(f"%{query}%")
            )
        )

    if min_salary:
        jobs = jobs.filter(Job.min_salary >= min_salary)

    if category_id:
        jobs = jobs.filter(Job.category_id == category_id)

    jobs = jobs.all()

    # ✅ Make sure Application.student_id and current_user.id match types
    applied_job_ids = [
        app.job_id
        for app in Application.query
            .with_entities(Application.job_id)
            .filter(Application.student_id == int(current_user.id))
            .all()
    ]
    applied_job_ids = [job_id for (job_id,) in applied_job_ids]  # unpack tuples

    categories = Category.query.all()

    return render_template(
        'student/dashboard.html',
        jobs=jobs,
        categories=categories,
        query=query,
        min_salary=min_salary,
        category_id=category_id,
        applied_job_ids=applied_job_ids
    )

@student_bp.route('/jobs')
@login_required
def view_jobs():
    student_id = session.get('student_id')

    if not student_id:
        return redirect(url_for('auth.login'))

    # Get all jobs
    jobs = Job.query.order_by(Job.posted_on.desc()).all()

    # Get list of job_ids the student already applied for
    applied_job_ids = db.session.query(Application.job_id).filter_by(student_id=student_id).all()

    # Flatten & ensure integers
    applied_job_ids = [int(job_id) for (job_id,) in applied_job_ids]

    return render_template('student/jobs.html', jobs=jobs, applied_job_ids=applied_job_ids)

@student_bp.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    student_id = session.get('student_id')
    if not student_id:
        return redirect(url_for('auth.login'))

    existing_app = Application.query.filter_by(student_id=student_id, job_id=job_id).first()

    if existing_app:
        flash('You have already applied for this job.', 'warning')
        return redirect(url_for('student.view_jobs',job_id=job_id))

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
@login_required
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
@login_required
def edit_profile():
    if 'student_id' not in session:
        return redirect(url_for('auth.login'))

    student = Student.query.get_or_404(session['student_id'])

    if request.method == 'POST':
        student.name = request.form['name']
        student.cgpa = request.form['cgpa']
        student.phone = request.form['phone']
        student.github_id = request.form['github_id']
        student.linkedin_id = request.form['linkedin_id']
        student.portfolio = request.form['portfolio']
        student.experience = request.form['experience']
        student.address = request.form['address']
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

    resume_folder = os.path.join(current_app.root_path, 'static', 'resumes')
    resume_filename = os.path.basename(student.resume)
    resume_path = os.path.join(resume_folder, resume_filename)

    if not os.path.exists(resume_path):
        flash("Resume file not found on server.", "danger")
        return redirect(url_for('student.student_dashboard'))

    return send_from_directory(directory=resume_folder, path=resume_filename, as_attachment=False)



@student_bp.route('/applications/status/<status>')
def view_applications_by_status(status):
    if 'student_id' not in session:
        return redirect(url_for('auth.login'))

    apps = Application.query.filter_by(student_id=session['student_id'], status=status).all()
    return render_template('student/my_applications.html', applications=apps, filter_status=status)

@student_bp.route('/job/<int:job_id>')
@login_required
def job_details(job_id):
    student_id = session.get('student_id')

    if not student_id:
        return redirect(url_for('auth.login'))

    job = Job.query.get_or_404(job_id)

    # Check if this student already applied
    applied = Application.query.filter_by(student_id=student_id, job_id=job_id).first() is not None

    return render_template('student/job_details.html', job=job, applied=applied)



@student_bp.route('/jobs/filter-json')
def filter_jobs_json():
    query = request.args.get('q', '').strip()
    job_types = request.args.getlist('job_type')
    experience_levels = request.args.getlist('experience')
    locations = request.args.getlist('location')
    min_salary = request.args.get('min_salary', type=int)

    jobs_query = Job.query.order_by(Job.posted_on.desc())

    if query:
        jobs_query = jobs_query.filter(db.or_(
            Job.title.ilike(f'%{query}%'),
            Job.company.ilike(f'%{query}%'),
            Job.description.ilike(f'%{query}%'),
            Job.tags.ilike(f'%{query}%')
        ))

    if job_types:
        jobs_query = jobs_query.filter(Job.job_type.in_(job_types))

    if experience_levels:
        jobs_query = jobs_query.filter(Job.experience_level.in_(experience_levels))

    if locations:
        jobs_query = jobs_query.filter(Job.location.in_(locations))

    if min_salary is not None:
        jobs_query = jobs_query.filter(Job.min_salary >= min_salary)

    jobs = jobs_query.all()

    return jsonify([
        {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "type": job.job_type,
            "experience": job.experience_level,
            "salary": job.min_salary,
            "posted_on": job.posted_on.strftime('%Y-%m-%d')
        }
        for job in jobs
    ])
