"""Integration tests of the leadouts_summary run steps on local Spark.

Each test writes the job's input rows from tests/fixtures/ to disk as the job reads them: in
each source's file format and partition layout. test_transform and test_write compare with
the job's output, the reviewed expected rows of its last transformation.
"""

from datetime import date, timedelta
from pathlib import Path

import pytest
from pyspark.sql import SparkSession

from leadouts_test.jobs.leadouts_summary import (
    leadouts_summary_transformations as job,
)
from leadouts_test.utils.schema import schema_definitions
from tests.fixtures.leadouts_summary import expected, inputs
from tests.helpers import (
    SourceFixture,
    column_types,
    fixture_dates,
    processing_dates,
    review_message,
    row_key,
    rows_to_df,
    write_sources,
)

# How the job reads each source, and the input rows the tests write for it.
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

# The output contract's non-nullable columns.
NOT_NULL_COLUMNS = [
    "date_utc",
    "shop_id",
    "leadouts",
]


def test_read(spark: SparkSession, test_dir: Path) -> None:
    """read() loads every input row of every source, in its contract's column types."""
    assert inputs.CONVERT_PRICE_TO_EUR_REVIEWED, review_message(
        "prepare_leadouts_data",
        "CONVERT_PRICE_TO_EUR",
    )
    args = job.parse_arguments(write_sources(spark, SOURCES, test_dir))
    sources = job.read(args, processing_dates(SOURCES))
    assert set(sources) == set(SOURCES)
    for alias, source in SOURCES.items():
        assert sources[alias].count() == len(source.rows), alias
        assert column_types(sources[alias].schema) == column_types(source.schema), alias


def test_read_no_data_raises(spark: SparkSession, test_dir: Path) -> None:
    """read() fails for a date with no input rows, since a source may not be empty."""
    assert inputs.CONVERT_PRICE_TO_EUR_REVIEWED, review_message(
        "prepare_leadouts_data",
        "CONVERT_PRICE_TO_EUR",
    )
    args = job.parse_arguments(write_sources(spark, SOURCES, test_dir))
    day_before = date.fromisoformat(processing_dates(SOURCES)[0]) - timedelta(days=1)
    with pytest.raises(ValueError, match="read no rows"):
        job.read(args, [day_before.isoformat()])


def test_transform(spark: SparkSession, test_dir: Path) -> None:
    """transform() over the sources read returns the job's reviewed output rows."""
    assert inputs.CONVERT_PRICE_TO_EUR_REVIEWED, review_message(
        "prepare_leadouts_data",
        "CONVERT_PRICE_TO_EUR",
    )
    assert expected.GROUP_LEADOUTS_REVIEWED, review_message("leadouts_summary", "GROUP_LEADOUTS")
    args = job.parse_arguments(write_sources(spark, SOURCES, test_dir))
    df_actual = job.transform(**job.read(args, processing_dates(SOURCES)))
    df_expected = rows_to_df(spark, expected.GROUP_LEADOUTS_ROWS, OUTPUT_SCHEMA)
    columns = df_expected.columns
    assert column_types(df_actual.schema) == column_types(df_expected.schema)
    actual = df_actual.select(columns).collect()
    expected_rows = df_expected.collect()
    assert sorted(actual, key=row_key) == sorted(expected_rows, key=row_key)


def test_write(spark: SparkSession, test_dir: Path) -> None:
    """write() stores the reviewed output rows as parquet with the contract's column types."""
    assert inputs.CONVERT_PRICE_TO_EUR_REVIEWED, review_message(
        "prepare_leadouts_data",
        "CONVERT_PRICE_TO_EUR",
    )
    assert expected.GROUP_LEADOUTS_REVIEWED, review_message("leadouts_summary", "GROUP_LEADOUTS")
    output = rows_to_df(spark, expected.GROUP_LEADOUTS_ROWS, OUTPUT_SCHEMA)
    job.write(output, str(test_dir))
    result = spark.read.parquet(str(test_dir))
    assert column_types(result.schema) == column_types(OUTPUT_SCHEMA)
    assert result.count() == len(expected.GROUP_LEADOUTS_ROWS)
    for column in NOT_NULL_COLUMNS:
        assert result.filter(result[column].isNull()).isEmpty(), column
    # One folder per partition value.
    partition_key = "date_utc"
    folders = sorted(path.name for path in test_dir.iterdir() if path.is_dir())
    dates = fixture_dates(expected.GROUP_LEADOUTS_ROWS, partition_key)
    assert folders == [f"{partition_key}={day}" for day in dates]


def test_write_incorrect_schema(spark: SparkSession, test_dir: Path) -> None:
    """write() refuses output whose column types differ from the output contract's."""
    column, other_type = "date_utc", "string"
    output = spark.createDataFrame([], OUTPUT_SCHEMA)
    output = output.withColumn(column, output[column].cast(other_type))
    with pytest.raises(ValueError, match="Schema validation failed"):
        job.write(output, str(test_dir))
