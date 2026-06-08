from __future__ import annotations


def test_login_success(client):
    """
    Verify admin login succeeds and returns JWT token.
    """

    response = client.post(
        "/admin/api/v1/login",
        json={
            "username": "admin",
            "password": "test@2025",  # adjust if different in .env
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client):
    """
    Wrong password should return 401.
    """

    response = client.post(
        "/admin/api/v1/login",
        json={
            "username": "admin",
            "password": "wrong_password",
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert "detail" in data


def test_login_unknown_user(client):
    """
    Non-existent user should return 401.
    """

    response = client.post(
        "/admin/api/v1/login",
        json={
            "username": "unknown_user",
            "password": "password",
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid credentials"


def test_login_empty_username(client):
    """
    Pydantic validation should fail.
    """

    response = client.post(
        "/admin/api/v1/login",
        json={
            "username": "",
            "password": "admin123",
        },
    )

    assert response.status_code in (400, 422)


def test_login_empty_password(client):
    """
    Pydantic validation should fail.
    """

    response = client.post(
        "/admin/api/v1/login",
        json={
            "username": "admin",
            "password": "",
        },
    )

    assert response.status_code in (400, 422)
