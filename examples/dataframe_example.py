"""
Example of generating a model from a pandas DataFrame.
"""

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from smart_schema import CSVAdapter, ModelGenerator, ModelValidator


def main():
    """Run the DataFrame example."""
    # Create models directory if it doesn't exist
    models_dir = Path(__file__).parent / "generated_models"
    models_dir.mkdir(exist_ok=True)

    # Add models directory to Python path
    sys.path.append(str(models_dir))

    # Create sample DataFrame
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Product A", "Product B", "Product C"],
            "price": [10.99, 20.50, 15.75],
            "stock": [100, 50, 75],
            "is_active": [True, True, False],
            "category": ["Electronics", "Books", "Electronics"],
            "tags": [["new", "sale"], ["bestseller"], ["clearance"]],
            "metadata": [
                {"color": "red", "weight": 1.5},
                {"color": "blue", "weight": 0.8},
                {"color": "black", "weight": 2.0},
            ],
            "last_updated": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
        }
    )

    # Generate model using the new structure
    generator = ModelGenerator(name="Product")
    model = generator.from_dataframe(df, datetime_columns=["last_updated"])

    # Save model to file
    model_file = models_dir / "product_model.py"
    with open(model_file, "w") as f:
        f.write("from pydantic import BaseModel\n")
        f.write("from typing import List, Dict\n")
        f.write("from datetime import datetime\n\n")
        f.write(f"class {model.__name__}(BaseModel):\n")
        for field_name, field in model.model_fields.items():
            if field_name == "last_updated":
                f.write(f"    {field_name}: datetime\n")
            else:
                f.write(f"    {field_name}: {field.annotation.__name__}\n")

    print(f"Generated model file: {model_file}")

    # Load and use the generated model
    from product_model import Product

    # Validate DataFrame against the model
    validator = ModelValidator(Product)
    valid_records, invalid_records = validator.validate_dataframe(df)

    print("\nValidation Results:")
    print(f"Valid records: {len(valid_records)}")
    print(f"Invalid records: {len(invalid_records)}")

    if invalid_records:
        print("\nInvalid Records Details:")
        for record in invalid_records:
            print(f"\nRecord: {record['record']}")
            for error in record["errors"]:
                print(f"  - {error['msg']}")


if __name__ == "__main__":
    main()
