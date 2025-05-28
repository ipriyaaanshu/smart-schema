"""
Generated Pydantic model.
"""

from builtins import float
from builtins import str
from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import Union, Optional, Any, List, Dict
import math

class SalesRecord(BaseModel):
    Date: datetime
    ProductID: str
    ProductName: str
    Category: str
    QuantitySold: float
    UnitPrice: float
    TotalPrice: float
    Region: str


    @validator('*', pre=True)
    def handle_nan(cls, v: Any) -> Any:
        if isinstance(v, float) and math.isnan(v):
            return None
        return v
