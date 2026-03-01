"""Tests for WebSocket endpoint."""

from starlette.testclient import TestClient

from foundrai.api import deps
from foundrai.api.app import create_app
from foundrai.config import FoundrAIConfig, PersistenceConfig, ServerConfig


def test_ws_connection(tmp_path):
    """Test WebSocket connection and handshake."""
    db_path = str(tmp_path / "ws_test.db")
    config = FoundrAIConfig(
        persistence=PersistenceConfig(sqlite_path=db_path),
        server=ServerConfig(cors_origins=["*"]),
    )
    deps._db = None
    deps._config = None

    app = create_app(config)
    client = TestClient(app)

    with client.websocket_connect("/ws/sprints/test-sprint") as ws:
        data = ws.receive_json()
        assert data["type"] == "connection.established"
        assert data["data"]["sprint_id"] == "test-sprint"
        assert data["sequence"] == 0

    # Cleanup
    deps._db = None
    deps._config = None


def test_ws_ping_pong(tmp_path):
    """Test WebSocket ping/pong."""
    db_path = str(tmp_path / "ws_test2.db")
    config = FoundrAIConfig(
        persistence=PersistenceConfig(sqlite_path=db_path),
        server=ServerConfig(cors_origins=["*"]),
    )
    deps._db = None
    deps._config = None

    app = create_app(config)
    client = TestClient(app)

    with client.websocket_connect("/ws/sprints/test-sprint") as ws:
        ws.receive_json()  # consume handshake
        ws.send_text("ping")
        resp = ws.receive_text()
        assert resp == "pong"

    deps._db = None
    deps._config = None
