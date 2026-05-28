"""
Regression tests for the ch03 companion catalog service.

These map 1:1 to the four smoke tests of Listing 3.15, plus a few extra
assertions that lock in the patterns described in sections 3.3 through 3.6.

Run against a live service:
    BASE_URL=http://localhost:8080 pytest -v
"""
import os
import httpx
import pytest


BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080")


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as c:
        yield c


# --- Pattern 1 & 3: complete spec, served at /openapi.json ------------------
def test_openapi_document_served(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert spec["openapi"].startswith("3.1")
    assert spec["info"]["title"] == "Catalog Service"
    assert set(spec["paths"].keys()) == {
        "/catalog/products/{product_id}",
        "/catalog/search",
    }


def test_search_endpoint_is_marked_confidence_aware(client):
    """Pattern 6 / semantic-contract synthesis: the x-confidence-aware
    extension and x-fallback-strategy must be present on /catalog/search."""
    spec = client.get("/openapi.json").json()
    search = spec["paths"]["/catalog/search"]["get"]
    assert search.get("x-confidence-aware") is True
    assert search.get("x-fallback-strategy") == "keyword_ilike"
    assert search.get("x-side-effects") == "none"


def test_descriptions_present_on_every_endpoint(client):
    """Pattern 2: every endpoint carries a natural-language description."""
    spec = client.get("/openapi.json").json()
    for path, methods in spec["paths"].items():
        for method, op in methods.items():
            assert op.get("description"), f"{method.upper()} {path} has no description"
            assert op.get("operationId"), f"{method.upper()} {path} has no operationId"


# --- Pattern 4 & 6: deterministic shape with a decision block ---------------
def test_search_returns_decision_block(client):
    r = client.get("/catalog/search", params={"q": "jacket"})
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"results", "decision"}

    decision = body["decision"]
    assert decision["strategy"] == "keyword_ilike"
    assert decision["confidence"] is None              # explicit null, not omitted
    assert decision["fallback_used"] is True
    assert decision["fallback_strategy"] == "keyword_ilike"


def test_search_results_carry_explicit_null_match_score(client):
    """Pattern 4: every field appears every time; absent values are null."""
    r = client.get("/catalog/search", params={"q": "jacket"})
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) >= 1
    for item in results:
        # match_score must be present as a field, even when its value is null
        assert "match_score" in item
        assert item["match_score"] is None


def test_search_returns_empty_results_with_decision_block(client):
    """The envelope is invariant: empty results still carry the decision."""
    r = client.get("/catalog/search", params={"q": "nonexistent-xyz-no-match"})
    assert r.status_code == 200
    body = r.json()
    assert body["results"] == []
    assert body["decision"]["fallback_used"] is True


# --- Pattern 5: structured error envelope, framework-validation path --------
def test_empty_query_returns_structured_validation_error(client):
    r = client.get("/catalog/search", params={"q": ""})
    assert r.status_code == 422
    err = r.json()
    assert err["error_code"] == "VALIDATION_FAILED"
    assert err["type"] == "validation_error"
    assert err["field"] == "q"
    assert err["retryable"] is False


def test_too_long_query_returns_structured_validation_error(client):
    r = client.get("/catalog/search", params={"q": "x" * 201})
    assert r.status_code == 422
    err = r.json()
    assert err["type"] == "validation_error"
    assert err["field"] == "q"


def test_out_of_range_limit_returns_structured_validation_error(client):
    r = client.get("/catalog/search", params={"q": "x", "limit": 999})
    assert r.status_code == 422
    err = r.json()
    assert err["type"] == "validation_error"
    assert err["field"] == "limit"


# --- Pattern 5: structured error envelope, application-level path -----------
def test_missing_product_returns_structured_404(client):
    r = client.get("/catalog/products/p_999")
    assert r.status_code == 404
    err = r.json()
    assert err["error_code"] == "PRODUCT_NOT_FOUND"
    assert err["type"] == "validation_error"
    assert err["field"] == "product_id"
    assert err["retryable"] is False


def test_malformed_product_id_returns_structured_error(client):
    r = client.get("/catalog/products/not-a-valid-id")
    assert r.status_code == 422
    err = r.json()
    assert err["error_code"] == "INVALID_PRODUCT_ID"
    assert err["type"] == "validation_error"
    assert err["field"] == "product_id"
    assert err["hint"] is not None  # the hint helps an agent correct the call


def test_existing_product_returns_canonical_shape(client):
    r = client.get("/catalog/products/p_001")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"id", "name", "price_cents", "description"}
    assert body["id"] == "p_001"
    assert isinstance(body["price_cents"], int)
