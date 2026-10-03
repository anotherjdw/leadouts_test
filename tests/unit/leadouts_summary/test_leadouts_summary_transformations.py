"""Unit tests of the leadouts_summary transformations.

One test per transformation: it runs the transformation on its input rows and compares the
result with its reviewed expected rows, both from this job's modules in tests/fixtures/. An
input that is another transformation's output is that transformation's expected rows.
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DateType,
    DecimalType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from leadouts_test.jobs.leadouts_summary import (
    leadouts_summary_transformations as job,
)
from leadouts_test.utils.schema import schema_definitions
from tests.fixtures.leadouts_summary import expected, inputs
from tests.helpers import (
    column_types,
    review_message,
    row_key,
    rows_to_df,
)

# The output of each transformation that another one takes as input: the columns the job
# spec gives it, all nullable, since the type check below ignores nullable.
FILTER_LEADOUTS_SCHEMA = StructType(
    [
        StructField("click_id", StringType(), nullable=True),
        StructField("type", StringType(), nullable=True),
        StructField("price", DecimalType(10, 2), nullable=True),
        StructField("shop_id", IntegerType(), nullable=True),
        StructField("date_utc", DateType(), nullable=True),
    ]
)


def test_filter_leadouts(spark: SparkSession) -> None:
    """filter_leadouts returns exactly its reviewed expected rows."""
    assert inputs.CONVERT_PRICE_TO_EUR_REVIEWED, review_message(
        "prepare_leadouts_data",
        "CONVERT_PRICE_TO_EUR",
    )
    assert expected.FILTER_LEADOUTS_REVIEWED, review_message("leadouts_summary", "FILTER_LEADOUTS")
    df_actual = job.filter_leadouts(
        rows_to_df(
            spark,
            inputs.PREPARE_LEADOUTS_DATA_ROWS,
            schema_definitions.prepare_leadouts_data_schema,
        ),
    )
    df_expected = rows_to_df(spark, expected.FILTER_LEADOUTS_ROWS, FILTER_LEADOUTS_SCHEMA)
    columns = df_expected.columns
    assert column_types(df_actual.schema) == column_types(df_expected.schema)
    actual = df_actual.select(columns).collect()
    expected_rows = df_expected.collect()
    assert sorted(actual, key=row_key) == sorted(expected_rows, key=row_key)


def test_group_leadouts(spark: SparkSession) -> None:
    """group_leadouts returns exactly its reviewed expected rows."""
    assert inputs.CONVERT_PRICE_TO_EUR_REVIEWED, review_message(
        "prepare_leadouts_data",
        "CONVERT_PRICE_TO_EUR",
    )
    assert expected.GROUP_LEADOUTS_REVIEWED, review_message("leadouts_summary", "GROUP_LEADOUTS")
    df_actual = job.group_leadouts(
        rows_to_df(spark, expected.FILTER_LEADOUTS_ROWS, FILTER_LEADOUTS_SCHEMA),
    )
    df_expected = rows_to_df(
        spark,
        expected.GROUP_LEADOUTS_ROWS,
        schema_definitions.leadouts_summary_schema,
    )
    columns = df_expected.columns
    assert column_types(df_actual.schema) == column_types(df_expected.schema)
    actual = df_actual.select(columns).collect()
    expected_rows = df_expected.collect()
    assert sorted(actual, key=row_key) == sorted(expected_rows, key=row_key)
