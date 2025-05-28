"""
Generated Pydantic model.
"""

import math
from builtins import bool, float, int, str
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class Specifications(BaseModel):
    switch_type: str
    layout: str
    connectivity: List[str]


class SupplierInfo(BaseModel):
    supplier_id: str
    name: str


class ProductCreateRequest(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    stock: int
    description: Optional[str]
    specifications: Specifications
    supplier_info: SupplierInfo
    is_active: bool
    tags: Optional[List]

    @validator("*", pre=True)
    def handle_nan(cls, v: Any) -> Any:
        if isinstance(v, float) and math.isnan(v):
            return None
        return v
