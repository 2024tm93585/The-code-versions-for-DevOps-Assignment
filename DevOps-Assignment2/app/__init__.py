from flask import Flask
from .models import init_db


def create_app(config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'aceest-secret-key-2024'
    app.config['DATABASE'] = 'aceest_fitness.db'
    app.config['TESTING'] = False

    if config:
        app.config.update(config)

    with app.app_context():
        init_db(app)

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
