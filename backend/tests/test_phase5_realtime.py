"""
Phase 5 (Day 31-35): SocketIO tests using Flask-SocketIO test client.
"""
import pytest
from app import create_app, socketio


@pytest.fixture(scope="module")
def app():
    application = create_app("testing")
    return application


@pytest.fixture(scope="module")
def socket_client(app):
    with app.app_context():
        client = socketio.test_client(app)
        yield client
        client.disconnect()


def test_connect_and_server_ack(socket_client):
    """Socket connects and receives server_ack event."""
    assert socket_client.is_connected()
    received = socket_client.get_received()
    ack_events = [e for e in received if e["name"] == "server_ack"]
    assert ack_events, "Expected server_ack on connect"
    assert "Connected to CareWatch" in ack_events[0]["args"][0]["message"]


def test_join_patient_room(socket_client):
    """join_patient_room responds with room_joined."""
    socket_client.emit("join_patient_room", {"patient_id": 1})
    received = socket_client.get_received()
    events = [e for e in received if e["name"] == "room_joined"]
    assert events, "Expected room_joined event"
    assert events[0]["args"][0]["patient_id"] == 1


def test_leave_patient_room(socket_client):
    """leave_patient_room responds with room_left."""
    socket_client.emit("leave_patient_room", {"patient_id": 1})
    received = socket_client.get_received()
    events = [e for e in received if e["name"] == "room_left"]
    assert events, "Expected room_left event"
    assert events[0]["args"][0]["patient_id"] == 1


def test_ping_server(socket_client):
    """ping_server echoes back pong_server."""
    socket_client.emit("ping_server", {"test": "hello"})
    received = socket_client.get_received()
    pongs = [e for e in received if e["name"] == "pong_server"]
    assert pongs, "Expected pong_server event"
    assert pongs[0]["args"][0]["echo"]["test"] == "hello"


def test_join_room_missing_patient_id(socket_client):
    """join_patient_room without patient_id returns error."""
    socket_client.emit("join_patient_room", {})
    received = socket_client.get_received()
    errors = [e for e in received if e["name"] == "error"]
    assert errors, "Expected error when patient_id missing"


def test_stop_stream_no_crash(socket_client):
    """stop_live_stream for non-running stream doesn't crash."""
    socket_client.emit("stop_live_stream", {"patient_id": 999})
    # No exception means success; stream_status may or may not be emitted
    socket_client.get_received()  # drain


def test_reconnect_ack(socket_client):
    """reconnect_ack for a patient returns reconnect_confirmed."""
    socket_client.emit("reconnect_ack", {"patient_id": 1})
    received = socket_client.get_received()
    confirmed = [e for e in received if e["name"] == "reconnect_confirmed"]
    assert confirmed, "Expected reconnect_confirmed event"
    assert confirmed[0]["args"][0]["patient_id"] == 1
