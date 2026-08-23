from fastapi.testclient import TestClient
from services.api.app import main
from services.api.app.main import app

client = TestClient(app)


def test_requires_intent_text():
    response = client.post("/intent/interpret", json={"intent": "   "})
    assert response.status_code == 422


def test_returns_interpreted_categories(monkeypatch):
    def fake_interpret(intent, supported_categories):
        assert "family" in intent
        assert "school" in supported_categories
        return {"summary": "Family-friendly everyday life", "categories": ["school", "park"]}

    monkeypatch.setattr(main, "interpret_map_intent", fake_interpret)

    response = client.post("/intent/interpret", json={"intent": "Great for a family with kids."})
    assert response.status_code == 200
    assert response.json() == {"summary": "Family-friendly everyday life", "categories": ["school", "park"]}
