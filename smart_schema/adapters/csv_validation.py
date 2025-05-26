"""
CSV validation utilities.
"""

import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Type, Union

import pandas as pd
from pydantic import BaseModel, ValidationError
from rich.console import Console
from rich.table import Table

from ..core.model_utils import generate_pydantic_model
from ..utils.dataframe_utils import validate_dataframe_with_model

console = Console()


def load_model_from_file(model_path: Union[str, Path]) -> Type[BaseModel]:
    """
    Dynamically load a Pydantic model from a Python file.
    """
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    # Load the module
    spec = importlib.util.spec_from_file_location("model_module", model_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load model from {model_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Find the first BaseModel subclass in the module
    model_class = None
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and issubclass(attr, BaseModel) and attr != BaseModel:
            model_class = attr
            break

    if model_class is None:
        raise ValueError(f"No Pydantic model found in {model_path}")

    return model_class


def validate_csv(
    csv_path: Union[str, Path],
    model: Type[BaseModel],
    chunk_size: int = 1000,
) -> Tuple[List[Dict], List[Tuple[int, Dict, ValidationError]]]:
    """
    Validate CSV data against a Pydantic model.

    Returns:
        Tuple containing:
        - List of valid records
        - List of tuples containing (row_number, data, error) for invalid records
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    valid_records = []
    invalid_records = []

    # Read CSV in chunks to handle large files
    for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
        for idx, row in chunk.iterrows():
            try:
                # Convert row to dict and validate
                record = row.to_dict()
                validated = model.model_validate(record)
                valid_records.append(validated.model_dump())
            except ValidationError as e:
                invalid_records.append((idx + 2, record, e))  # +2 for header row and 1-based index

    return valid_records, invalid_records


def generate_validation_report(
    valid_records: List[Dict],
    invalid_records: List[Tuple[int, Dict, ValidationError]],
    output_path: Optional[Union[str, Path]] = None,
) -> None:
    """
    Generate a validation report using Rich tables.
    """
    # Summary table
    summary = Table(title="Validation Summary")
    summary.add_column("Total Records", justify="right")
    summary.add_column("Valid Records", justify="right")
    summary.add_column("Invalid Records", justify="right")
    summary.add_column("Success Rate", justify="right")

    total = len(valid_records) + len(invalid_records)
    success_rate = f"{(len(valid_records) / total * 100):.1f}%" if total > 0 else "0%"

    summary.add_row(
        str(total),
        str(len(valid_records)),
        str(len(invalid_records)),
        success_rate,
    )

    console.print(summary)

    # Invalid records table
    if invalid_records:
        errors = Table(title="Invalid Records")
        errors.add_column("Row", justify="right")
        errors.add_column("Data", style="yellow")
        errors.add_column("Error", style="red")

        for row_num, data, error in invalid_records:
            errors.add_row(
                str(row_num),
                str(data),
                str(error),
            )

        console.print(errors)

    # Save valid records if output path is provided
    if output_path:
        output_path = Path(output_path)
        df = pd.DataFrame(valid_records)
        df.to_csv(output_path, index=False)
        console.print(f"\n[green]Valid records saved to: {output_path}[/green]")
