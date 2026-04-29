def test_register_success(client) -> None:
    response = client.post(
        "/auth/register",
        json={"email": "john@example.com", "password": "Password123!"},
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["email"] == "john@example.com"
    assert "id" in data


def test_register_duplicate_email_returns_conflict(client) -> None:
    payload = {"email": "john@example.com", "password": "Password123!"}
    first = client.post("/auth/register", json=payload)
    second = client.post("/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
