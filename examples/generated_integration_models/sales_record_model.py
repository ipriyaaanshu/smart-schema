"""
Generated Pydantic model.
"""

import math
from builtins import float, str
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class SalesRecord(BaseModel):
    Date: datetime
    ProductID: str
    ProductName: str
    Category: str
    QuantitySold: float
    UnitPrice: float
    TotalPrice: float
    Region: str

    @validator("*", pre=True)
    def handle_nan(cls, v: Any) -> Any:
        if isinstance(v, float) and math.isnan(v):
            return None
        return v
