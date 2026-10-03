"""One Spark StructType per data contract used by a rendered job.

Tool-owned and rebuilt whole from the contracts in `contracts/`. Edit the contracts, not
this file.
"""

from pyspark.sql.types import (
    DateType,
    DecimalType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

leadouts_summary_schema = StructType(
    [
        StructField("date_utc", DateType(), nullable=False),
        StructField("shop_id", IntegerType(), nullable=False),
        StructField("leadouts", IntegerType(), nullable=False),
    ]
)

prepare_leadouts_data_schema = StructType(
    [
        StructField("click_id", StringType(), nullable=False),
        StructField("type", StringType(), nullable=True),
        StructField("price", DecimalType(10, 2), nullable=True),
        StructField("shop_id", IntegerType(), nullable=False),
        StructField("date_utc", DateType(), nullable=False),
    ]
)

raw_leadouts_data_schema = StructType(
    [
        StructField("ClickId", StringType(), nullable=False),
        StructField("Type", StringType(), nullable=True),
        StructField("Price", IntegerType(), nullable=True),
        StructField("ShopId", IntegerType(), nullable=False),
        StructField("DateUTC", DateType(), nullable=False),
    ]
)
