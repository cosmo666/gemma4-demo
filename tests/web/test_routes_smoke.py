import pytest
from fastapi.testclient import TestClient

from app.web.server import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/dashboards",
        "/review",
        "/documents",
        "/chat",
        "/config",
    ],
)
def test_route_returns_200_and_html(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Expense Lens" in r.text


def test_static_css_tokens_served(client):
    r = client.get("/static/css/tokens.css")
    assert r.status_code == 200
    assert "--color-primary" in r.text
