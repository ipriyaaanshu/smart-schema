from datetime import datetime

from pydantic import BaseModel


class Product(BaseModel):
    id: int
    name: str
    category: str
    stock: int
    price: float
    last_updated: datetime
