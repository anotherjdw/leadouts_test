"""Expected output rows of the prepare_leadouts_data transformations.

One list per transformation. `engineering-automation generate expected-outputs` drafts
each empty list from the transformation's description and input rows, without seeing its
code. Check every row, correct it, then set that transformation's REVIEWED flag to True.
Its test fails until you do.
"""

from datetime import date, datetime
from decimal import Decimal

from pyspark.sql import Row

CONVERT_COLUMN_NAMES_TO_SNAKE_CASE_REVIEWED = True
CONVERT_COLUMN_NAMES_TO_SNAKE_CASE_ROWS: list[Row] = [
    Row(click_id="ClickId_1", type="ad", price=100, shop_id=100000, date_utc=date(2026, 1, 1)),
    Row(click_id="ClickId_2", type="offer", price=200, shop_id=200000, date_utc=date(2026, 1, 1)),
    Row(click_id="ClickId_3", type="offer", price=300, shop_id=300000, date_utc=date(2026, 1, 1)),
]

CONVERT_PRICE_TO_EUR_REVIEWED = True
CONVERT_PRICE_TO_EUR_ROWS: list[Row] = [
    Row(
        click_id="ClickId_1",
        type="ad",
        price=Decimal(1.00),
        shop_id=100000,
        date_utc=date(2026, 1, 1),
    ),
    Row(
        click_id="ClickId_2",
        type="offer",
        price=Decimal(2.00),
        shop_id=200000,
        date_utc=date(2026, 1, 1),
    ),
    Row(
        click_id="ClickId_3",
        type="offer",
        price=Decimal(3.00),
        shop_id=300000,
        date_utc=date(2026, 1, 1),
    ),
]
