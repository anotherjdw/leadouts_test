"""Input rows for the leadouts_summary tests, one list per source.

Every source reads another job's output, so its rows are that job's expected output rows,
imported from its fixtures below with their REVIEWED flag. There is nothing to fill in
here; the tests fail until those rows are reviewed.
"""

from datetime import date, datetime
from decimal import Decimal

from pyspark.sql import Row

from tests.fixtures.prepare_leadouts_data.expected import CONVERT_PRICE_TO_EUR_REVIEWED
from tests.fixtures.prepare_leadouts_data.expected import (
    CONVERT_PRICE_TO_EUR_ROWS as PREPARE_LEADOUTS_DATA_ROWS,
)
