from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import HTTPException, Security

from pydantic_settings import BaseSettings
from starlette import status
from typing import Optional


class Settings(BaseSettings):
    username: Optional[str] = None
    password: Optional[str] = None


settings = Settings()


def get_authorization(credentials: HTTPBasicCredentials = Security(HTTPBasic())):
    if credentials.username != settings.username or credentials.password != settings.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True
