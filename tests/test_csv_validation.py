"""
Tests for CSV validation functionality.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest
from pydantic import BaseModel, ValidationError

from smart_schema.csv_validation import load_model_from_file, validate_csv


class TestModel(BaseModel):
    """Test model for validation."""

    name: str
    age: int
    active: bool


def test_load_model_from_file():
    """Test loading a model from a Python file."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w") as f:
        f.write(
            """
from pydantic import BaseModel

class TestModel(BaseModel):
    name: str
    age: int
    active: bool
"""
        )
        f.flush()

        model = load_model_from_file(f.name)
        assert model.__name__ == "TestModel"
        assert issubclass(model, BaseModel)


def test_validate_csv_valid_data():
    """Test CSV validation with valid data."""
    # Create test CSV
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w") as f:
        f.write("name,age,active\nAlice,25,true\nBob,30,false\n")
        f.flush()

        # Validate
        valid_records, invalid_records = validate_csv(f.name, TestModel)

        assert len(valid_records) == 2
        assert len(invalid_records) == 0
        assert valid_records[0]["name"] == "Alice"
        assert valid_records[0]["age"] == 25
        assert valid_records[0]["active"] is True


def test_validate_csv_invalid_data():
    """Test CSV validation with invalid data."""
    # Create test CSV with invalid data
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w") as f:
        f.write("name,age,active\nAlice,invalid,true\nBob,30,not_bool\n")
        f.flush()

        # Validate
        valid_records, invalid_records = validate_csv(f.name, TestModel)

        assert len(valid_records) == 0
        assert len(invalid_records) == 2

        # Check first error
        row_num, data, error = invalid_records[0]
        assert row_num == 2  # 1-based index + header
        assert data["name"] == "Alice"
        assert "age" in str(error)  # Error should mention age field

        # Check second error
        row_num, data, error = invalid_records[1]
        assert row_num == 3
        assert data["name"] == "Bob"
        assert "active" in str(error)  # Error should mention active field
