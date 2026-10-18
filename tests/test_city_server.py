"""Actual city/session integration: journal recovery and local HTTP controls."""
import copy
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
import threading

import pytest

from kalends.city_server import CitySession, make_handler


def test_journal_recovery_reproduces_live_fork_and_timeline_specific_steps(tmp_path):
    path = tmp_path / "city.json"
    session = CitySession(path)
    session.apply("reset", {"seed": 42, "n_agents": 8, "n_ticks": 12})
    session.apply("step", {"count": 3, "timeline": "original"})
    session.apply("fork", {"kind": "correction", "agent": "Livia"})
    session.apply("step", {"count": 3, "timeline": "both"})
    session.apply("step", {"count": 1, "timeline": "branch"})
    expected = session.state()
    commands = copy.deepcopy(session.commands)
    recovered = CitySession(path)
    assert recovered.state() == expected
    assert recovered.commands == commands
    assert json.loads(path.read_text())["commands"] == commands
    assert not path.with_suffix(".tmp").exists()


def test_reset_replaces_command_history_and_discards_existing_branch(tmp_path):
    path = tmp_path / "city.json"
    session = CitySession(path)
    session.apply("step", {"count": 2})
    session.apply("fork", {"kind": "none"})
    session.apply("step", {"count": 1})
    state = session.apply("reset", {"seed": 17, "n_ticks": 8})
    assert state["branch"] is None
    assert state["comparison"] is None
    assert state["original"]["tick"] == -1
    assert len(session.commands) == 1
    assert session.commands[0]["operation"] == "reset"
    assert CitySession(path).state() == state


def test_recorded_commands_do_not_retain_caller_owned_mutable_data(tmp_path):
    path = tmp_path / "city.json"
    session = CitySession(path)
    request = {"count": 2, "timeline": "original"}
    session.apply("step", request)
    request["count"] = 9
    # A later write must not rewrite the meaning of an earlier command.
    session.apply("step", {"count": 1})
    assert session.commands[1]["data"]["count"] == 2
    assert CitySession(path).state() == session.state()


@pytest.mark.parametrize("operation, data", (
    ("step", {"count": 0}),
    ("step", {"count": -1}),
    ("step", {"count": True}),
    ("step", {"count": "2"}),
    ("step", {"count": 97}),
    ("step", {"timeline": "missing"}),
    ("step", {"timeline": "branch"}),
    ("reset", {"undocumented_option": 1}),
    ("fork", {"kind": "remove_message", "event_id": -1}),
    ("fork", {"kind": "correction", "agent": "Not an agent"}),
    ("launch", {}),
))
def test_rejected_commands_change_neither_world_nor_recovery_journal(tmp_path, operation, data):
    path = tmp_path / "city.json"
    session = CitySession(path)
    session.apply("step", {"count": 2})
    before_state = session.state()
    before_commands = copy.deepcopy(session.commands)
    before_disk = path.read_bytes()
    with pytest.raises(ValueError):
        session.apply(operation, data)
    assert session.state() == before_state
    assert session.commands == before_commands
    assert path.read_bytes() == before_disk


def test_unsupported_journal_version_is_rejected_without_rewriting_input(tmp_path):
    path = tmp_path / "city.json"
    source = '{"version": 9000, "commands": []}\n'
    path.write_text(source)
    with pytest.raises(ValueError, match="unsupported city journal version"):
        CitySession(path)
    assert path.read_text() == source


def test_concurrent_step_commands_are_serialized_to_the_same_actual_history():
    session = CitySession()
    session.apply("reset", {"n_ticks": 12, "seed": 42})
    failures = []

    def worker():
        try:
            for _ in range(2):
                session.apply("step", {"count": 1})
        except BaseException as exc:
            failures.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
        assert not thread.is_alive()
    expected = CitySession()
    expected.apply("reset", {"n_ticks": 12, "seed": 42})
    expected.apply("step", {"count": 6})
    assert not failures
    assert session.state() == expected.state()
    assert len(session.commands) == 7


@pytest.fixture
def live_http():
    session = CitySession()
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(session))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()

    def request(method, path, data=None, headers=None, raw=None):
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
        body = raw if raw is not None else json.dumps(data) if data is not None else None
        sent_headers = dict(headers or {})
        if body is not None:
            sent_headers.setdefault("Content-Type", "application/json")
        try:
            connection.request(method, path, body, sent_headers)
            response = connection.getresponse()
            payload = response.read()
            return response.status, json.loads(payload), dict(response.getheaders())
        finally:
            connection.close()

    yield session, request
    server.shutdown()
    server.server_close()
    worker.join(timeout=10)


def test_http_step_export_and_trace_use_the_same_live_simulation(live_http):
    session, request = live_http
    status, state, headers = request("GET", "/api/state")
    assert status == 200
    assert state == session.state()
    assert headers["Cache-Control"] == "no-store"
    assert headers["X-Content-Type-Options"] == "nosniff"
    status, advanced, _ = request("POST", "/api/step", {"count": 3})
    assert status == 200
    assert advanced["original"]["tick"] == 2
    assert advanced == session.state()
    status, export, _ = request("GET", "/api/export")
    assert status == 200
    assert export["state"] == advanced
    assert export["commands"] == session.commands
    event_id = advanced["original"]["events"][-1]["event_id"]
    status, trace, _ = request("GET", f"/api/trace?event_id={event_id}")
    assert status == 200
    assert trace == session.original.trace(event_id)


def test_http_fork_and_branch_step_leave_original_timeline_unchanged(live_http):
    session, request = live_http
    request("POST", "/api/step", {"count": 3})
    original = copy.deepcopy(session.state()["original"])
    status, forked, _ = request("POST", "/api/fork", {"kind": "none"})
    assert status == 200
    assert forked["comparison"]["identical"]
    status, advanced, _ = request("POST", "/api/step", {"count": 2, "timeline": "branch"})
    assert status == 200
    assert advanced["original"] == original
    assert advanced["branch"]["tick"] == original["tick"] + 2


@pytest.mark.parametrize("method, path, data, headers, raw, expected", (
    ("POST", "/api/step", {"count": 0}, None, None, 400),
    ("POST", "/api/step", None, None, "[]", 400),
    ("POST", "/api/step", None, None, "{", 400),
    ("POST", "/api/step", {"count": 1}, {"Origin": "https://other.example"}, None, 403),
    ("POST", "/api/unknown", {}, None, None, 404),
    ("GET", "/api/trace?timeline=branch&event_id=0", None, None, None, 400),
    ("GET", "/api/trace?event_id=not-a-number", None, None, None, 400),
    ("GET", "/../pyproject.toml", None, None, None, 404),
))
def test_http_rejections_do_not_mutate_live_history(live_http, method, path, data, headers, raw, expected):
    session, request = live_http
    before = session.state()
    commands = copy.deepcopy(session.commands)
    status, error, _ = request(method, path, data, headers, raw)
    assert status == expected
    assert "error" in error
    assert session.state() == before
    assert session.commands == commands
