import datetime
from dataclasses import dataclass


@dataclass
class Spending:
    amount: float
    item: str
    categories: list[str]
    date: datetime.date
