from datetime import date, timedelta


def _get_access_token(client) -> str:
    register_payload = {"email": "jane@example.com", "password": "Password123!"}
    client.post("/auth/register", json=register_payload)
    login = client.post("/auth/login", json=register_payload)
    return login.get_json()["access_token"]


def test_task_invalid_transition_returns_conflict(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "My task",
            "description": "Details",
            "due_date": (date.today() + timedelta(days=2)).isoformat(),
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.get_json()["id"]

    invalid_update = client.put(
        f"/tasks/{task_id}",
        headers=headers,
        json={"status": "complete"},
    )

    assert invalid_update.status_code == 409
