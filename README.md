# Smart Schema: Intelligent Pydantic Model Generation and Data Validation

**Smart Schema is a Python library designed to simplify and accelerate the process of data schema definition and validation. It empowers you to automatically generate Pydantic models from various data sources and validate your data against these models with ease.**

Whether you're working with CSVs, JSON data, or need to define schemas from textual descriptions, Smart Schema provides intuitive tools to streamline your data workflows. With optional OpenAI integration, it can infer sophisticated schemas, including nested structures and appropriate data types, saving you significant development time.

## Key Features

*   **Pydantic Model Generation**:
    *   From **Pandas DataFrames**: Infer schemas directly from your tabular data.
    *   From **JSON Data/Files**: Create models based on JSON objects or files.
    *   From **Field Descriptions**: Generate models programmatically by describing your fields (name, description, nullability).
*   **Intelligent Schema Inference**:
    *   Leverage **OpenAI (GPT models)** for advanced schema inference, including type detection, nested structures, and field descriptions.
    *   Reliable basic inference as a fallback when OpenAI is not used.
*   **Comprehensive Data Validation**:
    *   Validate Pandas DataFrames against generated Pydantic models.
    *   Validate individual data records (dictionaries).
*   **Utility Functions**:
    *   **Save Models**: Persist generated Pydantic models to Python files, including all necessary imports (e.g., `datetime`, `List`, `Optional`).
    *   **Load & Validate JSON**: A convenience function to load a JSON file (e.g., configuration) and validate it against a model in one step.
*   **Command-Line Interface (CLI)**:
    *   Generate models and validate data directly from your terminal.
    *   Includes CSV splitting capabilities.
*   **Customizable**: Handle datetime columns, CSV delimiters, encodings, and more.

## Installation

You can install Smart Schema using pip. Ensure you have Python 3.8+ installed.

```bash
pip install smart-schema
```
For OpenAI-powered smart inference, you'll also need the `openai` library:
```bash
pip install openai
```

## Quickstart

Here's a glimpse of how you can use Smart Schema:

First, we'll import the necessary modules from `smart-schema` and other standard libraries.
```python
import pandas as pd
from smart_schema import ModelGenerator, ModelValidator, save_model_to_file, load_and_validate_json_as_model
from pathlib import Path
from pydantic import BaseModel # For type hinting if needed
from typing import Type # For type hinting
```

**1. Generate a Model from a Pandas DataFrame**

You can create a Pydantic model directly from a Pandas DataFrame. Smart Schema will infer the data types. Here, `smart_inference=False` means we are using the basic inference. Set it to `True` to use OpenAI's capabilities (requires an API key).

```python
# --- 1. Generate a Model from a Pandas DataFrame ---
data = {'id': [1, 2], 'name': ['Product A', 'Product B'], 'price': [10.99, None]}
df = pd.DataFrame(data)

# Initialize generator (smart_inference=True uses OpenAI if API key is set)
generator = ModelGenerator(name="Product", smart_inference=False) # Set to True for OpenAI
product_model_df = generator.from_dataframe(df)

print("\n--- Generated Model from DataFrame ---")
print(product_model_df.model_json_schema())
```

**2. Generate a Model from JSON Data**

Similarly, you can generate a model from a Python dictionary (representing JSON data).

```python
# --- 2. Generate a Model from JSON Data ---
json_data = {
    "order_id": "ORD123",
    "customer": {"name": "Jane Doe", "email": "jane@example.com"},
    "items": [{"item_id": "ITEM001", "quantity": 2, "price_per_item": 5.00}]
}
json_model_generator = ModelGenerator(name="Order", smart_inference=False) # Set to True for OpenAI
order_model_json = json_model_generator.from_json(json_data)

print("\n--- Generated Model from JSON ---")
print(order_model_json.model_json_schema())
```

**3. Generate a Model from Field Descriptions (with Smart Inference)**

Smart Schema can generate Pydantic models from a list of field descriptions. When `smart_inference=True`, it leverages OpenAI to intelligently infer data types and other model characteristics from your textual descriptions. This is highly effective for creating robust models quickly.

*Note: This feature uses OpenAI when `smart_inference=True`. Ensure your `OPENAI_API_KEY` environment variable is set for the smart inference to utilize the OpenAI API. If the key is not set, the model generation will fall back to basic type inference where possible based on the descriptions, or default to `Any`.*

```python
# --- 3. Generate a Model from Field Descriptions ---
field_descriptions = [
    {"name": "event_id", "description": "Unique event identifier (UUID string)", "nullable": False},
    {"name": "timestamp", "description": "Event occurrence time (ISO format, e.g., 2023-10-26T10:00:00Z)", "nullable": False},
    {"name": "event_type", "description": "Type of event (e.g., 'user_login', 'item_purchase')", "nullable": False},
    {"name": "payload", "description": "Arbitrary event data, can be a nested JSON object", "nullable": True}
]

# Initialize generator with smart_inference=True
desc_model_generator = ModelGenerator(name="EventLog", smart_inference=True, openai_model="gpt-4o-mini") 

# Generate the model
# Ensure OPENAI_API_KEY is set in your environment for this to use OpenAI's full capabilities
event_log_model = desc_model_generator.from_description(field_descriptions) 

print("\n--- Generated Model from Description (Smart Inference) ---")
if event_log_model:
    # You can inspect the model (e.g., print its schema)
    print(event_log_model.model_json_schema())

    # Example usage (assuming OpenAI inferred types like str, datetime, dict):
    # test_event = {
    #     "event_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    #     "timestamp": "2023-10-26T10:00:00Z",
    #     "event_type": "user_login",
    #     "payload": {"user_id": "usr_123", "ip_address": "192.168.1.1"}
    # }
    # validated_event = event_log_model(**test_event)
    # print("\nValidated Event:", validated_event.model_dump_json(indent=2))
else:
    print("Failed to generate model from description. Check API key or fallback behavior.")
```

**4. Save a Generated Model to a Python File**

Once you've generated a model, you can save it as a `.py` file. `smart-schema` ensures all necessary imports (like `datetime`, `List`, `Optional`, and nested models) are included.

```python
# --- 4. Save a Generated Model to File ---
MODELS_DIR = Path("generated_readme_models")
MODELS_DIR.mkdir(exist_ok=True)
product_model_df_file = MODELS_DIR / "product_model_df.py"
save_model_to_file(product_model_df, output_path=str(product_model_df_file), model_name="Product")
print(f"\nProduct model from DataFrame saved to: {product_model_df_file}")
```

**5. Validate Data using `ModelValidator`**

Use `ModelValidator` to check data against your Pydantic models.

*Validating a Pandas DataFrame:*

```python
# --- 5. Validate Data using ModelValidator ---
# Example: Validate the DataFrame used for generation
validator = ModelValidator(product_model_df)
valid_df_records, invalid_df_records = validator.validate_dataframe(df)
print(f"\nDataFrame Validation - Valid: {len(valid_df_records)}, Invalid: {len(invalid_df_records)}")
if invalid_df_records:
    print("First invalid DataFrame record details:", invalid_df_records[0])
```

*Validating a single dictionary record (e.g., an API request payload):*

```python
# Example: Validate a single dictionary record (e.g., an API request)
valid_order_payload = {
    "order_id": "ORD456",
    "customer": {"name": "John Smith", "email": "john@example.com"},
    "items": [{"item_id": "ITEM002", "quantity": 1, "price_per_item": 15.75}]
}
order_validator = ModelValidator(order_model_json) # Use the model generated from JSON
is_valid, errors = order_validator.validate_record(valid_order_payload)
if is_valid:
    print("\nSingle order record is VALID.")
else:
    print("\nSingle order record is INVALID:", errors)
```

**6. Load and Validate a JSON Configuration File**

Smart Schema provides a utility to load a JSON file (like an application configuration) and validate it against a Pydantic model in a single step.

First, let's define a Pydantic model for our configuration and create a dummy JSON file for this example:
```python
# --- 6. Load and Validate a JSON Configuration File ---
# First, create a dummy model class (as if it was loaded from a .py file)
# and a dummy config file for the example.
class AppConfig(BaseModel):
    app_name: str
    version: str
    debug_mode: bool
    port: int

dummy_config_content = '''
{
    "app_name": "MyAwesomeApp",
    "version": "1.0.1",
    "debug_mode": true,
    "port": 8000
}
'''
CONFIG_DIR = Path("temp_config_data")
CONFIG_DIR.mkdir(exist_ok=True)
dummy_config_file = CONFIG_DIR / "sample_config.json"
with open(dummy_config_file, 'w') as f:
    f.write(dummy_config_content)
```

Now, use `load_and_validate_json_as_model`:
```python
print("\n--- Loading and Validating JSON Config File ---")
# loaded_config_model would be the Pydantic model for your config, 
# either defined manually or generated by smart-schema and imported.
loaded_config = load_and_validate_json_as_model(dummy_config_file, AppConfig)
if loaded_config:
    print(f"Config for '{loaded_config.app_name}' v{loaded_config.version} loaded successfully.")
    print(f"Debug mode: {loaded_config.debug_mode}, Port: {loaded_config.port}")
else:
    print("Failed to load or validate config file.")

# Clean up dummy config
dummy_config_file.unlink()
CONFIG_DIR.rmdir()
```

## Smart Inference with OpenAI

To enable smart inference for model generation (`from_dataframe`, `from_json`, `from_description`), set `smart_inference=True` when creating a `ModelGenerator` instance and ensure your `OPENAI_API_KEY` environment variable is set.

```python
generator = ModelGenerator(name="MyModel", smart_inference=True, openai_model="gpt-4o-mini")
# Now, methods like from_dataframe(df) will use OpenAI.
```
You can also pass the `api_key` and `openai_model` parameters directly to the generation methods. Smart Schema uses `gpt-4o-mini` by default for smart inference but can be configured to use other compatible models.

## Command-Line Interface (CLI)

Smart Schema also provides a powerful CLI for quick operations without writing Python scripts.

```bash
# Generate a Pydantic model from a CSV file
smart-schema generate-model data/my_data.csv -o generated_models/my_data_model.py --type csv

# Generate a model from a JSON file, inferring model name from output file
smart-schema generate-model data/my_config.json -o generated_models/my_config_model.py --type json

# Validate a JSON file against a generated Pydantic model
smart-schema validate data/my_config.json -m generated_models/my_config_model.py --type json

# Split a large CSV by number of rows
smart-schema split data/large_data.csv --rows 10000 -o output_chunks/chunk_

# Get help for a specific command
smart-schema generate-model --help
```
*(Note: Ensure your `PATH` includes the directory where pip installs scripts, or use `python -m smart_schema.cli.cli ...`)*

## Use Cases

Smart Schema is versatile and can be applied in various scenarios:

*   **ETL Pipelines**: Validate data integrity at each step of your data extraction, transformation, and loading processes.
*   **API Development**: Enforce request and response schemas for robust API contracts (e.g., with FastAPI, Flask).
*   **Configuration Management**: Ensure application configuration files are correctly structured and typed on startup.
*   **Data Cleaning & Preparation**: Systematically check data consistency during data science and analytics workflows.
*   **Data Migration**: Validate data before and after migrating between different systems or databases.

Refer to the `examples/` directory in the repository for more detailed usage patterns, including:
*   `quickstart.ipynb`: Covers core generation and validation.
*   `integration_quickbook.ipynb`: Demonstrates practical integration scenarios for CSVs, API-like JSON, and configuration files.

## Contributing

Contributions are welcome! If you'd like to contribute, please feel free to fork the repository, make your changes, and submit a pull request. If you find any bugs or have feature suggestions, please open an issue.

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
