from datetime import datetime
from typing import List

from pydantic import BaseModel


class Notifications(BaseModel):
    email: str
    enabled: bool


class Inventory(BaseModel):
    low_stock_threshold: int
    categories: List[str]
    notifications: Notifications


class InventoryConfig(BaseModel):
    inventory: Inventory
