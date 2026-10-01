"""The SparkSession every job in this project runs on."""

from pyspark.sql import SparkSession


def spark_session() -> SparkSession:
    """Return the active SparkSession, creating one if none exists.

    In Glue this picks up the session Glue has configured. No Hive support is
    enabled: jobs read and write files by path and never use the catalog.

    Returns:
        The active SparkSession.
    """
    return SparkSession.builder.getOrCreate()
