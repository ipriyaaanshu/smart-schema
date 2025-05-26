"""
Example of complex validation combining JSON and DataFrame data.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from smart_schema import CSVAdapter, ModelGenerator, ModelValidator


def main():
    """Run the complex example."""
    # Create models directory if it doesn't exist
    models_dir = Path(__file__).parent / "generated_models"
    models_dir.mkdir(exist_ok=True)

    # Add models directory to Python path
    sys.path.append(str(models_dir))

    # Configuration model from JSON
    config_data = {
        "inventory": {
            "low_stock_threshold": 50,
            "categories": ["Electronics", "Books", "Clothing"],
            "notifications": {"email": "admin@example.com", "enabled": True},
        }
    }

    # Generate configuration model
    config_generator = ModelGenerator(name="InventoryConfig")
    config_model = config_generator.from_json(config_data)

    # Save config model to file
    config_model_file = models_dir / "inventory_config_model.py"
    with open(config_model_file, "w") as f:
        f.write("from pydantic import BaseModel\n")
        f.write("from typing import List\n")
        f.write("from datetime import datetime\n\n")

        f.write("class Notifications(BaseModel):\n")
        f.write("    email: str\n")
        f.write("    enabled: bool\n\n")

        f.write("class Inventory(BaseModel):\n")
        f.write("    low_stock_threshold: int\n")
        f.write("    categories: List[str]\n")
        f.write("    notifications: Notifications\n\n")

        f.write("class InventoryConfig(BaseModel):\n")
        f.write("    inventory: Inventory\n")

    # Product data from DataFrame
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "name": ["Laptop", "Book", "T-shirt", "Phone"],
            "category": ["Electronics", "Books", "Clothing", "Electronics"],
            "stock": [45, 200, 30, 60],
            "price": [999.99, 19.99, 29.99, 699.99],
            "last_updated": pd.to_datetime(
                ["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01"]
            ),
        }
    )

    # Generate product model
    product_generator = ModelGenerator(name="Product")
    product_model = product_generator.from_dataframe(df, datetime_columns=["last_updated"])

    # Save product model to file
    product_model_file = models_dir / "product_model.py"
    with open(product_model_file, "w") as f:
        f.write("from pydantic import BaseModel\n")
        f.write("from datetime import datetime\n\n")
        f.write(f"class {product_model.__name__}(BaseModel):\n")
        for field_name, field in product_model.model_fields.items():
            if field_name == "last_updated":
                f.write(f"    {field_name}: datetime\n")
            else:
                f.write(f"    {field_name}: {field.annotation.__name__}\n")

    print("Generated model files:")
    print(f"- Configuration: {config_model_file}")
    print(f"- Products: {product_model_file}")

    # Load models
    from inventory_config_model import InventoryConfig
    from product_model import Product

    # Validate configuration
    config = InventoryConfig(**config_data)
    print("\nValidated configuration:")
    print(f"Low stock threshold: {config.inventory.low_stock_threshold}")
    print(f"Notification email: {config.inventory.notifications.email}")

    # Validate products
    validator = ModelValidator(Product)
    valid_products, invalid_products = validator.validate_dataframe(df)

    print("\nProduct Validation Results:")
    print(f"Valid products: {len(valid_products)}")
    print(f"Invalid products: {len(invalid_products)}")

    # Check for low stock items
    low_stock_items = [
        product
        for product in valid_products
        if (
            product["category"] in config.inventory.categories
            and product["stock"] < config.inventory.low_stock_threshold
        )
    ]

    if low_stock_items:
        print("\nLow Stock Items:")
        for item in low_stock_items:
            print(f"- {item['name']} (Category: {item['category']}, Stock: {item['stock']})")

    if invalid_products:
        print("\nInvalid Products Details:")
        for product in invalid_products:
            print(f"\nProduct: {product['record']}")
            for error in product["errors"]:
                print(f"  - {error['msg']}")


if __name__ == "__main__":
    main()
