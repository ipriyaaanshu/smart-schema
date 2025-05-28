from pydantic import BaseModel
from typing import List
from datetime import datetime

class Notifications(BaseModel):
    email: str
    enabled: bool

class Inventory(BaseModel):
    low_stock_threshold: int
    categories: List[str]
    notifications: Notifications

class InventoryConfig(BaseModel):
    inventory: Inventory
