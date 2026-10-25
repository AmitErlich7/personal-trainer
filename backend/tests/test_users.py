import pytest


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


def make_user(client):
    return client.post("/users", json={"name": "Amit", "email": "a@x.com"}).json()["id"]


def test_set_max_hr(client):
    user_id = make_user(client)
    response = client.patch(f"/users/{user_id}", json={"max_hr": 190})
    assert response.status_code == 200
    assert response.json()["max_hr"] == 190
    # Also check what was saved, not only what the update answered.
    assert client.get(f"/users/{user_id}").json()["max_hr"] == 190


def test_max_hr_can_be_cleared_with_null(client):
    user_id = make_user(client)
    client.patch(f"/users/{user_id}", json={"max_hr": 190})
    response = client.patch(f"/users/{user_id}", json={"max_hr": None})
    assert response.status_code == 200
    assert response.json()["max_hr"] is None


@pytest.mark.parametrize("bad_value", [99, 251, "fast"])
def test_max_hr_out_of_range_rejected(client, bad_value):
    user_id = make_user(client)
    response = client.patch(f"/users/{user_id}", json={"max_hr": bad_value})
    assert response.status_code == 422
    assert client.get(f"/users/{user_id}").json()["max_hr"] is None


def test_update_rejects_other_fields(client):
    user_id = make_user(client)
    response = client.patch(f"/users/{user_id}", json={"max_hr": 190, "is_admin": True})
    assert response.status_code == 422
    assert client.get(f"/users/{user_id}").json()["max_hr"] is None


def test_update_without_max_hr_rejected(client):
    user_id = make_user(client)
    assert client.patch(f"/users/{user_id}", json={}).status_code == 422


def test_update_unknown_user_404(client):
    response = client.patch("/users/999", json={"max_hr": 190})
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
