from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    is_active: bool
    category: str
    tags: List
    metadata: Dict
    last_updated: datetime
