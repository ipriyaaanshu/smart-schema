import os
from pathlib import Path

import pandas as pd
import pytest

from smart_schema.adapters.csv_adapter import CSVAdapter


@pytest.fixture(scope="session")
def data_dir():
    data_path = Path(__file__).parent / "data"
    data_path.mkdir(exist_ok=True)
    return data_path


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})


def test_read_write_csv(data_dir, sample_dataframe):
    adapter = CSVAdapter()
    file_path = data_dir / "test.csv"
    adapter.write_csv(sample_dataframe, str(file_path))
    df_read = adapter.read_csv(str(file_path))
    pd.testing.assert_frame_equal(df_read, sample_dataframe)


def test_read_csv_in_chunks(data_dir, sample_dataframe):
    adapter = CSVAdapter(chunk_size=2)
    file_path = data_dir / "test.csv"
    sample_dataframe.to_csv(file_path, index=False)
    chunks = list(adapter.read_csv_in_chunks(str(file_path)))
    assert len(chunks) == 2
    pd.testing.assert_frame_equal(pd.concat(chunks, ignore_index=True), sample_dataframe)


def test_split_by_rows(data_dir, sample_dataframe):
    adapter = CSVAdapter()
    file_path = data_dir / "test.csv"
    sample_dataframe.to_csv(file_path, index=False)
    output_files = adapter.split_by_rows(str(file_path), 2)
    assert len(output_files) == 2
    df1 = pd.read_csv(output_files[0])
    df2 = pd.read_csv(output_files[1])
    assert len(df1) == 2
    assert len(df2) == 1


def test_split_by_column(data_dir):
    adapter = CSVAdapter()
    df = pd.DataFrame({"A": [1, 2, 1], "B": ["x", "y", "z"]})
    file_path = data_dir / "test.csv"
    df.to_csv(file_path, index=False)
    output_files = adapter.split_by_column(str(file_path), "A")
    assert len(output_files) == 2
    for f in output_files:
        assert Path(f).exists()


def test_split_dataframe(sample_dataframe):
    adapter = CSVAdapter()
    chunks = adapter.split_dataframe(sample_dataframe, 2)
    assert len(chunks) == 2
    assert len(chunks[0]) == 2
    assert len(chunks[1]) == 1


def test_write_chunk_to_file(data_dir, sample_dataframe):
    adapter = CSVAdapter()
    output_path = data_dir / "chunk.csv"
    adapter._write_chunk_to_file(sample_dataframe, output_path)
    df_read = pd.read_csv(output_path)
    pd.testing.assert_frame_equal(df_read, sample_dataframe)
