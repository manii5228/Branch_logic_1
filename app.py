from flask import Flask
from extensions import db, migrate, login_manager
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # Import models (required for migrations to recognize them)
    from models import User, Job, Application

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from main.routes import main_bp
    from auth.routes import auth_bp
    from student.routes import student_bp
    from admin.routes import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app

# Create the app instance
app = create_app()

# Optional: Only for running locally or for manual script use
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)