"""
Smart Schema - A tool for generating and validating data schemas.
"""

from .core.model_generator import ModelGenerator
from .core.model_validator import ModelValidator
from .adapters.csv_inference import infer_column_types
from .adapters.csv_splitter import split_by_rows, split_by_column
from .adapters.csv_validation import validate_csv, generate_validation_report

__version__ = "0.1.0"

__all__ = [
    "ModelGenerator",
    "ModelValidator",
    "infer_column_types",
    "split_by_rows",
    "split_by_column",
    "validate_csv",
    "generate_validation_report",
]
