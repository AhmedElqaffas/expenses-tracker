import datetime
import uuid
from dataclasses import dataclass

@dataclass
class Category:
    id: uuid.UUID
    name: str

@dataclass
class Spending:
    amount: float
    item: str
    categories: list[Category]
    date: datetime.date
