import pytest
from uuid import uuid4


async def test_update_user(client, create_user_in_database, get_user_from_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Test",
        "surname": "Testov",
        "email": "qwe@example.com",
        "is_active": True
    }
    user_data_updated = {
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivan@example.com",
    }
    
    await create_user_in_database(**user_data)
    resp = await client.patch(f"/user/?user_id={user_data['user_id']}", json=user_data_updated)
    assert resp.status_code == 200
    resp_data = resp.json()

    assert resp_data["updated_user_id"] == str(user_data["user_id"])
    user_from_db = await get_user_from_database(user_data["user_id"])

    assert user_from_db["name"] == user_data_updated["name"]
    assert user_from_db["surname"] == user_data_updated["surname"]
    assert user_from_db["email"] == user_data_updated["email"]
    assert user_from_db["is_active"] is True


@pytest.mark.parametrize(
    ["user_data_updated", "expected_status_code", "expected_detail"],
    [
        (
            {},
            422,
            {"detail": "At least one parameter for user update info should be provided"}
        ),
        (
            {"name": "123"},
            422,
            {"detail": "Name should contains only letters"}
        ),
        (
            {"email": ""},
            422,
            {"detail": [
                {
                    "type": "value_error",
                    "loc": [
                        "body",
                        "email"
                    ],
                    "msg": "value is not a valid email address: An email address must have an @-sign.",
                    "input": "",
                    "ctx": {
                        "reason": "An email address must have an @-sign."
                    }
                }
            ]}
        ),
        (
            {"surname": ""},
            422,
            {"detail": [{
                "type": "string_too_short",
                "loc": [
                    "body",
                    "surname"
                ],
                "msg": "String should have at least 1 character",
                "input": "",
                "ctx": {
                    "min_length": 1
                }
            }]}
        ),
        (
            {"name": ""},
            422,
            {"detail": [{
                "type": "string_too_short",
                "loc": [
                    "body",
                    "name"
                ],
                "msg": "String should have at least 1 character",
                "input": "",
                "ctx": {
                    "min_length": 1
                }
            }]}
        ),
        (
            {"surname": "123"},
            422,
            {"detail": "Surname should contains only letters"}
        ),
        (
            {"email": "123"},
            422,
            {"detail": [{
                "type": "value_error",
                "loc": [
                    "body",
                    "email"
                ],
                "msg": "value is not a valid email address: An email address must have an @-sign.",
                "input": "123",
                "ctx": {
                    "reason": "An email address must have an @-sign."
                }
            }]}
        )
    ]
)

async def test_update_user_validation_error(client, create_user_in_database, get_user_from_database, user_data_updated,
                                            expected_status_code, expected_detail):
    user_data = {
        "user_id": uuid4(),
        "name": "Test",
        "surname": "Testov",
        "email": "test@example.com",
        "is_active": True
    }
    await create_user_in_database(**user_data)
    resp = await client.patch(f"/user/?user_id={user_data['user_id']}", json=user_data_updated)
    assert resp.status_code == expected_status_code
    resp_data = resp.json()
    assert resp_data == expected_detail