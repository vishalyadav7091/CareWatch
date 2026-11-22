from app.routes.auth import auth_bp
from app.routes.patients import patients_bp
from app.routes.beds import beds_bp
from app.routes.vitals import vitals_bp
from app.routes.alerts import alerts_bp
from app.routes.devices import devices_bp
from app.routes.acquisition import acquisition_bp
from app.routes.ml import ml_bp
from app.routes.audit import audit_bp

__all__ = [
    "auth_bp",
    "patients_bp",
    "beds_bp",
    "vitals_bp",
    "alerts_bp",
    "devices_bp",
    "acquisition_bp",
    "ml_bp",
    "audit_bp",
]
