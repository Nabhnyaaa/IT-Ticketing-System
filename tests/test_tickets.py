import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import uuid

#Testing creation of tickets
@pytest.mark.asyncio
async def test__ticket():
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://testserver"
    ) as ac:
        # Create a user first with unique email
        user_res = await ac.post("/users/create-user/", json={"name": "Test User1", "email": f"ticket_user_{uuid.uuid4().hex[:6]}@gmail.com", "password": "pass123"})
        user_id = user_res.json()["id"]
        ticket_data = {
            "title": "Projector",
            "description": "Projector in Room 302 is not displaying",
            "user_id": user_id,
        }
        #Test for ticket creation
        response = await ac.post("/tickets/create-ticket/", json=ticket_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == ticket_data["title"]
        assert data["description"] == ticket_data["description"]
        assert data["user_id"] == ticket_data["user_id"]
        assert data["status"] == "OPEN"

        #Test for ticket updation
        update_data = {
            "status": "CLOSED",
            "response": "The projector has been fixed on 17/8/2026"
        }
        response = await ac.put(f"/tickets/{data['id']}", json=update_data)
        assert response.status_code == 200
        assert response.json()["status"] == update_data["status"]

        #Test for ticket retrieval
        response = await ac.get(f"/tickets/{data['id']}")
        assert response.status_code == 200
        response = await ac.get("/tickets/")
        assert response.status_code == 200

        #Test for ticket deletion
        response = await ac.delete(f"/tickets/{data['id']}")
        assert response.status_code == 200
        await ac.delete(f"/users/{data['user_id']}")
