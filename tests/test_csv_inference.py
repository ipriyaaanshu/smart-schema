import pandas as pd
import pytest
from pydantic import ValidationError

from smart_schema.adapters import csv_inference
from smart_schema.core import model_utils


def test_infer_column_types_simple():
    df = pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})
    types = csv_inference.infer_column_types(df)
    # Accept int, float, or numpy integer types
    assert issubclass(types["A"], (int, float))
    assert issubclass(types["B"], str)


def test_infer_column_types_empty():
    df = pd.DataFrame({"A": [], "B": []})
    types = csv_inference.infer_column_types(df)
    assert "A" in types and "B" in types


def test_generate_schema_from_dataframe():
    df = pd.DataFrame({"A": [1, 2], "B": ["foo", "bar"]})
    schema = model_utils.generate_schema_from_dataframe(df)
    assert "A" in schema and "B" in schema
    assert "type" in schema["A"]
    assert "type" in schema["B"]


def test_generate_pydantic_model_from_schema():
    schema = {
        "A": {"type": int, "is_nullable": False, "description": "col A"},
        "B": {"type": str, "is_nullable": True, "description": "col B"},
    }
    model = model_utils.generate_pydantic_model(schema, "TestModel")
    instance = model(A=1, B="foo")
    assert instance.A == 1
    assert instance.B == "foo"


def test_generate_pydantic_model_from_schema_missing_required():
    schema = {
        "A": {"type": int, "is_nullable": False, "description": "col A"},
        "B": {"type": str, "is_nullable": True, "description": "col B"},
    }
    model = model_utils.generate_pydantic_model(schema, "TestModel")
    with pytest.raises(ValidationError):
        model(B="foo")
