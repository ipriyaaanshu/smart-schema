from pydantic import BaseModel


class UserModel(BaseModel):
    username: str
    email: str
    age: int
    is_active: bool
