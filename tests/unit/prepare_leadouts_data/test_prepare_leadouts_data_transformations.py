"""Unit tests of the prepare_leadouts_data transformations.

One test per transformation: it runs the transformation on its input rows and compares the
result with its reviewed expected rows, both from this job's modules in tests/fixtures/. An
input that is another transformation's output is that transformation's expected rows.
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DateType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from leadouts_test.jobs.prepare_leadouts_data import (
    prepare_leadouts_data_transformations as job,
)
from leadouts_test.utils.schema import schema_definitions
from tests.fixtures.prepare_leadouts_data import expected, inputs
from tests.helpers import (
    column_types,
    inputs_message,
    review_message,
    row_key,
    rows_to_df,
)

# The output of each transformation that another one takes as input: the columns the job
# spec gives it, all nullable, since the type check below ignores nullable.
CONVERT_COLUMN_NAMES_TO_SNAKE_CASE_SCHEMA = StructType(
    [
        StructField("click_id", StringType(), nullable=True),
        StructField("type", StringType(), nullable=True),
        StructField("price", IntegerType(), nullable=True),
        StructField("shop_id", IntegerType(), nullable=True),
        StructField("date_utc", DateType(), nullable=True),
    ]
)


def test_convert_column_names_to_snake_case(spark: SparkSession) -> None:
    """convert_column_names_to_snake_case returns exactly its reviewed expected rows."""
    assert inputs.INPUTS_FILLED, inputs_message("prepare_leadouts_data")
    assert expected.CONVERT_COLUMN_NAMES_TO_SNAKE_CASE_REVIEWED, review_message(
        "prepare_leadouts_data",
        "CONVERT_COLUMN_NAMES_TO_SNAKE_CASE",
    )
    df_actual = job.convert_column_names_to_snake_case(
        rows_to_df(
            spark,
            inputs.RAW_LEADOUTS_DATA_ROWS,
            schema_definitions.raw_leadouts_data_schema,
        ),
    )
    df_expected = rows_to_df(
        spark,
        expected.CONVERT_COLUMN_NAMES_TO_SNAKE_CASE_ROWS,
        CONVERT_COLUMN_NAMES_TO_SNAKE_CASE_SCHEMA,
    )
    columns = df_expected.columns
    assert column_types(df_actual.schema) == column_types(df_expected.schema)
    actual = df_actual.select(columns).collect()
    expected_rows = df_expected.collect()
    assert sorted(actual, key=row_key) == sorted(expected_rows, key=row_key)


def test_convert_price_to_eur(spark: SparkSession) -> None:
    """convert_price_to_eur returns exactly its reviewed expected rows."""
    assert inputs.INPUTS_FILLED, inputs_message("prepare_leadouts_data")
    assert expected.CONVERT_PRICE_TO_EUR_REVIEWED, review_message(
        "prepare_leadouts_data",
        "CONVERT_PRICE_TO_EUR",
    )
    df_actual = job.convert_price_to_eur(
        rows_to_df(
            spark,
            expected.CONVERT_COLUMN_NAMES_TO_SNAKE_CASE_ROWS,
            CONVERT_COLUMN_NAMES_TO_SNAKE_CASE_SCHEMA,
        ),
    )
    df_expected = rows_to_df(
        spark,
        expected.CONVERT_PRICE_TO_EUR_ROWS,
        schema_definitions.prepare_leadouts_data_schema,
    )
    columns = df_expected.columns
    assert column_types(df_actual.schema) == column_types(df_expected.schema)
    actual = df_actual.select(columns).collect()
    expected_rows = df_expected.collect()
    assert sorted(actual, key=row_key) == sorted(expected_rows, key=row_key)
