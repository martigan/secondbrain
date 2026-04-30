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


def test_list_tasks_filter_status_eq_returns_expected_items(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    task = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Status eq target",
            "description": "Should become running",
            "due_date": (date.today() + timedelta(days=2)).isoformat(),
        },
    ).get_json()
    client.put(f"/tasks/{task['id']}", headers=headers, json={"status": "running"})

    response = client.get("/tasks?status_eq=running", headers=headers)

    assert response.status_code == 200
    items = response.get_json()["items"]
    assert items
    assert all(item["status"] == "running" for item in items)


def test_list_tasks_filter_status_in_returns_union(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    task = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Status in target",
            "description": "Will be running",
            "due_date": (date.today() + timedelta(days=3)).isoformat(),
        },
    ).get_json()
    client.put(f"/tasks/{task['id']}", headers=headers, json={"status": "running"})

    response = client.get("/tasks?status_in=new,running", headers=headers)

    assert response.status_code == 200
    statuses = {item["status"] for item in response.get_json()["items"]}
    assert statuses.issubset({"new", "running"})


def test_list_tasks_filter_due_date_range(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Within range",
            "description": "due date in range",
            "due_date": (date.today() + timedelta(days=6)).isoformat(),
        },
    )
    client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Out of range",
            "description": "due date out of range",
            "due_date": (date.today() + timedelta(days=20)).isoformat(),
        },
    )

    gte = (date.today() + timedelta(days=5)).isoformat()
    lte = (date.today() + timedelta(days=10)).isoformat()
    response = client.get(f"/tasks?due_date_gte={gte}&due_date_lte={lte}", headers=headers)

    assert response.status_code == 200
    titles = {item["title"] for item in response.get_json()["items"]}
    assert "Within range" in titles
    assert "Out of range" not in titles


def test_list_tasks_filter_title_contains_case_insensitive(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Quarterly REPORT",
            "description": "Case test",
            "due_date": (date.today() + timedelta(days=7)).isoformat(),
        },
    )

    response = client.get("/tasks?title_contains=report", headers=headers)

    assert response.status_code == 200
    titles = [item["title"] for item in response.get_json()["items"]]
    assert "Quarterly REPORT" in titles


def test_list_tasks_filter_created_at_range(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Created at target",
            "description": "created_at range",
            "due_date": (date.today() + timedelta(days=8)).isoformat(),
        },
    )

    response = client.get(
        "/tasks?created_at_gte=2000-01-01T00:00:00Z&created_at_lte=2100-01-01T00:00:00Z",
        headers=headers,
    )

    assert response.status_code == 200
    assert any(item["title"] == "Created at target" for item in response.get_json()["items"])


def test_list_tasks_filter_with_pagination_no_overlap(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    for index in range(5):
        created = client.post(
            "/tasks",
            headers=headers,
            json={
                "title": f"Filter page {index}",
                "description": "pagination + filter",
                "due_date": (date.today() + timedelta(days=30 + index)).isoformat(),
            },
        ).get_json()
        client.put(f"/tasks/{created['id']}", headers=headers, json={"status": "running"})

    first = client.get("/tasks?status_eq=running&limit=2", headers=headers).get_json()
    second = client.get(
        f"/tasks?status_eq=running&limit=2&cursor={first['page']['next_cursor']}",
        headers=headers,
    ).get_json()

    first_ids = {item["id"] for item in first["items"]}
    second_ids = {item["id"] for item in second["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_list_tasks_filter_cursor_mismatch_returns_bad_request(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    for index in range(3):
        created = client.post(
            "/tasks",
            headers=headers,
            json={
                "title": f"Cursor mismatch {index}",
                "description": "cursor mismatch",
                "due_date": (date.today() + timedelta(days=40 + index)).isoformat(),
            },
        ).get_json()
        client.put(f"/tasks/{created['id']}", headers=headers, json={"status": "running"})

    first_page = client.get("/tasks?status_eq=running&limit=2", headers=headers)
    assert first_page.status_code == 200
    cursor = first_page.get_json()["page"]["next_cursor"]

    mismatch_response = client.get(
        f"/tasks?status_eq=new&limit=2&cursor={cursor}",
        headers=headers,
    )

    assert mismatch_response.status_code == 400
    assert mismatch_response.get_json()["message"] == "Invalid cursor"


def test_list_tasks_filter_conflicting_status_filters_returns_validation_error(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/tasks?status_eq=new&status_in=new,running", headers=headers)

    assert response.status_code == 400
    assert response.get_json()["message"] == "Validation error"


def test_list_tasks_filter_invalid_ranges_return_validation_error(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response_due_date = client.get(
        "/tasks?due_date_gte=2026-06-01&due_date_lte=2026-05-01",
        headers=headers,
    )
    response_created_at = client.get(
        "/tasks?created_at_gte=2026-06-01T00:00:00Z&created_at_lte=2026-05-01T00:00:00Z",
        headers=headers,
    )

    assert response_due_date.status_code == 400
    assert response_created_at.status_code == 400


def test_list_tasks_filter_invalid_values_return_validation_error(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response_status = client.get("/tasks?status_eq=invalid-status", headers=headers)
    response_date = client.get("/tasks?due_date_gte=not-a-date", headers=headers)
    response_datetime = client.get("/tasks?created_at_gte=not-a-datetime", headers=headers)
    response_status_in = client.get("/tasks?status_in=new,invalid", headers=headers)

    assert response_status.status_code == 400
    assert response_date.status_code == 400
    assert response_datetime.status_code == 400
    assert response_status_in.status_code == 400


def test_list_tasks_sort_due_date_asc(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Later",
            "description": "sort test",
            "due_date": (date.today() + timedelta(days=15)).isoformat(),
        },
    )
    client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Sooner",
            "description": "sort test",
            "due_date": (date.today() + timedelta(days=5)).isoformat(),
        },
    )

    response = client.get("/tasks?sort=due_date:asc", headers=headers)

    assert response.status_code == 200
    items = response.get_json()["items"]
    assert len(items) >= 2
    assert items[0]["due_date"] <= items[1]["due_date"]


def test_list_tasks_sort_status_then_created_at(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    running = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Running task",
            "description": "sort test",
            "due_date": (date.today() + timedelta(days=6)).isoformat(),
        },
    ).get_json()
    new_task = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "New task",
            "description": "sort test",
            "due_date": (date.today() + timedelta(days=7)).isoformat(),
        },
    ).get_json()
    client.put(f"/tasks/{running['id']}", headers=headers, json={"status": "running"})

    response = client.get("/tasks?sort=status:asc,created_at:desc", headers=headers)

    assert response.status_code == 200
    statuses = [item["status"] for item in response.get_json()["items"]]
    assert statuses.index("new") < statuses.index("running")
    assert new_task["id"] in {item["id"] for item in response.get_json()["items"]}


def test_list_tasks_sort_with_pagination_no_overlap(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    for index in range(5):
        client.post(
            "/tasks",
            headers=headers,
            json={
                "title": f"Sorted page {index}",
                "description": "sort + pagination",
                "due_date": (date.today() + timedelta(days=10 + index)).isoformat(),
            },
        )

    page_1 = client.get("/tasks?sort=due_date:asc&limit=2", headers=headers)
    assert page_1.status_code == 200
    first_data = page_1.get_json()
    cursor = first_data["page"]["next_cursor"]
    page_2 = client.get(f"/tasks?sort=due_date:asc&limit=2&cursor={cursor}", headers=headers)
    assert page_2.status_code == 200
    second_data = page_2.get_json()

    first_ids = {item["id"] for item in first_data["items"]}
    second_ids = {item["id"] for item in second_data["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_list_tasks_invalid_sort_returns_validation_error(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    invalid_cases = [
        "/tasks?sort=bad",
        "/tasks?sort=title:asc",
        "/tasks?sort=due_date:up",
        "/tasks?sort=due_date:asc,due_date:desc",
    ]
    for path in invalid_cases:
        response = client.get(path, headers=headers)
        assert response.status_code == 400
        assert response.get_json()["message"] == "Validation error"


def test_list_tasks_cursor_sort_mismatch_returns_bad_request(client) -> None:
    token = _get_access_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    for index in range(3):
        client.post(
            "/tasks",
            headers=headers,
            json={
                "title": f"Sort mismatch {index}",
                "description": "cursor sort mismatch",
                "due_date": (date.today() + timedelta(days=20 + index)).isoformat(),
            },
        )

    first_page = client.get("/tasks?sort=due_date:asc&limit=2", headers=headers)
    assert first_page.status_code == 200
    cursor = first_page.get_json()["page"]["next_cursor"]

    mismatch = client.get(f"/tasks?sort=created_at:desc&limit=2&cursor={cursor}", headers=headers)
    assert mismatch.status_code == 400
    assert mismatch.get_json()["message"] == "Invalid cursor"
