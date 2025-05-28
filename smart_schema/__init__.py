"""
Smart Schema - A tool for generating and validating data schemas.
"""

from .adapters.csv_adapter import CSVAdapter
from .adapters.csv_inference import infer_column_types
from .adapters.csv_splitter import split_by_column, split_by_rows
from .adapters.csv_validation import generate_validation_report, validate_csv
from .core.model_generator import ModelGenerator
from .core.model_utils import (
    generate_model_from_schema,
    generate_pydantic_model,
    load_and_validate_json_as_model,
    save_model_to_file,
)
from .core.model_validator import ModelValidator
from .core.schema_inferrer import SchemaInferrer

__all__ = [
    "CSVAdapter",
    "ModelGenerator",
    "ModelValidator",
    "SchemaInferrer",
    "save_model_to_file",
    "generate_pydantic_model",
    "generate_model_from_schema",
    "load_and_validate_json_as_model",
    "infer_column_types",
    "split_by_rows",
    "split_by_column",
    "validate_csv",
    "generate_validation_report",
]
