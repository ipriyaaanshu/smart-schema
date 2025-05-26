"""
Example of generating a Pydantic model from field definitions.
"""

import sys
from pathlib import Path

import pandas as pd

from smart_schema import CSVAdapter, ModelGenerator


def main():
    """Run the schema generation example."""
    # Create models directory if it doesn't exist
    models_dir = Path(__file__).parent / "generated_models"
    models_dir.mkdir(exist_ok=True)

    # Add models directory to Python path
    sys.path.append(str(models_dir))

    # Create sample DataFrame with example data
    df = pd.DataFrame(
        {
            "username": ["johndoe", "superman"],
            "email": ["john@example.com", "superman@krypton.com"],
            "age": [25, 30],
            "is_active": [True, True],
        }
    )

    # Generate the model using the new structure
    generator = ModelGenerator(name="UserModel")
    model = generator.from_dataframe(df)

    # Save the model to a file
    model_file = models_dir / "user_model.py"
    with open(model_file, "w") as f:
        f.write("from pydantic import BaseModel\n\n")
        f.write(f"class {model.__name__}(BaseModel):\n")
        for field_name, field in model.model_fields.items():
            f.write(f"    {field_name}: {field.annotation.__name__}\n")

    print(f"\nGenerated model file: {model_file}")

    # Demonstrate how to use the generated model
    print("\nYou can now import and use the generated model like this:")
    print("from user_model import UserModel")
    print("user = UserModel(username='johndoe', email='john@example.com', age=25, is_active=True)")


if __name__ == "__main__":
    main()
