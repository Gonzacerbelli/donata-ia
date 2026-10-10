from pydantic import BaseModel, Field

from ..models.domain import User


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class UserOut(BaseModel):
    id: str
    email: str | None = None
    name: str | None = None
    picture: str | None = None


class UserSummary(BaseModel):
    id: str
    name: str | None = None
    email: str | None = None


class GoogleAuthStart(BaseModel):
    url: str


class GoogleAuthCallback(BaseModel):
    code: str
    state: str


class AuthCodeExchange(BaseModel):
    code: str = Field(min_length=1, max_length=200)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


def user_to_out(user: User) -> UserOut:
    return UserOut(
        id=user.id or "",
        email=user.email,
        name=user.name,
        picture=user.picture,
    )
