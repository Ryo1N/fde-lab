def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"

def test_list_job_boards(client):
    response = client.get("/api/job-boards")
    assert response.status_code == 200
    assert response.json() == []