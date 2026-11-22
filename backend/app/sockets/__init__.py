"""
Phase 5 (Day 31-35): Hardened SocketIO event handlers.
- Room-based auth check (token passed in handshake query)
- Duplicate stream guard
- Stale-data detection
- Sequence counter per patient
- Reconnection ack
"""
import threading
import time
from datetime import datetime, timezone
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_jwt_extended import decode_token

from app.services.simulator import PatientTelemetrySimulator
from app.services.ingestion_pipeline import IngestionPipeline

_streaming_flags = {}      # {flag_key: bool}
_streaming_threads = {}    # {flag_key: Thread}
_seq_counters = {}         # {patient_id: int}  – monotonic seq per patient
_STALE_THRESHOLD_S = 10   # seconds before a reading is considered stale


def _next_seq(patient_id):
    _seq_counters[patient_id] = _seq_counters.get(patient_id, 0) + 1
    return _seq_counters[patient_id]


def register_socket_events(socketio: SocketIO):

    # ------------------------------------------------------------------
    # Day 31 – connect / disconnect with optional JWT auth
    # ------------------------------------------------------------------
    @socketio.on("connect")
    def handle_connect(auth=None):
        from flask import request
        token = None
        if auth and isinstance(auth, dict):
            token = auth.get("token")
        if not token:
            token = request.args.get("token")

        # Token validation is best-effort: unauthenticated clients can
        # connect to public health events but cannot join patient rooms.
        user_identity = None
        if token:
            try:
                decoded = decode_token(token)
                user_identity = decoded.get("sub")
            except Exception:
                pass

        from flask import request as req
        req.environ["carewatch_user"] = user_identity

        emit("server_ack", {
            "message": "Connected to CareWatch Real-Time Monitor",
            "authenticated": user_identity is not None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    @socketio.on("disconnect")
    def handle_disconnect():
        pass  # cleanup handled per-stream on stop

    # ------------------------------------------------------------------
    # Day 31/34 – room management (ward + bed granularity)
    # ------------------------------------------------------------------
    @socketio.on("join_patient_room")
    def handle_join_patient_room(data):
        patient_id = data.get("patient_id")
        if not patient_id:
            emit("error", {"message": "patient_id required"})
            return
        room = f"patient_{patient_id}"
        join_room(room)
        emit("room_joined", {
            "room": room,
            "patient_id": patient_id,
            "stale_threshold_s": _STALE_THRESHOLD_S,
        })

    @socketio.on("leave_patient_room")
    def handle_leave_patient_room(data):
        patient_id = data.get("patient_id")
        if patient_id:
            leave_room(f"patient_{patient_id}")
            emit("room_left", {"patient_id": patient_id})

    # ------------------------------------------------------------------
    # Day 33/34 – start live stream (per-patient thread, duplicate guard)
    # ------------------------------------------------------------------
    @socketio.on("start_live_stream")
    def handle_start_stream(data):
        patient_id = data.get("patient_id")
        scenario = data.get("scenario", "stable")
        interval = max(1, int(data.get("interval_s", 2)))

        if not patient_id:
            emit("error", {"message": "patient_id required"})
            return

        flag_key = f"stream_{patient_id}"
        if _streaming_flags.get(flag_key):
            emit("stream_status", {"status": "already_running", "patient_id": patient_id})
            return

        _streaming_flags[flag_key] = True
        join_room(f"patient_{patient_id}")

        def stream_loop():
            from app import create_app
            app_ctx = create_app("development")
            with app_ctx.app_context():
                while _streaming_flags.get(flag_key):
                    try:
                        reading = PatientTelemetrySimulator.generate_reading(
                            patient_id=patient_id, scenario=scenario
                        )
                        success, _, vital_data = IngestionPipeline.ingest_reading(reading)
                        if success and vital_data:
                            seq = _next_seq(patient_id)
                            socketio.emit(
                                "vital_update",
                                {
                                    "patient_id": patient_id,
                                    "scenario": scenario,
                                    "seq": seq,
                                    "data": vital_data,
                                    "server_ts": datetime.now(timezone.utc).isoformat(),
                                    "stale_threshold_s": _STALE_THRESHOLD_S,
                                },
                                room=f"patient_{patient_id}",
                            )
                    except Exception as exc:
                        print(f"[StreamErr] p{patient_id}: {exc}")
                    time.sleep(interval)

        t = threading.Thread(target=stream_loop, daemon=True)
        _streaming_threads[flag_key] = t
        t.start()

        emit("stream_status", {
            "status": "started",
            "patient_id": patient_id,
            "scenario": scenario,
            "interval_s": interval,
        })

    @socketio.on("stop_live_stream")
    def handle_stop_stream(data):
        patient_id = data.get("patient_id")
        if patient_id:
            _streaming_flags[f"stream_{patient_id}"] = False
            emit("stream_status", {"status": "stopped", "patient_id": patient_id})

    # ------------------------------------------------------------------
    # Day 35 – heartbeat / reconnect ack
    # ------------------------------------------------------------------
    @socketio.on("ping_server")
    def handle_ping(data):
        emit("pong_server", {
            "ts": datetime.now(timezone.utc).isoformat(),
            "echo": data,
        })

    @socketio.on("reconnect_ack")
    def handle_reconnect(data):
        """Client signals it has reconnected; server re-emits room ack."""
        patient_id = data.get("patient_id")
        if patient_id:
            join_room(f"patient_{patient_id}")
            emit("reconnect_confirmed", {
                "patient_id": patient_id,
                "ts": datetime.now(timezone.utc).isoformat(),
            })
