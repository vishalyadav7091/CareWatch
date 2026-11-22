from flask import Blueprint, jsonify, request
from app.models import MedicalDevice, DeviceAssignment, Bed
from app import db

devices_bp = Blueprint("devices", __name__, url_prefix="/api/v1/devices")


@devices_bp.route("", methods=["GET"])
def get_devices():
    """Retrieve all ICU bedside devices."""
    devices = MedicalDevice.query.all()
    results = []
    for d in devices:
        d_dict = d.to_dict()
        # Find active assigned bed
        active_assignment = next((a for a in d.assignments if a.unassigned_at is None), None)
        if active_assignment:
            d_dict["assigned_bed"] = {
                "bed_id": active_assignment.bed.id,
                "bed_number": active_assignment.bed.bed_number,
                "assigned_at": active_assignment.assigned_at.isoformat(),
            }
        else:
            d_dict["assigned_bed"] = None
        results.append(d_dict)

    return jsonify({
        "success": True,
        "count": len(results),
        "data": results,
    }), 200


@devices_bp.route("", methods=["POST"])
def register_device():
    """Register a new ICU bedside device."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Request body must be JSON"}), 400

    device_code = data.get("device_code")
    if not device_code:
        return jsonify({"success": False, "error": "device_code is required"}), 400

    if MedicalDevice.query.filter_by(device_code=device_code).first():
        return jsonify({"success": False, "error": "device_code already exists"}), 409

    device = MedicalDevice(
        device_code=device_code,
        manufacturer=data.get("manufacturer"),
        model=data.get("model"),
        device_type=data.get("device_type", "Bedside Multi-Parameter Monitor"),
        connection_status=data.get("connection_status", "connected"),
    )
    db.session.add(device)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Device registered successfully",
        "data": device.to_dict(),
    }), 201


@devices_bp.route("/<int:device_id>/status", methods=["PATCH"])
def update_device_status(device_id):
    """Update device connection heartbeat/status."""
    device = db.session.get(MedicalDevice, device_id)
    if not device:
        return jsonify({"success": False, "error": "Device not found"}), 404

    data = request.get_json()
    new_status = data.get("connection_status")
    if new_status not in ["connected", "disconnected", "unknown"]:
        return jsonify({
            "success": False,
            "error": "Invalid connection_status. Must be connected, disconnected, or unknown",
        }), 400

    device.connection_status = new_status
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Device {device.device_code} status updated to {new_status}",
        "data": device.to_dict(),
    }), 200

