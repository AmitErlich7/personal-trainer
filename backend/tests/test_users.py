def test_create_user_returns_201_and_id(client):
    response = client.post("/users", json={"name": "Amit", "email": "a@x.com"})
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["max_hr"] is None


def test_get_user_404(client):
    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_duplicate_email_rejected(client):
    client.post("/users", json={"name": "Amit", "email": "a@x.com"})
    response = client.post("/users", json={"name": "Other", "email": "a@x.com"})
    assert response.status_code == 409
