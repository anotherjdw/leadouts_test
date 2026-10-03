"""End-to-end test of the leadouts_summary job on local Spark.

The test runs the job's Glue entry point, run(), which parses its arguments from sys.argv,
reads the job's input rows from tests/fixtures/, which the test writes to disk as the job
reads them, and writes the output. The rows read back must be the job's reviewed output
rows: the expected rows of its last transformation.
"""

import sys
from pathlib import Path

import pytest
from pyspark.sql import SparkSession

from leadouts_test.jobs.leadouts_summary import (
    leadouts_summary as job,
)
from leadouts_test.utils.schema import schema_definitions
from tests.fixtures.leadouts_summary import expected, inputs
from tests.helpers import (
    SourceFixture,
    column_types,
    processing_dates,
    review_message,
    row_key,
    rows_to_df,
    write_sources,
)

# How the job reads each source, and the input rows the test writes for it.
SOURCES = {
    "prepare_leadouts_data": SourceFixture(
        argument="PREPARE_LEADOUTS_DATA_INPUT_PATH",
        rows=inputs.PREPARE_LEADOUTS_DATA_ROWS,
        schema=schema_definitions.prepare_leadouts_data_schema,
        file_format="parquet",
        partition_key="date_utc",
    ),
}

OUTPUT_SCHEMA = schema_definitions.leadouts_summary_schema


def test_run_end_to_end(
    spark: SparkSession, test_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """run() over the input rows writes exactly the job's reviewed output rows."""
    assert inputs.CONVERT_PRICE_TO_EUR_REVIEWED, review_message(
        "prepare_leadouts_data",
        "CONVERT_PRICE_TO_EUR",
    )
    assert expected.GROUP_LEADOUTS_REVIEWED, review_message("leadouts_summary", "GROUP_LEADOUTS")
    dates = processing_dates(SOURCES)
    output_path = str(test_dir / "output")
    argv = [
        "leadouts_summary.py",
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
    df_expected = rows_to_df(spark, expected.GROUP_LEADOUTS_ROWS, OUTPUT_SCHEMA)
    columns = df_expected.columns
    assert column_types(df_actual.schema) == column_types(df_expected.schema)
    actual = df_actual.select(columns).collect()
    expected_rows = df_expected.collect()
    assert sorted(actual, key=row_key) == sorted(expected_rows, key=row_key)
