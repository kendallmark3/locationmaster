from fastapi.testclient import TestClient
from services.api.app import main
from services.api.app.main import app

client = TestClient(app)


def _create_project_with_point():
    created = client.post("/projects", json={"name": "Test Story", "rawIntent": "Sell the site"}).json()
    project_id = created["id"]
    client.put(f"/projects/{project_id}", json={
        "name": "Test Story",
        "rawIntent": "Sell the site",
        "points": [{
            "id": "11111111-1111-1111-1111-111111111111",
            "label": "Downtown Golf Club",
            "category": "golf",
            "symbol": "golf",
            "longitude": -96.8,
            "latitude": 32.8,
            "coordinateSource": "geocoder",
            "providerPlaceId": "abc123",
        }],
    })
    return project_id


def test_narrative_requires_a_visible_point():
    created = client.post("/projects", json={"name": "Empty Story", "rawIntent": "Sell the site"}).json()
    response = client.post(f"/projects/{created['id']}/narrative")
    assert response.status_code == 422


def test_narrative_returns_generated_text(monkeypatch):
    project_id = _create_project_with_point()

    captured = {}

    def fake_generate(raw_intent, points):
        captured["raw_intent"] = raw_intent
        captured["points"] = points
        return "Move here for the golf."

    monkeypatch.setattr(main, "generate_relocation_narrative", fake_generate)

    response = client.post(f"/projects/{project_id}/narrative")
    assert response.status_code == 200
    assert response.json() == {"narrative": "Move here for the golf."}
    assert captured["raw_intent"] == "Sell the site"
    assert captured["points"][0]["label"] == "Downtown Golf Club"
