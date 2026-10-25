def test_get_user_by_id_no_longer_exists(client, make_user):
    user = make_user()
    # The id exists, but there is no longer a route that looks users up by id.
    assert client.get(f"/users/{user.id}").status_code == 404


def test_signup_route_no_longer_exists(client):
    # Accounts now come from Supabase sign-in, not from a signup request.
    response = client.post("/users", json={"name": "Amit", "email": "a@x.com"})
    assert response.status_code == 404
