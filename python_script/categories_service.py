import os
import uuid

import psycopg

from commands import CommandService, CommandSpec, ArgSpec, Commands
from model import Category


class CategoriesService(CommandService):
    """Responsible for: \n
        - keeping track of all categories
        - adding/deleting categories
    """

    categories: list[Category]

    def load_categories(self):
        """loads categories from database"""
        with psycopg.connect(os.environ["DB_CONNECTION_STRING"]) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                SELECT id, name FROM categories
                """)
                # map tuples to category
                categories = [Category(id=c[0], name=c[1]) for c in cur.fetchall()]
            conn.close()
        self.categories = categories

    def get_categories(self):
        """Returns list of categories"""
        return self.categories

    def add_category(self, name: str):
        """Adds a new category"""
        category = Category(id=uuid.uuid4(), name=name)
        with psycopg.connect(os.environ["DB_CONNECTION_STRING"]) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                INSERT INTO categories (id, name) VALUES (%s, %s)
                """, (category.id, name))
            conn.commit()
            conn.close()
        self.categories.append(category)

    def remove_category(self, name: str):
        """Removes category by name"""
        # remove from database
        with psycopg.connect(os.environ["DB_CONNECTION_STRING"]) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                            DELETE FROM categories WHERE name = %s
                            """, [name])
            conn.commit()
            conn.close()
        # remove from cache
        self.categories = [c for c in self.categories if c.name != name]

    def get_commands(self) -> list[CommandSpec]:
        return [
            CommandSpec(name=Commands.ADD_CATEGORY,
                        description="Adds a new spending category",
                        args=[
                            ArgSpec("category_name"),
                        ],
                        ),
            CommandSpec(name=Commands.REMOVE_CATEGORY,
                        description="Removes a spending category",
                        args=[
                            ArgSpec("category_name",
                                    lambda categories_service: [c.name for c in categories_service.get_categories()]),
                        ],
                        ),
        ]

    async def execute(self, command: str, args: dict[str, str], app) -> None:
        if command == Commands.ADD_CATEGORY:
            self.add_category(args.get("category_name"))
        elif command == Commands.REMOVE_CATEGORY:
            self.remove_category(args.get("category_name"))
