import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import create_app, socketio

env_name = os.getenv("FLASK_ENV", "development")
app = create_app(env_name)

# Ensure database tables and demo seed exist on deployment
with app.app_context():
    try:
        from app import db
        db.create_all()
        from seed_data import seed_demo_data
        seed_demo_data(env_name)
        print("[Startup] Database tables and demo staff successfully verified!")
    except Exception as e:
        print("[Startup] Note during auto-seed:", e)

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    print(f"Starting CareWatch backend with SocketIO on http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug, use_reloader=False, allow_unsafe_werkzeug=True)
