from pydantic import BaseModel


class AuthRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisteredResponse(BaseModel):
    id: str
    name: str
    username: str
