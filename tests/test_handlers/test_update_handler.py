from uuid import uuid4

import pytest

from tests.conftest import create_test_auth_headers_for_user


async def test_update_user(client, create_user_in_database, get_user_from_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Test",
        "surname": "Testov",
        "email": "qwe@example.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
    }
    user_data_updated = {
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivan@example.com",
    }

    await create_user_in_database(**user_data)
    resp = await client.patch(
        f"/user/?user_id={user_data['user_id']}",
        json=user_data_updated,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
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
            {
                "detail": "At least one parameter for user update info should be provided"
            },
        ),
        (
            {"name": "123"},
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "name"],
                        "msg": "Value error, Name should contains only letters",
                        "input": "123",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {"email": ""},
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "",
                        "ctx": {"reason": "An email address must have an @-sign."},
                    }
                ]
            },
        ),
        (
            {"surname": ""},
            422,
            {
                "detail": [
                    {
                        "type": "string_too_short",
                        "loc": ["body", "surname"],
                        "msg": "String should have at least 1 character",
                        "input": "",
                        "ctx": {"min_length": 1},
                    }
                ]
            },
        ),
        (
            {"name": ""},
            422,
            {
                "detail": [
                    {
                        "type": "string_too_short",
                        "loc": ["body", "name"],
                        "msg": "String should have at least 1 character",
                        "input": "",
                        "ctx": {"min_length": 1},
                    }
                ]
            },
        ),
        (
            {"surname": "123"},
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "surname"],
                        "msg": "Value error, Surname should contains only letters",
                        "input": "123",
                        "ctx": {"error": {}},
                    }
                ]
            },
        ),
        (
            {"email": "123"},
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "123",
                        "ctx": {"reason": "An email address must have an @-sign."},
                    }
                ]
            },
        ),
    ],
)
async def test_update_user_validation_error(
    client,
    create_user_in_database,
    get_user_from_database,
    user_data_updated,
    expected_status_code,
    expected_detail,
):
    user_data = {
        "user_id": uuid4(),
        "name": "Test",
        "surname": "Testov",
        "email": "test@example.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
    }
    await create_user_in_database(**user_data)
    resp = await client.patch(
        f"/user/?user_id={user_data['user_id']}",
        json=user_data_updated,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert resp.status_code == expected_status_code
    resp_data = resp.json()
    assert resp_data == expected_detail


async def test_update_user_check_one_is_updated(
    client, create_user_in_database, get_user_from_database
):
    user_data_1 = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
    }
    user_data_2 = {
        "user_id": uuid4(),
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivan@kek.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
    }
    user_data_3 = {
        "user_id": uuid4(),
        "name": "Petr",
        "surname": "Petrov",
        "email": "petr@kek.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
    }
    user_data_updated = {
        "name": "Nikifor",
        "surname": "Nikiforov",
        "email": "cheburek@kek.com",
    }
    for user_data in [user_data_1, user_data_2, user_data_3]:
        await create_user_in_database(**user_data)
    resp = await client.patch(
        f"/user/?user_id={user_data_1['user_id']}",
        json=user_data_updated,
        headers=create_test_auth_headers_for_user(user_data_1["email"]),
    )
    assert resp.status_code == 200
    resp_data = resp.json()
    assert resp_data["updated_user_id"] == str(user_data_1["user_id"])
    user_from_db = await get_user_from_database(user_data_1["user_id"])
    assert user_from_db["name"] == user_data_updated["name"]
    assert user_from_db["surname"] == user_data_updated["surname"]
    assert user_from_db["email"] == user_data_updated["email"]
    assert user_from_db["is_active"] is user_data_1["is_active"]
    assert user_from_db["user_id"] == user_data_1["user_id"]

    user_from_db = await get_user_from_database(user_data_2["user_id"])
    assert user_from_db["name"] == user_data_2["name"]
    assert user_from_db["surname"] == user_data_2["surname"]
    assert user_from_db["email"] == user_data_2["email"]
    assert user_from_db["is_active"] is user_data_2["is_active"]
    assert user_from_db["user_id"] == user_data_2["user_id"]

    user_from_db = await get_user_from_database(user_data_3["user_id"])
    assert user_from_db["name"] == user_data_3["name"]
    assert user_from_db["surname"] == user_data_3["surname"]
    assert user_from_db["email"] == user_data_3["email"]
    assert user_from_db["is_active"] is user_data_3["is_active"]
    assert user_from_db["user_id"] == user_data_3["user_id"]


async def test_update_user_id_validation_error(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
    }
    await create_user_in_database(**user_data)
    user_data_updated = {
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "cheburek@kek.com",
    }
    resp = await client.patch(
        "/user/?user_id=123",
        json=user_data_updated,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert resp.status_code == 422
    data_from_response = resp.json()
    print(data_from_response)
    assert data_from_response == {
        "detail": [
            {
                "type": "uuid_parsing",
                "loc": ["query", "user_id"],
                "msg": "Input should be a valid UUID, invalid length: expected length 32 for simple format, found 3",
                "input": "123",
                "ctx": {
                    "error": "invalid length: expected length 32 for simple format, found 3"
                },
            }
        ]
    }


async def test_update_user_not_found_error(client, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
    }
    await create_user_in_database(**user_data)
    user_data_updated = {
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "cheburek@kek.com",
    }
    user_id = uuid4()
    resp = await client.patch(
        f"/user/?user_id={user_id}",
        json=user_data_updated,
        headers=create_test_auth_headers_for_user(user_data["email"]),
    )
    assert resp.status_code == 404
    resp_data = resp.json()
    assert resp_data == {"detail": f"User with id {user_id} not found."}


async def test_update_user_duplicate_email_error(client, create_user_in_database):
    user_data_1 = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
    }
    user_data_2 = {
        "user_id": uuid4(),
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivan@kek.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
    }
    user_data_updated = {
        "email": user_data_2["email"],
    }
    for user_data in [user_data_1, user_data_2]:
        await create_user_in_database(**user_data)
    resp = await client.patch(
        f"/user/?user_id={user_data_1['user_id']}",
        json=user_data_updated,
        headers=create_test_auth_headers_for_user(user_data_1["email"]),
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "User with this email already exists"
