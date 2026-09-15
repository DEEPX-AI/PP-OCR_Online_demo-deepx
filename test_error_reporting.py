#!/usr/bin/env python3
"""What the demo shows when the OCR server refuses a request.

The backend answers an impossible request with a 503 and a sentence that
says exactly what to do - "Device 'npu' is not available on this deployment.
Available: cpu. Run ./run.sh --sanity-check to see why." The demo used to
throw that sentence away (`raise RuntimeError("API request failed")` drops
`e.response`) and pop a toast reading "Error processing file: API request
failed", which tells the user nothing.

Raising also left the results area untouched: gradio's `.then()` runs whether
or not the previous step succeeded, so `results_state` kept its old value and
the UI either stayed blank or, worse, went on showing the previous file's
results next to an error toast.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def app():
    spec = importlib.util.spec_from_file_location("demoapp", HERE / "app.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["demoapp"] = m
    spec.loader.exec_module(m)
    return m


class FakeResponse:
    """Enough of requests.Response for the error path."""

    def __init__(self, status_code, body, reason="Service Unavailable"):
        self.status_code = status_code
        self.reason = reason
        self.text = body if isinstance(body, str) else json.dumps(body)

    def json(self):
        return json.loads(self.text)

    def raise_for_status(self):
        import requests
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(
                f"{self.status_code} Server Error", response=self)


NPU_MISSING = {"detail": "Device 'npu' is not available on this deployment. "
                         "Available: cpu. Run ./run.sh --sanity-check to see why."}


def visible_of(x):
    """gradio hands back either a component or an update dict."""
    if isinstance(x, dict):
        return x.get("visible")
    return getattr(x, "visible", None)


def value_of(x):
    if isinstance(x, dict):
        return x.get("value", "")
    return getattr(x, "value", "")


# ------------------------------------------------ reading the server's reply ---

def test_fastapi_detail_becomes_the_message(app):
    err = app.describe_api_failure(response=FakeResponse(503, NPU_MISSING))
    assert err["status"] == 503
    assert "Device 'npu' is not available" in err["message"]
    assert "--sanity-check" in err["message"]


def test_a_non_json_body_is_still_reported(app):
    err = app.describe_api_failure(response=FakeResponse(502, "<html>bad gateway</html>"))
    assert err["status"] == 502
    assert "bad gateway" in err["message"]


def test_an_empty_body_falls_back_to_the_status_line(app):
    err = app.describe_api_failure(response=FakeResponse(500, "", reason="Internal Server Error"))
    assert err["status"] == 500
    assert err["message"].strip()


def test_no_response_at_all_reports_the_exception(app):
    """The server is not running: requests raises before any response exists."""
    import requests
    err = app.describe_api_failure(
        exc=requests.exceptions.ConnectionError("Connection refused"), response=None)
    assert err["status"] is None
    assert "Connection refused" in err["message"]
    assert err["hint"]           # tell them to start the server


# ------------------------------------------------------ process_file behaviour ---

def test_process_file_returns_the_error_instead_of_raising(app, monkeypatch, tmp_path):
    img = tmp_path / "x.png"
    img.write_bytes(b"not really a png")
    monkeypatch.setattr(app.requests, "post",
                        lambda *a, **k: FakeResponse(503, NPU_MISSING))

    out = app.process_file(None, str(img), True, False, False, False,
                           "min", 736, 0.3, 0.6, 1.5, 0.0, True)

    assert out is not None, "returning None leaves the previous run's results on screen"
    assert out["error"]["status"] == 503
    assert "Device 'npu' is not available" in out["error"]["message"]


def test_a_successful_call_carries_no_error(app, monkeypatch, tmp_path):
    img = tmp_path / "x.png"
    img.write_bytes(b"not really a png")
    ok = {"result": {"ocrResults": [], "performanceMetrics": {"backend": "CPU"}}}
    monkeypatch.setattr(app.requests, "post", lambda *a, **k: FakeResponse(200, ok, reason="OK"))

    out = app.process_file(None, str(img), False, False, False, False,
                           "min", 736, 0.3, 0.6, 1.5, 0.0, True)
    assert out.get("error") is None


# ----------------------------------------------------------- what the UI shows ---

def test_the_results_area_opens_for_an_error(app):
    """Otherwise the only channel is a toast that vanishes."""
    _, tabs = app.hide_spinner({"error": {"status": 503, "message": "nope", "hint": None}})
    assert visible_of(tabs) is True


def test_update_display_renders_the_message_and_clears_stale_images(app):
    err = {"error": {"status": 503, "message": "Device 'npu' is not available", "hint": "h"}}
    out = app.update_display(err)

    rendered = " ".join(str(value_of(o)) for o in out)
    assert "Device 'npu' is not available" in rendered, "the reason must reach the screen"
    assert "503" in rendered

    images = out[:app.MAX_NUM_PAGES]
    assert all(visible_of(i) is False for i in images), \
        "a failed run must not leave the previous run's pages visible"


def test_update_display_still_renders_a_normal_result(app):
    ok = {"overall_ocr_res_images": [], "output_json": {"ocrResults": []},
          "input_images": [], "performance_metrics": None}
    out = app.update_display(ok)
    assert len(out) == app.MAX_NUM_PAGES + 1 + len(app.gallery_list) + 2
