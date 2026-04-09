"""
Integration tests for Experiments 2–4.
Run while the FastAPI server is up on http://127.0.0.1:8000
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "mlops-demo-key-2024"

DIVIDER = "=" * 60


def test_health():
    print(f"\n{DIVIDER}")
    print("TEST: GET /health")
    print(DIVIDER)
    r = requests.get(f"{BASE_URL}/health")
    print(f"Status: {r.status_code}")
    print(f"Body  : {json.dumps(r.json(), indent=2)}")
    assert r.status_code == 200
    assert r.json()["model_loaded"] is True
    print("✅ PASSED")


def test_predict_no_auth():
    print(f"\n{DIVIDER}")
    print("TEST: POST /predict WITHOUT auth (expect 401)")
    print(DIVIDER)
    r = requests.post(
        f"{BASE_URL}/predict",
        json={"hours": 5, "attendance": 70, "previous_score": 60},
    )
    print(f"Status: {r.status_code}")
    print(f"Body  : {json.dumps(r.json(), indent=2)}")
    assert r.status_code == 401
    print("✅ PASSED — unauthenticated request correctly rejected")


def test_predict_api_key():
    print(f"\n{DIVIDER}")
    print("TEST: POST /predict with API Key")
    print(DIVIDER)
    r = requests.post(
        f"{BASE_URL}/predict",
        json={"hours": 5, "attendance": 70, "previous_score": 60},
        headers={"X-API-Key": API_KEY},
    )
    print(f"Status: {r.status_code}")
    print(f"Body  : {json.dumps(r.json(), indent=2)}")
    assert r.status_code == 200
    assert "predicted_final_score" in r.json()
    print("✅ PASSED — prediction returned with API Key auth")


def test_predict_jwt():
    print(f"\n{DIVIDER}")
    print("TEST: POST /predict with JWT")
    print(DIVIDER)
    # 1. Get a token
    token_resp = requests.post(f"{BASE_URL}/token?username=test_user")
    token = token_resp.json()["access_token"]
    print(f"JWT token: {token[:40]}...")

    # 2. Use the token
    r = requests.post(
        f"{BASE_URL}/predict",
        json={"hours": 8, "attendance": 90, "previous_score": 80},
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"Status: {r.status_code}")
    print(f"Body  : {json.dumps(r.json(), indent=2)}")
    assert r.status_code == 200
    assert "predicted_final_score" in r.json()
    print("✅ PASSED — prediction returned with JWT auth")


def test_predict_invalid_api_key():
    print(f"\n{DIVIDER}")
    print("TEST: POST /predict with INVALID API Key (expect 401)")
    print(DIVIDER)
    r = requests.post(
        f"{BASE_URL}/predict",
        json={"hours": 5, "attendance": 70, "previous_score": 60},
        headers={"X-API-Key": "wrong-key"},
    )
    print(f"Status: {r.status_code}")
    print(f"Body  : {json.dumps(r.json(), indent=2)}")
    assert r.status_code == 401
    print("✅ PASSED — invalid key correctly rejected")


def test_predict_validation_error():
    print(f"\n{DIVIDER}")
    print("TEST: POST /predict with INVALID data (expect 422)")
    print(DIVIDER)
    r = requests.post(
        f"{BASE_URL}/predict",
        json={"hours": -5, "attendance": 200, "previous_score": 60},
        headers={"X-API-Key": API_KEY},
    )
    print(f"Status: {r.status_code}")
    print(f"Body  : {json.dumps(r.json(), indent=2)}")
    assert r.status_code == 422
    print("✅ PASSED — validation error correctly returned")


def test_request_id_header():
    print(f"\n{DIVIDER}")
    print("TEST: X-Request-ID header present in response")
    print(DIVIDER)
    r = requests.get(f"{BASE_URL}/health")
    request_id = r.headers.get("X-Request-ID")
    print(f"X-Request-ID: {request_id}")
    assert request_id is not None and len(request_id) == 12
    print("✅ PASSED — request ID is present and correctly formatted")


if __name__ == "__main__":
    test_health()
    test_predict_no_auth()
    test_predict_api_key()
    test_predict_jwt()
    test_predict_invalid_api_key()
    test_predict_validation_error()
    test_request_id_header()
    print(f"\n{'🎉' * 3}  ALL TESTS PASSED  {'🎉' * 3}\n")
