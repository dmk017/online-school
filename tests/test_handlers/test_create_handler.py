import pytest


async def test_create_user(client, get_user_from_database):
    user_data = {
        "name": "Test",
        "surname": "Testov",
        "email": "qwe@example.com",
        "password": "SamplePass1!",
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


async def test_create_user_duplicate_email_error(client, get_user_from_database):
    user_data = {
        "name": "Test",
        "surname": "Testov",
        "email": "test@example.com",
        "password": "SamplePass1!",
    }
    user_data_same_email = {
        "name": "Petr",
        "surname": "Petrov",
        "email": "test@example.com",
        "password": "SamplePass1!",
    }
    resp = await client.post("/user/", json=user_data)
    data_from_resp = resp.json()

    assert resp.status_code == 200
    assert data_from_resp["name"] == user_data["name"]
    assert data_from_resp["surname"] == user_data["surname"]
    assert data_from_resp["email"] == user_data["email"]
    assert data_from_resp["is_active"] is True

    user_from_db = await get_user_from_database(data_from_resp["user_id"])

    assert user_from_db["name"] == user_data["name"]
    assert user_from_db["surname"] == user_data["surname"]
    assert user_from_db["email"] == user_data["email"]
    assert user_from_db["is_active"] is True
    assert str(user_from_db["user_id"]) == data_from_resp["user_id"]

    resp = await client.post("/user/", json=user_data_same_email)
    assert resp.status_code == 409
    assert "User with this email already exists" in resp.json()["detail"]


@pytest.mark.parametrize(
    ["user_data_from_creation", "expected_status_code", "expected_detail"],
    [
        (
            {},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "name"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "surname"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "email"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "password"],
                        "msg": "Field required",
                        "input": {},
                    },
                ]
            },
        ),
        (
            {"name": 123, "surname": 456, "email": "qwe", "password": "SamplePass1!"},
            422,
            {
                "detail": [
                    {
                        "type": "string_type",
                        "loc": ["body", "name"],
                        "msg": "Input should be a valid string",
                        "input": 123,
                    },
                    {
                        "type": "string_type",
                        "loc": ["body", "surname"],
                        "msg": "Input should be a valid string",
                        "input": 456,
                    },
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "qwe",
                        "ctx": {"reason": "An email address must have an @-sign."},
                    },
                ]
            },
        ),
        (
            {
                "name": "123",
                "surname": "456",
                "email": "qwe",
                "password": "SamplePass1!",
            },
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "name"],
                        "msg": "Value error, Name should contains only letters",
                        "input": "123",
                        "ctx": {"error": {}},
                    },
                    {
                        "type": "value_error",
                        "loc": ["body", "surname"],
                        "msg": "Value error, Surname should contains only letters",
                        "input": "456",
                        "ctx": {"error": {}},
                    },
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "qwe",
                        "ctx": {"reason": "An email address must have an @-sign."},
                    },
                ]
            },
        ),
        (
            {"name": "Ivan", "surname": "Ivanov", "email": "qwe"},
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "qwe",
                        "ctx": {"reason": "An email address must have an @-sign."},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "password"],
                        "msg": "Field required",
                        "input": {"name": "Ivan", "surname": "Ivanov", "email": "qwe"},
                    },
                ]
            },
        ),
        (
            {
                "name": "Ivan",
                "surname": 456,
                "email": "qwe",
                "password": "SamplePass1!",
            },
            422,
            {
                "detail": [
                    {
                        "type": "string_type",
                        "loc": ["body", "surname"],
                        "msg": "Input should be a valid string",
                        "input": 456,
                    },
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "qwe",
                        "ctx": {"reason": "An email address must have an @-sign."},
                    },
                ]
            },
        ),
    ],
)
async def test_create_user_validation_error(
    client, user_data_from_creation, expected_status_code, expected_detail
):
    resp = await client.post("/user/", json=user_data_from_creation)
    data_from_resp = resp.json()
    assert resp.status_code == expected_status_code
    assert data_from_resp == expected_detail
