import argparse
import datetime
import os
import uuid
from dataclasses import dataclass

import psycopg
from dotenv import load_dotenv

load_dotenv()
db_connection_string = os.environ.get("DB_CONNECTION_STRING")

@dataclass
class Spending:
    amount: float
    item: str
    categories: list[str]
    date: datetime.date


def get_available_categories():
    with psycopg.connect(db_connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT name FROM categories
            """)
            # map tuples to category names
            categories = sorted([c[0] for c in cur.fetchall()])
        conn.close()
    return categories

def setup_parser():
    parser = argparse.ArgumentParser(
        prog='Spendings Tracker',
        description='Saves your spendings to a sql database',
        add_help=True)
    parser.add_argument("amount", help="Amount of the spending")
    parser.add_argument("item", help="The item paid for")
    parser.add_argument("categories", help="Categories of the spending", nargs='+', choices=categories,
                        type=lambda s: s.lower())  # allow uppercase
    parser.add_argument("-d", "--date", help="Date of the spending in MM-YYYY or DD-MM-YYYY format",
                        required=False, default=datetime.datetime.now().strftime("%d-%m-%Y"))
    return parser

def parse(parser: argparse.ArgumentParser) -> Spending:
    args = parser.parse_args()
    amount = float(args.amount)
    item = args.item
    categories = args.categories
    # get date
    try:
        date = datetime.datetime.strptime(args.date, "%d-%m-%Y")
    except ValueError:
        try:
            date = datetime.datetime.strptime(args.date, "%m-%Y")
        except ValueError:
            print(f"{args.date} does not match MM-YYYY or DD-MM-YYYY format")
            exit(1)
    return Spending(amount=amount, item=item, categories=categories, date=date)

def store(spending: Spending):
    spending_id = uuid.uuid4()
    amount = spending.amount
    item = spending.item
    categories = spending.categories
    date = spending.date
    print("Recording the following spending:")
    print(f"\tPaid {amount} on {date.day}-{date.month}-{date.year} for {item}. #{(' #'.join(categories))}")
    with psycopg.connect(db_connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO spendings (id, amount, item, date) VALUES (%s, %s, %s, %s)
            """, (spending_id, amount, item, date)
                        )
            categories_placeholder = ', '.join(['%s'] * len(categories))
            cur.execute(f"""
            SELECT id FROM categories
            WHERE name IN ({categories_placeholder})
            """, categories)
            categories_id = [c[0] for c in cur.fetchall()]

            for category_id in categories_id:
                cur.execute("""
                INSERT INTO spendings_categories (spending, category) VALUES (%s, %s)
                """, (spending_id, category_id)
                            )
        conn.commit()
        conn.close()

print("Fetching spending categories...")
categories = get_available_categories()
parser = setup_parser()
spending: Spending = parse(parser)
store(spending)

