# tests/test_mqtt_client.py
import json
import pytest
from app.mqtt_client import on_connect, on_message


class DummyClient:
    def __init__(self):
        self.subscriptions = []

    def subscribe(self, topic):
        self.subscriptions.append(topic)


def dummy_process_message(topic, data):
    assert topic == "iot/sensors/test"
    assert data == {"temp": 25}


@pytest.fixture(autouse=True)
def patch_process_message(monkeypatch):
    monkeypatch.setattr("app.mqtt_client.process_message", dummy_process_message)


def test_on_connect():
    client = DummyClient()
    on_connect(client, None, None, 0)
    assert "iot/sensors/#" in client.subscriptions


def test_on_message():
    # Create a dummy message object.
    class DummyMsg:
        topic = "iot/sensors/test"
        payload = json.dumps({"temp": 25}).encode("utf-8")

    msg = DummyMsg()
    on_message(None, None, msg)
