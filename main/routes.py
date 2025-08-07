from flask import Blueprint, render_template
from models import Job
main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def home():
    recent_jobs = Job.query.order_by(Job.posted_on.desc()).limit(6).all()
    return render_template("index.html", recent_jobs=recent_jobs)

@main_bp.route("/blog")
def blog():
    return render_template("blog.html")

@main_bp.route("/job")
def job():
    return render_template("job.html")