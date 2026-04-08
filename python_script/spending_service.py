import asyncio
import os
import uuid
from datetime import datetime

import psycopg

from categories_service import CategoriesService
from commands import CommandService, Command, CommandArg, Commands
from model import Category


class SpendingService(CommandService):
    """Responsible for: \n
        - adding a spending
    """

    def __init__(self, categories_service: CategoriesService):
        self.categories_service = categories_service

    def add_spending(self, name: str,
                     amount: float,
                     categories: list[Category],
                     date: datetime = datetime.now().strftime("%d-%m-%Y")):
        """Adds a new spending

        :argument name: the item you paid for
        :argument amount: the amount you paid
        :argument categories: the categories the item belongs to
        :argument date: when you made the payment
        """

        spending_id = uuid.uuid4()
        with psycopg.connect(os.environ["DB_CONNECTION_STRING"]) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                            INSERT INTO spendings (id, amount, item, date) VALUES (%s, %s, %s, %s)
                            """, (spending_id, amount, name, date)
                            )
                for category in categories:
                    cur.execute("""
                    INSERT INTO spendings_categories (spending, category) VALUES (%s, %s)
                    """, (spending_id, category.id)
                                )
            conn.commit()
            conn.close()

    def get_commands(self) -> list[Command]:
        return [
            Command(name=Commands.RECORD_SPENDING,
                    description="Record a spending",
                    args=[
                        CommandArg("item_name",
                                   "the item you paid for",
                                   True),
                        CommandArg("amount",
                                   "the amount you paid",
                                   True),
                        CommandArg("category_name",
                                   "the category this item belongs to",
                                   True,
                                   lambda: [c.name for c in self.categories_service.get_categories()]),
                        CommandArg("date",
                                   "the date you made the payment",
                                   False),
                    ],
                    ),
        ]

    async def execute(self, command: str, args: dict[str, str], app) -> None:
        if command == Commands.RECORD_SPENDING:

            item_name = args.get("item_name")
            amount = float(args.get("amount"))
            date = args.get("date")

            categories: list[Category] = [c for c in self.categories_service.get_categories()
                                          if c.name == args.get("category_name")]

            if not date:
                date = datetime.now()
            else:
                try:
                    date = datetime.strptime(args.get("date"), "%d-%m-%Y")
                except ValueError:
                    try:
                        date = datetime.strptime(args.get("date"), "%m-%Y")
                    except ValueError:
                        print(f"{args.get("date")} does not match MM-YYYY or DD-MM-YYYY format")

            app.text_area.start_loading("Recording spending...")
            await asyncio.to_thread(self.add_spending, item_name, amount, categories, date)
            app.text_area.stop_loading(f"Paid {amount} on {date.day}-{date.month}-{date.year} for {item_name}."
                                       f" #{(' #'.join([c.name for c in categories]))}")
