from pathlib import Path

import pandas as pd
import pytest

from smart_schema.adapters import csv_validation
from smart_schema.core import model_utils


@pytest.fixture(scope="session")
def data_dir():
    data_path = Path("tests/data")
    data_path.mkdir(exist_ok=True)
    return data_path


def test_validate_csv(data_dir):
    df = pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})
    file_path = data_dir / "test.csv"
    df.to_csv(file_path, index=False)
    schema = {
        "A": {"type": int, "is_nullable": False, "description": "col A"},
        "B": {"type": str, "is_nullable": False, "description": "col B"},
    }
    model = model_utils.generate_pydantic_model(schema, "TestModel")
    csv_validation.validate_csv(str(file_path), model)


def test_validate_csv_missing_column(data_dir):
    df = pd.DataFrame({"A": [1, 2, 3]})
    file_path = data_dir / "test.csv"
    df.to_csv(file_path, index=False)
    schema = {
        "A": {"type": int, "is_nullable": False, "description": "col A"},
        "B": {"type": str, "is_nullable": False, "description": "col B"},
    }
    with pytest.raises(Exception):
        csv_validation.validate_csv(str(file_path), schema)


def test_validate_csv_with_nullable(data_dir):
    df = pd.DataFrame({"A": [1, None, 3], "B": ["x", "y", "z"]})
    file_path = data_dir / "test.csv"
    df.to_csv(file_path, index=False)
    schema = {
        "A": {"type": int, "is_nullable": True, "description": "col A"},
        "B": {"type": str, "is_nullable": False, "description": "col B"},
    }

    model = model_utils.generate_pydantic_model(schema, "TestModel")
    # Should not raise
    csv_validation.validate_csv(str(file_path), model)
