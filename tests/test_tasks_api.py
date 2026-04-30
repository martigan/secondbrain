from datetime import date, timedelta


def _get_access_token(client) -> str:
    register_payload = {"email": "api-user@example.com", "password": "Password123!"}
    client.post("/auth/register", json=register_payload)
    login_response = client.post("/auth/login", json=register_payload)
    return login_response.get_json()["access_token"]


def test_create_task_success(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Write tests",
            "description": "Add more REST API tests",
            "due_date": (date.today() + timedelta(days=3)).isoformat(),
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == "Write tests"
    assert data["status"] == "new"


def test_update_task_success(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Initial title",
            "description": "Initial description",
            "due_date": (date.today() + timedelta(days=4)).isoformat(),
        },
    )
    task_id = create_response.get_json()["id"]

    update_response = client.put(
        f"/tasks/{task_id}",
        headers=headers,
        json={"title": "Updated title", "status": "running"},
    )

    assert update_response.status_code == 200
    data = update_response.get_json()
    assert data["title"] == "Updated title"
    assert data["status"] == "running"


def test_create_task_with_past_due_date_returns_validation_error(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Invalid task",
            "description": "This should fail",
            "due_date": (date.today() - timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Validation error"


def test_update_task_with_invalid_uuid_returns_bad_request(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        "/tasks/not-a-valid-uuid",
        headers=headers,
        json={"title": "Should fail"},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Invalid task id"


def test_list_tasks_with_cursor_pagination_no_overlap(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    for index in range(5):
        create_response = client.post(
            "/tasks",
            headers=headers,
            json={
                "title": f"Task {index}",
                "description": "Pagination seed",
                "due_date": (date.today() + timedelta(days=10 + index)).isoformat(),
            },
        )
        assert create_response.status_code == 201

    page_1 = client.get("/tasks?limit=2", headers=headers)
    assert page_1.status_code == 200
    page_1_data = page_1.get_json()
    assert len(page_1_data["items"]) == 2
    assert page_1_data["page"]["has_next"] is True
    next_cursor = page_1_data["page"]["next_cursor"]
    assert isinstance(next_cursor, str)

    page_2 = client.get(f"/tasks?limit=2&cursor={next_cursor}", headers=headers)
    assert page_2.status_code == 200
    page_2_data = page_2.get_json()
    assert len(page_2_data["items"]) == 2

    first_page_ids = {item["id"] for item in page_1_data["items"]}
    second_page_ids = {item["id"] for item in page_2_data["items"]}
    assert first_page_ids.isdisjoint(second_page_ids)


def test_list_tasks_with_invalid_cursor_returns_bad_request(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/tasks?cursor=invalid-cursor-token", headers=headers)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Invalid cursor"


def test_list_tasks_with_invalid_limit_returns_validation_error(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    for invalid_limit in (0, -1, 101):
        response = client.get(f"/tasks?limit={invalid_limit}", headers=headers)
        assert response.status_code == 400
        assert response.get_json()["message"] == "Validation error"
