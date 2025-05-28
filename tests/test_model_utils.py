import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from pydantic import BaseModel, ValidationError

from smart_schema.core import model_utils


@pytest.fixture(scope="session")
def data_dir():
    data_path = Path("tests/data")
    data_path.mkdir(exist_ok=True)
    return data_path


def test_generate_schema_from_json():
    data = {"a": 1, "b": "foo"}
    schema = model_utils.generate_schema_from_json(data)
    assert "a" in schema and "b" in schema
    assert schema["a"]["type"] == int
    assert schema["b"]["type"] == str


def test_generate_schema_from_dataframe():
    df = pd.DataFrame({"a": [1, 2], "b": ["foo", "bar"]})
    schema = model_utils.generate_schema_from_dataframe(df)
    assert "a" in schema and "b" in schema
    assert schema["a"]["type"] in [int, float, Any]
    assert schema["b"]["type"] == str


def test_generate_pydantic_model():
    schema = {
        "a": {"type": int, "is_nullable": False, "description": "col a"},
        "b": {"type": str, "is_nullable": True, "description": "col b"},
    }
    model = model_utils.generate_pydantic_model(schema, "TestModel")
    instance = model(a=1, b="foo")
    assert instance.a == 1
    assert instance.b == "foo"
    with pytest.raises(ValidationError):
        model(b="foo")


def test_save_and_load_model(data_dir):
    schema = {
        "a": {"type": int, "is_nullable": False, "description": "col a"},
        "b": {"type": str, "is_nullable": True, "description": "col b"},
    }
    model = model_utils.generate_pydantic_model(schema, "TestModel")
    file_path = data_dir / "test_model.py"
    model_utils.save_model_to_file(model, str(file_path), "TestModel")
    assert file_path.exists()
    # Optionally, check file content
    with open(file_path) as f:
        content = f.read()
    assert "class TestModel" in content


def test_load_and_validate_json_as_model(data_dir):
    class DummyModel(BaseModel):
        a: int
        b: str

    data = {"a": 1, "b": "foo"}
    file_path = data_dir / "data.json"
    with open(file_path, "w") as f:
        json.dump(data, f)
    instance = model_utils.load_and_validate_json_as_model(file_path, DummyModel)
    assert instance.a == 1
    assert instance.b == "foo"
    # Invalid data
    with open(file_path, "w") as f:
        json.dump({"a": "not_an_int", "b": "foo"}, f)
    assert model_utils.load_and_validate_json_as_model(file_path, DummyModel) is None
