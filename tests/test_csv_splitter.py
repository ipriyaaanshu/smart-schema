from pathlib import Path

import pandas as pd
import pytest

from smart_schema.adapters import csv_splitter


@pytest.fixture(scope="session")
def data_dir():
    data_path = Path("tests/data")
    data_path.mkdir(exist_ok=True)
    return data_path


@pytest.fixture
def sample_csv(data_dir):
    df = pd.DataFrame({"A": [1, 2, 1, 2], "B": ["x", "y", "z", "w"]})
    file_path = data_dir / "test.csv"
    df.to_csv(file_path, index=False)
    return file_path, df


def test_split_by_rows(data_dir, sample_csv):
    file_path, df = sample_csv
    csv_splitter.split_by_rows(str(file_path), 2)
    assert (data_dir / "test_part1.csv").exists()
    assert (data_dir / "test_part2.csv").exists()
    df1 = pd.read_csv(data_dir / "test_part1.csv")
    df2 = pd.read_csv(data_dir / "test_part2.csv")
    assert len(df1) == 2
    assert len(df2) == 2


def test_split_by_column(data_dir, sample_csv):
    file_path, df = sample_csv
    csv_splitter.split_by_column(str(file_path), "A")
    assert (data_dir / "test_A_1.csv").exists()
    assert (data_dir / "test_A_2.csv").exists()
    df1 = pd.read_csv(data_dir / "test_A_1.csv")
    df2 = pd.read_csv(data_dir / "test_A_2.csv")
    assert set(df1["A"]) == {1}
    assert set(df2["A"]) == {2}


def test_split_dataframe_by_row_count():
    df = pd.DataFrame({"A": range(5)})
    splitter = csv_splitter
    chunks = splitter.split_dataframe_by_row_count(splitter, df, 2)
    assert len(chunks) == 3
    assert len(chunks[0]) == 2
    assert len(chunks[1]) == 2
    assert len(chunks[2]) == 1


def test_split_by_column_invalid_column(data_dir, sample_csv):
    file_path, df = sample_csv
    with pytest.raises(ValueError):
        csv_splitter.split_by_column(str(file_path), "C")
