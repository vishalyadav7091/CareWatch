from datetime import datetime, timezone
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from sqlalchemy import text
from config import config_by_name

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO()


def create_app(config_name="development"):
    """Application factory for CareWatch Flask backend."""
    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, "development"))

    # Initialize extensions
    cors_origins = app.config.get("CORS_ORIGINS", "*")
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="threading",
        logger=False,
        engineio_logger=False,
    )

    # Register HTTP blueprints
    from app.routes import (
        auth_bp, patients_bp, beds_bp, vitals_bp,
        alerts_bp, devices_bp, acquisition_bp, ml_bp, audit_bp,
    )
    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(beds_bp)
    app.register_blueprint(vitals_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(acquisition_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(audit_bp)

    # Register SocketIO event handlers
    from app.sockets import register_socket_events
    register_socket_events(socketio)

    # Health routes
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "CareWatch Backend",
            "version": "1.0.0",
            "realtime": "flask-socketio",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }), 200

    @app.route("/api/health/db", methods=["GET"])
    def db_health_check():
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()
            db_dialect = db.engine.dialect.name
            return jsonify({
                "status": "healthy",
                "database_connection": "connected",
                "database_engine": db_dialect,
                "table_count": len(table_names),
                "tables": table_names,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }), 200
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "database_connection": "disconnected",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }), 503

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"success": False, "error": "Internal server error"}), 500

    return app
