from datetime import timedelta, datetime, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from typing import Annotated

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status

from pwdlib import PasswordHash


from schemas import UserInDB, TokenData


SECRET_KEY = "afc57d53c86db28f99f5a29b9fd183d627f435a78bd379dc30b1d31995f81d15"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummypassword")


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False

    if not verify_password(password, user.hashed_password):
        return False

    return user


from database import get_connection
from schemas import UserInDB


def get_user(username: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, fullname, hashed_password FROM users WHERE username = ?",
        (username,),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return UserInDB(
            username=row["username"],
            fullname=row["fullname"],
            hashed_password=row["hashed_password"],
        )

    return None


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
