from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Optional

from jose import jwt

import settings


def create_access_token(data: dict, expire_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expire_delta:
        expire = now + expire_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
