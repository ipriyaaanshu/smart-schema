# Smart Schema

Smart Schema is a powerful Python package for generating and validating data schemas from various data sources. It provides a flexible and intuitive way to work with structured data, particularly focusing on CSV files and JSON data.

## Features

- **Schema Generation**: Automatically generate Pydantic models from:
  - CSV files
  - JSON data
  - Pandas DataFrames
- **Data Validation**: Validate data against generated schemas
- **CSV Processing**:
  - Split large CSV files
  - Infer column types
  - Validate CSV data
- **Model Management**: Save and load generated models
- **Rich CLI**: User-friendly command-line interface with detailed output

## Installation

### As a Binary (CLI Tool)

```bash
# Using pip
pip install smart-schema

# Using pipx (recommended for CLI tools)
pipx install smart-schema
```

### As a Library

```bash
# Using pip
pip install smart-schema

# Using Poetry
poetry add smart-schema

# From Source
git clone https://github.com/yourusername/smart-schema.git
cd smart-schema
pip install -e .
```

## Command Line Interface

Smart Schema provides a powerful CLI tool for working with data schemas. After installation, you can use the `smart-schema` command.

### Basic Commands

```bash
# Show help and available commands
smart-schema --help

# Show help for a specific command
smart-schema generate-model --help
```

### Generate Models

```bash
# Generate a model from a CSV file
smart-schema generate-model data.csv --output models/product_model.py

# Generate a model with specific datetime columns
smart-schema generate-model data.csv --datetime-columns created_at,updated_at --output models/product_model.py

# Generate a model from JSON data
smart-schema generate-model data.json --type json --output models/order_model.py
```

### Validate Data

```bash
# Validate a CSV file against a model
smart-schema validate data.csv --model models/product_model.py

# Validate and save valid records
smart-schema validate data.csv --model models/product_model.py --output valid_data.csv

# Show detailed validation errors
smart-schema validate data.csv --model models/product_model.py --verbose
```

### Process CSV Files

```bash
# Split a large CSV file into smaller chunks
smart-schema split data.csv --rows 1000 --output split_

# Split a CSV file by column values
smart-schema split data.csv --by-column category --output category_

# Infer column types from a CSV file
smart-schema infer-types data.csv --output types.json
```

### Common Options

```bash
# Show progress bar for long operations
smart-schema generate-model data.csv --progress

# Specify input file encoding
smart-schema generate-model data.csv --encoding utf-8

# Use a different delimiter for CSV files
smart-schema generate-model data.csv --delimiter ";"

# Skip header row in CSV files
smart-schema generate-model data.csv --no-header
```

### Output Formats

```bash
# Save model as Python file (default)
smart-schema generate-model data.csv --output models/product_model.py

# Save model as JSON schema
smart-schema generate-model data.csv --output schema.json --format json

# Save validation report as HTML
smart-schema validate data.csv --model models/product_model.py --output report.html --format html
```

### Examples

1. Generate a model from a CSV file and validate it:
```bash
# Generate model
smart-schema generate-model products.csv --output models/product_model.py

# Validate the same file
smart-schema validate products.csv --model models/product_model.py
```

2. Process a large CSV file:
```bash
# Split into 1000-row chunks
smart-schema split large_file.csv --rows 1000 --output chunks/chunk_

# Generate model from first chunk
smart-schema generate-model chunks/chunk_1.csv --output models/data_model.py

# Validate all chunks
for f in chunks/chunk_*.csv; do
    smart-schema validate "$f" --model models/data_model.py
done
```

3. Work with JSON data:
```bash
# Generate model from JSON
smart-schema generate-model config.json --type json --output models/config_model.py

# Validate JSON data
smart-schema validate data.json --model models/config_model.py --type json
```

## Quickstart

### Basic Usage

```python
from smart_schema import ModelGenerator, ModelValidator

# Generate a model from a CSV file
generator = ModelGenerator(name="Product")
model = generator.from_dataframe(
    df,
    datetime_columns=['last_updated']
)

# Validate data against the model
validator = ModelValidator(model)
valid_records, invalid_records = validator.validate_dataframe(df)
```

### Command Line Interface

```bash
# Generate a model from a CSV file
smart-schema generate-model data.csv --output models/product_model.py

# Validate a CSV file against a model
smart-schema validate data.csv --model models/product_model.py

# Split a large CSV file
smart-schema split data.csv --rows 1000
```

## Detailed Usage

### Generating Models

#### From CSV Files

```python
from smart_schema import ModelGenerator
import pandas as pd

# Read CSV file
df = pd.read_csv('data.csv')

# Generate model
generator = ModelGenerator(name="Product")
model = generator.from_dataframe(
    df,
    datetime_columns=['created_at', 'updated_at']
)

# Save model to file
model_file = "models/product_model.py"
with open(model_file, "w") as f:
    f.write(f"from pydantic import BaseModel\n\n")
    f.write(f"class {model.__name__}(BaseModel):\n")
    for field_name, field in model.model_fields.items():
        f.write(f"    {field_name}: {field.annotation.__name__}\n")
```

#### From JSON Data

```python
from smart_schema import ModelGenerator

# Sample JSON data
json_data = {
    "user": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com"
    },
    "orders": [
        {
            "order_id": "ORD-001",
            "items": [
                {"product_id": "P1", "quantity": 2}
            ]
        }
    ]
}

# Generate model
generator = ModelGenerator(name="OrderSystem")
model = generator.from_json(
    json_data,
    datetime_columns=['order_created_at']
)
```

### Validating Data

```python
from smart_schema import ModelValidator

# Validate DataFrame
validator = ModelValidator(model)
valid_records, invalid_records = validator.validate_dataframe(df)

# Print validation results
print(f"Valid records: {len(valid_records)}")
print(f"Invalid records: {len(invalid_records)}")

if invalid_records:
    print("\nInvalid Records Details:")
    for record in invalid_records:
        print(f"\nRecord: {record['record']}")
        for error in record['errors']:
            print(f"  - {error['msg']}")
```

### Working with CSV Files

#### Splitting Large Files

```python
from smart_schema.adapters.csv_splitter import split_by_rows, split_by_column

# Split by number of rows
split_by_rows(
    "large_file.csv",
    rows_per_file=1000,
    output_prefix="split_"
)

# Split by column value
split_by_column(
    "data.csv",
    column="category",
    output_prefix="category_"
)
```

#### Inferring Column Types

```python
from smart_schema.adapters.csv_inference import infer_column_types
import pandas as pd

df = pd.read_csv("data.csv")
column_types = infer_column_types(df)
print("Inferred column types:", column_types)
```

## Contributing

We welcome contributions! Here's how you can help:

### Setting Up Development Environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/smart-schema.git
   cd smart-schema
   ```