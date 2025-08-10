from flask import Blueprint, render_template, redirect, url_for
from models import Job, Application, Student, Category

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def home():
    # Fetch data to be displayed on the homepage
    job_count = Job.query.count()
    student_count = Student.query.count()
    application_count = Application.query.count()

    return render_template("index.html", 
                           job_count=job_count,
                           student_count=student_count,
                           application_count=application_count)
@main_bp.route("/blog")
def blog():
    return render_template("blog.html")

@main_bp.route("/job")
def job():
    return render_template("job.html")
