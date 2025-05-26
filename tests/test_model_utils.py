"""
Tests for smart-schema model generation and validation utilities.
"""

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pytest

from smart_schema.model_utils import (
    _generate_schema_from_dict,
    _infer_type_from_value,
    generate_model_from_schema,
    generate_pydantic_model,
    generate_schema_from_dataframe,
    generate_schema_from_json,
)

# Test data
SAMPLE_JSON = {
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "is_active": True,
        "preferences": {"theme": "dark", "notifications": True},
    },
    "orders": [
        {
            "order_id": "ORD-001",
            "items": [{"product_id": "P1", "quantity": 2}, {"product_id": "P2", "quantity": 1}],
            "total": 99.99,
        }
    ],
}

SAMPLE_DF = pd.DataFrame(
    {
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "age": [25, 30, None],
        "is_active": [True, False, True],
        "score": [95.5, 88.0, 92.5],
    }
)


def test_infer_type_from_value():
    """Test type inference from values."""
    assert _infer_type_from_value(1) == int
    assert _infer_type_from_value(1.0) == float
    assert _infer_type_from_value("test") == str
    assert _infer_type_from_value(True) == bool
    assert _infer_type_from_value(None) == Any
    assert _infer_type_from_value([]) == List[Any]
    assert _infer_type_from_value([1, 2, 3]) == List[int]
    assert _infer_type_from_value({}) == Dict[str, Any]
    assert _infer_type_from_value({"key": "value"}) == Dict[str, Any]


def test_generate_schema_from_dict():
    """Test schema generation from dictionary."""
    schema = _generate_schema_from_dict(SAMPLE_JSON)

    # Check top-level fields
    assert "user" in schema
    assert "orders" in schema

    # Check nested user fields
    user_schema = schema["user"]["nested_schema"]
    assert "id" in user_schema
    assert "name" in user_schema
    assert "email" in user_schema
    assert "is_active" in user_schema
    assert "preferences" in user_schema

    # Check preferences fields
    prefs_schema = user_schema["preferences"]["nested_schema"]
    assert "theme" in prefs_schema
    assert "notifications" in prefs_schema

    # Check orders list
    assert schema["orders"]["type"].__origin__ == List


def test_generate_schema_from_json():
    """Test schema generation from JSON."""
    # Test with dictionary
    schema = generate_schema_from_json(SAMPLE_JSON)
    assert isinstance(schema, dict)
    assert "user" in schema
    assert "orders" in schema

    # Test with JSON string
    json_str = json.dumps(SAMPLE_JSON)
    schema_from_str = generate_schema_from_json(json_str)
    assert schema == schema_from_str

    # Test with invalid JSON
    with pytest.raises(ValueError):
        generate_schema_from_json("invalid json")

    # Test with non-dict JSON
    with pytest.raises(ValueError):
        generate_schema_from_json("[1, 2, 3]")


def test_generate_schema_from_dataframe():
    """Test schema generation from DataFrame."""
    schema = generate_schema_from_dataframe(SAMPLE_DF)

    # Check all columns are present
    assert "id" in schema
    assert "name" in schema
    assert "age" in schema
    assert "is_active" in schema
    assert "score" in schema

    # Check types
    assert schema["id"]["type"] == int
    assert schema["name"]["type"] == str
    assert schema["age"]["type"] == int
    assert schema["is_active"]["type"] == bool
    assert schema["score"]["type"] == float

    # Check nullable fields
    assert schema["age"]["is_nullable"] == True
    assert schema["id"]["is_nullable"] == False

    # Check descriptions
    for field in schema.values():
        assert "description" in field
        assert "total_rows" in field["description"]
        assert "null_count" in field["description"]
        assert "unique_count" in field["description"]


def test_generate_pydantic_model():
    """Test Pydantic model generation."""
    schema = generate_schema_from_json(SAMPLE_JSON)
    model = generate_pydantic_model(schema, "TestModel")

    # Check model creation
    assert model.__name__ == "TestModel"

    # Check field types
    assert model.model_fields["user"].annotation.__name__ == "UserModel"
    assert model.model_fields["orders"].annotation.__origin__ == List

    # Test model validation
    instance = model(**SAMPLE_JSON)
    assert instance.user.name == "John Doe"
    assert instance.orders[0].total == 99.99


def test_generate_model_from_schema():
    """Test model generation and file saving."""
    schema = generate_schema_from_json(SAMPLE_JSON)
    output_file = generate_model_from_schema(schema, "TestModel")

    # Check file creation
    assert Path(output_file).exists()

    # Check file contents
    content = Path(output_file).read_text()
    assert "class TestModel" in content
    assert "from pydantic import BaseModel" in content
    assert "from typing import" in content

    # Clean up
    Path(output_file).unlink()


def test_complex_validation():
    """Test complex validation scenarios."""
    # Create a schema with various field types
    schema = {
        "id": {"type": int, "is_nullable": False},
        "name": {"type": str, "is_nullable": False},
        "age": {"type": int, "is_nullable": True},
        "scores": {"type": List[float], "is_nullable": True},
        "metadata": {"type": Dict[str, Any], "is_nullable": True},
    }

    # Generate model
    model = generate_pydantic_model(schema, "ComplexModel")

    # Test valid data
    valid_data = {
        "id": 1,
        "name": "Test",
        "age": 25,
        "scores": [95.5, 88.0],
        "metadata": {"key": "value"},
    }
    instance = model(**valid_data)
    assert instance.id == 1
    assert instance.name == "Test"
    assert instance.age == 25
    assert instance.scores == [95.5, 88.0]
    assert instance.metadata == {"key": "value"}

    # Test invalid data
    with pytest.raises(ValueError):
        model(id="invalid", name="Test")

    # Test nullable fields
    valid_data["age"] = None
    valid_data["scores"] = None
    valid_data["metadata"] = None
    instance = model(**valid_data)
    assert instance.age is None
    assert instance.scores is None
    assert instance.metadata is None


def test_dataframe_validation():
    """Test DataFrame validation with generated models."""
    # Generate model from DataFrame
    schema = generate_schema_from_dataframe(SAMPLE_DF)
    model = generate_pydantic_model(schema, "DataFrameModel")

    # Test valid data
    valid_data = SAMPLE_DF.iloc[0].to_dict()
    instance = model(**valid_data)
    assert instance.id == 1
    assert instance.name == "Alice"
    assert instance.age == 25
    assert instance.is_active == True
    assert instance.score == 95.5

    # Test invalid data
    invalid_data = valid_data.copy()
    invalid_data["id"] = "invalid"
    with pytest.raises(ValueError):
        model(**invalid_data)

    # Test nullable fields
    invalid_data = valid_data.copy()
    invalid_data["age"] = None
    instance = model(**invalid_data)
    assert instance.age is None
