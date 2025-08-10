from flask import Blueprint,render_template, redirect, url_for, flash, request, session,send_from_directory, current_app,send_file
from models import Job,Application,Student,Category
from extensions import db
from flask_login import login_required, current_user
import os

admin_bp = Blueprint('admin', __name__,url_prefix='/admin')

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return "Access Denied: Admins Only", 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_students = Student.query.count()
    total_jobs = Job.query.count()
    total_applications = Application.query.count()

    return render_template(
        'admin/dashboard.html',
        total_students=total_students,
        total_jobs=total_jobs,
        total_applications=total_applications,
        
    )



#----------jobs management------

@admin_bp.route('/jobs/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_job():
    from admin.forms import JobForm
    from models import Category
    form = JobForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    if form.validate_on_submit():
        new_job = Job(
            title=form.title.data,
            company=form.company.data,
            location=form.location.data,
            category_id=form.category_id.data,
            tags=form.tags.data,
            description=form.description.data,
            job_type=form.job_type.data,                # NEW
            experience_level=form.experience_level.data, # NEW
            min_salary=form.min_salary.data 
        )
        db.session.add(new_job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('admin.jobs'))
    return render_template('admin/create_job.html', form=form)


@admin_bp.route('/jobs')
@login_required
@admin_required
def jobs():
    jobs = Job.query.order_by(Job.posted_on.desc()).all()
    return render_template('admin/job_list.html', jobs=jobs)

@admin_bp.route('/jobs/edit/<int:job_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_job(job_id):
    from admin.forms import JobForm
    from models import Category
    job = Job.query.get_or_404(job_id)
    form = JobForm(obj=job)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        job.title = form.title.data
        job.company = form.company.data
        job.location = form.location.data
        job.category_id = form.category_id.data
        job.tags = form.tags.data
        job.description = form.description.data
        db.session.commit()
        flash("Job updated successfully!", "info")
        return redirect(url_for('admin.jobs'))

    return render_template('admin/edit_job.html', form=form)

@admin_bp.route('/jobs/delete/<int:job_id>')
@login_required
@admin_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash("Job deleted!", "danger")
    return redirect(url_for('admin.jobs'))

#---------APPLICANTS MANAGEMENT---------
@admin_bp.route('/applicants/<int:job_id>')
@login_required
@admin_required
def view_applicants(job_id):
    job = Job.query.get_or_404(job_id)
    applicants = job.applications  # list of Application objects
    return render_template('admin/view_applicants.html', job=job, applicants=applicants)

@admin_bp.route('/applicants/download/<int:job_id>')
@login_required
@admin_required
def download_applicants(job_id):
    from openpyxl import Workbook
    from flask import send_file
    import os
    from io import BytesIO

    job = Job.query.get_or_404(job_id)
    applications = job.applications

    wb = Workbook()
    ws = wb.active
    ws.title = "Applicants"
    ws.append(["Student Name", "Email", "Resume", "Status", "Applied On"])

    for app in applications:
        student = app.student
        user = student.user
        ws.append([
            student.name,
            user.email,
            student.resume,
            app.status,
            app.applied_on.strftime("%Y-%m-%d %H:%M")
        ])

    # Save to memory (not to disk)
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        download_name=f"applicants_job_{job_id}.xlsx",
        as_attachment=True
    )

@admin_bp.route('/applications')
@login_required
@admin_required
def all_applications():
    applications = Application.query.order_by(Application.applied_on.desc()).all()
    return render_template('admin/all_applications.html', applications=applications)

@admin_bp.route('/applications/update/<int:application_id>', methods=['POST'])
@login_required
@admin_required
def update_application_status(application_id):
    application = Application.query.get_or_404(application_id)
    new_status = request.form.get("status")
    if new_status:
        application.status = new_status
        db.session.commit()
        flash("Application status updated.", "success")
    return redirect(request.referrer or url_for('admin.all_applications'))



@admin_bp.route('/students/<int:student_id>')
@login_required
@admin_required
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    applications = student.applied_jobs
    return render_template('admin/student_details.html', student=student, applications=applications)

@admin_bp.route('/search')
@login_required
@admin_required
def search():
    query = request.args.get('q', '')
    jobs = Job.query.filter(Job.title.ilike(f"%{query}%")).all()
    students = Student.query.filter(Student.name.ilike(f"%{query}%")).all()
    return render_template('admin/search_results.html', jobs=jobs, students=students, query=query)

#----------CATEGORIES MANAGEMENT---------
@admin_bp.route('/categories')
@login_required
@admin_required
def manage_categories():
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories)

# View all categories


# Add category
@admin_bp.route('/categories/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    name = request.form.get('name')
    if name:
        existing = Category.query.filter_by(name=name).first()
        if existing:
            flash('Category already exists.', 'warning')
        else:
            db.session.add(Category(name=name))
            db.session.commit()
            flash('Category added.', 'success')
    return redirect(url_for('admin.manage_categories'))

# Edit category
@admin_bp.route('/categories/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    new_name = request.form.get('name')
    if new_name:
        category.name = new_name
        db.session.commit()
        flash('Category updated.', 'success')
    return redirect(url_for('admin.manage_categories'))


@admin_bp.route('/categories/delete/<int:id>')
@login_required
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted.', 'info')
    return redirect(url_for('admin.manage_categories'))


@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    job_count = Job.query.count()
    application_count = Application.query.count()
    student_count = Student.query.count()
    
    # Fetch all categories to display individual charts
    categories = Category.query.all()
    
    # You can add chart data here
    return render_template('admin/analytics.html', job_count=job_count,
                            application_count=application_count,
                            student_count=student_count,
                            categories=categories)

@admin_bp.route('/students/<int:student_id>/resume')
@login_required
@admin_required
def download_resume(student_id):
    student = Student.query.get_or_404(student_id)
    return send_file(student.resume, as_attachment=True)

@admin_bp.route('/applicants/download/all')# all jobs combined
@login_required
@admin_required
def download_all_applicants():
    from openpyxl import Workbook
    from io import BytesIO
    from flask import send_file

    wb = Workbook()
    ws = wb.active
    ws.title = "All Applicants"
    ws.append(["Job Title", "Student Name", "Email", "Resume", "Status", "Applied On"])

    applications = Application.query.order_by(Application.applied_on.desc()).all()

    for app in applications:
        student = app.student
        user = student.user
        ws.append([
            app.job.title,
            student.name,
            user.email,
            student.resume,
            app.status,
            app.applied_on.strftime("%Y-%m-%d %H:%M")
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(output, download_name="all_applicants.xlsx", as_attachment=True)


@admin_bp.route('/students')
@login_required
@admin_required
def view_students():
    students = Student.query.all()
    return render_template('admin/students.html', students=students)

@admin_bp.route('/resume/view/<int:student_id>')
@login_required
@admin_required
def view_resume(student_id):
    student = Student.query.get_or_404(student_id)
    print("Student ID:", student_id)
    print("Resume path in DB:", student.resume)

    if not student.resume:
        flash("This student has not uploaded a resume.", "warning")
        return redirect(url_for('admin.view_students'))

    resume_folder = os.path.join(current_app.root_path, 'static', 'resumes')
    resume_filename = os.path.basename(student.resume)
    resume_path = os.path.join(resume_folder, resume_filename)

    print("Full resume path:", resume_path)

    if not os.path.exists(resume_path):
        flash("Resume file not found on server.", "danger")
        return redirect(url_for('admin.view_students'))

    return send_from_directory(directory=resume_folder, path=resume_filename, as_attachment=False)
