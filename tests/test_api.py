"""
Automated tests for the Mini BI Assistant.
Run with: pytest tests/test_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Valid: Health check returns 200 and 48 rows."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["rows_in_db"] == 48

def test_valid_question_total_revenue():
    """Valid: Total revenue question."""
    resp = client.post("/ask", json={"question": "What is the total revenue?"})
    assert resp.status_code == 200
    assert resp.json()["intent"] == "total_revenue"
    assert "₹" in resp.json()["answer"]

def test_valid_question_top_product():
    """Valid: Top product question returns a supporting table."""
    resp = client.post("/ask", json={"question": "Which product generated the highest revenue?"})
    assert resp.status_code == 200
    assert resp.json()["intent"] == "top_product"
    assert len(resp.json()["supporting_table"]) > 0

def test_invalid_question_too_short():
    """Invalid: Empty question gets rejected by Pydantic (422)."""
    resp = client.post("/ask", json={"question": ""})
    assert resp.status_code == 422

def test_unsupported_question():
    """Unsupported: Unrelated question returns 400 with a helpful message."""
    resp = client.post("/ask", json={"question": "tell me a joke"})
    assert resp.status_code == 400
    assert "couldn't understand" in resp.json()["detail"]

def test_edge_case_month_comparison():
    """Edge Case: Comparison requires two months. Passing only one fails."""
    resp = client.post("/ask", json={"question": "Compare January"})
    assert resp.status_code == 400