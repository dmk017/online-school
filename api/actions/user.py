from logging import getLogger
from typing import Union
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from api.models import ShowUser
from api.models import UserCreate
from db.dals import UserDAL
from hashing import Hasher


logger = getLogger(__name__)


async def _create_new_user(body: UserCreate, db) -> ShowUser:
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            try:
                user = await user_dal.create_user(
                    name=body.name,
                    surname=body.surname,
                    email=body.email,
                    hashed_password=Hasher.get_password_hash(body.password),
                )
                return ShowUser(
                    user_id=user.user_id,
                    name=user.name,
                    surname=user.surname,
                    email=user.email,
                    is_active=user.is_active,
                )
            except IntegrityError as err:
                logger.error(err)
                raise HTTPException(
                    status_code=409, detail="User with this email already exists"
                )


async def _delete_user(user_id, db) -> Union[UUID, None]:
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            deleted_user_id = await user_dal.delete_user(user_id=user_id)
            return deleted_user_id


async def _get_user_by_id(user_id, db) -> Union[ShowUser, None]:
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            user = await user_dal.get_user_by_id(user_id=user_id)
            if user is not None:
                return ShowUser(
                    user_id=user.user_id,
                    name=user.name,
                    surname=user.surname,
                    email=user.email,
                    is_active=user.is_active,
                )


async def _update_user(
    updated_user_params: dict, user_id: UUID, db
) -> Union[UUID, None]:
    async with db as session:
        async with session.begin():
            user_dal = UserDAL(session)
            try:
                updated_user_id = await user_dal.update_user(
                    user_id=user_id, **updated_user_params
                )
                return updated_user_id
            except IntegrityError as err:
                logger.error(err)
                raise HTTPException(
                    status_code=409, detail="User with this email already exists"
                )
