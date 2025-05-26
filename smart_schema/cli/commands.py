"""
Command-line interface commands for Smart Schema.
"""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..adapters.csv_adapter import CSVAdapter
from ..adapters.postgres_adapter import PostgresAdapter
from ..core.model_generator import ModelGenerator
from ..core.model_validator import ModelValidator

app = typer.Typer(
    name="smart-schema",
    help="Generate and validate Pydantic models from structured data",
    add_completion=False,
)
console = Console()


@app.command()
def gen_model(
    input_file: str = typer.Argument(None, help="Path to input CSV file"),
    output_file: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Path to output Python file (default: input_file_model.py)",
    ),
    # PostgreSQL connection options
    pg_table: str = typer.Option(
        None,
        "--pg-table",
        help="Name of the PostgreSQL table to introspect",
    ),
    pg_host: str = typer.Option(
        "localhost",
        "--pg-host",
        help="PostgreSQL host (default: localhost)",
    ),
    pg_port: int = typer.Option(
        5432,
        "--pg-port",
        help="PostgreSQL port (default: 5432)",
    ),
    pg_user: str = typer.Option(
        None,
        "--pg-user",
        help="PostgreSQL username",
    ),
    pg_password: str = typer.Option(
        None,
        "--pg-password",
        help="PostgreSQL password",
    ),
    pg_database: str = typer.Option(
        None,
        "--pg-database",
        help="PostgreSQL database name",
    ),
    pg_schema: str = typer.Option(
        "public",
        "--pg-schema",
        help="PostgreSQL schema (default: public)",
    ),
):
    """Generate a Pydantic model from a CSV file or a PostgreSQL table."""
    if input_file:
        console.print(
            Panel.fit(
                f"Generating model from {input_file}...",
                title="Smart Schema",
                border_style="blue",
            )
        )

        # Generate model from CSV
        csv_adapter = CSVAdapter()
        df = csv_adapter.read_csv(input_file)
        generator = ModelGenerator()
        model = generator.from_dataframe(df)

        # Save model to file
        if output_file is None:
            input_path = Path(input_file)
            output_file = input_path.with_name(f"{input_path.stem}_model.py")

        with open(output_file, "w") as f:
            f.write(f"from pydantic import BaseModel\n\n")
            f.write(f"class {model.__name__}(BaseModel):\n")
            for field_name, field in model.model_fields.items():
                f.write(f"    {field_name}: {field.annotation.__name__}\n")

        console.print(f"[green]Model saved to: {output_file}[/green]")

    elif pg_table and all([pg_user, pg_password, pg_database]):
        console.print(
            Panel.fit(
                f"Generating model from PostgreSQL table '{pg_table}'...",
                title="Smart Schema",
                border_style="blue",
            )
        )

        try:
            # Generate model from PostgreSQL table
            conn_params = {
                "user": pg_user,
                "password": pg_password,
                "host": pg_host,
                "port": pg_port,
                "database": pg_database,
            }

            pg_adapter = PostgresAdapter(conn_params)
            model = asyncio.run(pg_adapter.generate_model_from_table(pg_table, pg_schema))

            # Save model to file
            output_path = output_file or f"{pg_table}_model.py"
            with open(output_path, "w") as f:
                f.write(f"from pydantic import BaseModel\n\n")
                f.write(f"class {model.__name__}(BaseModel):\n")
                for field_name, field in model.model_fields.items():
                    f.write(f"    {field_name}: {field.annotation.__name__}\n")

            console.print(f"[green]Model saved to: {output_path}[/green]")

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            raise typer.Exit(1)
    else:
        console.print(
            "[red]Error: Must specify either a CSV file or PostgreSQL connection parameters (--pg-table, --pg-user, --pg-password, --pg-database)[/red]"
        )
        raise typer.Exit(1)


@app.command()
def validate(
    input_file: str = typer.Argument(..., help="Path to input CSV file"),
    model_file: str = typer.Argument(..., help="Path to Python file containing Pydantic model"),
    output_file: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Path to save valid records (optional)",
    ),
    chunk_size: int = typer.Option(
        1000,
        "--chunk-size",
        "-c",
        help="Number of rows to process at once",
    ),
):
    """Validate CSV data against a Pydantic model."""
    console.print(
        Panel.fit(
            f"Validating {input_file} against {model_file}...",
            title="Smart Schema",
            border_style="blue",
        )
    )

    try:
        # Load model
        import importlib.util

        spec = importlib.util.spec_from_file_location("model", model_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get the first class from the module
        model_class = next(
            (
                getattr(module, name)
                for name in dir(module)
                if isinstance(getattr(module, name), type)
                and issubclass(getattr(module, name), BaseModel)
            ),
            None,
        )

        if not model_class:
            raise ValueError("No Pydantic model found in the specified file")

        # Validate CSV
        csv_adapter = CSVAdapter(chunk_size=chunk_size)
        validator = ModelValidator(model_class)

        valid_records = []
        invalid_records = []

        for chunk in csv_adapter.read_csv_in_chunks(input_file):
            chunk_valid, chunk_invalid = validator.validate_dataframe(chunk)
            valid_records.extend(chunk_valid)
            invalid_records.extend(chunk_invalid)

        # Save valid records if output file specified
        if output_file and valid_records:
            import pandas as pd

            pd.DataFrame(valid_records).to_csv(output_file, index=False)
            console.print(f"[green]Valid records saved to: {output_file}[/green]")

        # Print validation summary
        console.print(f"\n[bold]Validation Summary:[/bold]")
        console.print(f"Total records: {len(valid_records) + len(invalid_records)}")
        console.print(f"Valid records: {len(valid_records)}")
        console.print(f"Invalid records: {len(invalid_records)}")

        if invalid_records:
            console.print("\n[bold]Validation Errors:[/bold]")
            for record in invalid_records[:5]:  # Show first 5 errors
                console.print(f"\nRecord: {record['record']}")
                for error in record["errors"]:
                    console.print(f"  - {error['msg']}")

            if len(invalid_records) > 5:
                console.print(f"\n... and {len(invalid_records) - 5} more errors")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def split(
    input_file: str = typer.Argument(..., help="Path to input CSV file"),
    rows: int = typer.Option(None, "--rows", "-r", help="Number of rows per output file"),
    column: str = typer.Option(None, "--column", "-c", help="Column to split on"),
    output_prefix: str = typer.Option(
        None, "--output-prefix", help="Prefix for output files (optional)"
    ),
):
    """Split a CSV file into multiple files."""
    if not rows and not column:
        console.print("[red]Error: Must specify either --rows or --column[/red]")
        raise typer.Exit(1)
    if rows and column:
        console.print("[red]Error: Specify only one of --rows or --column[/red]")
        raise typer.Exit(1)

    console.print(
        Panel.fit(
            f"Splitting {input_file}...",
            title="Smart Schema",
            border_style="blue",
        )
    )

    try:
        csv_adapter = CSVAdapter()

        if rows:
            output_files = csv_adapter.split_by_rows(input_file, rows, output_prefix)
        else:
            output_files = csv_adapter.split_by_column(input_file, column, output_prefix)

        console.print(f"[green]Split into {len(output_files)} files:[/green]")
        for file in output_files:
            console.print(f"  - {file}")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


def main():
    """Entry point for the CLI."""
    app()
