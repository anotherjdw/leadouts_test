"""Input rows for the prepare_leadouts_data tests, one list per source.

Replace the example rows with 3-5 rows that exercise the transformations, then set
INPUTS_FILLED = True. Column names and types follow each source's contract.
"""

from datetime import date, datetime
from decimal import Decimal

from pyspark.sql import Row

INPUTS_FILLED = True

RAW_LEADOUTS_DATA_ROWS = [
    Row(ClickId="ClickId_1", Type="ad", Price=100, ShopId=100000, DateUTC=date(2026, 1, 1)),
    Row(ClickId="ClickId_2", Type="offer", Price=200, ShopId=200000, DateUTC=date(2026, 1, 1)),
    Row(ClickId="ClickId_3", Type="offer", Price=300, ShopId=300000, DateUTC=date(2026, 1, 1)),
]
