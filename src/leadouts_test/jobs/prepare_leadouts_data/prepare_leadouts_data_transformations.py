"""Transformations and run steps of the prepare_leadouts_data ETL job.

parse_arguments, read, transform and write are scaffold-owned: `generate create-job` renders
them from the job spec, and `generate codegen` never changes them. Every other function is a
transformation whose body `generate codegen` writes.
"""

import argparse
import re

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType

from leadouts_test.utils.dataframes import (
    create_pyspark_dataframe,
    validate_pyspark_dataframe,
    write_pyspark_dataframe,
)
from leadouts_test.utils.schema import schema_definitions
from leadouts_test.utils.spark import spark_session


def convert_column_names_to_snake_case(raw_leadouts_data: DataFrame) -> DataFrame:
    """Convert DataFrame column names from camelCase to snake_case.

    Transforms all column names by inserting underscores before uppercase letters
    and converting the entire name to lowercase.

    Args:
        raw_leadouts_data: DataFrame with camelCase column names including
            ClickId, Type, Price, ShopId, and DateUTC.

    Returns:
        DataFrame with the same data but column names converted to snake_case:
            click_id, type, price, shop_id, date_utc.
    """

    def to_snake_case(name: str) -> str:
        s1 = re.sub("([A-Z]+)([A-Z][a-z])", "\\1_\\2", name)
        return re.sub("([a-z\\d])([A-Z])", "\\1_\\2", s1).lower()

    df = raw_leadouts_data
    for col_name in df.columns:
        snake = to_snake_case(col_name)
        df = df.withColumnRenamed(col_name, snake)
    return df


def convert_price_to_eur(convert_column_names_to_snake_case_result: DataFrame) -> DataFrame:
    """Converts the price column from integer cents to EUR decimal values.

    Divides the price column by 100 and casts the result to decimal(10,2),
    preserving all other columns unchanged.

    Args:
        convert_column_names_to_snake_case_result: DataFrame containing click data
            with price expressed as integer cents.

    Returns:
        DataFrame with the price column converted to decimal(10,2) representing
        EUR values (original cents divided by 100).
    """
    return convert_column_names_to_snake_case_result.withColumn(
        "price", (F.col("price") / 100).cast(DecimalType(10, 2))
    )


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse this job's Glue arguments, ignoring the ones Glue adds itself."""
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--RAW_LEADOUTS_DATA_INPUT_PATH", type=str)
    parser.add_argument("--OUTPUT_PATH", type=str)
    parser.add_argument("--PROCESSING_TYPE", type=str)
    parser.add_argument("--LOOKBACK_DAYS", type=int)
    parser.add_argument("--START_DATE", type=str)
    parser.add_argument("--END_DATE", type=str)
    parser.add_argument("--JOB_NAME", type=str)
    parser.add_argument("--JOB_RUN_ID", type=str)
    parser.add_argument("--environment", type=str)
    return parser.parse_known_args(argv)[0]


def read(args: argparse.Namespace, processing_dates: list[str]) -> dict[str, DataFrame]:
    """Read every source for the processing dates; an empty source fails unless allowed."""
    spark = spark_session()
    sources = {
        "raw_leadouts_data": create_pyspark_dataframe(
            spark=spark,
            file_path=args.RAW_LEADOUTS_DATA_INPUT_PATH,
            schema=schema_definitions.raw_leadouts_data_schema,
            file_format="json",
            date_ranges=processing_dates,
            partition_key="DateUTC",
        ),
    }
    if sources["raw_leadouts_data"].isEmpty():
        raise ValueError(
            f"Source 'raw_leadouts_data' read no rows for {processing_dates}. "
            "To allow this, set allow_empty: true on this source in "
            "prepare_leadouts_data.yaml."
        )
    return sources


def transform(raw_leadouts_data: DataFrame) -> DataFrame:
    """Run the transformations in dependency order and return the job's output."""
    convert_column_names_to_snake_case_result = convert_column_names_to_snake_case(
        raw_leadouts_data,
    )
    convert_price_to_eur_result = convert_price_to_eur(convert_column_names_to_snake_case_result)
    return convert_price_to_eur_result


def write(output: DataFrame, output_file_path: str) -> None:
    """Check the output against its contract, then write it as parquet."""
    output = output.persist()
    try:
        validate_pyspark_dataframe(
            output,
            schema_definitions.prepare_leadouts_data_schema,
            unique_key=["click_id"],
        )
        write_pyspark_dataframe(
            output_dataframe=output,
            output_file_path=output_file_path,
            file_format="parquet",
            partition_key="date_utc",
        )
    finally:
        output.unpersist()
