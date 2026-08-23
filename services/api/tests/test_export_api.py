from fastapi.testclient import TestClient

from services.api.app.main import app

client = TestClient(app)


def _create_exportable_project():
    created = client.post("/projects", json={"name": "Export Story", "rawIntent": "Show nearby schools"}).json()
    project_id = created["id"]
    saved = client.put(
        f"/projects/{project_id}",
        json={
            "name": "Export Story",
            "rawIntent": "Show nearby schools",
            "points": [
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "label": "Subject",
                    "category": "subject",
                    "symbol": "subject",
                    "longitude": -96.8,
                    "latitude": 32.8,
                    "coordinateSource": "geocoder",
                    "providerPlaceId": "abc123",
                },
                {
                    "id": "22222222-2222-2222-2222-222222222222",
                    "label": "School",
                    "category": "school",
                    "symbol": "school",
                    "longitude": -96.75,
                    "latitude": 32.82,
                    "coordinateSource": "map_click",
                },
            ],
        },
    ).json()
    return project_id, saved["version"]


def test_export_returns_png_image():
    project_id, version = _create_exportable_project()
    response = client.post(
        f"/projects/{project_id}/export",
        json={
            "projectId": project_id,
            "projectVersion": version,
            "format": "png",
            "width": 800,
            "height": 600,
        },
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_export_rejects_stale_version():
    project_id, version = _create_exportable_project()
    response = client.post(
        f"/projects/{project_id}/export",
        json={
            "projectId": project_id,
            "projectVersion": version - 1,
            "format": "jpeg",
        },
    )
    assert response.status_code == 409


def test_export_rejects_project_id_mismatch():
    project_id, version = _create_exportable_project()
    response = client.post(
        f"/projects/{project_id}/export",
        json={
            "projectId": "00000000-0000-0000-0000-000000000000",
            "projectVersion": version,
            "format": "jpeg",
        },
    )
    assert response.status_code == 409
