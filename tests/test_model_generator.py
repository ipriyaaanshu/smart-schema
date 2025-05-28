import os
from pathlib import Path

import pandas as pd
import pytest
from pydantic import BaseModel, ValidationError

from smart_schema.core import model_generator


@pytest.fixture(scope="session")
def data_dir():
    data_path = Path("tests/data")
    data_path.mkdir(exist_ok=True)
    return data_path


def test_from_dataframe_basic(data_dir):
    df = pd.DataFrame({"a": [1, 2], "b": ["foo", "bar"]})
    csv_path = data_dir / "test_dataframe.csv"
    df.to_csv(csv_path, index=False)
    gen = model_generator.ModelGenerator(name="TestModel")
    model = gen.from_dataframe(df)
    # Happy path: valid instance
    instance = model(a=1, b="foo")
    assert instance.a == 1
    assert instance.b == "foo"
    # Edge case: missing required field
    with pytest.raises(ValidationError):
        model(b="foo")


def test_from_json_basic():
    data = {"a": 1, "b": "foo"}
    gen = model_generator.ModelGenerator(name="TestModel")
    model = gen.from_json(data)
    # Happy path: valid instance
    instance = model(a=1, b="foo")
    assert instance.a == 1
    assert instance.b == "foo"
    # Edge case: missing required field
    with pytest.raises(ValidationError):
        model(b="foo")


def test_from_description_basic(monkeypatch):
    # Mock OpenAI if smart_inference is True
    field_desc = [
        {"name": "a", "description": "An integer", "nullable": False},
        {"name": "b", "description": "A string", "nullable": True},
    ]
    gen = model_generator.ModelGenerator(name="TestModel", smart_inference=False)
    # Edge case: smart_inference is needed for schema from description
    with pytest.raises(ValueError):
        model = gen.from_description(field_desc)
