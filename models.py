from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student' or 'admin'
    student = db.relationship('Student', backref='user', uselist=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    resume = db.Column(db.String(150)) 
    
    # 🔽 Additional details
    github_id = db.Column(db.String(100))
    linkedin_id = db.Column(db.String(100))
    cgpa = db.Column(db.Float)
    experience = db.Column(db.Text)
    portfolio = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(250))  # New address field
    
    applied_jobs = db.relationship('Application', backref='student', lazy=True)
    
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    job_type = db.Column(db.String(50))  # e.g., Full-time, Part-time
    experience_level = db.Column(db.String(50))  # Entry, Mid, Senior

    # 🔽 Salary fields added
    min_salary = db.Column(db.Integer, nullable=True)
    max_salary = db.Column(db.Integer, nullable=True)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    tags = db.Column(db.String(100))  # Optional: "Python,Remote,Internship"
    posted_on = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship('Category', backref='jobs')
    applications = db.relationship('Application', backref='job', cascade="all, delete-orphan", lazy=True)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'rejected'
