"""End-to-end test of the prepare_leadouts_data job on local Spark.

The test runs the job's Glue entry point, run(), which parses its arguments from sys.argv,
reads the job's input rows from tests/fixtures/, which the test writes to disk as the job
reads them, and writes the output. The rows read back must be the job's reviewed output
rows: the expected rows of its last transformation.
"""

import sys
from pathlib import Path

import pytest
from pyspark.sql import SparkSession

from leadouts_test.jobs.prepare_leadouts_data import (
    prepare_leadouts_data as job,
)
from leadouts_test.utils.schema import schema_definitions
from tests.fixtures.prepare_leadouts_data import expected, inputs
from tests.helpers import (
    SourceFixture,
    column_types,
    inputs_message,
    processing_dates,
    review_message,
    row_key,
    rows_to_df,
    write_sources,
)

# How the job reads each source, and the input rows the test writes for it.
SOURCES = {
    "raw_leadouts_data": SourceFixture(
        argument="RAW_LEADOUTS_DATA_INPUT_PATH",
        rows=inputs.RAW_LEADOUTS_DATA_ROWS,
        schema=schema_definitions.raw_leadouts_data_schema,
        file_format="json",
        partition_key="DateUTC",
    ),
}

OUTPUT_SCHEMA = schema_definitions.prepare_leadouts_data_schema


def test_run_end_to_end(
    spark: SparkSession, test_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """run() over the input rows writes exactly the job's reviewed output rows."""
    assert inputs.INPUTS_FILLED, inputs_message("prepare_leadouts_data")
    assert expected.CONVERT_PRICE_TO_EUR_REVIEWED, review_message(
        "prepare_leadouts_data",
        "CONVERT_PRICE_TO_EUR",
    )
    dates = processing_dates(SOURCES)
    output_path = str(test_dir / "output")
    argv = [
        "prepare_leadouts_data.py",
        *write_sources(spark, SOURCES, test_dir / "sources"),
        "--OUTPUT_PATH",
        output_path,
        "--PROCESSING_TYPE",
        "backfill",
        "--START_DATE",
        dates[0],
        "--END_DATE",
        dates[-1],
    ]
    monkeypatch.setattr(sys, "argv", argv)
    job.run()
    df_actual = spark.read.parquet(output_path)
    df_expected = rows_to_df(spark, expected.CONVERT_PRICE_TO_EUR_ROWS, OUTPUT_SCHEMA)
    columns = df_expected.columns
    assert column_types(df_actual.schema) == column_types(df_expected.schema)
    actual = df_actual.select(columns).collect()
    expected_rows = df_expected.collect()
    assert sorted(actual, key=row_key) == sorted(expected_rows, key=row_key)
