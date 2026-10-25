def test_get_user_404(client):
    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_signup_route_no_longer_exists(client):
    # Accounts now come from Supabase sign-in, not from a signup request.
    response = client.post("/users", json={"name": "Amit", "email": "a@x.com"})
    assert response.status_code == 404
