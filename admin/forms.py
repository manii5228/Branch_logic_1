from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField,SelectField,IntegerField
from wtforms.validators import DataRequired

class JobForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired()])
    company = StringField('Company Name', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    category_id = SelectField("Category",  choices=[], coerce=int, validators=[DataRequired()])
    tags = StringField('Tags')          # Optional
    description = TextAreaField('Job Description', validators=[DataRequired()])
    submit = SubmitField('Post Job')
    job_type = SelectField("Job Type", choices=[
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Contract', 'Contract'),
        ('Internship', 'Internship')
    ])
    experience_level = SelectField("Experience Level", choices=[
        ('Entry Level', 'Entry Level'),
        ('Mid Level', 'Mid Level'),
        ('Senior Level', 'Senior Level'),
        ('Executive', 'Executive')
    ])
    min_salary = IntegerField("Minimum Salary")
    max_salary = IntegerField("Maximum Salary")