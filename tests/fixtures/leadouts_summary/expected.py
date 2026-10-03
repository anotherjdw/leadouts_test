"""Expected output rows of the leadouts_summary transformations.

One list per transformation. `engineering-automation generate expected-outputs` drafts
each empty list from the transformation's description and input rows, without seeing its
code. Check every row, correct it, then set that transformation's REVIEWED flag to True.
Its test fails until you do.
"""

from datetime import date, datetime
from decimal import Decimal

from pyspark.sql import Row

FILTER_LEADOUTS_REVIEWED = True
FILTER_LEADOUTS_ROWS: list[Row] = [
    Row(
        click_id="ClickId_2",
        type="offer",
        price=Decimal("2.00"),
        shop_id=200000,
        date_utc=date(2026, 1, 1),
    ),
    Row(
        click_id="ClickId_3",
        type="offer",
        price=Decimal("3.00"),
        shop_id=300000,
        date_utc=date(2026, 1, 1),
    ),
]

GROUP_LEADOUTS_REVIEWED = True
GROUP_LEADOUTS_ROWS: list[Row] = [
    Row(date_utc=date(2026, 1, 1), shop_id=200000, leadouts=1),
    Row(date_utc=date(2026, 1, 1), shop_id=300000, leadouts=1),
]
