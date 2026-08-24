import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_ticket():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        password = "pass123"
        admin_email = f"ticket_admin_{uuid.uuid4().hex[:8]}@mail.com"
        user_email = f"ticket_user_{uuid.uuid4().hex[:8]}@mail.com"

        await ac.post("/auth/register", json={
            "name": "Ticket Admin",
            "email": admin_email,
            "password": password,
            "role": "ADMIN",
        })
        admin_login = await ac.post("/auth/login", data={
            "username": admin_email,
            "password": password,
        })
        assert admin_login.status_code == 200
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        user_res = await ac.post("/auth/register", json={
            "name": "Test User1",
            "email": user_email,
            "password": password,
            "role": "USER",
        })
        assert user_res.status_code == 201
        user_id = user_res.json()["user_id"]

        user_login = await ac.post("/auth/login", data={
            "username": user_email,
            "password": password,
        })
        assert user_login.status_code == 200
        user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}

        ticket_data = {
            "title": "Projector",
            "description": "Projector in Room 302 is not displaying",
            "category": "Hardware",
            "priority": "LOW",
        }
        response = await ac.post("/tickets/create-ticket/", headers=user_headers, json=ticket_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == ticket_data["title"]
        assert data["description"] == ticket_data["description"]
        assert data["user_id"] == user_id
        assert data["status"] == "OPEN"

        update_response = await ac.put(
            f"/tickets/{data['id']}",
            headers=admin_headers,
            json={"status": "CLOSED", "response": "The projector has been fixed"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "CLOSED"

        response = await ac.get(f"/tickets/{data['id']}", headers=user_headers)
        assert response.status_code == 200
        response = await ac.get("/tickets/", headers=user_headers)
        assert response.status_code == 200

        response = await ac.delete(f"/tickets/{data['id']}", headers=admin_headers)
        assert response.status_code == 200
        response = await ac.delete(f"/users/{user_id}", headers=admin_headers)
        assert response.status_code == 200
