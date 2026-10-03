"""Transformations and run steps of the leadouts_summary ETL job.

parse_arguments, read, transform and write are scaffold-owned: `generate create-job` renders
them from the job spec, and `generate codegen` never changes them. Every other function is a
transformation whose body `generate codegen` writes.
"""

import argparse

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from leadouts_test.utils.dataframes import (
    create_pyspark_dataframe,
    validate_pyspark_dataframe,
    write_pyspark_dataframe,
)
from leadouts_test.utils.schema import schema_definitions
from leadouts_test.utils.spark import spark_session


def filter_leadouts(prepare_leadouts_data: DataFrame) -> DataFrame:
    """Filter out rows with specific type values from leadouts data.

    Args:
        prepare_leadouts_data: DataFrame containing leadout records with click_id,
            type, price, shop_id, and date_utc columns.

    Returns:
        DataFrame with the same schema but excluding rows where type is 'ad' or 'rating'.
    """
    return prepare_leadouts_data.filter(~F.col("type").isin("ad", "rating"))


def group_leadouts(filter_leadouts_result: DataFrame) -> DataFrame:
    """Groups leadouts by date_utc and shop_id with a distinct count of click_id.

    Args:
        filter_leadouts_result: DataFrame containing leadout records with click_id,
            type, price, shop_id, and date_utc columns.

    Returns:
        DataFrame grouped by date_utc and shop_id with the distinct count of
        click_id values as the 'leadouts' column.
    """
    return (
        filter_leadouts_result.groupBy("date_utc", "shop_id")
        .agg(F.countDistinct("click_id").cast("int").alias("leadouts"))
        .select("date_utc", "shop_id", "leadouts")
    )


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse this job's Glue arguments, ignoring the ones Glue adds itself."""
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--PREPARE_LEADOUTS_DATA_INPUT_PATH", type=str)
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
        "prepare_leadouts_data": create_pyspark_dataframe(
            spark=spark,
            file_path=args.PREPARE_LEADOUTS_DATA_INPUT_PATH,
            schema=schema_definitions.prepare_leadouts_data_schema,
            file_format="parquet",
            date_ranges=processing_dates,
            partition_key="date_utc",
        ),
    }
    if sources["prepare_leadouts_data"].isEmpty():
        raise ValueError(
            f"Source 'prepare_leadouts_data' read no rows for {processing_dates}. "
            "To allow this, set allow_empty: true on this source in "
            "leadouts_summary.yaml."
        )
    return sources


def transform(prepare_leadouts_data: DataFrame) -> DataFrame:
    """Run the transformations in dependency order and return the job's output."""
    filter_leadouts_result = filter_leadouts(prepare_leadouts_data)
    group_leadouts_result = group_leadouts(filter_leadouts_result)
    return group_leadouts_result


def write(output: DataFrame, output_file_path: str) -> None:
    """Check the output against its contract, then write it as parquet."""
    output = output.persist()
    try:
        validate_pyspark_dataframe(
            output,
            schema_definitions.leadouts_summary_schema,
            unique_key=["date_utc", "shop_id"],
        )
        write_pyspark_dataframe(
            output_dataframe=output,
            output_file_path=output_file_path,
            file_format="parquet",
            partition_key="date_utc",
        )
    finally:
        output.unpersist()
