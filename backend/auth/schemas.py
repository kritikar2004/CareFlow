from pydantic import BaseModel, ConfigDict


class RegisterRequest(BaseModel):
    hospital_name: str
    phone: str
    email: str
    password: str
    city: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    hospital_name: str
    phone: str
    email: str
    city: str

    model_config = ConfigDict(from_attributes=True)