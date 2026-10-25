def test_create_user_returns_201_and_id(client):
    response = client.post("/users", json={"name": "Amit", "email": "a@x.com"})
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["max_hr"] is None


def test_signup_rejects_max_hr(client):
    response = client.post(
        "/users", json={"name": "Amit", "email": "a@x.com", "max_hr": 190}
    )
    assert response.status_code == 422


def test_signup_rejects_is_admin(client):
    response = client.post(
        "/users", json={"name": "Amit", "email": "a@x.com", "is_admin": True}
    )
    assert response.status_code == 422


def test_rejected_signup_creates_no_user(client):
    client.post("/users", json={"name": "Amit", "email": "a@x.com", "is_admin": True})
    # The same email works afterwards, so nothing was saved the first time.
    response = client.post("/users", json={"name": "Amit", "email": "a@x.com"})
    assert response.status_code == 201
    assert response.json()["is_admin"] is False


def test_get_user_404(client):
    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_duplicate_email_rejected(client):
    client.post("/users", json={"name": "Amit", "email": "a@x.com"})
    response = client.post("/users", json={"name": "Other", "email": "a@x.com"})
    assert response.status_code == 409


def test_signup_still_works_after_duplicate_email_rejected(client):
    client.post("/users", json={"name": "Amit", "email": "a@x.com"})
    client.post("/users", json={"name": "Other", "email": "a@x.com"})
    response = client.post("/users", json={"name": "Dana", "email": "d@x.com"})
    assert response.status_code == 201


def test_blank_name_rejected(client):
    response = client.post("/users", json={"name": "   ", "email": "a@x.com"})
    assert response.status_code == 422


def test_invalid_email_rejected(client):
    response = client.post("/users", json={"name": "Amit", "email": "not-an-email"})
    assert response.status_code == 422


def test_email_is_trimmed_and_lowercased(client):
    response = client.post("/users", json={"name": " Amit ", "email": " A@X.com "})
    assert response.status_code == 201
    assert response.json()["email"] == "a@x.com"
    assert response.json()["name"] == "Amit"


def test_duplicate_email_ignores_case(client):
    client.post("/users", json={"name": "Amit", "email": "a@x.com"})
    response = client.post("/users", json={"name": "Other", "email": "A@X.COM"})
    assert response.status_code == 409
