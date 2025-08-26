async def test_create_user(client, get_user_from_database):
    user_data = {
        "name": "Test",
        "surname": "Testov",
        "email": "qwe@example.com"
    }
    
    resp = await client.post("/user/", json=user_data)
    data_from_resp = resp.json()

    assert resp.status_code == 200
    assert data_from_resp["name"] == user_data["name"]
    assert data_from_resp["surname"] == user_data["surname"]
    assert data_from_resp["email"] == user_data["email"]

    users_from_db = await get_user_from_database(data_from_resp["user_id"])

    assert str(users_from_db["user_id"]) == data_from_resp["user_id"]
    assert users_from_db["name"] == user_data["name"]
    assert users_from_db["surname"] == user_data["surname"]
    assert users_from_db["email"] == user_data["email"]
    assert users_from_db["is_active"] is True
