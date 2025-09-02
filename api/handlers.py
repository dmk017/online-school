from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.actions.auth import get_current_user_from_token
from api.actions.user import _create_new_user
from api.actions.user import _delete_user
from api.actions.user import _get_user_by_id
from api.actions.user import _update_user
from api.actions.user import check_user_permissions
from api.models import DeleteUserResponse
from api.models import ShowUser
from api.models import UpdateUserRequest
from api.models import UpdateUserResponse
from api.models import UserCreate
from db.models import User
from db.session import get_db


user_router = APIRouter()


@user_router.post("/", response_model=ShowUser)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)) -> ShowUser:
    return await _create_new_user(body, db)


@user_router.delete("/", response_model=DeleteUserResponse)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
) -> DeleteUserResponse:
    user_for_deletion = await _get_user_by_id(user_id, db)

    if user_for_deletion is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    if not check_user_permissions(
        target_user=user_for_deletion, current_user=current_user
    ):
        raise HTTPException(status_code=403, detail="Forbidden.")

    deleted_user_id = await _delete_user(user_id, db)
    if deleted_user_id is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    return DeleteUserResponse(deleted_user_id=deleted_user_id)


@user_router.get("/", response_model=ShowUser)
async def get_user_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
) -> ShowUser:
    user = await _get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    return user


@user_router.patch("/", response_model=UpdateUserResponse)
async def update_user_by_id(
    user_id: UUID,
    body: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
):
    updated_user_params = body.model_dump(exclude_none=True)
    if updated_user_params == {}:
        raise HTTPException(
            status_code=422,
            detail="At least one parameter for user update info should be provided",
        )
    user_for_update = await _get_user_by_id(user_id, db)
    if user_for_update is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    if user_id != current_user.user_id:
        if check_user_permissions(
            target_user=user_for_update, current_user=current_user
        ):
            raise HTTPException(status_code=403, detail="Forbidden.")
    updated_user_id = await _update_user(
        updated_user_params=updated_user_params, session=db, user_id=user_id
    )
    return UpdateUserResponse(updated_user_id=updated_user_id)


@user_router.patch("/admin_privileges", response_model=UpdateUserResponse)
async def grand_admin_privileges(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
):
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Forbidden.")
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=406, detail="Cannot manage privileges of itself."
        )

    user_from_promotion = await _get_user_by_id(user_id, db)
    if user_from_promotion.is_admin or user_from_promotion.is_superadmin:
        raise HTTPException(
            status_code=409,
            detail=f"User with id {user_id} already promoted to admin / superadmin.",
        )
    if user_from_promotion is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )

    updated_user_params = {
        "roles": user_from_promotion.enrich_admin_roles_by_admin_role()
    }
    updated_user_id = await _update_user(
        updated_user_params=updated_user_params, session=db, user_id=user_id
    )
    return UpdateUserResponse(updated_user_id=updated_user_id)


@user_router.delete("/admin_privileges", response_model=UpdateUserResponse)
async def revoke_admin_privileges(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
):
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Forbidden.")
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=406, detail="Cannot manage privileges of itself."
        )

    user_for_revoke_admin_privileges = await _get_user_by_id(user_id, db)
    if not user_for_revoke_admin_privileges.is_admin:
        raise HTTPException(
            status_code=409, detail=f"User with id {user_id} has no admin privileges."
        )
    if user_for_revoke_admin_privileges is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    updated_user_params = {
        "roles": user_for_revoke_admin_privileges.remove_admin_privileges_from_model()
    }
    updated_user_id = await _update_user(
        updated_user_params=updated_user_params, session=db, user_id=user_id
    )
    return UpdateUserResponse(updated_user_id=updated_user_id)
