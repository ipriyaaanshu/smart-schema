"""
Command-line interface for Smart Schema.
"""

from pathlib import Path
from typing import List, Optional, Type

import typer
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel

from ..adapters.csv_inference import infer_column_types
from ..adapters.csv_splitter import split_by_column, split_by_rows
from ..adapters.csv_validation import generate_validation_report, validate_csv
from ..core.model_generator import ModelGenerator
from ..core.model_validator import ModelValidator

app = typer.Typer(
    name="smart-schema",
    help="Smart Schema - A tool for generating and validating data schemas.",
    no_args_is_help=True,
)
console = Console()


def _ensure_path(path: str) -> Path:
    """Convert string path to Path object."""
    return Path(path)


@app.command()
def generate_model(
    input_file: Optional[str] = typer.Argument(
        None, help="Input CSV or JSON file (optional for JSON)"
    ),
    output: str = typer.Option("--output", "-o", help="Output model file path"),
    type: str = typer.Option("csv", "--type", "-t", help="Input file type (csv or json)"),
    datetime_columns: Optional[List[str]] = typer.Option(
        None, "--datetime-columns", "-d", help="List of datetime columns"
    ),
    encoding: str = typer.Option("utf-8", "--encoding", "-e", help="File encoding"),
    delimiter: str = typer.Option(",", "--delimiter", help="CSV delimiter"),
    no_header: bool = typer.Option(False, "--no-header", help="CSV has no header row"),
    progress: bool = typer.Option(False, "--progress", help="Show progress bar"),
):
    """Generate a Pydantic model from a CSV or JSON file or JSON data from stdin."""
    try:
        output_path = _ensure_path(output)

        # Generate model
        generator = ModelGenerator(name=output_path.stem)

        if type.lower() == "csv":
            if not input_file:
                raise ValueError("Input file is required for CSV type")
            input_path = _ensure_path(input_file)
            console.print(
                Panel.fit(
                    f"Generating model from {input_path}...",
                    title="Smart Schema",
                    border_style="blue",
                )
            )
            import pandas as pd

            df = pd.read_csv(
                input_path,
                encoding=encoding,
                delimiter=delimiter,
                header=None if no_header else 0,
            )
            model = generator.from_dataframe(df, datetime_columns=datetime_columns)
        elif type.lower() == "json":
            import json
            import sys

            if input_file:
                input_path = _ensure_path(input_file)
                console.print(
                    Panel.fit(
                        f"Generating model from {input_path}...",
                        title="Smart Schema",
                        border_style="blue",
                    )
                )
                with open(input_path, encoding=encoding) as f:
                    data = json.load(f)
            else:
                console.print(
                    Panel.fit(
                        "Reading JSON data from stdin...",
                        title="Smart Schema",
                        border_style="blue",
                    )
                )
                data = json.load(sys.stdin)

            model = generator.from_json(data, datetime_columns=datetime_columns)
        else:
            raise ValueError(f"Unsupported file type: {type}")

        # Save model to file
        with open(output_path, "w") as f:
            f.write("from pydantic import BaseModel\n")
            f.write("from typing import List, Dict, Optional, Any\n")
            f.write("from datetime import datetime\n\n")

            # Collect all models and their dependencies
            models = {}

            def collect_models(model_class: Type[BaseModel]) -> None:
                """Collect all models and their dependencies."""
                if model_class.__name__ in models:
                    return

                models[model_class.__name__] = model_class

                for field in model_class.model_fields.values():
                    field_type = field.annotation
                    if hasattr(field_type, "__origin__") and field_type.__origin__ is list:
                        # Handle List types
                        item_type = field_type.__args__[0]
                        if hasattr(item_type, "__name__") and item_type.__name__ != "Any":
                            collect_models(item_type)
                    elif hasattr(field_type, "__name__") and field_type.__name__ != "Any":
                        # Handle nested models
                        if hasattr(field_type, "model_fields"):
                            collect_models(field_type)

            # Collect all models
            collect_models(model)

            # Write models in dependency order
            written_models = set()

            def write_model(model_class: Type[BaseModel]) -> None:
                """Write a model and its dependencies."""
                if model_class.__name__ in written_models:
                    return

                # Write dependencies first
                for field in model_class.model_fields.values():
                    field_type = field.annotation
                    if hasattr(field_type, "__origin__") and field_type.__origin__ is list:
                        item_type = field_type.__args__[0]
                        if hasattr(item_type, "__name__") and item_type.__name__ != "Any":
                            write_model(item_type)
                    elif hasattr(field_type, "__name__") and field_type.__name__ != "Any":
                        if hasattr(field_type, "model_fields"):
                            write_model(field_type)

                # Write the model
                f.write(f"class {model_class.__name__}(BaseModel):\n")
                for field_name, field in model_class.model_fields.items():
                    field_type = field.annotation
                    if hasattr(field_type, "__origin__") and field_type.__origin__ is list:
                        item_type = field_type.__args__[0]
                        f.write(f"    {field_name}: List[{item_type.__name__}]\n")
                    else:
                        f.write(f"    {field_name}: {field_type.__name__}\n")
                f.write("\n")
                written_models.add(model_class.__name__)

            # Write all models
            write_model(model)

        console.print(f"[green]Model generated successfully: {output_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error generating model: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(
    input_file: str = typer.Argument(help="Input CSV or JSON file to validate"),
    model: str = typer.Option("--model", "-m", help="Model file path"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file for valid records"
    ),
    type: str = typer.Option("csv", "--type", "-t", help="Input file type (csv or json)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed validation errors"),
    encoding: str = typer.Option("utf-8", "--encoding", "-e", help="File encoding"),
    delimiter: str = typer.Option(",", "--delimiter", help="CSV delimiter"),
):
    """Validate a CSV or JSON file against a Pydantic model."""
    try:
        input_path = _ensure_path(input_file)
        model_path = _ensure_path(model)
        output_path = _ensure_path(output) if output else None

        console.print(
            Panel.fit(
                f"Validating {input_path} against {model_path}...",
                title="Smart Schema",
                border_style="blue",
            )
        )

        # Load model
        import importlib.util

        spec = importlib.util.spec_from_file_location("model_module", model_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find the first BaseModel subclass
        model_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseModel) and attr != BaseModel:
                model_class = attr
                break

        if model_class is None:
            raise ValueError(f"No Pydantic model found in {model_path}")

        # Validate data
        validator = ModelValidator(model_class)

        if type.lower() == "csv":
            import pandas as pd

            df = pd.read_csv(input_path, encoding=encoding, delimiter=delimiter)
            valid_records, invalid_records = validator.validate_dataframe(df)
        elif type.lower() == "json":
            import json

            with open(input_path, encoding=encoding) as f:
                data = json.load(f)
            valid_records, invalid_records = validator.validate_json(data)
        else:
            raise ValueError(f"Unsupported file type: {type}")

        # Generate report
        generate_validation_report(valid_records, invalid_records, output_path)

        if output_path:
            console.print(f"[green]Valid records saved to: {output_path}[/green]")

        if verbose and invalid_records:
            console.print("\n[red]Invalid Records:[/red]")
            for record in invalid_records:
                console.print(f"\nRecord: {record['record']}")
                for error in record["errors"]:
                    console.print(f"  - {error['msg']}")

    except Exception as e:
        console.print(f"[red]Error validating data: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def split(
    input_file: str = typer.Argument(help="Input CSV file to split"),
    rows: Optional[int] = typer.Option(None, "--rows", "-r", help="Number of rows per file"),
    by_column: Optional[str] = typer.Option(None, "--by-column", "-c", help="Column to split by"),
    output: str = typer.Option("--output", "-o", help="Output file prefix"),
    encoding: str = typer.Option("utf-8", "--encoding", "-e", help="File encoding"),
    delimiter: str = typer.Option(",", "--delimiter", help="CSV delimiter"),
):
    """Split a CSV file into multiple files."""
    try:
        input_path = _ensure_path(input_file)

        console.print(
            Panel.fit(
                f"Splitting {input_path}...",
                title="Smart Schema",
                border_style="blue",
            )
        )

        if rows:
            split_by_rows(input_path, rows, output)
        elif by_column:
            split_by_column(input_path, by_column, output)
        else:
            raise ValueError("Either --rows or --by-column must be specified")

        console.print(f"[green]Files split successfully with prefix: {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error splitting file: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def infer_types(
    input_file: str = typer.Argument(help="Input CSV file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output JSON file for types"),
    encoding: str = typer.Option("utf-8", "--encoding", "-e", help="File encoding"),
    delimiter: str = typer.Option(",", "--delimiter", help="CSV delimiter"),
):
    """Infer column types from a CSV file."""
    try:
        input_path = _ensure_path(input_file)
        output_path = _ensure_path(output) if output else None

        console.print(
            Panel.fit(
                f"Inferring types from {input_path}...",
                title="Smart Schema",
                border_style="blue",
            )
        )

        import pandas as pd

        df = pd.read_csv(input_path, encoding=encoding, delimiter=delimiter)
        types = infer_column_types(df)

        if output_path:
            import json

            with open(output_path, "w") as f:
                json.dump(types, f, indent=2)
            console.print(f"[green]Types saved to: {output_path}[/green]")
        else:
            console.print("\n[blue]Inferred Types:[/blue]")
            for column, type_info in types.items():
                console.print(f"  {column}: {type_info}")

    except Exception as e:
        console.print(f"[red]Error inferring types: {str(e)}[/red]")
        raise typer.Exit(1)


def main():
    app()


if __name__ == "__main__":
    main()
