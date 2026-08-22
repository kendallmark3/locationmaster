from fastapi.testclient import TestClient
from services.api.app.main import app

client = TestClient(app)

def test_save_and_reload_round_trip():
    created = client.post("/projects", json={"name": "Test Story", "rawIntent": "Tell the story"}).json()
    project_id = created["id"]

    point = {
        "id": "11111111-1111-1111-1111-111111111111",
        "label": "HQ",
        "category": "subject",
        "symbol": "subject",
        "longitude": -96.8,
        "latitude": 32.8,
        "coordinateSource": "geocoder",
        "providerPlaceId": "abc123",
    }
    saved = client.put(f"/projects/{project_id}", json={
        "name": "Test Story",
        "rawIntent": "Tell the story",
        "points": [point],
        "center": [-96.8, 32.8],
        "zoom": 12,
    }).json()

    assert saved["version"] == 2
    assert saved["center"] == [-96.8, 32.8]
    assert len(saved["points"]) == 1
    assert saved["points"][0]["label"] == "HQ"

    reloaded = client.get(f"/projects/{project_id}").json()
    assert reloaded == saved

def test_save_rejects_point_missing_coordinate_source():
    created = client.post("/projects", json={"name": "Test Story", "rawIntent": "Tell the story"}).json()
    project_id = created["id"]

    response = client.put(f"/projects/{project_id}", json={
        "name": "Test Story",
        "rawIntent": "Tell the story",
        "points": [{
            "id": "11111111-1111-1111-1111-111111111111",
            "label": "HQ",
            "category": "subject",
            "symbol": "subject",
            "longitude": -96.8,
            "latitude": 32.8,
        }],
    })
    assert response.status_code == 422
