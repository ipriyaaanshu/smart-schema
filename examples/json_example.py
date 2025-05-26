"""
Example of generating a model from JSON data.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from smart_schema import ModelGenerator, ModelValidator


def main():
    """Run the JSON example."""
    # Create models directory if it doesn't exist
    models_dir = Path(__file__).parent / "generated_models"
    models_dir.mkdir(exist_ok=True)

    # Add models directory to Python path
    sys.path.append(str(models_dir))

    # Sample JSON data with nested structures
    json_data = {
        "user": {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "is_active": True,
            "preferences": {"theme": "dark", "notifications": True},
        },
        "orders": [
            {
                "order_id": "ORD-001",
                "items": [{"product_id": "P1", "quantity": 2}, {"product_id": "P2", "quantity": 1}],
                "total": 99.99,
                "created_at": "2024-03-20T10:00:00",
            }
        ],
        "metadata": {"created_at": "2024-03-20", "version": "1.0"},
    }

    # Generate model using the new structure
    generator = ModelGenerator(name="OrderSystem")
    model = generator.from_json(
        json_data, datetime_columns=["order_created_at", "metadata_created_at"]
    )

    # Save model to file with proper nested structure
    model_file = models_dir / "order_system_model.py"
    with open(model_file, "w") as f:
        f.write("from pydantic import BaseModel\n")
        f.write("from typing import List, Dict\n")
        f.write("from datetime import datetime\n\n")

        # Write nested models
        f.write("class UserPreferences(BaseModel):\n")
        f.write("    theme: str\n")
        f.write("    notifications: bool\n\n")

        f.write("class User(BaseModel):\n")
        f.write("    id: int\n")
        f.write("    name: str\n")
        f.write("    email: str\n")
        f.write("    is_active: bool\n")
        f.write("    preferences: UserPreferences\n\n")

        f.write("class OrderItem(BaseModel):\n")
        f.write("    product_id: str\n")
        f.write("    quantity: int\n\n")

        f.write("class Order(BaseModel):\n")
        f.write("    order_id: str\n")
        f.write("    items: List[OrderItem]\n")
        f.write("    total: float\n")
        f.write("    created_at: datetime\n\n")

        f.write("class Metadata(BaseModel):\n")
        f.write("    created_at: datetime\n")
        f.write("    version: str\n\n")

        f.write("class OrderSystem(BaseModel):\n")
        f.write("    user: User\n")
        f.write("    orders: List[Order]\n")
        f.write("    metadata: Metadata\n")

    print(f"Generated model file: {model_file}")

    # Load and use the generated model
    from order_system_model import OrderSystem

    # Create an instance
    order_system = OrderSystem(**json_data)
    print("\nValidated JSON data:")
    print(f"User name: {order_system.user.name}")
    print(f"First order total: ${order_system.orders[0].total}")
    print(f"System version: {order_system.metadata.version}")


if __name__ == "__main__":
    main()
