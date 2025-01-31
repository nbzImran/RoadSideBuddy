from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional,  NumberRange

class SignupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    phone = StringField('Phone', validators=[Optional()])

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])

class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[Optional(), Length(min=1)])
    email = StringField('Email', validators=[Optional(), Email()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])


class ServiceForm(FlaskForm):
    """form for creating or updatin a service."""

    service_id = StringField(
        "Service ID",
        validators=[DataRequired(message="Service Id is required.")]
    )
    service_type = StringField(
        "service Type",
        validators=[DataRequired(message="Service Type is required."),
                    Length(max=100, message="Type cannot exceed 100 characters.")]
    )
    price = DecimalField(
        "price ($)",
        validators=[DataRequired(message="price is required"),
                    NumberRange(min=0, message="price Must be greacter than zero")]
    )
    description = TextAreaField(
        "Descrition",
        validators=[DataRequired(message="description is required"),
                    Length(max=50)]
    )

    submit = SubmitField("Submit")

class EmailForm(FlaskForm):
    recipient = StringField(
        'Recipient Email', 
        validators=[
            DataRequired(), 
            Email(message="Enter a valid email address")
        ]
    )
    subject = StringField(
        'Subject', 
        validators=[
            DataRequired(), 
            Length(max=100, message="Subject must be less than 100 characters")
        ]
    )
    message = TextAreaField(
        'Message', 
        validators=[
            DataRequired(), 
            Length(max=1000, message="Message must be less than 1000 characters")
        ]
    )
    submit = SubmitField('Send Email')