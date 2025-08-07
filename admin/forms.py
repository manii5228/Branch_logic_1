from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField,SelectField
from wtforms.validators import DataRequired

class JobForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired()])
    company = StringField('Company Name', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    category_id = StringField("Category",  validators=[DataRequired()])
    tags = StringField('Tags')          # Optional
    description = TextAreaField('Job Description', validators=[DataRequired()])
    submit = SubmitField('Post Job')
