import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_users():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        password = "password123"
        admin_email = f"admin_{uuid.uuid4().hex[:8]}@mail.com"
        user_email = f"user_{uuid.uuid4().hex[:8]}@mail.com"

        admin_registration = await ac.post("/auth/register", json={
            "name": "Test Admin",
            "email": admin_email,
            "password": password,
            "role": "ADMIN",
        })
        assert admin_registration.status_code == 201

        admin_login = await ac.post("/auth/login", data={
            "username": admin_email,
            "password": password,
        })
        assert admin_login.status_code == 200
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        response = await ac.post("/users/create-user/", headers=admin_headers, json={
            "name": "Test User2",
            "email": user_email,
            "password": password,
            "role": "USER",
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "Test User2"
        assert "@" in data["email"]

        user_login = await ac.post("/auth/login", data={
            "username": user_email,
            "password": password,
        })
        assert user_login.status_code == 200
        user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}

        update_response = await ac.put(f"/users/{data['id']}", headers=user_headers, json={
            "name": "Updated User2",
            "email": "UpdatedT2User@mail.com",
            "password": "updatedpassword123",
        })
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated User2"

        get_response = await ac.get(f"/users/{data['id']}", headers=user_headers)
        assert get_response.status_code == 200
        get_response = await ac.get("/users/", headers=admin_headers)
        assert get_response.status_code == 200

        delete_response = await ac.delete(f"/users/{data['id']}", headers=admin_headers)
        assert delete_response.status_code == 200
