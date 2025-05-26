from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class UserPreferences(BaseModel):
    theme: str
    notifications: bool

class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    preferences: UserPreferences

class OrderItem(BaseModel):
    product_id: str
    quantity: int

class Order(BaseModel):
    order_id: str
    items: List[OrderItem]
    total: float
    created_at: datetime

class Metadata(BaseModel):
    created_at: datetime
    version: str

class OrderSystem(BaseModel):
    user: User
    orders: List[Order]
    metadata: Metadata
