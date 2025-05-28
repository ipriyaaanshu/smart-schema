"""
Generated Pydantic model.
"""

import math
from builtins import int, str
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class TestModel(BaseModel):
    a: int
    b: Optional[str] = None

    @validator("*", pre=True)
    def handle_nan(cls, v: Any) -> Any:
        if isinstance(v, float) and math.isnan(v):
            return None
        return v
