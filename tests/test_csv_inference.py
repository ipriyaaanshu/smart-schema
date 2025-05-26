"""
Tests for CSV schema inference functionality.
"""

import pandas as pd
import pytest
from pydantic import BaseModel

from smart_schema.csv_inference import generate_model, infer_column_types


def test_infer_column_types():
    """Test type inference from DataFrame columns."""
    df = pd.DataFrame(
        {
            "int_col": [1, 2, 3],
            "float_col": [1.0, 2.0, 3.0],
            "str_col": ["a", "b", "c"],
            "bool_col": [True, False, True],
        }
    )

    types = infer_column_types(df)
    assert types["int_col"] == int
    assert types["float_col"] == float
    assert types["str_col"] == str
    assert types["bool_col"] == bool


def test_generate_model():
    """Test Pydantic model generation from DataFrame."""
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "active": [True, False, True],
        }
    )

    model = generate_model(df, model_name="TestModel")

    # Test model instantiation
    instance = model(name="Test", age=40, active=True)
    assert isinstance(instance, BaseModel)
    assert instance.name == "Test"
    assert instance.age == 40
    assert instance.active is True

    # Test validation
    with pytest.raises(ValueError):
        model(name="Test", age="invalid", active=True)
