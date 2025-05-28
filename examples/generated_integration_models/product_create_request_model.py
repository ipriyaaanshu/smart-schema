"""
Generated Pydantic model.
"""

from builtins import bool
from builtins import float
from builtins import int
from builtins import str
from pydantic import BaseModel, Field, validator
from typing import Union, Optional, Any, List, Dict
import math

class SupplierInfo(BaseModel):
    supplier_id: str
    name: str

class Specifications(BaseModel):
    switch_type: str
    layout: str
    connectivity: List[str]

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


    @validator('*', pre=True)
    def handle_nan(cls, v: Any) -> Any:
        if isinstance(v, float) and math.isnan(v):
            return None
        return v
