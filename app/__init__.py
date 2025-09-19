from pathlib import Path

from flask import Flask
from flask_socketio import SocketIO


socketio = SocketIO(cors_allowed_origins="*")


def create_app():
    """Application factory.

    Keeps template/static folders at repo root for compatibility.
    """
    base_dir = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(base_dir / "static"),
    )

    # Secret key
    from .config import SECRET_KEY

    app.config["SECRET_KEY"] = SECRET_KEY

    # Initialize SocketIO extension
    socketio.init_app(app)

    # Register blueprints
    from .routes.api import api_bp

    app.register_blueprint(api_bp)

    # Basic routes
    @app.route("/")
    def index():
        from flask import render_template

        return render_template("index.html")

    return app
