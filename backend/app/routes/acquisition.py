from flask import Blueprint, jsonify, request
from app.services.simulator import PatientTelemetrySimulator
from app.services.device_adapter import IntelliVueDeviceAdapter
from app.services.ingestion_pipeline import IngestionPipeline

acquisition_bp = Blueprint("acquisition", __name__, url_prefix="/api/v1/acquisition")


@acquisition_bp.route("/simulate/<int:patient_id>", methods=["POST"])
def simulate_telemetry(patient_id):
    """Simulate a telemetry frame for a patient with a selected clinical scenario.
    
    Supported scenarios: stable, arrhythmia_tachycardia, desaturation_hypoxia, septic_shock
    """
    scenario = request.args.get("scenario", "stable")
    raw_reading = PatientTelemetrySimulator.generate_reading(
        patient_id=patient_id,
        scenario=scenario,
    )
    success, msg, data = IngestionPipeline.ingest_reading(raw_reading)
    if not success:
        return jsonify({"success": False, "error": msg}), 400

    return jsonify({
        "success": True,
        "message": f"Telemetry simulated for scenario: {scenario}",
        "scenario": scenario,
        "data": data,
    }), 201


@acquisition_bp.route("/adapter/intellivue", methods=["POST"])
def ingest_intellivue_stream():
    """Ingest raw device telemetry stream via Philips IntelliVue Adapter."""
    raw_payload = request.get_json()
    if not raw_payload:
        return jsonify({"success": False, "error": "JSON body required"}), 400

    adapter = IntelliVueDeviceAdapter()
    try:
        parsed = adapter.parse_payload(raw_payload)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    success, msg, data = IngestionPipeline.ingest_reading(parsed)
    if not success:
        return jsonify({"success": False, "error": msg}), 400

    return jsonify({
        "success": True,
        "message": "IntelliVue device packet parsed and ingested",
        "data": data,
    }), 201

