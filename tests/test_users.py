import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


## Testing creation of users
@pytest.mark.asyncio
async def test_users():
    #Test for user creation
    async with AsyncClient(
            transport=ASGITransport(app=app), 
            base_url="http://testserver"
        ) as ac:
        response = await ac.post("/users/create-user/", json={"name": "Test User2", "email": "T2User@mail.com", "password": "password123"})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "Test User2"
        assert '@' in data["email"]

        #Test for user updation
        update_response = await ac.put(f"/users/{data['id']}", json={"name": "Updated User2", "email": "UpdatedT2User@mail.com", "password": "updatedpassword123"})
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["name"] == "Updated User2"

        #Test for user retrieval
        get_response = await ac.get(f"/users/{data['id']}")
        assert get_response.status_code == 200
        get_response = await ac.get(f"/users/")
        assert get_response.status_code == 200

        #Test for user deletion
        delete_response = await ac.delete(f"/users/{data['id']}")
        assert delete_response.status_code == 200
